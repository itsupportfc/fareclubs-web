"""
TBO SSR (Special Service Request) API Schemas

Request and response models for TBO SSR API.
Used to get available baggage, meals, and seat options.
"""

from typing import Annotated

from pydantic import Field

from .base import TBOBaseSchema, TBOError
from .common import Baggage as BaggageModel
from .common import Meal as MealModel
from .common import SeatDynamic as SeatDynamicModel
from .common import SimpleMeal as SimpleMealModel

# ==============================================================================
# SSR REQUEST
# ==============================================================================


class TBOSSRRequest(TBOBaseSchema):
    """TBO SSR API request"""

    EndUserIp: str
    TokenId: str
    TraceId: str
    ResultIndex: str


# ==============================================================================
# SSR RESPONSE
# ==============================================================================


class TBOSSRResponseBody(TBOBaseSchema):
    """Inner response body from TBO SSR API"""

    ResponseStatus: int
    Error: TBOError
    TraceId: str

    # Nested by segment: Baggage[segment_index][option_index]
    Baggage: Annotated[
        list[list[BaggageModel]] | None,
        Field(description=" [ [for outgoing],[for incoming]]", default=None),
    ]
    MealDynamic: Annotated[
        list[list[MealModel]] | None,
        Field(description=" [ [for outgoing],[for incoming]]", default=None),
    ]
    SeatDynamic: Annotated[
        list[SeatDynamicModel] | None,
        Field(description=" [ [for outgoing],[for incoming]]", default=None),
    ]

    Meal: Annotated[
        list[SimpleMealModel] | None,
        Field(description="for Non-LCC flights", default=None),
    ]


class TBOSSRResponse(TBOBaseSchema):
    """TBO SSR API response wrapper"""

    Response: TBOSSRResponseBody
