from datetime import datetime

from pydantic import Field

from app.schemas.tbo_common import (
    BaseSchema,
    Fare,
    FareRule,
    Segment,
    TBOError,
    TripIndicator,
    KeyValue
)


# Request models
class Meal(BaseSchema):
    code: str
    description: str


class SeatPreference(BaseSchema):
    code: str
    description: str


class PassengerFare(BaseSchema):
    currency: str
    base_fare: float
    tax: float
    # tax_breakup: list[KeyValue] | None = None
    yq_tax: float | None = Field(alias="YQTax")
    additional_txn_fee_ofrd: float | None = None
    additional_txn_fee_pub: float | None = None
    # pg_charge: float | None = Field(None,alias="PGCharge")
    other_charges: float | None = None
    # charge_bu: list[KeyValue] | None = None
    discount: float | None = None
    published_fare: float | None = None
    # commission_earned: float | None = None
    # plb_earned: float | None = Field(None,alias="PLBEarned")
    # incentive_earned: float | None = None
    offered_fare: float | None = None
    tds_on_commission: float | None = None
    tds_on_plb: float | None = None
    tds_on_incentive: float | None = None
    service_fee: float | None = None



class Passenger(BaseSchema):
    title: str
    first_name: str
    last_name: str
    pax_type: int  # 1: Adult, 2: Child, 3: Infant
    date_of_birth: datetime
    gender: int
    passport_no: str | None = None
    passport_expiry: datetime | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    country_code: str
    country_name: str | None = None
    nationality: str
    contact_no: str
    email: str
    is_lead_pax: bool
    gst_company_address: str | None = None
    gst_company_contact_number: str | None = None
    gst_company_name: str | None = None
    gst_number: str | None = None
    gst_company_email: str | None = None
    # nested models
    fare: PassengerFare
    meal: Meal | None = None
    seat_preference: SeatPreference | None = None
    # baggage?


class TBOBookRequest(BaseSchema):
    end_user_ip: str
    trace_id: str
    result_index: str
    passengers: list[Passenger]


# Response models


class ResponsePassenger(BaseSchema):
    pax_id: int
    title: str
    first_name: str
    last_name: str
    pax_type: int
    date_of_birth: datetime
    gender: int
    passport_no: str | None = None
    passport_expiry: datetime | None = None
    city: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    nationality: str | None = None
    contact_no: str | None = None
    email: str | None = None
    is_lead_pax: bool
    fare: Fare
    meal: Meal | None = None
    gst_company_address: str | None = None
    gst_company_contact_number: str | None = None
    gst_company_email: str | None = None
    gst_company_name: str | None = None
    gst_number: str | None = None

    # missing fields?
    # Ssr : []
    # DocumentDetails : []


class FlightItinerary(BaseSchema):
    pnr: str = Field(alias="PNR")
    booking_id: int
    trip_indicator: TripIndicator
    is_domestic: bool
    source: int  # ya int?
    origin: str
    destination: str
    airline_code: str
    validating_airline_code: str
    airline_remark: str | None = None
    is_lcc: bool = Field(alias="IsLCC")
    non_refundable: bool
    fare_type: str
    cancellation_charges: float | None = None

    fare: Fare
    passenger: list[ResponsePassenger]
    segments: list[Segment]
    fare_rules: list[FareRule]

    status: int | None = None


class InnerResponse(BaseSchema):
    pnr: str = Field(alias="PNR")
    booking_id: int
    ssr_denied: bool | None = Field(alias="SSRDenied")
    ssr_message: str | None = Field(alias="SSRMessage")
    """ Status	String	[NotSet = 0, Successful = 1, Failed = 2, OtherFare = 3, OtherClass = 4, BookedOther = 5, NotConfirmed = 6]	Mandatory """
    status: int
    is_price_changed: bool | None = None
    is_time_changed: bool | None = None
    flight_itinerary: FlightItinerary


class TBOBookResponseStructure(BaseSchema):
    error: TBOError
    trace_id: str
    response_status: int
    response: InnerResponse


class TBOBookResponse(BaseSchema):
    response: TBOBookResponseStructure
