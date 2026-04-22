"""Frontend-facing schemas for booking checkout.

Design goals:
- be explicit about *direction* with outbound_leg / inbound_leg
- be explicit about *ownership* with provider_* vs booking_record_*
- never overload one field with two meanings (the old booking_id bug)
"""

from __future__ import annotations

from app.domain.booking_enums import (
    BookingLegStatus,
    BookingOverallStatus,
    LegDirection,
    TripType,
)
from app.schemas.internal.base import InternalBaseSchema
from pydantic import model_validator


class PassengerFareInfo(InternalBaseSchema):
    """Per-passenger fare details from fare quote."""

    currency: str = "INR"
    base_fare: float
    tax: float
    yq_tax: float | None = None
    other_charges: float | None = None
    additional_txn_fee_ofrd: float = 0
    additional_txn_fee_pub: float = 0
    pg_charge: float = 0


class SsrSelection(InternalBaseSchema):
    """SSR codes selected by the customer for one segment."""

    meal_code: str | None = None
    meal_description: str | None = None
    seat_code: str | None = None
    seat_description: str | None = None
    baggage_code: str | None = None


class GstInfo(InternalBaseSchema):
    gst_company_name: str
    gst_number: str
    gst_company_address: str | None = None
    gst_company_contact_number: str | None = None
    gst_company_email: str | None = None


class PassengerInfo(InternalBaseSchema):
    """Passenger details sent to the backend at confirm time."""

    title: str
    first_name: str
    last_name: str
    pax_type: int
    date_of_birth: str
    gender: int
    address_line1: str
    city: str
    country_code: str
    nationality: str
    contact_no: str
    email: str
    is_lead_pax: bool
    address_line2: str | None = None
    country_name: str | None = None

    passport_no: str | None = None
    passport_expiry: str | None = None
    is_passport_required: bool | None = None
    passport_issue_date: str | None = None
    passport_issue_country_code: str | None = None

    pan: str | None = None
    gst: GstInfo | None = None

    fare: PassengerFareInfo
    ssr: SsrSelection | None = None
    ssr_segments_outbound: list[SsrSelection | None] | None = None
    ssr_segments_inbound: list[SsrSelection | None] | None = None

    @model_validator(mode="after")
    def normalize_legacy_ssr_field(self):
        """Backward compatibility for old frontend payloads.

        If the old single `ssr` field is present, treat it as a one-segment outbound
        SSR selection so old clients do not break instantly.
        """

        if not self.ssr_segments_outbound and self.ssr:
            self.ssr_segments_outbound = [self.ssr]
        return self


class BookingCreateOrderRequest(InternalBaseSchema):
    """Step 1 of checkout: create a Razorpay order for verified fares."""

    fare_id_outbound: str
    fare_id_inbound: str | None = None
    trip_type: TripType = TripType.ONEWAY
    is_international_return: bool = False
    client_total_amount: float

    # Flattened across passengers × segments (order doesn't matter — we just
    # sum prices). Backend uses these + cached raw_ssr to recompute SSR prices
    # server-side so the Razorpay order amount equals fare + tax + SSR.
    ssr_selections_outbound: list[SsrSelection | None] | None = None
    ssr_selections_inbound: list[SsrSelection | None] | None = None


class BookingCreateOrderResponse(InternalBaseSchema):
    """Explicit payment naming so frontend never confuses payment/order IDs."""

    payment_order_id: str
    payment_amount_paise: int
    payment_currency: str
    razorpay_public_key: str
    verified_total_amount: float


class BookingConfirmRequest(InternalBaseSchema):
    """Step 2 of checkout: confirm booking after payment completion."""

    fare_id_outbound: str
    fare_id_inbound: str | None = None
    trip_type: TripType
    is_international_return: bool = False
    passengers: list[PassengerInfo]
    client_total_amount: float
    accept_price_change: bool = False

    payment_order_id: str
    payment_id: str
    payment_signature: str


class ConfirmPassengerInfo(InternalBaseSchema):
    title: str
    first_name: str
    last_name: str
    pax_type: int
    ticket_number: str | None = None
    email: str | None = None
    contact_no: str | None = None
    seat_numbers: list[str | None] | None = None


class SegmentBaggageInfo(InternalBaseSchema):
    fare_basis: str | None = None
    baggage: str | None = None
    cabin_baggage: str | None = None
    meal: str | None = None


class FareBreakdownInfo(InternalBaseSchema):
    currency: str = "INR"
    base_fare: float
    tax: float
    total_fare: float
    tax_breakup: list[dict] | None = None


class MiniFareRuleInfo(InternalBaseSchema):
    journey_points: str
    type: str
    details: str | None = None


class BookingConfirmationLeg(InternalBaseSchema):
    """One leg of the final booking response.

    Naming rules:
    - booking_record_* => our DB row / internal identifiers
    - provider_* => values created by TBO / airline side
    - customer_message => human-readable message safe to show directly in UI
    """

    leg_direction: LegDirection
    leg_status: BookingLegStatus

    booking_record_id: int | None = None
    provider_booking_id: int | None = None
    provider_pnr: str | None = None
    provider_is_lcc: bool | None = None
    provider_ticket_status: int | None = None
    provider_ssr_denied: bool | None = None
    provider_ssr_message: str | None = None
    provider_price_changed: bool = False
    provider_time_changed: bool = False
    provider_raw_available: bool = False

    invoice_no: str | None = None
    invoice_amount: float | None = None
    customer_message: str | None = None

    segment_baggage: list[SegmentBaggageInfo] | None = None
    fare_breakdown: FareBreakdownInfo | None = None
    mini_fare_rules: list[MiniFareRuleInfo] | None = None


class BookingConfirmResponse(InternalBaseSchema):
    """Trip-level booking confirmation response.

    Important: outbound_leg / inbound_leg remove the need for dozens of ambiguous
    *_outbound / *_inbound primitives while staying explicit and frontend-friendly.
    """

    overall_status: BookingOverallStatus
    outbound_leg: BookingConfirmationLeg
    inbound_leg: BookingConfirmationLeg | None = None

    passengers: list[ConfirmPassengerInfo] | None = None

    support_phone: str | None = None
    support_email: str | None = None

    payment_order_id: str | None = None
    payment_id: str | None = None
