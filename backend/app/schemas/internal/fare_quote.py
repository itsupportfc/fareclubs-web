from typing import Literal

from app.schemas.internal.base import InternalBaseSchema
from app.schemas.internal.flight import FareOption
from pydantic import Field


class FareQuoteRequest(InternalBaseSchema):
    """Request for fare quote - handles oneway and roundtrip"""

    trip_type: Literal["oneway", "roundtrip"]

    # Outbound (required)
    fare_id_outbound: str
    initial_price_outbound: float

    # Inbound (required for roundtrip)
    fare_id_inbound: str | None = None
    initial_price_inbound: float | None = None


class FlightPriceDetail(InternalBaseSchema):
    """Price detail for a single flight"""

    original_price: float
    new_price: float
    difference: float


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
