"""
Internal Schemas

Frontend-facing schemas with camelCase JSON output.
Provider-agnostic - works with TBO, Amadeus, etc.
"""

from .base import InternalBaseSchema
from .flight import (
    # Response building blocks
    Airline,
    Airport,
    # Type aliases
    CabinClass,
    Direction,
    FareBreakdown,
    FareOption,
    FlightGroup,
    FlightSearchError,
    # Request
    FlightSearchRequest,
    # Response
    FlightSearchResponse,
    FlightSegment,
    PassengerType,
    TripType,
)

__all__ = [
    # Base
    "InternalBaseSchema",
    # Type aliases
    "CabinClass",
    "Direction",
    "PassengerType",
    "TripType",
    # Request
    "FlightSearchRequest",
    # Response building blocks
    "Airline",
    "Airport",
    "FareBreakdown",
    "FareOption",
    "FlightGroup",
    "FlightSegment",
    # Response
    "FlightSearchResponse",
    "FlightSearchError",
]
