"""Persistence-focused booking service.

This file intentionally does *not* know about HTTP, BackgroundTasks, or cache.
That makes it reusable from API routes, jobs, and admin scripts.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from app.db.models.booking import Booking, BookingPassenger, Payment
from app.domain.booking_enums import (
    BookingRecordStatus,
    PaymentStatus,
    TicketStatus,
    ticket_status_to_booking_record_status,
)
from app.schemas.tbo.booking_details import TBOGetBookingDetailsResponse
from app.schemas.tbo.ticket import TBOTicketResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_captured_payment(
        self,
        *,
        user_id: int | None,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        amount_paise: int,
    ) -> tuple[Payment, bool]:
        """Idempotent payment creation.

        If the payment already exists we return it, which lets confirm_booking become
        safe to retry after mobile refreshes or frontend timeouts.
        """

        result = await self.db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        existing_payment = result.scalar_one_or_none()
        if existing_payment is not None:
            return existing_payment, False

        payment = Payment(
            user_id=user_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            amount_paise=amount_paise,
            status=PaymentStatus.CAPTURED.value,
        )
        self.db.add(payment)
        await self.db.flush()
        return payment, True

    async def save_ticketed_leg(
        self,
        *,
        user_id: int | None,
        payment: Payment,
        provider: str,
        ticket_response: TBOTicketResponse,
        direction: str,
        trip_type: str,
        linked_booking_id: int | None = None,
    ) -> Booking:
        inner = ticket_response.Response.Response
        if inner is None:
            raise ValueError("Ticket response is missing Response.Response")

        itinerary = inner.FlightItinerary
        fare = itinerary.Fare

        booking = Booking(
            user_id=user_id,
            payment_id=payment.id,
            provider=provider,
            provider_booking_id=itinerary.BookingId,
            pnr=itinerary.PNR,
            trip_type=trip_type,
            direction=direction,
            linked_booking_id=linked_booking_id,
            origin=itinerary.Origin,
            destination=itinerary.Destination,
            airline_code=itinerary.AirlineCode,
            is_lcc=itinerary.IsLCC,
            is_domestic=itinerary.IsDomestic,
            status=ticket_status_to_booking_record_status(inner.TicketStatus),
            ticket_status=inner.TicketStatus,
            base_fare=Decimal(str(fare.BaseFare)),
            tax=Decimal(str(fare.Tax)),
            total_fare=Decimal(str(fare.PublishedFare)),
            is_refundable=not itinerary.NonRefundable,
            provider_raw=ticket_response.model_dump(mode="json"),
        )
        self.db.add(booking)
        await self.db.flush()

        await self._persist_passengers(booking=booking, itinerary=itinerary)
        logger.info(
            "Persisted ticketed %s leg (booking_id=%s, provider_booking_id=%s, pnr=%s)",
            direction,
            booking.id,
            booking.provider_booking_id,
            booking.pnr,
        )
        return booking

    async def save_recovered_leg(
        self,
        *,
        user_id: int | None,
        payment: Payment,
        provider: str,
        details_response: TBOGetBookingDetailsResponse,
        direction: str,
        trip_type: str,
        provider_ticket_status: int,
        is_lcc: bool,
        linked_booking_id: int | None = None,
    ) -> Booking:
        itinerary = details_response.Response.FlightItinerary
        fare = itinerary.Fare

        booking = Booking(
            user_id=user_id,
            payment_id=payment.id,
            provider=provider,
            provider_booking_id=itinerary.BookingId,
            pnr=itinerary.PNR,
            trip_type=trip_type,
            direction=direction,
            linked_booking_id=linked_booking_id,
            origin=itinerary.Origin,
            destination=itinerary.Destination,
            airline_code=itinerary.AirlineCode,
            is_lcc=is_lcc,
            is_domestic=itinerary.IsDomestic,
            status=ticket_status_to_booking_record_status(provider_ticket_status),
            ticket_status=provider_ticket_status,
            base_fare=Decimal(str(fare.BaseFare if fare.BaseFare is not None else 0)),
            tax=Decimal(str(fare.Tax if fare.Tax is not None else 0)),
            total_fare=Decimal(
                str(
                    fare.PublishedFare
                    if fare.PublishedFare is not None
                    else (fare.BaseFare or 0) + (fare.Tax or 0)
                )
            ),
            is_refundable=not itinerary.NonRefundable,
            provider_raw=details_response.model_dump(mode="json"),
        )
        self.db.add(booking)
        await self.db.flush()

        await self._persist_passengers(booking=booking, itinerary=itinerary)
        logger.info(
            "Persisted recovered %s leg (booking_id=%s, provider_booking_id=%s, pnr=%s)",
            direction,
            booking.id,
            booking.provider_booking_id,
            booking.pnr,
        )
        return booking

    async def save_failed_leg(
        self,
        *,
        user_id: int | None,
        payment: Payment,
        provider: str,
        direction: str,
        trip_type: str,
        is_lcc: bool,
        error_message: str,
        is_domestic: bool = True,
        parse_error_raw: dict | None = None,
    ) -> Booking:
        """Persist a post-payment failure so ops still has a trackable booking record."""

        booking = Booking(
            user_id=user_id,
            payment_id=payment.id,
            provider=provider,
            provider_booking_id=0,
            pnr="PENDING",
            trip_type=trip_type,
            direction=direction,
            origin="",
            destination="",
            airline_code="",
            is_lcc=is_lcc,
            is_domestic=is_domestic,
            status=(
                BookingRecordStatus.NEEDS_ATTENTION.value
                if parse_error_raw
                else BookingRecordStatus.PENDING.value
            ),
            ticket_status=(
                TicketStatus.PROVIDER_ERROR if parse_error_raw else TicketStatus.PENDING
            ),
            base_fare=Decimal("0"),
            tax=Decimal("0"),
            total_fare=Decimal("0"),
            is_refundable=False,
            provider_raw=parse_error_raw or {"error": error_message},
        )
        self.db.add(booking)
        await self.db.flush()
        return booking

    async def get_booking_by_id_and_pnr(
        self,
        *,
        booking_record_id: int,
        pnr: str,
    ) -> Booking | None:
        result = await self.db.execute(
            select(Booking).where(
                Booking.id == booking_record_id,
                Booking.pnr == pnr,
            )
        )
        return result.scalar_one_or_none()

    async def get_bookings_by_payment(self, payment_id: int) -> list[Booking]:
        result = await self.db.execute(
            select(Booking)
            .options(selectinload(Booking.passengers))
            .where(Booking.payment_id == payment_id)
        )
        return list(result.scalars().all())

    async def get_outbound_booking_by_payment(self, payment_id: int) -> Booking | None:
        result = await self.db.execute(
            select(Booking)
            .options(selectinload(Booking.passengers))
            .where(
                Booking.payment_id == payment_id,
                Booking.direction == "outbound",
            )
        )
        return result.scalar_one_or_none()

    async def _persist_passengers(self, *, booking: Booking, itinerary) -> None:
        for provider_passenger in itinerary.Passenger or []:
            ticket_number = (
                provider_passenger.Ticket.TicketNumber
                if provider_passenger.Ticket
                else None
            )
            seat_numbers = None
            if provider_passenger.SegmentAdditionalInfo:
                seat_numbers = [
                    segment.Seat
                    for segment in provider_passenger.SegmentAdditionalInfo
                    if getattr(segment, "Seat", None)
                ] or None

            passenger = BookingPassenger(
                booking_id=booking.id,
                title=provider_passenger.Title,
                first_name=provider_passenger.FirstName,
                last_name=provider_passenger.LastName,
                pax_type=provider_passenger.PaxType,
                gender=provider_passenger.Gender,
                date_of_birth=(
                    provider_passenger.DateOfBirth.date()
                    if provider_passenger.DateOfBirth
                    else None
                ),
                email=provider_passenger.Email or None,
                contact_no=provider_passenger.ContactNo or None,
                is_lead_pax=provider_passenger.IsLeadPax,
                nationality=provider_passenger.Nationality or None,
                passport_no=provider_passenger.PassportNo,
                provider_pax_id=provider_passenger.PaxId,
                ticket_number=ticket_number,
                seat_numbers=seat_numbers,
                base_fare=Decimal(str(provider_passenger.Fare.BaseFare or 0)),
                tax=Decimal(str(provider_passenger.Fare.Tax or 0)),
            )
            self.db.add(passenger)

        await self.db.flush()
