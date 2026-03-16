"""
TBO Common Models

Shared models used across multiple TBO API endpoints.
All field names match TBO JSON exactly (PascalCase).
"""

from datetime import datetime
from typing import Annotated

from pydantic import Field

from .base import TBOBaseSchema
from .enums import (
    BaggageDescriptionEnum,
    FlightCabinClass,
    JourneyType,
    MealDescriptionEnum,
    SeatAvailabilityTypeEnum,
    SeatDescriptionEnum,
    SeatTypeEnum,
    SeatWayTypeEnum,
)
from .enums import PassengerType as PassengerTypeEnum
from .enums import TripIndicator as TripIndicatorEnum

# ----------------------------------------------------------------------
# Simple Shared Models
# ----------------------------------------------------------------------


class KeyValue(TBOBaseSchema):
    """Key-value pair for tax breakups, etc."""

    key: str
    value: float


# ----------------------------------------------------------------------
# Airport & Location Models
# ----------------------------------------------------------------------


class AirportInfo(TBOBaseSchema):
    """Airport details"""

    AirportCode: str
    AirportName: str | None = None
    Terminal: str | None = None
    CityCode: str
    CityName: str
    CountryCode: str
    CountryName: str


class OriginInfo(TBOBaseSchema):
    """Origin airport with departure time"""

    Airport: AirportInfo
    DepTime: datetime


class DestinationInfo(TBOBaseSchema):
    """Destination airport with arrival time"""

    Airport: AirportInfo
    ArrTime: datetime


# ----------------------------------------------------------------------
# Airline Model
# ----------------------------------------------------------------------


class AirlineInfo(TBOBaseSchema):
    """Airline and flight details"""

    AirlineCode: str
    AirlineName: str = ""
    FlightNumber: str
    FareClass: str = ""
    OperatingCarrier: str = ""


# ----------------------------------------------------------------------
# Segment Model
# ----------------------------------------------------------------------


class Segment(TBOBaseSchema):
    """Flight segment (one leg of a journey)"""

    # Baggage
    Baggage: str | None = None
    CabinBaggage: str | None = None

    # Class & Fare
    CabinClass: FlightCabinClass
    SupplierFareClass: str | None = None

    # Trip info
    TripIndicator: TripIndicatorEnum
    SegmentIndicator: int

    # Availability
    NoOfSeatAvailable: int | None = None

    # Duration
    Duration: int | None = None  # minutes
    AccumulatedDuration: int | None = None  # Total journey time (on last segment)
    GroundTime: int | None = None  # layover minutes
    Mile: int | None = None

    # Status
    StopOver: bool | None = None
    Craft: str | None = None
    Remark: str | None = None
    IsETicketEligible: bool = True
    FlightStatus: Annotated[str, Field(description="e.g. Confirmed", default="")]
    Status: str = ""

    # Stop point times (for stops)
    StopPointArrivalTime: datetime | None = None
    StopPointDepartureTime: datetime | None = None

    # PNR
    AirlinePNR: str | None = None

    # Nested models
    Airline: AirlineInfo
    Origin: OriginInfo
    Destination: DestinationInfo


# ----------------------------------------------------------------------
# Fare Models
# ----------------------------------------------------------------------


class Fare(TBOBaseSchema):
    """Fare/pricing details"""

    Currency: str
    BaseFare: float
    Tax: float

    # Tax details
    TaxBreakup: list[KeyValue] | None = None
    YQTax: float = 0.0

    # Transaction fees
    AdditionalTxnFeeOfrd: float = 0.0
    AdditionalTxnFeePub: float = 0.0
    PGCharge: float | None = None
    OtherCharges: float = 0.0
    ChargeBU: list[KeyValue] = []

    # Pricing
    Discount: Annotated[float, Field(description=" Will be zero for API customer.")] = 0.0
    PublishedFare: float
    OfferedFare: float
    ServiceFee: float = 0.0

    # Commission (sensitive - internal use only)
    CommissionEarned: float = 0.0
    PLBEarned: float = 0.0
    IncentiveEarned: float = 0.0
    TdsOnCommission: float = 0.0
    TdsOnPLB: float = 0.0
    TdsOnIncentive: float = 0.0

    # SSR charges
    TotalBaggageCharges: float | None = None
    TotalMealCharges: float | None = None
    TotalSeatCharges: float | None = None
    TotalSpecialServiceCharges: float | None = None


class FareBreakdown(TBOBaseSchema):
    """Per-passenger-type fare breakdown"""

    Currency: str
    PassengerType: PassengerTypeEnum
    PassengerCount: int
    BaseFare: float
    Tax: float
    TaxBreakUp: list[KeyValue] | None = None
    YQTax: float = 0.0
    AdditionalTxnFeeOfrd: float = 0.0
    AdditionalTxnFeePub: float = 0.0
    PGCharge: float | None = None
    SupplierReissueCharges: float | None = None


class FareClassification(TBOBaseSchema):
    """Fare brand/type info"""

    Color: str | None = None
    Type: str | None = None


# ----------------------------------------------------------------------
# Fare Rules
# ----------------------------------------------------------------------


class FareRule(TBOBaseSchema):
    """Fare rule details"""

    Origin: str
    Destination: str
    Airline: str
    FareBasisCode: str = ""
    FareRuleDetail: str = ""  # HTML content
    FareRestriction: str | None = None
    FareFamilyCode: str | None = None
    FareRuleIndex: str | None = None


class MiniFareRule(TBOBaseSchema):
    """Mini fare rule (cancellation/reissue info)"""

    JourneyPoints: str
    Type: str  # Cancellation / Reissue
    From: str | None = None  # Time value
    To: str | None = None
    Unit: str | None = None  # Time unit
    Details: str | None = None  # Amount/percentage
    OnlineReissueAllowed: bool | None = None
    OnlineRefundAllowed: bool | None = None


# ----------------------------------------------------------------------
# SSR Models (Baggage, Meal, Seat)
# ----------------------------------------------------------------------


class Baggage(TBOBaseSchema):
    """Extra baggage option"""

    AirlineCode: str
    FlightNumber: str
    WayType: Annotated[int, Field(description="Segment = 1,FullJourney = 2")]
    Code: str
    Description: Annotated[
        BaggageDescriptionEnum,
        Field(
            description=(
                "Baggage inclusion type.\n"
                "0 = NotSet\n"
                "1 = Included (upgradeable if option exists)\n"
                "2 = Direct (purchase, not upgradeable)\n"
                "3 = Imported\n"
                "4 = Upgrade\n"
                "5 = ImportedUpgrade"
            ),
        ),
    ]
    Weight: float
    Currency: str
    Price: float
    Origin: str
    Destination: str
    Text: str | None = None


class SimpleMeal(TBOBaseSchema):
    """Simple meal option for Non-LCC flights"""

    Code: str
    Description: str


class Meal(TBOBaseSchema):
    """Meal option"""

    AirlineCode: str
    FlightNumber: str
    WayType: Annotated[int, Field(description="Segment = 1,FullJourney = 2")]
    Code: str
    Description: MealDescriptionEnum
    AirlineDescription: str | None = None
    Quantity: int  # should be int
    Currency: str
    Price: float
    Origin: str
    Destination: str


class Seat(TBOBaseSchema):
    """Seat selection option"""

    AirlineCode: str
    FlightNumber: str
    CraftType: str  # need this mapping?
    Origin: str
    Destination: str
    AvailablityType: SeatAvailabilityTypeEnum
    Description: SeatDescriptionEnum
    Code: str
    RowNo: str
    SeatNo: str | None = None
    SeatType: int
    SeatWayType: SeatWayTypeEnum
    Compartment: int
    Deck: int
    Currency: str
    Price: float
    Text: str | None = None


class RowSeatsModel(TBOBaseSchema):
    """Row of seats"""

    Seats: list[Seat]


class SegmentSeatModel(TBOBaseSchema):
    """Seats for a segment"""

    RowSeats: Annotated[
        list[RowSeatsModel],
        Field(description="[{row 1 seats },{row 2 seats}]", default=None),
    ]


class SeatDynamic(TBOBaseSchema):
    """Dynamic seat map"""

    SegmentSeat: Annotated[
        list[SegmentSeatModel],
        Field(description="[{1st segment },{2nd segment}]", default=None),
    ]


class Barcode(TBOBaseSchema):
    """Barcode for mobile boarding"""

    Index: int
    Format: str
    Content: str
    BarCodeInBase64: str | None = None
    JourneyWayType: JourneyType


class BarcodeDetailsModel(TBOBaseSchema):
    """Barcode details per passenger"""

    Id: int
    Barcode: list[Barcode]
