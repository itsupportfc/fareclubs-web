"""
TBO Ticket API Schemas

Request and response models for TBO Ticket API.
- LCC: Pass passenger details, get PNR + Invoice in response
- Non-LCC: Pass PNR from Book response, get Invoice in response
"""

from datetime import datetime
from typing import Annotated

from pydantic import Field

from .base import TBOBaseSchema, TBOError
from .common import (
    Baggage as BaggageModel,
)
from .common import (
    BarcodeDetailsModel,
    FareRule,
    Segment,
)
from .common import (
    Fare as FareModel,
)
from .common import (
    Meal as MealModel,
)
from .common import (
    Seat as SeatModel,
)
from .enums import JourneyType as JourneyTypeEnum
from .enums import PassengerType as PassengerTypeEnum

# ==============================================================================
# TICKET REQUEST - LCC
# ==============================================================================


class PassengerFareSmall(TBOBaseSchema):
    """Minimal fare for ticket request"""

    BaseFare: float
    Tax: float
    YQTax: float = 0
    AdditionalTxnFeeOfrd: float = 0
    AdditionalTxnFeePub: float = 0
    PGCharge: float = 0


class TicketPassengerRequest(TBOBaseSchema):
    """Passenger for LCC ticket request"""

    Title: str
    FirstName: str
    LastName: str
    PaxType: int  # 1=Adult, 2=Child, 3=Infant
    Gender: int  # 1=Male, 2=Female
    DateOfBirth: str  # Note: string format for ticket
    AddressLine1: str
    AddressLine2: str | None = None
    City: str
    CountryCode: str
    CountryName: str | None = None
    ContactNo: str
    Email: str
    IsLeadPax: bool  # only one passenger can be lead pax
    Nationality: str

    Fare: PassengerFareSmall

    # Passport
    IsPassportRequired: bool | None = None
    PassportNo: str | None = None
    PassportExpiry: datetime | None = None
    PassportIssueDate: datetime | None = None
    PassportIssueCountryCode: str | None = None

    # PAN card
    PAN: str | None = None

    # GST (lead pax only)
    GSTCompanyAddress: str | None = None
    GSTCompanyContactNumber: str | None = None
    GSTCompanyName: str | None = None
    GSTNumber: str | None = None
    GSTCompanyEmail: str | None = None

    # SSR selections
    Baggage: list[BaggageModel] | None = None
    MealDynamic: list[MealModel] | None = None
    SeatDynamic: list[SeatModel] | None = None


class TBOTicketLCCRequest(TBOBaseSchema):
    """TBO Ticket API request for LCC airlines"""

    EndUserIp: str
    TokenId: str
    TraceId: str
    ResultIndex: str
    Passengers: list[TicketPassengerRequest]


# ==============================================================================
# TICKET REQUEST - NON-LCC
# ==============================================================================


class PassportInfo(TBOBaseSchema):
    """Passport details for Non-LCC ticket request"""

    PassportNumber: str
    PassportExpiry: str
    DateOfBirth: str
    PaxId: int


class TBOTicketNonLCCRequest(TBOBaseSchema):
    """TBO Ticket API request for Non-LCC airlines"""

    EndUserIp: str
    TokenId: str
    TraceId: str
    PNR: str
    BookingId: int
    Passport: list[PassportInfo] | None = None
    IsPriceChangeAccepted: bool | None = None


# ==============================================================================
# TICKET RESPONSE
# ==============================================================================


# class Barcode(TBOBaseSchema):
#     """Barcode for mobile boarding"""

#     Index: int
#     Format: str
#     Content: str
#     BarCodeInBase64: str | None = None
#     JourneyWayType: JourneyType


# class BarcodeDetailsModel(TBOBaseSchema):
#     """Barcode details per passenger"""

#     Id: int
#     Barcode: list[Barcode]


class DocumentDetailsModel(TBOBaseSchema):
    """Travel document details"""

    DocumentExpiryDate: str
    DocumentIssueDate: str | None = None
    DocumentIssuingCountry: str | None = None
    DocumentNumber: str
    DocumentTypeId: str
    PaxId: int
    ResultFareType: int


class SSRDetail(TBOBaseSchema):
    """SSR detail in response"""

    Detail: str
    SSRCode: str = Field(alias="SsrCode")
    SSRStatus: str | None = Field(default=None, alias="SsrStatus")
    Status: int


class SegmentAdditionalInfoModel(TBOBaseSchema):
    """Additional segment info in ticket"""

    FareBasis: str = ""
    NVA: str = ""  # Not valid after
    NVB: str = ""  # Not valid before
    Baggage: str = ""
    Meal: str | None = None
    Seat: str | None = None
    SpecialService: str | None = None
    CabinBaggage: str = ""


class TicketDetails(TBOBaseSchema):
    """Ticket details"""

    TicketId: Annotated[
        int, Field(description="Unique ticket id TBO gives in response")
    ]
    TicketNumber: str
    IssueDate: datetime
    ValidatingAirline: str
    Remarks: str = ""
    ServiceFeeDisplayType: str = ""
    Status: str
    ConjunctionNumber: str = ""
    TicketType: str = ""


class TicketPassengerResponse(TBOBaseSchema):
    """Passenger in ticket response"""

    PaxId: Annotated[int, Field(description="Unique pax id TBO gives in response")]
    Title: Annotated[
        str, Field(description="Adult Mr/Mrs Child Miss/Mstr Infant Miss/Mstr")
    ]
    FirstName: str
    LastName: str
    PaxType: PassengerTypeEnum
    DateOfBirth: datetime
    Gender: int

    IsPanRequired: bool | None = Field(default=None, alias="IsPANRequired")
    IsPassportRequired: bool | None = None
    PAN: str | None = None
    PassportNo: str | None = None

    AddressLine1: str
    City: str
    CountryCode: str
    Nationality: str
    ContactNo: str
    Email: str
    IsLeadPax: bool

    Baggage: list[BaggageModel] | None = None
    MealDynamic: list[MealModel] | None = None
    SeatDynamic: list[SeatModel] | None = None

    FFAirlineCode: str | None = None
    FFNumber: str | None = None

    Fare: FareModel
    BarcodeDetails: BarcodeDetailsModel | None = None
    DocumentDetails: list[DocumentDetailsModel] | None = None
    GuardianDetails: dict | None = None
    IsReissued: bool | None = None
    SSR: list[SSRDetail] | None = Field(default=None, alias="Ssr")
    Ticket: TicketDetails | None = None
    SegmentAdditionalInfo: list[SegmentAdditionalInfoModel] | None = None
    SegmentAdditionalInfoForReturn: list[SegmentAdditionalInfoModel] | None = None


class PNRHistoryModel(TBOBaseSchema):
    """PNR history entry"""

    CreatedBy: int
    CreatedOn: datetime
    LastModifiedBy: int
    LastModifiedOn: datetime
    PNRHistory: str


class InvoiceModel(TBOBaseSchema):
    """Invoice details"""

    CreditNoteGSTIN: str | None = None
    GSTIN: str | None = None
    InvoiceCreatedOn: datetime
    InvoiceId: int
    InvoiceNo: str
    InvoiceAmount: float
    Remarks: str
    InvoiceStatus: int


class PenaltyChargesModel(TBOBaseSchema):
    """Penalty charges info"""

    ReissueCharge: str | None = None
    CancellationCharge: str | None = None


class TicketItinerary(TBOBaseSchema):
    """Complete ticket itinerary"""

    BookingId: int
    PNR: str
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

    Fare: FareModel
    Passenger: list[TicketPassengerResponse]
    Segments: list[Segment]
    FareRules: list[FareRule]
    MiniFareRules: list | None = None
    PenaltyCharges: PenaltyChargesModel | None = None

    Status: int
    Invoice: list[InvoiceModel] | None = None
    InvoiceAmount: float | None = None
    InvoiceNo: str | None = None
    InvoiceStatus: int | None = None
    InvoiceCreatedOn: datetime | None = None
    Remarks: str | None = None
    PNRHistory: list[PNRHistoryModel] | None = None

    # Optional fields
    AgentRemarks: str | None = None
    CommentDetails: list | None = None
    FareClassification: str | None = None
    IsAutoReissuanceAllowed: bool | None = None
    IsSeatsBooked: bool | None = None
    IssuancePCC: str | None = Field(default=None, alias="IssuancePcc")
    JourneyType: int | None = None
    SearchCombinationType: int | None = None
    SupplierFareClasses: str | None = None
    TripIndicator: int | None = None
    BookingAllowedForRoamer: bool | None = None
    IsCouponAppilcable: bool | None = None
    IsManual: bool | None = None
    ResultFareType: str | None = None
    CreditNoteNo: str | None = None
    CreditNoteCreatedOn: datetime | None = None
    CancellationCharges: list | None = None
    IsWebCheckInAllowed: bool | None = None


class TicketInnerResponse(TBOBaseSchema):
    """Inner ticket response"""

    PNR: str
    BookingId: int
    SSRDenied: bool
    SSRMessage: str | None = None
    IsPriceChanged: bool
    IsTimeChanged: bool
    FlightItinerary: TicketItinerary
    Message: str | None = None
    # make an enum for this?
    TicketStatus: Annotated[
        int,
        Field(
            description="Failed = 0, Successful = 1, NotSaved = 2, NotCreated = 3, NotAllowed = 4, InProgress = 5, TicketAlreadyCreated = 6, PriceChanged = 8, OtherError = 9"
        ),
    ]


class TBOTicketResponseBody(TBOBaseSchema):
    """Outer response body"""

    ResponseStatus: int
    Error: TBOError
    TraceId: str
    B2B2BStatus: bool | None = None
    Response: TicketInnerResponse | None = None


class TBOTicketResponse(TBOBaseSchema):
    """TBO Ticket API response wrapper"""

    Response: TBOTicketResponseBody
