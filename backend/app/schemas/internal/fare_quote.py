from typing import Literal

from app.schemas.internal.base import InternalBaseSchema
from pydantic import Field


class FareQuoteRequest(InternalBaseSchema):
    """Request for fare quote - handles oneway and roundtrip"""

    trip_type: Literal["oneway", "roundtrip"]
    fare_id_outbound: str
    initial_price_outbound: float
    fare_id_inbound: str | None = None
    initial_price_inbound: float | None = None
    is_international_return: bool = False  # When True, skip inbound TBO call


class FlightPriceDetail(InternalBaseSchema):
    """Price detail for a single flight"""

    original_price: float
    new_price: float
    difference: float


class PerPassengerFare(InternalBaseSchema):
    """Display-only per-head fare summary for one passenger type.

    The full TBO FareBreakdown is cached server-side as `fare_quote_{fare_id}`
    and used directly when building the provider Book/Ticket passenger Fare
    block. The frontend never sends provider fare components back.
    """

    pax_type: int  # 1=Adult, 2=Child, 3=Infant
    currency: str = "INR"
    base_fare: float
    taxes_and_surcharges: float
    total_fare: float


class FareQuoteFlags(InternalBaseSchema):
    """Compliance requirement flags from TBO FareQuote Itinerary.

    Frontend uses these to conditionally show PAN/Passport/GST form fields.
    """

    is_pan_required: bool = False
    is_passport_required: bool = False
    # is_passport_full_detail_required: bool = False
    is_gst_allowed: bool = False
    is_lcc: bool = False


class FareQuoteResponse(InternalBaseSchema):
    """Response for fare quote"""

    is_price_changed: bool = Field(
        description="True if ANY flight price changed beyond tolerance"
    )
    outbound: FlightPriceDetail | None = Field(
        default=None, description="Outbound flight price details (if changed)"
    )
    inbound: FlightPriceDetail | None = Field(
        default=None, description="Inbound flight price details (if changed)"
    )
    message: str = Field(default="", description="Summary message of price changes")

    # Per-passenger fare breakdown for each pax type
    per_passenger_fares_outbound: list[PerPassengerFare] = Field(default_factory=list)
    per_passenger_fares_inbound: list[PerPassengerFare] = Field(default_factory=list)

    # Requirement flags
    flags_outbound: FareQuoteFlags | None = None
    flags_inbound: FareQuoteFlags | None = None

    # Schedule change detection
    is_time_changed_outbound: bool = False
    is_time_changed_inbound: bool = False

    # Authoritative customer-payable totals from the fare-quote PublishedFare.
    # Always populated, regardless of whether the price changed (the
    # is_price_changed / outbound / inbound fields above only fire on user-
    # visible bumps ≥ ₹50). The frontend uses these as the source of truth for
    # outboundSelectedFare.totalPrice / returnSelectedFare.totalPrice so the
    # client-side grand total stays in sync with verified_price_paise_*.
    verified_total_price_outbound: float = Field(
        description="PublishedFare for outbound (customer-payable total, in INR)"
    )
    verified_total_price_inbound: float | None = Field(
        default=None,
        description=(
            "PublishedFare for inbound — set for domestic roundtrip only. "
            "International roundtrip and oneway leave this None (the outbound "
            "value covers the whole booking)."
        ),
    )
