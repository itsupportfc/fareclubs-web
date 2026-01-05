"""
TBO Fare Rule API Schemas

Request and response models for TBO FareRule API.
Used to get detailed fare rules (cancellation, changes, etc.)
"""

from datetime import datetime

from .base import TBOBaseSchema, TBOError

# ==============================================================================
# FARE RULE REQUEST
# ==============================================================================


class TBOFareRuleRequest(TBOBaseSchema):
    """TBO FareRule API request"""

    EndUserIp: str
    TokenId: str
    TraceId: str
    ResultIndex: str


# ==============================================================================
# FARE RULE RESPONSE
# ==============================================================================


class FareRuleDetail(TBOBaseSchema):
    """Detailed fare rule info"""

    Airline: str
    DepartureTime: datetime | None = None
    Destination: str
    FareBasisCode: str
    FareInclusions: list[str] | None = None
    FareRestriction: str | None = None
    FareRuleDetail: str  # HTML content
    FlightId: int | None = None
    Origin: str
    ReturnDate: datetime | None = None


class TBOFareRuleResponseBody(TBOBaseSchema):
    """Inner response body from TBO FareRule API"""

    ResponseStatus: int
    Error: TBOError
    TraceId: str
    FareRules: list[FareRuleDetail]


class TBOFareRuleResponse(TBOBaseSchema):
    """TBO FareRule API response wrapper"""

    Response: TBOFareRuleResponseBody
