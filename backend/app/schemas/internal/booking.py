"""
Internal Booking Schemas

Frontend-facing schemas for the 2-step booking flow:
  1. POST /flights/booking/create-order  → BookingCreateOrderRequest / BookingCreateOrderResponse
  2. POST /flights/booking/confirm       → BookingConfirmRequest / BookingConfirmResponse
"""

from typing import Literal

from app.schemas.internal.base import InternalBaseSchema


class PassengerFareInfo(InternalBaseSchema):
    """Per-passenger fare details (from fare-quote response)."""

    currency: str = "INR"
    base_fare: float
    tax: float
    yq_tax: float | None = None
    other_charges: float | None = None
    additional_txn_fee_ofrd: float = 0
    additional_txn_fee_pub: float = 0
    pg_charge: float = 0


class SsrSelection(InternalBaseSchema):
    """SSR codes selected by the user (from the SSR endpoint response).
    The transformer enriches these codes into full TBO objects using the cached SSR data.
    """

    meal_code: str | None = None
    meal_description: str | None = None
    seat_code: str | None = None
    seat_description: str | None = None
    baggage_code: str | None = None


class GstInfo(InternalBaseSchema):
    """GST details for B2B invoicing. Only lead passenger carries these."""

    gst_company_name: str
    gst_number: str  # 15-char GSTIN
    gst_company_address: str | None = None
    gst_company_contact_number: str | None = None
    gst_company_email: str | None = None


class PassengerInfo(InternalBaseSchema):
    """Passenger details for booking."""

    title: str
    first_name: str
    last_name: str
    pax_type: int  # 1=Adult, 2=Child, 3=Infant
    date_of_birth: str  # "YYYY-MM-DD"
    gender: int  # 1=Male, 2=Female
    address_line1: str
    city: str
    country_code: str
    nationality: str
    contact_no: str
    email: str
    is_lead_pax: bool
    address_line2: str | None = None
    country_name: str | None = None

    # Passport
    passport_no: str | None = None
    passport_expiry: str | None = None  # "YYYY-MM-DD"
    is_passport_required: bool | None = None
    # Full passport details (when IsPassportRequiredAtTicket=true)
    passport_issue_date: str | None = None  # "YYYY-MM-DD"
    passport_issue_country_code: str | None = None  # 2-letter ISO

    # PAN card (Indian domestic flights when IsPanRequiredAtBook=true)
    pan: str | None = None  # 10-char e.g. "ABCDE1234F"

    # GST (lead pax only, when GSTAllowed=true)
    gst: GstInfo | None = None

    fare: PassengerFareInfo
    ssr: SsrSelection | None = None


# ==============================================================================
# STEP 1: Create Razorpay Order
# ==============================================================================


class BookingCreateOrderRequest(InternalBaseSchema):
    fare_id_outbound: str
    fare_id_inbound: str | None = None
    trip_type: Literal["oneway", "roundtrip"]
    is_international_return: bool = False
    passengers: list[PassengerInfo]
    total_amount: float


class BookingCreateOrderResponse(InternalBaseSchema):
    razorpay_order_id: str
    amount: int  # paise
    currency: str  # "INR"
    razorpay_key_id: str


# ==============================================================================
# STEP 2: Confirm Booking (after payment)
# ==============================================================================


class BookingConfirmRequest(InternalBaseSchema):
    fare_id_outbound: str
    fare_id_inbound: str | None = None
    trip_type: Literal["oneway", "roundtrip"]
    is_international_return: bool = False
    passengers: list[PassengerInfo]
    total_amount: float
    accept_price_change: bool = False
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class ConfirmPassengerInfo(InternalBaseSchema):
    """Passenger info returned in booking confirmation."""

    title: str
    first_name: str
    last_name: str
    pax_type: int  # 1=Adult, 2=Child, 3=Infant
    ticket_number: str | None = None
    email: str | None = None
    contact_no: str | None = None


class SegmentBaggageInfo(InternalBaseSchema):
    """Per-segment baggage info from ticket response."""

    fare_basis: str | None = None
    baggage: str | None = None  # "15 KG"
    cabin_baggage: str | None = None  # "7 KG"


class FareBreakdownInfo(InternalBaseSchema):
    """Overall fare breakdown for the booking."""

    currency: str = "INR"
    base_fare: float
    tax: float
    total_fare: float
    tax_breakup: list[dict] | None = None  # [{key, value}]


class MiniFareRuleInfo(InternalBaseSchema):
    """Mini fare rule (cancellation/reissue policy)."""

    journey_points: str
    type: str  # "Cancellation" | "Reissue"
    details: str | None = None


class BookingConfirmResponse(InternalBaseSchema):
    pnr: str
    booking_id: int
    is_lcc: bool
    ticket_status: int
    ssr_denied: bool
    ssr_message: str | None = None
    invoice_no: str | None = None
    invoice_amount: float | None = None
    pnr_inbound: str | None = None
    booking_id_inbound: int | None = None
    is_price_changed: bool = False
    is_time_changed: bool = False
    status: Literal["confirmed", "pending", "partial"] = "confirmed"
    inbound_status: Literal["confirmed", "failed", "pending"] | None = None
    inbound_error_message: str | None = None
    support_phone: str | None = None
    support_email: str | None = None
    error_message: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_order_id: str | None = None
    passengers: list[ConfirmPassengerInfo] | None = None
    segment_baggage: list[SegmentBaggageInfo] | None = None
    fare_breakdown: FareBreakdownInfo | None = None
    mini_fare_rules: list[MiniFareRuleInfo] | None = None
