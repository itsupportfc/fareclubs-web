"""
TBO API Schemas

All schemas for TBO Flight API endpoints.
Field names match TBO JSON exactly (PascalCase).
"""

# Base
# Auth
from .auth import (
    TBOAuthRequest,
    TBOAuthResponse,
    TBOLogoutRequest,
    TBOLogoutResponse,
    TBOMember,
)
from .base import TBOBaseSchema, TBOError

# Book
from .book import (
    BookPassenger,
    # FlightItinerary,
    MealSelection,
    PassengerFare,
    SeatPref,
    TBOBookRequest,
    TBOBookResponse,
)

# Booking Details
from .booking_details import (
    TBOGetBookingDetailsRequest,
    TBOGetBookingDetailsResponse,
)

# Common models
from .common import (
    AirlineInfo,
    AirportInfo,
    Baggage,
    DestinationInfo,
    Fare,
    FareBreakdown,
    FareClassification,
    FareRule,
    KeyValue,
    Meal,
    MiniFareRule,
    OriginInfo,
    # RowSeats,
    Seat,
    SeatDynamic,
    Segment,
    # SegmentSeat,
)

# Enums
from .enums import (
    FlightCabinClass,
    JourneyType,
    PassengerType,
    TripIndicator,
)

# Fare Quote
from .fare_quote import (
    TBOFareQuoteRequest,
    TBOFareQuoteResponse,
    TBOFareQuoteResponseBody,
)

# Fare Rule
from .fare_rule import (
    FareRuleDetail,
    TBOFareRuleRequest,
    TBOFareRuleResponse,
)

# Search
from .search import (
    Itinerary,
    SearchSegment,
    TBOResponseBody,
    TBOSearchRequest,
    TBOSearchResponse,
)

# SSR
from .ssr import (
    TBOSSRRequest,
    TBOSSRResponse,
)

# Ticket
from .ticket import (
    TBOTicketLCCRequest,
    TBOTicketNonLCCRequest,
    TBOTicketResponse,
    TicketItinerary,
)

__all__ = [
    # Base
    "TBOBaseSchema",
    "TBOError",
    # Enums
    "FlightCabinClass",
    "JourneyType",
    "PassengerType",
    "TripIndicator",
    # Common
    "AirlineInfo",
    "AirportInfo",
    "Baggage",
    "DestinationInfo",
    "Fare",
    "FareBreakdown",
    "FareClassification",
    "FareRule",
    "KeyValue",
    "Meal",
    "MiniFareRule",
    "OriginInfo",
    "RowSeats",
    "Seat",
    "SeatDynamic",
    "Segment",
    "SegmentSeat",
    # Auth
    "TBOAuthRequest",
    "TBOAuthResponse",
    "TBOLogoutRequest",
    "TBOLogoutResponse",
    "TBOMember",
    # Search
    "Itinerary",
    "SearchSegment",
    "TBOResponseBody",
    "TBOSearchRequest",
    "TBOSearchResponse",
    # Fare Quote
    "TBOFareQuoteRequest",
    "TBOFareQuoteResponse",
    "TBOFareQuoteResponseBody",
    # Fare Rule
    "FareRuleDetail",
    "TBOFareRuleRequest",
    "TBOFareRuleResponse",
    # SSR
    "TBOSSRRequest",
    "TBOSSRResponse",
    # Book
    "BookPassenger",
    # "FlightItinerary",
    "MealSelection",
    "PassengerFare",
    "SeatPref",
    "TBOBookRequest",
    "TBOBookResponse",
    # Ticket
    "TBOTicketLCCRequest",
    "TBOTicketNonLCCRequest",
    "TBOTicketResponse",
    "TicketItinerary",
    # Booking Details
    "TBOGetBookingDetailsRequest",
    "TBOGetBookingDetailsResponse",
]
