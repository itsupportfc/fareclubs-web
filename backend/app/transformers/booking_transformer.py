"""Booking confirmation transformer.

Keep booking-confirm parsing here instead of bloating the giant TBOTransformer class.
This transformer converts provider responses into *our* confirmation schemas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.db.models.booking import Booking
from app.domain.booking_enums import (
    BookingLegStatus,
    LegDirection,
    booking_record_status_to_leg_status,
    ticket_status_to_leg_status,
)
from app.schemas.internal.booking import (
    BookingConfirmationLeg,
    ConfirmPassengerInfo,
    FareBreakdownInfo,
    MiniFareRuleInfo,
    SegmentBaggageInfo,
)
from app.schemas.tbo.booking_details import TBOGetBookingDetailsResponse
from app.schemas.tbo.ticket import TBOTicketResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class BookingLegTransformResult:
    leg: BookingConfirmationLeg
    passengers: list[ConfirmPassengerInfo] | None = None


class BookingConfirmationTransformer:
    """Transforms successful provider responses and DB rows into response schemas."""

    def build_from_ticket_response(
        self,
        *,
        ticket_response: TBOTicketResponse,
        leg_direction: LegDirection,
        booking_record_id: int | None = None,
    ) -> BookingLegTransformResult:
        inner = ticket_response.Response.Response
        itinerary = inner.FlightItinerary

        return BookingLegTransformResult(
            leg=BookingConfirmationLeg(
                leg_direction=leg_direction,
                leg_status=ticket_status_to_leg_status(inner.TicketStatus),
                booking_record_id=booking_record_id,
                provider_booking_id=itinerary.BookingId,
                provider_pnr=itinerary.PNR,
                provider_is_lcc=itinerary.IsLCC,
                provider_ticket_status=inner.TicketStatus,
                provider_ssr_denied=inner.SSRDenied,
                provider_ssr_message=inner.SSRMessage,
                provider_price_changed=inner.IsPriceChanged,
                provider_time_changed=inner.IsTimeChanged,
                provider_raw_available=True,
                invoice_no=itinerary.InvoiceNo,
                invoice_amount=itinerary.InvoiceAmount,
                segment_baggage=self._extract_segment_baggage(itinerary),
                fare_breakdown=self._extract_fare_breakdown(itinerary),
                mini_fare_rules=self._extract_mini_fare_rules(itinerary),
            ),
            passengers=self._extract_confirm_passengers(itinerary),
        )

    def build_from_booking_details_response(
        self,
        *,
        details_response: TBOGetBookingDetailsResponse,
        leg_direction: LegDirection,
        provider_ticket_status: int,
        provider_is_lcc: bool,
        booking_record_id: int | None = None,
    ) -> BookingLegTransformResult:
        itinerary = details_response.Response.FlightItinerary
        return BookingLegTransformResult(
            leg=BookingConfirmationLeg(
                leg_direction=leg_direction,
                leg_status=ticket_status_to_leg_status(provider_ticket_status),
                booking_record_id=booking_record_id,
                provider_booking_id=itinerary.BookingId,
                provider_pnr=itinerary.PNR,
                provider_is_lcc=provider_is_lcc,
                provider_ticket_status=provider_ticket_status,
                provider_raw_available=True,
                invoice_no=itinerary.InvoiceNo,
                invoice_amount=itinerary.InvoiceAmount,
                segment_baggage=self._extract_segment_baggage(itinerary),
                fare_breakdown=self._extract_fare_breakdown(itinerary),
                mini_fare_rules=self._extract_mini_fare_rules(itinerary),
            ),
            passengers=self._extract_confirm_passengers(itinerary),
        )

    def build_from_booking_record(
        self, *, booking: Booking
    ) -> BookingLegTransformResult:
        """Used for idempotent duplicate-confirm retries.

        It reads enough from our DB to rebuild a stable response even if the original
        API call already finished earlier.
        """

        payload = booking.provider_raw or {}
        itinerary = self._extract_itinerary_from_raw(payload)

        return BookingLegTransformResult(
            leg=BookingConfirmationLeg(
                leg_direction=LegDirection(booking.direction),
                leg_status=booking_record_status_to_leg_status(booking.status),
                booking_record_id=booking.id,
                provider_booking_id=(
                    booking.provider_booking_id
                    if booking.provider_booking_id > 0
                    else None
                ),
                provider_pnr=booking.pnr,
                provider_is_lcc=booking.is_lcc,
                provider_ticket_status=booking.ticket_status,
                provider_raw_available=bool(booking.provider_raw),
                invoice_no=getattr(itinerary, "InvoiceNo", None) if itinerary else None,
                invoice_amount=getattr(itinerary, "InvoiceAmount", None)
                if itinerary
                else None,
                segment_baggage=self._extract_segment_baggage(itinerary)
                if itinerary
                else None,
                fare_breakdown=self._extract_fare_breakdown(itinerary)
                if itinerary
                else None,
                mini_fare_rules=self._extract_mini_fare_rules(itinerary)
                if itinerary
                else None,
            ),
            passengers=self._extract_confirm_passengers_from_booking_record(booking),
        )

    def build_failed_leg(
        self,
        *,
        leg_direction: LegDirection,
        booking_record_id: int | None,
        provider_is_lcc: bool,
        customer_message: str,
        provider_ticket_status: int | None = None,
    ) -> BookingLegTransformResult:
        return BookingLegTransformResult(
            leg=BookingConfirmationLeg(
                leg_direction=leg_direction,
                leg_status=(
                    ticket_status_to_leg_status(provider_ticket_status)
                    if provider_ticket_status is not None
                    else BookingLegStatus.PENDING
                ),
                booking_record_id=booking_record_id,
                provider_booking_id=None,
                provider_pnr="PENDING",
                provider_is_lcc=provider_is_lcc,
                provider_ticket_status=provider_ticket_status,
                provider_ssr_denied=False,
                provider_raw_available=False,
                customer_message=customer_message,
            ),
            passengers=None,
        )

    def _extract_confirm_passengers(
        self, itinerary
    ) -> list[ConfirmPassengerInfo] | None:
        passengers_info: list[ConfirmPassengerInfo] = []
        for provider_passenger in itinerary.Passenger or []:
            seat_numbers = None
            if provider_passenger.SegmentAdditionalInfo:
                seat_numbers = [
                    segment.Seat if getattr(segment, "Seat", None) else None
                    for segment in provider_passenger.SegmentAdditionalInfo
                ]
            ticket_number = (
                provider_passenger.Ticket.TicketNumber
                if provider_passenger.Ticket
                else None
            )
            passengers_info.append(
                ConfirmPassengerInfo(
                    title=provider_passenger.Title,
                    first_name=provider_passenger.FirstName,
                    last_name=provider_passenger.LastName,
                    pax_type=provider_passenger.PaxType,
                    ticket_number=ticket_number,
                    email=provider_passenger.Email or None,
                    contact_no=provider_passenger.ContactNo or None,
                    seat_numbers=seat_numbers,
                )
            )
        return passengers_info or None

    def _extract_confirm_passengers_from_booking_record(
        self, booking: Booking
    ) -> list[ConfirmPassengerInfo] | None:
        passengers = []
        for passenger in booking.passengers or []:
            passengers.append(
                ConfirmPassengerInfo(
                    title=passenger.title,
                    first_name=passenger.first_name,
                    last_name=passenger.last_name,
                    pax_type=passenger.pax_type,
                    ticket_number=passenger.ticket_number,
                    email=passenger.email,
                    contact_no=passenger.contact_no,
                    seat_numbers=passenger.seat_numbers,
                )
            )
        return passengers or None

    def _extract_segment_baggage(self, itinerary) -> list[SegmentBaggageInfo] | None:
        segment_baggage = []
        first_passenger = itinerary.Passenger[0] if itinerary.Passenger else None
        if first_passenger and first_passenger.SegmentAdditionalInfo:
            for segment_info in first_passenger.SegmentAdditionalInfo:
                segment_baggage.append(
                    SegmentBaggageInfo(
                        fare_basis=segment_info.FareBasis,
                        baggage=segment_info.Baggage,
                        cabin_baggage=segment_info.CabinBaggage,
                        meal=segment_info.Meal or None,
                    )
                )
        return segment_baggage or None

    def _extract_fare_breakdown(self, itinerary) -> FareBreakdownInfo | None:
        fare = getattr(itinerary, "Fare", None)
        if fare is None:
            return None
        tax_breakup = None
        if fare.TaxBreakup:
            tax_breakup = [
                {"key": item.key, "value": item.value} for item in fare.TaxBreakup
            ]
        return FareBreakdownInfo(
            currency=fare.Currency or "INR",
            base_fare=fare.BaseFare or 0,
            tax=fare.Tax or 0,
            total_fare=(
                fare.PublishedFare
                if fare.PublishedFare is not None
                else (fare.BaseFare or 0) + (fare.Tax or 0)
            ),
            tax_breakup=tax_breakup,
        )

    def _extract_mini_fare_rules(self, itinerary) -> list[MiniFareRuleInfo] | None:
        mini_fare_rules: list[MiniFareRuleInfo] = []
        if itinerary.MiniFareRules:
            for rule_block in itinerary.MiniFareRules:
                if isinstance(rule_block, list):
                    for rule in rule_block:
                        if isinstance(rule, dict):
                            mini_fare_rules.append(
                                MiniFareRuleInfo(
                                    journey_points=rule.get("JourneyPoints", ""),
                                    type=rule.get("Type", ""),
                                    details=rule.get("Details"),
                                )
                            )
                elif isinstance(rule_block, dict):
                    mini_fare_rules.append(
                        MiniFareRuleInfo(
                            journey_points=rule_block.get("JourneyPoints", ""),
                            type=rule_block.get("Type", ""),
                            details=rule_block.get("Details"),
                        )
                    )
        return mini_fare_rules or None

    def _extract_itinerary_from_raw(self, raw: dict):
        """Rehydrate provider_raw into a real Pydantic itinerary.

        booking_service stores two shapes in provider_raw:
        - Ticket flow:   TBOTicketResponse.model_dump(mode="json")
                         → itinerary lives at .Response.Response.FlightItinerary
                           (TicketItinerary)
        - Recovery flow: TBOGetBookingDetailsResponse.model_dump(mode="json")
                         → itinerary lives at .Response.FlightItinerary
                           (BookingFlightItinerary)

        Both itinerary types expose the attributes the downstream extract
        helpers depend on:
            .Passenger[*].SegmentAdditionalInfo, .Passenger[*].Ticket,
            .Fare, .MiniFareRules, .InvoiceNo, .InvoiceAmount.

        Returning None is safe — every caller already guards with
        `if itinerary else None`.
        """
        try:
            return TBOTicketResponse.model_validate(
                raw
            ).Response.Response.FlightItinerary
        except (ValidationError, AttributeError):
            pass  # fall through to the recovery shape

        try:
            return TBOGetBookingDetailsResponse.model_validate(
                raw
            ).Response.FlightItinerary
        except (ValidationError, AttributeError):
            logger.warning(
                "build_from_booking_record: provider_raw didn't match ticket or "
                "booking-details schema; downstream extractors will see itinerary=None"
            )
            return None
