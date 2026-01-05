"""
TBO Get Booking Details API Schemas

Request and response models for TBO GetBookingDetails API.
Used to check booking status after network errors or for booking retrieval.
"""

from datetime import datetime

from .base import TBOBaseSchema, TBOError
from .common import Fare as FareModel
from .common import FareRule, Segment

# ==============================================================================
# REQUEST
# ==============================================================================


class TBOGetBookingDetailsRequest(TBOBaseSchema):
    """TBO GetBookingDetails API request"""

    EndUserIp: str
    TokenId: str
    PNR: str
    BookingId: int


# ==============================================================================
# RESPONSE
# ==============================================================================


class BarcodeDetailsModel(TBOBaseSchema):
    """Barcode details"""

    Id: int
    Barcode: list


class DocumentDetailsModel(TBOBaseSchema):
    """Document details"""

    DocumentExpiryDate: str
    DocumentIssueDate: str
    DocumentIssuingCountry: str
    DocumentNumber: str
    DocumentTypeId: str
    PaxId: int
    ResultFareType: int


class SSRDetail(TBOBaseSchema):
    """SSR detail"""

    Detail: str
    SSRCode: str
    SSRStatus: str | None = None
    Status: int


class SegmentAdditionalInfoModel(TBOBaseSchema):
    """Segment additional info"""

    FareBasis: str
    NVA: str
    NVB: str
    Baggage: str
    Meal: str
    Seat: str
    SpecialService: str
    CabinBaggage: str


class TicketDetails(TBOBaseSchema):
    """Ticket details"""

    TicketId: int
    TicketNumber: str
    IssueDate: datetime
    ValidatingAirline: str
    Remarks: str
    ServiceFeeDisplayType: str
    Status: str
    ConjunctionNumber: str
    TicketType: str


class BookingPassenger(TBOBaseSchema):
    """Passenger in booking details"""

    PaxId: int
    Title: str
    FirstName: str
    LastName: str
    PaxType: int
    DateOfBirth: datetime
    Gender: int

    IsPanRequired: bool | None = None
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

    FFAirlineCode: str | None = None
    FFNumber: str | None = None

    Fare: FareModel
    BarcodeDetails: BarcodeDetailsModel | None = None
    DocumentDetails: list[DocumentDetailsModel] | None = None
    GuardianDetails: dict | None = None
    SSR: list[SSRDetail] | None = None
    Ticket: TicketDetails | None = None
    SegmentAdditionalInfo: list[SegmentAdditionalInfoModel] | None = None


class PenaltyChargesModel(TBOBaseSchema):
    """Penalty charges"""

    ReissueCharge: str
    CancellationCharge: str


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


class PNRHistoryModel(TBOBaseSchema):
    """PNR history"""

    CreatedBy: int
    CreatedOn: datetime
    LastModifiedBy: int
    LastModifiedOn: datetime
    PNRHistory: str


class BookingFlightItinerary(TBOBaseSchema):
    """Complete booking itinerary"""

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
    Passenger: list[BookingPassenger]
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
    IssuancePCC: str | None = None
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


class TBOGetBookingDetailsInnerResponse(TBOBaseSchema):
    """Inner response"""

    ResponseStatus: int
    Error: TBOError
    TraceId: str
    FlightItinerary: BookingFlightItinerary


class TBOGetBookingDetailsResponse(TBOBaseSchema):
    """TBO GetBookingDetails API response wrapper"""

    Response: TBOGetBookingDetailsInnerResponse
