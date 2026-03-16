"""
TBO Book API Schemas

Request and response models for TBO Book API.
- LCC: Book API not used (go directly to Ticket)
- Non-LCC: Book API creates a held PNR, then call Ticket to issue
"""

from datetime import datetime
from typing import Annotated

from pydantic import Field

from .base import TBOBaseSchema, TBOError
from .common import BarcodeDetailsModel, FareRule, Segment
from .common import Fare as FareModel
from .enums import TripIndicator

# ==============================================================================
# BOOK REQUEST
# ==============================================================================


class MealSelection(TBOBaseSchema):
    """Meal selection for passenger"""

    Code: str
    Description: int


class SeatDynamicSelection(TBOBaseSchema):
    """Seat selection for passenger"""

    Code: str
    Description: int


class BaggageSelection(TBOBaseSchema):
    """Baggage selection for passenger"""

    Code: str
    Description: int


class PassengerFare(TBOBaseSchema):
    """Fare details for passenger in booking request"""

    Currency: str
    BaseFare: float
    Tax: float
    YQTax: float | None = None
    AdditionalTxnFeeOfrd: float | None = None
    AdditionalTxnFeePub: float | None = None
    PGCharge: float | None = None
    OtherCharges: float | None = None
    Discount: float | None = None
    PublishedFare: float | None = None
    OfferedFare: float | None = None
    TdsOnCommission: float | None = None
    TdsOnPLB: float | None = None
    TdsOnIncentive: float | None = None
    ServiceFee: float | None = None


class BookPassenger(TBOBaseSchema):
    """Passenger details for booking request"""

    Title: str
    FirstName: str
    LastName: str
    PaxType: int  # 1: Adult, 2: Child, 3: Infant
    DateOfBirth: datetime  # make it optional
    Gender: int

    # Passport (required for international)
    PassportNo: str | None = None
    PassportExpiry: datetime | None = None
    PassportIssueDate: datetime | None = None
    PassportIssueCountryCode: str | None = None

    # PAN card (Indian domestic, when IsPanRequiredAtBook=true)
    PAN: str | None = None

    # Contact
    AddressLine1: str
    AddressLine2: str | None = None
    City: str
    CountryCode: str
    CountryName: str | None = None
    Nationality: str
    ContactNo: str
    Email: str
    IsLeadPax: bool

    # GST (optional, for Indian B2B)
    GSTCompanyAddress: str | None = None
    GSTCompanyContactNumber: str | None = None
    GSTCompanyName: str | None = None
    GSTNumber: str | None = None
    GSTCompanyEmail: str | None = None

    # Fare and SSR
    Fare: PassengerFare
    MealDynamic: MealSelection | None = None
    SeatDynamic: SeatDynamicSelection | None = None
    Baggage: BaggageSelection | None = None


class TBOBookRequest(TBOBaseSchema):
    """TBO Book API request (Non-LCC only)"""

    EndUserIp: str
    TokenId: str
    TraceId: str
    ResultIndex: str
    Passengers: list[BookPassenger]


# ==============================================================================
# BOOK RESPONSE
# ==============================================================================


class ResponsePassenger(TBOBaseSchema):
    """Passenger Schema in booking response"""

    PaxId: Annotated[int, Field(description="Unique pax id TBO gives in response")]
    Title: str
    FirstName: str
    LastName: str
    PaxType: Annotated[int, Field(description=" 1=Adult, 2=Child, 3=Infant")]
    DateOfBirth: datetime | None = None
    Gender: Annotated[int, Field(description=" 1=Male, 2=Female ??? need to confirm")]
    PassportNo: str | None = None
    PassportExpiry: datetime | None = None
    AddressLine1: str | None = None
    City: str | None = None
    CountryCode: str | None = None
    CountryName: str | None = None
    Nationality: str | None = None
    ContactNo: str | None = None
    Email: str | None = None
    IsLeadPax: bool
    FFAirlineCode: str | None = None
    FFNumber: str | None = None
    Fare: FareModel

    Meal: MealSelection | None = None
    Seat: SeatDynamicSelection | None = None
    Baggage: list | None = None
    Ssr: list | None = None
    SegmentAdditionalInfo: list | None = None
    DocumentDetails: list | None = None

    GSTCompanyAddress: str | None = None
    GSTCompanyContactNumber: str | None = None
    GSTCompanyEmail: str | None = None
    GSTCompanyName: str | None = None
    GSTNumber: str | None = None

    BarcodeDetails: BarcodeDetailsModel | None = None


class FlightItineraryModel(TBOBaseSchema):
    """Flight itinerary in booking response"""

    PNR: str
    BookingId: int
    TripIndicator: TripIndicator
    IsDomestic: bool
    Source: int
    Origin: str
    Destination: str
    AirlineCode: str
    ValidatingAirlineCode: str
    AirlineRemark: str | None = None
    IsLCC: bool
    NonRefundable: bool
    FareType: str
    CancellationCharges: float | None = None

    Fare: FareModel
    Passenger: list[ResponsePassenger]

    Segments: list[Segment]
    FareRules: list[FareRule]

    LastTicketDate: Annotated[
        datetime | None, Field(description="need to call /ticket method before this date.")
    ] = None
    Status: int | None = None


class BookInnerResponse(TBOBaseSchema):
    """Inner response structure"""

    PNR: str
    BookingId: int
    SSRDenied: bool
    SSRMessage: str | None = None
    Status: Annotated[
        int,
        Field(
            description="NotSet = 0, Successful = 1, Failed = 2, OtherFare = 3, OtherClass = 4, BookedOther = 5, NotConfirmed = 6"
        ),
    ]
    IsPriceChanged: bool
    IsTimeChanged: bool
    FlightItinerary: FlightItineraryModel


class TBOBookResponseBody(TBOBaseSchema):
    """Outer response body"""

    ResponseStatus: int
    Error: TBOError
    TraceId: str
    Response: BookInnerResponse | None = None


class TBOBookResponse(TBOBaseSchema):
    """TBO Book API response wrapper"""

    Response: TBOBookResponseBody
