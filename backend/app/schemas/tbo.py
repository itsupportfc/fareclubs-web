# app/schemas/TBO.py
import json
from datetime import datetime
from enum import IntEnum
from typing import Annotated, Optional
from unittest.mock import Base

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_pascal


# ----------------------------------------------------------------------
#  Base Schema: Handles PascalCase ↔ snake_case automatically
# ----------------------------------------------------------------------
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_pascal,  # Converts field names to PascalCase when exporting/loading
        populate_by_name=True,  # Allows both PascalCase and snake_case inputs
        extra="ignore",  # Ignore unexpected fields from TBO
        from_attributes=True,  # Allow ORM/attribute style access
    )

    # .model_dump_json(by_alias=True) => for PascalCase JSON output


# ========================
# AUTH
# ========================


class TBOAuthRequest(BaseSchema):
    client_id: str
    user_name: str
    password: str
    end_user_ip: str


class TBOError(BaseSchema):
    error_code: int
    error_message: str | None = None


class TBOMember(BaseSchema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    member_id: Optional[int] = None
    agency_id: Optional[int] = None
    login_name: Optional[str] = None
    login_details: Optional[str] = None
    is_primary_agent: Optional[bool] = None


class TBOAuthResponse(BaseSchema):
    status: int
    token_id: Optional[str] = None
    error: Optional[TBOError] = None
    member: Optional[TBOMember] = None


# ========================
# LOGOUT
# ========================


class TBOLogoutRequest(BaseSchema):
    client_id: str
    end_user_ip: str
    token_agency_id: int
    token_member_id: int
    token_id: str


class TBOLogoutResponse(BaseSchema):
    status: int
    error: TBOError


# ========================
# ENUMS
# ========================


class JourneyType(IntEnum):
    ONEWAY = 1
    RETURN = 2
    MULTISTOP = 3
    ADVANCE_SEARCH = 4
    SPECIAL_RETURN = 5


class PassengerType(IntEnum):
    ADULT = 1
    CHILD = 2
    INFANT = 3


class FlightCabinClass(IntEnum):
    ALL = 1
    ECONOMY = 2
    PREMIUM_ECONOMY = 3
    BUSINESS = 4
    PREMIUM_BUSINESS = 5
    FIRST = 6


class TripIndicator(IntEnum):
    OUTBOUND = 1
    INBOUND = 2


# ========================
# SEARCH REQUEST
# ========================


class SearchSegment(BaseSchema):
    origin: str
    destination: str
    flight_cabin_class: FlightCabinClass
    preferred_departure_time: datetime
    preferred_arrival_time: datetime


class TBOSearchRequest(BaseSchema):
    end_user_ip: str
    # token_id: str # related to TBO, frontend shuold not deal with it
    adult_count: int
    child_count: int
    infant_count: int
    direct_flight: bool = False
    one_stop_flight: bool = False
    journey_type: JourneyType
    preferred_airlines: Optional[list[str]] = None
    segments: list[SearchSegment]
    sources: Optional[list[str]] = None


# ========================
# SEARCH RESPONSE
# ========================


class KeyValue(BaseSchema):
    key: str
    value: float


# ----------------------------------------------------------------------
#  Airport + Route Models
# ----------------------------------------------------------------------
class AirportInfo(BaseSchema):
    airport_code: str
    airport_name: str
    terminal: str | None = None
    city_code: str
    city_name: str
    country_code: str
    country_name: str


class OriginInfo(BaseSchema):
    airport: AirportInfo
    dep_time: Annotated[datetime, Field(description="Departure time in ISO8601")]


class DestinationInfo(BaseSchema):
    airport: AirportInfo
    arr_time: Annotated[datetime, Field(description="Arrival time in ISO8601")]


class AirlineInfo(BaseSchema):
    airline_code: str
    airline_name: str
    flight_number: str
    fare_class: str | None = None
    operating_carrier: str | None = None


# ----------------------------------------------------------------------
#  Segment Model
# ----------------------------------------------------------------------
class Segment(BaseSchema):
    baggage: str | None = None
    cabin_baggage: str | None = None
    cabin_class: FlightCabinClass
    supplier_fare_class: str | None = None
    trip_indicator: TripIndicator
    segment_indicator: int | None = None
    no_of_seat_available: int | None = None  # at this price
    duration: Annotated[int, Field(ge=0, description="Duration in minutes")]
    ground_time: int | None = None
    mile: int | None = None
    stop_over: bool | None = None
    craft: str | None = None
    remark: str | None = None
    is_e_ticket_eligible: bool | None = None
    flight_status: str | None = None
    status: str | None = None
    stop_point_arrival_time: datetime | None = None
    stop_point_departure_time: datetime | None = None
    # NESTED MODELS
    airline: AirlineInfo
    origin: OriginInfo
    destination: DestinationInfo


# ----------------------------------------------------------------------
#  Fare & Fare Breakdown
# ----------------------------------------------------------------------
class Fare(BaseSchema):
    # all fields included as per TBO docs
    currency: str
    base_fare: float
    tax: float
    tax_breakup: list[KeyValue] | None = None
    yq_tax: float | None = Field(alias="YQTax")
    additional_txn_fee_ofrd: float | None = None
    additional_txn_fee_pub: float | None = None
    pg_charge: float | None = Field(alias="PGCharge")
    other_charges: float | None = None
    charge_bu: list[KeyValue] | None = None
    discount: float | None = None
    published_fare: float | None = None
    commission_earned: float | None = None
    plb_earned: float | None = Field(alias="PLBEarned")
    incentive_earned: float | None = None
    offered_fare: float | None = None
    tds_on_commission: float | None = None
    tds_on_plb: float | None = None
    tds_on_incentive: float | None = None
    service_fee: float | None = None
    total_baggage_charges: float | None = None
    total_meal_charges: float | None = None
    total_seat_charges: float | None = None
    total_special_service_charges: float | None = None


class FareBreakdown(BaseSchema):
    # all fields included as per TBO docs
    currency: str
    passenger_type: PassengerType
    passenger_count: int
    base_fare: float
    tax: float
    tax_break_up: list[KeyValue] | None = None
    yq_tax: float | None = Field(alias="YQTax")
    additional_txn_fee_ofrd: float | None = None
    additional_txn_fee_pub: float | None = None
    pg_charge: float | None = None
    supplier_reissue_charges: float | None = None


class FareClassification(BaseSchema):
    color: str | None = None
    type: str | None = None


# ----------------------------------------------------------------------
#  Fare Rules and Mini Rules
# ----------------------------------------------------------------------
class FareRule(BaseSchema):
    # all fields included as per TBO docs
    origin: str
    destination: str
    airline: str
    fare_basis_code: str | None = None
    fare_rule_detail: str | None = None
    fare_restriction: str | None = None
    fare_family_code: str | None = None
    fare_rule_index: str | None = None


class MiniFareRule(BaseSchema):
    journey_points: str  # sector on which it applies
    type: str  # Cancellation/ Reissue
    # From => Numeric value of Time
    from_: str | None = Field(None, alias="From")  # 'from' is a reserved keyword
    to: str | None = None
    unit: str | None = None  # Unit of Time
    details: str | None = None  # Amount or Percentage charged
    online_reissue_allowed: bool | None = None
    online_refund_allowed: bool | None = None


# ----------------------------------------------------------------------
#  Itinerary (Core Object)
# ----------------------------------------------------------------------
class Itinerary(BaseSchema):
    # many fields are not included..include as and when needed!!
    result_index: str  # main identifier
    source: int  # 6 = Indigo
    is_lcc: bool | None = Field(alias="IsLCC")
    is_refundable: bool
    is_free_meal_available: bool
    airline_code: str
    validating_airline: str
    is_pan_required_at_book: bool | None = None

    # these will decide passport details will be needed at these stages
    # need to store these then?    
    is_passport_required_at_book: bool | None = None
    is_passport_required_at_ticket: bool | None = None
    
    # is_coupon_appilcable: bool | None = None
    gst_allowed: bool | None = Field(alias="GSTAllowed")

    # NESTED MODELS
    fare: Fare
    fare_breakdown: list[FareBreakdown]
    segments: list[list[Segment]]
    fare_rules: list[FareRule]
    mini_fare_rules: list[list[MiniFareRule]] | None = None
    fare_classification: FareClassification | None = None


# ----------------------------------------------------------------------
# Root Response Models
# ----------------------------------------------------------------------
class TBOResponse(BaseSchema):
    result_recommendation_type: int | None = None
    response_status: int  # 1 = Success
    error: TBOError
    trace_id: str  # valid for 15 mins
    origin: str
    destination: str
    results: list[list[Itinerary]]


class TBOSearchResponse(BaseSchema):
    # as only 1 key value in response structure
    response: TBOResponse

