"""
Internal Flight Schemas

Frontend-facing schemas for flight search.
Provider-agnostic - works with TBO, Amadeus, etc.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .base import InternalBaseSchema

# ==============================================================================
# TYPE ALIASES
# ==============================================================================

TripType = Literal["oneway", "roundtrip"]
CabinClass = Literal["economy", "premium_economy", "business", "first"]
PassengerType = Literal["adult", "child", "infant"]
Direction = Literal["outbound", "inbound"]


# ==============================================================================
# SEARCH REQUEST
# ==============================================================================


class FlightSearchRequest(InternalBaseSchema):
    """
    Flight search request from frontend.
    Validated and transformed to provider-specific format by backend.
    """

    # Trip details
    trip_type: TripType
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: date
    return_date: date | None = None

    # Passengers
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=8)
    infants: int = Field(default=0, ge=0, le=4)

    # Preferences
    cabin_class: CabinClass = "economy"
    direct_only: bool = False
    preferred_airlines: list[str] | None = None

    # --- Validators ---

    # runs before validation
    @field_validator("origin", "destination", mode="before")
    @classmethod
    def uppercase_airport(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("departure_date")
    @classmethod
    def validate_departure(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Departure date cannot be in the past")
        return v

    @model_validator(mode="after")
    def validate_trip(self) -> "FlightSearchRequest":
        # Roundtrip requires return_date
        if self.trip_type == "roundtrip" and not self.return_date:
            raise ValueError("Return date required for roundtrip")

        # Return must be on or after departure
        if self.return_date and self.return_date < self.departure_date:
            raise ValueError("Return date must be on or after departure date")

        # Infants ≤ Adults (1 infant per adult lap)
        if self.infants > self.adults:
            raise ValueError("Infants cannot exceed adults")

        # Max 9 passengers (adults + children)
        if self.adults + self.children > 9:
            raise ValueError("Maximum 9 passengers allowed")

        # Origin ≠ Destination
        if self.origin == self.destination:
            raise ValueError("Origin and destination must differ")

        return self


# ==============================================================================
# RESPONSE BUILDING BLOCKS
# ==============================================================================


class Airport(InternalBaseSchema):
    """Airport information"""

    code: str
    name: str | None = None
    city: str
    country: str
    terminal: str | None = None


class Airline(InternalBaseSchema):
    """Airline information - frontend constructs logo URL as /static/logos/{code}.png"""

    code: str
    name: str


class FlightSegment(InternalBaseSchema):
    """
    Single flight segment (one takeoff to one landing).
    """

    # Route
    departure: Airport
    arrival: Airport
    departure_time: datetime
    arrival_time: datetime

    # Flight identity
    carrier: Airline
    flight_number: str
    operating_carrier: str | None = None
    aircraft: Annotated[
        str | None,
        Field(
            default=None,
            description="IATA aircraft type code (e.g., '321' for Airbus A321) ",
            examples=["321"],
        ),
    ]

    # Duration
    duration_minutes: int | None = None
    layover_minutes: int | None = None  # null for last segment

    # Baggage
    checked_baggage: str | None = None
    cabin_baggage: str | None = None

    # Class
    cabin_class: CabinClass
    booking_class: str | None = None  # RBD code

    # Direction (for roundtrip)
    # direction: Direction = "outbound" # will be inside outound_flights / inbound_flights

    # Availability
    seats_available: int | None = None

    # what about these?
    # trip_indicator: int # 1=outbound, 2=inbound
    # segment_indicator: int # 1=first, 2=second segment, etc.


class FareBreakdown(InternalBaseSchema):
    """Per passenger type pricing"""

    passenger_type: PassengerType
    count: int
    base_fare: float
    taxes: float
    total: float


class FareOption(InternalBaseSchema):
    """

    TBO Itinerary == FareOption

    Single bookable fare for a flight.

    Each fare has its own segments because fare-specific fields differ:
    - cabin_class, booking_class, baggage per segment

    provider_ref is OPAQUE to frontend - just pass it back when booking.
    fare_type comes from first segment's SupplierFareClass.
    """

    # Internal ID (we generate)
    fare_id: str

    # Provider reference (opaque to frontend)
    # provider: str = "tbo" # move inside provider_ref
    # provider_ref: dict  # {"TraceId", "ResultIndex", "Source", "IsLCC","Provider"}

    # Segments (fare-specific: cabin_class, baggage, booking_class differ per fare)
    segments: list[list[FlightSegment]]

    # Fare identity (from first segment's SupplierFareClass)
    fare_type: str | None = None  # "Saver", "Flexi", "Stretch", "Super 6E"

    # Pricing (customer-facing ONLY - no commissions)
    currency: str = "INR"
    base_fare: float
    taxes: float
    total_price: float
    # needed?
    # fare_breakdown: list[FareBreakdown] = Field(default_factory=list)

    # Attributes
    refundable: bool = False
    # changeable: bool = True # not such info given by TBO
    meal_included: bool = False

    # Booking flags
    # is_lcc: bool = False # needed here? in provider_ref
    passport_required: bool = False


class FlightGroup(InternalBaseSchema):
    """
    Flights grouped by physical route: carrier + flight_numbers + departure_times

    Multiple FareOptions for same physical flight(s).
    Each FareOption contains its own segments with fare-specific details.
    """

    # Group identity (for React keys)
    group_id: str

    # Summary (derived from first fare's segments for display)
    # carrier: Airline
    total_duration_minutes: int | None = None
    no_of_stops: int
    stop_airports: list[str] = Field(default_factory=list)

    # Route summary (for quick display without expanding fares)
    departure_time: datetime
    arrival_time: datetime
    origin: str  # Airport code
    destination: str  # Airport code

    # Fare options (sorted by price, cheapest first)
    fares: list[FareOption]

    # Quick access for UI
    lowest_price: float
    currency: str = "INR"


# ==============================================================================
# SEARCH RESPONSE
# ==============================================================================


class FlightSearchResponse(InternalBaseSchema):
    """
    Flight search response to frontend.

    For roundtrip:
    - Domestic: outbound_flights + inbound_flights (mix freely)
    - International: outbound_flights only, is_linked_fare=True
    """

    # Search ID (for session/caching)
    search_id: str

    # Echo request params
    trip_type: TripType
    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    passengers: dict  # {"adults": 1, "children": 0, "infants": 0}
    cabin_class: CabinClass

    # Results
    outbound_flights: list[FlightGroup] = Field(default_factory=list)
    inbound_flights: list[FlightGroup] = Field(default_factory=list)

    # Linked fare flag (international roundtrip)
    is_international_return: bool = False

    # Metadata
    # total_results: int  # needed?
    # search_time_ms: int  # needed?
    # results_valid_until: datetime  # needed?

    # Filter options (for frontend filter UI)
    # available_airlines: list[Airline] = []
    # This creates one shared list across all instances
    available_airlines: list[str] = Field(default_factory=list)
    price_range: dict = Field(default_factory=dict)  # {"min": 3500, "max": 25000}
    stops_available: list[int] = Field(default_factory=list)  # [0, 1, 2]


# ==============================================================================
# ERROR RESPONSE
# ==============================================================================


class FlightSearchError(InternalBaseSchema):
    """Standardized error response"""

    code: str  # "NO_FLIGHTS", "INVALID_ROUTE", "SESSION_EXPIRED"
    message: str
    details: dict | None = None
