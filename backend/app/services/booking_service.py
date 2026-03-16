import logging
from datetime import date, datetime
from decimal import Decimal

from app.db.models.booking import Booking, BookingPassenger, Payment
from app.schemas.tbo.booking_details import TBOGetBookingDetailsResponse
from app.schemas.tbo.ticket import TBOTicketResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_payment(
        self,
        user_id: int | None,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        amount_paise: int,
    ) -> Payment:
        """Create payment record after Razorpay verification."""
        payment = Payment(
            user_id=user_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            amount_paise=amount_paise,
            status="captured",
        )
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def save_booking(
        self,
        user_id: int | None,
        payment: Payment,
        provider: str,
        ticket_response: TBOTicketResponse,
        direction: str,
        trip_type: str,
        is_lcc: bool,
        linked_booking_id: int | None = None,
    ) -> Booking:
        """Extract relevant data from provider response and persist."""
        logger.info(
            "Persisting booking from ticket response (payment_id=%s, direction=%s, trip_type=%s)",
            payment.id,
            direction,
            trip_type,
        )
        inner = ticket_response.Response.Response
        if inner is None:
            raise ValueError("Cannot save booking: ticket response has no data")

        itinerary = inner.FlightItinerary
        fare = itinerary.Fare

        # Determine status from ticket status
        status = "confirmed" if inner.TicketStatus in (1, 6) else "pending"

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
            status=status,
            ticket_status=inner.TicketStatus,
            currency=fare.Currency,
            base_fare=Decimal(str(fare.BaseFare)),
            tax=Decimal(str(fare.Tax)),
            total_fare=Decimal(str(fare.PublishedFare)),
            is_refundable=not itinerary.NonRefundable,
            provider_raw=ticket_response.model_dump(mode="json"),
        )
        self.db.add(booking)
        await self.db.flush()

        # Create passenger rows
        for pax in itinerary.Passenger:
            ticket_number = None
            if pax.Ticket:
                ticket_number = pax.Ticket.TicketNumber

            dob = pax.DateOfBirth.date() if pax.DateOfBirth else date(2000, 1, 1)

            passenger = BookingPassenger(
                booking_id=booking.id,
                title=pax.Title,
                first_name=pax.FirstName,
                last_name=pax.LastName,
                pax_type=pax.PaxType,
                gender=pax.Gender,
                date_of_birth=dob,
                email=pax.Email or "",
                contact_no=pax.ContactNo or "",
                is_lead_pax=pax.IsLeadPax,
                nationality=pax.Nationality or "",
                passport_no=pax.PassportNo,
                provider_pax_id=pax.PaxId,
                ticket_number=ticket_number,
                base_fare=Decimal(str(pax.Fare.BaseFare)),
                tax=Decimal(str(pax.Fare.Tax)),
            )
            self.db.add(passenger)

        await self.db.flush()
        logger.info(
            "Booking persisted (booking_id=%s, pnr=%s, ticket_status=%s)",
            booking.id,
            booking.pnr,
            inner.TicketStatus,
        )
        return booking

    async def save_booking_from_details(
        self,
        user_id: int | None,
        payment: Payment,
        provider: str,
        details_response: TBOGetBookingDetailsResponse,
        direction: str,
        trip_type: str,
        is_lcc: bool,
        ticket_status: int,
        linked_booking_id: int | None = None,
    ) -> Booking:
        """Persist booking using GetBookingDetails response after timeout recovery."""
        itinerary = details_response.Response.FlightItinerary
        fare = itinerary.Fare
        status = "confirmed" if ticket_status in (1, 6) else "pending"

        logger.info(
            "Persisting booking from GetBookingDetails (payment_id=%s, pnr=%s, booking_id=%s, ticket_status=%s)",
            payment.id,
            itinerary.PNR,
            itinerary.BookingId,
            ticket_status,
        )

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
            status=status,
            ticket_status=ticket_status,
            currency=fare.Currency,
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

        for pax in itinerary.Passenger or []:
            ticket_number = pax.Ticket.TicketNumber if pax.Ticket else None
            dob = pax.DateOfBirth.date() if pax.DateOfBirth else date(2000, 1, 1)
            pax_fare = pax.Fare

            passenger = BookingPassenger(
                booking_id=booking.id,
                title=pax.Title,
                first_name=pax.FirstName,
                last_name=pax.LastName,
                pax_type=pax.PaxType,
                gender=pax.Gender,
                date_of_birth=dob,
                email=pax.Email or "",
                contact_no=pax.ContactNo or "",
                is_lead_pax=pax.IsLeadPax,
                nationality=pax.Nationality or "",
                passport_no=pax.PassportNo,
                provider_pax_id=pax.PaxId,
                ticket_number=ticket_number,
                base_fare=Decimal(
                    str(
                        pax_fare.BaseFare
                        if pax_fare and pax_fare.BaseFare is not None
                        else 0
                    )
                ),
                tax=Decimal(
                    str(pax_fare.Tax if pax_fare and pax_fare.Tax is not None else 0)
                ),
            )
            self.db.add(passenger)

        await self.db.flush()
        logger.info(
            "Recovered booking persisted from GetBookingDetails (booking_id=%s, pnr=%s)",
            booking.id,
            booking.pnr,
        )
        return booking

    async def get_booking_by_id(
        self,
        booking_id: int,
        user_id: int,
    ) -> Booking | None:
        """Fetch a booking by ID for the given user."""
        result = await self.db.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_booking_by_id_and_pnr(
        self,
        booking_id: int,
        pnr: str,
    ) -> Booking | None:
        """Fetch a booking by ID and PNR (for unauthenticated e-ticket download)."""
        result = await self.db.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.pnr == pnr,
            )
        )
        return result.scalar_one_or_none()

    async def save_failed_booking(
        self,
        user_id: int | None,
        payment: Payment,
        provider: str,
        direction: str,
        trip_type: str,
        is_lcc: bool,
        error_message: str,
    ) -> Booking:
        """Save a booking record when ticketing fails (post-payment)."""
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
            is_domestic=True,
            status="pending",
            ticket_status=0,
            base_fare=Decimal("0"),
            tax=Decimal("0"),
            total_fare=Decimal("0"),
            is_refundable=False,
            provider_raw={"error": error_message},
        )
        self.db.add(booking)
        await self.db.flush()
        return booking
