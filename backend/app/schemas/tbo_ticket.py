from datetime import datetime

from app.schemas.tbo_common import (
    Baggage,
    BaseSchema,
    Fare,
    FareRule,
    Meal,
    SeatDynamic,
    Segment,
    TBOError,
    JourneyType
)
from pydantic import Field


class PassengerFareSmall(BaseSchema):
    base_fare: float
    tax: float
    yq_tax: float = Field(alias="YQTax")
    additional_txn_fee_ofrd: float | None = None
    additional_txn_fee_pub: float | None = None
    pg_charge: float | None = Field(alias="PGCharge")


class Passenger(BaseSchema):
    title: str
    first_name: str
    last_name: str
    pax_type: int  # 1: Adult, 2: Child, 3: Infant
    gender: int
    date_of_birth: str
    address_line1: str
    address_line2: str | None = None
    city: str
    country_code: str
    country_name: str | None = None
    contact_no: str
    email: str
    is_lead_pax: bool
    nationality: str

    fare: PassengerFareSmall

    # passport details , not needed?
    is_passport_required: bool | None = None
    passport_no: str | None = None
    passport_expiry: datetime | None = None

    # nested models
    baggage: list[Baggage] | None = None
    meal: list[Meal] | None = None
    seat_dynamic: list[SeatDynamic] | None = None


# LCC request
class TBOTicketRequestLCC(BaseSchema):
    end_user_ip: str
    trace_id: str
    result_index: str
    passengers: list[Passenger]


# NON-LCC request
class TBOTicketRequestNonLCC(BaseSchema):
    end_user_ip: str
    trace_id: str
    result_index: str
    pnr: str = Field(alias="PNR")
    booking_id: int
    is_price_change_accepted: bool | None = None


# Response models
# class TBOTicketError(BaseSchema):
#     error_code: int
#     error_message: str


class Barcode(BaseSchema):
    index: int
    format: str
    content: str
    bar_code_in_base64: str | None = Field(alias="BarCodeInBase64")
    journey_way_type: JourneyType


class BarcodeDetails(BaseSchema):
    id: int
    barcode: list[Barcode]


class DocumentDetails(BaseSchema):
    document_expiry_date: str
    document_issue_date: str
    document_issuing_country: str
    document_number: str
    document_type_id: str
    pax_id: int
    result_fare_type: int


class SSR(BaseSchema):
    detail: str
    ssr_code: str
    ssr_status: str | None = None
    status: int


class SegmentAdditionalInfo(BaseSchema):
    fare_basis: str
    nva: str  # Not valid after
    nvb: str  # Not valid before
    baggage: str
    meal: str
    seat: str
    special_service: str
    cabin_baggage: str


class TicketDetails(BaseSchema):
    ticket_id: int
    ticket_number: str
    issue_date: datetime
    validating_airline: str
    remarks: str
    service_fee_display_type: str
    status: str
    conjunction_number: str
    ticket_type: str


class TicketPassenger(BaseSchema):
    barcode_details: BarcodeDetails | None = None
    document_details: list[DocumentDetails] | None = None
    guardian_details: dict | None = None
    pax_id: int
    title: str
    first_name: str
    last_name: str
    pax_type: int
    date_of_birth: datetime
    gender: int
    is_pan_required: bool | None = None
    is_passport_required: bool | None = None
    pan: str | None = None
    passport_no: str | None = None
    address_line1: str
    fare: Fare
    city: str
    country_code: str
    nationality: str
    contact_no: str
    email: str
    is_lead_pax: bool
    ff_airline_code: str | None = Field(None, alias="FFAirlineCode")
    ff_number: str | None = Field(None, alias="FFNumber")
    ssr: list[SSR] | None = None
    ticket: TicketDetails | None = None
    segment_additional_info: list[SegmentAdditionalInfo] | None = None


class PNRHistory(BaseSchema):
    created_by: int
    created_on: datetime
    last_modified_by: int
    last_modified_on: datetime
    pnr_history: str


class Invoice(BaseSchema):
    credit_note_gstin: str | None = Field(None, alias="CreditNoteGSTIN")
    gstin: str | None = None
    invoice_created_on: datetime
    invoice_id: int
    invoice_no: str
    invoice_amount: float
    remarks: str
    invoice_status: int


class PenaltyCharges(BaseSchema):
    reissue_charge: str
    cancellation_charge: str


class TicketItinerary(BaseSchema):
    agent_remarks: str | None = None
    comment_details: list | None = None
    fare_classification: str | None = None
    is_auto_reissuance_allowed: bool | None = None
    is_seats_booked: bool | None = None
    issuance_pcc: str | None = None
    journey_type: int | None = None
    search_combination_type: int | None = None
    supplier_fare_classes: str | None = None
    trip_indicator: int | None = None
    booking_allowed_for_roamer: bool | None = None
    booking_id: int
    is_coupon_appilcable: bool | None = None
    is_manual: bool | None = None
    pnr: str = Field(alias="PNR")
    is_domestic: bool
    result_fare_type: str | None = None
    source: int
    origin: str
    destination: str
    airline_code: str
    validating_airline_code: str
    airline_remark: str | None = None
    is_lcc: bool = Field(alias="IsLCC")
    non_refundable: bool
    fare_type: str
    credit_note_no: str | None = None
    fare: Fare
    credit_note_created_on: datetime | None = None
    passenger: list[TicketPassenger]
    cancellation_charges: list | None = None
    segments: list[Segment]
    fare_rules: list[FareRule]
    mini_fare_rules: list | None = None
    penalty_charges: PenaltyCharges | None = None
    status: int
    invoice: list[Invoice] | None = None
    invoice_amount: float | None = None
    invoice_no: str | None = None
    invoice_status: int | None = None
    invoice_created_on: datetime | None = None
    remarks: str | None = None
    pnr_history: list[PNRHistory] | None = None
    is_web_check_in_allowed: bool | None = None


class TBOTicketInnerResponse(BaseSchema):
    # itinerary_change_list: list | None = None
    pnr: str = Field(alias="PNR")
    booking_id: int
    ssr_denied: bool = Field(alias="SSRDenied")
    ssr_message: str | None = Field(None, alias="SSRMessage")
    is_price_changed: bool
    is_time_changed: bool
    flight_itinerary: TicketItinerary
    message: str | None = None
    ticket_status: int | None = None


class TBOTicketResponseStructure(BaseSchema):
    b2b2b_status: bool | None = Field(None, alias="B2B2BStatus")
    error: TBOError
    response_status: int
    trace_id: str
    response: TBOTicketInnerResponse


class TBOTicketResponse(BaseSchema):
    response: TBOTicketResponseStructure
