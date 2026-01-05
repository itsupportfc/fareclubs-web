"""
TBO Fare Quote API Schemas

Request and response models for TBO FareQuote API.
Used to get final pricing after search.
"""

from .base import TBOBaseSchema, TBOError
from .search import Itinerary

# ==============================================================================
# FARE QUOTE REQUEST
# ==============================================================================


class TBOFareQuoteRequest(TBOBaseSchema):
    """TBO FareQuote API request"""

    EndUserIp: str
    TokenId: str
    TraceId: str  # From search response
    ResultIndex: str  # From search response


# ==============================================================================
# FARE QUOTE RESPONSE
# ==============================================================================


class TBOFareQuoteResponseBody(TBOBaseSchema):
    """Inner response body from TBO FareQuote API"""

    ResponseStatus: int
    Error: TBOError
    TraceId: str
    IsPriceChanged: bool
    ItineraryChangeList: list | None = None
    Results: Itinerary  # Single itinerary with updated pricing


class TBOFareQuoteResponse(TBOBaseSchema):
    """TBO FareQuote API response wrapper"""

    Response: TBOFareQuoteResponseBody
