"""
TBO Search API Schemas

Request and response models for TBO Flight Search API.
All field names match TBO JSON exactly (PascalCase).
"""

from datetime import datetime

from .base import TBOBaseSchema, TBOError
from .common import (
    Fare as FareModel,
)
from .common import (
    FareBreakdown as FareBreakdownModel,
)
from .common import FareClassification as FareClassificationModel
from .common import (
    FareRule,
    MiniFareRule,
    Segment,
)
from .enums import FlightCabinClass as FlightCabinClassEnum
from .enums import JourneyType as JourneyTypeEnum

# ==============================================================================
# SEARCH REQUEST
# ==============================================================================


class SearchSegment(TBOBaseSchema):
    """Single segment in search request"""

    Origin: str
    Destination: str
    FlightCabinClass: FlightCabinClassEnum
    # 2015-08-10T00:00:00 for any time
    # 2015-08-10T08:00:00 for Morning Flights
    # 2015-08-10T14:00:00 for Afternoon Flights
    # 2015-08-10T19:00:00 for Evening Flights
    # 2015-08-10T01:00:00 for Night Flights
    PreferredDepartureTime: datetime
    PreferredArrivalTime: datetime | None = None


class TBOSearchRequest(TBOBaseSchema):
    """TBO Search API request"""

    EndUserIp: str
    TokenId: str  # From auth response
    AdultCount: int
    ChildCount: int
    InfantCount: int
    DirectFlight: bool = False
    OneStopFlight: bool = False
    JourneyType: JourneyTypeEnum
    PreferredAirlines: list[str] | None = None  # this filter works only on GDS airlines
    Segments: list[SearchSegment]
    Sources: list[str] | None = None


# ==============================================================================
# SEARCH RESPONSE
# ==============================================================================


class Itinerary(TBOBaseSchema):
    """
    Single flight itinerary (a bookable option).

    This is the core object returned in search results.
    Each Itinerary has its own ResultIndex for booking.
    """

    # Identifiers
    ResultIndex: str  # Main identifier for booking
    Source: int  # Supplier ID (e.g., 6 = Indigo)

    # Carrier info
    AirlineCode: str
    ValidatingAirline: str
    IsLCC: bool  # Low-cost carrier flag

    # Attributes
    IsRefundable: bool
    IsPanRequiredAtBook: bool | None = None
    IsPassportRequiredAtBook: bool | None = None
    IsPassportRequiredAtTicket: bool | None = None
    IsFreeMealAvailable: bool
    GSTAllowed: bool | None = None

    # Pricing
    Fare: FareModel
    FareBreakdown: list[FareBreakdownModel]
    FareClassification: FareClassificationModel | None = None

    ResultFareType: str

    # LastTicketDate: datetime

    # Flight details
    # Segments is nested: Segments[leg_index][segment_index]
    # For one-way: Segments[0] = [seg1, seg2, ...]
    # For return: Segments[0] = outbound, Segments[1] = inbound
    Segments: list[list[Segment]]

    # Rules
    FareRules: list[FareRule]
    MiniFareRules: list[list[MiniFareRule]] | None = None


class TBOResponseBody(TBOBaseSchema):
    """Inner response body from TBO Search API"""

    # [NotSet = 0, Successfull = 1, Failed = 2,
    # InValidRequest = 3, InValidSession = 4,InValidCredentials = 5
    ResponseStatus: int
    Error: TBOError
    TraceId: str  # Valid for ~15 minutes
    Origin: str
    Destination: str
    ResultRecommendationType: int

    # Results is nested: Results[direction_index][itinerary_index]
    # For one-way: Results[0] = [itinerary1, itinerary2, ...]
    # For domestic return: Results[0] = outbound, Results[1] = inbound
    # For international return: Results[0] = combined (check TripIndicator)
    Results: list[list[Itinerary]]


class TBOSearchResponse(TBOBaseSchema):
    """TBO Search API response wrapper"""

    Response: TBOResponseBody
