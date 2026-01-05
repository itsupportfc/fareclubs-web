from typing import Annotated, Literal

from app.schemas.internal.base import InternalBaseSchema
from pydantic import Field


class SsrRequest(InternalBaseSchema):
    """Schema for Special service requests"""

    trip_type: Literal["oneway", "roundtrip"]
    fare_id_outbound: str
    fare_id_inbound: Annotated[
        str | None, Field(default=None, description="Required for roundtrip")
    ]
    is_international_return: bool = False


class LccMealOptions(InternalBaseSchema):
    code: str
    description: str
    price: float
    # is_included: bool # needed?
    for_full_journey: bool = False


class BaggageOptions(InternalBaseSchema):
    code: str
    # description: str # needed in case of baggage?
    weight: float
    price: float
    # is_included: bool
    for_full_journey: bool


SeatStatus = Literal["available", "occupied", "blocked", "space"]
SeatType = Literal["window", "aisle", "middle"]


class SeatOptions(InternalBaseSchema):
    code: str
    price: float
    status: SeatStatus
    type: SeatType


class SeatRow(InternalBaseSchema):
    row_number: str
    seats: list[SeatOptions]


class LccSegmentSsrView(InternalBaseSchema):
    flight_number: str
    origin: str
    destination: str
    meal_options: list[LccMealOptions] = Field(default_factory=list)
    baggage_options: list[BaggageOptions] = Field(default_factory=list)
    seat_options: list[SeatRow] = Field(default_factory=list)


class LccSsrView(InternalBaseSchema):
    type: Literal["lcc"] = "lcc"
    segments: list[LccSegmentSsrView]


### NON-LCC SCHEMAS ###


class MealPreference(InternalBaseSchema):
    """Non-LCC meal preference - dietary request (journey-level, free)"""

    code: str
    description: str


class NonLccSegmentSsrView(InternalBaseSchema):
    """Non-LCC segment with baggage and seat options (no meals at segment level)"""

    flight_number: str
    origin: str
    destination: str
    baggage_options: list[BaggageOptions] = Field(default_factory=list)
    seat_options: list[SeatRow] = Field(default_factory=list)


class NonLccSsrView(InternalBaseSchema):
    """SSR view for Non-LCC flights"""

    type: Literal["nonLcc"] = "nonLcc"
    meal_preferences: list[MealPreference] = Field(
        default_factory=list,
        description="In nonLcc meals are paid for "
        "and they are same for both leg and all segments.",
    )
    segments: list[NonLccSegmentSsrView]


class SsrResponse(InternalBaseSchema):
    """Schema for Special service response"""

    outbound: LccSsrView | NonLccSsrView | None = None
    inbound: LccSsrView | NonLccSsrView | None = None
