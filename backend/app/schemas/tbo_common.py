from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_pascal
from typing_extensions import Annotated


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_pascal,  # Converts field names to PascalCase when exporting/loading
        populate_by_name=True,  # Allows both PascalCase and snake_case inputs
        extra="ignore",  # Ignore unexpected fields from TBO
        from_attributes=True,  # Allow ORM/attribute style access
    )

    # .model_dump_json(by_alias=True) => for PascalCase JSON output


class TBOError(BaseSchema):
    error_code: int
    error_message: str | None = None


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


class KeyValue(BaseSchema):
    key: str
    value: float


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


class Fare(BaseSchema):
    # all fields included as per TBO docs
    currency: str
    base_fare: float
    tax: float

    tax_breakup: list[KeyValue] | None = None

    yq_tax: float | None = Field(alias="YQTax")
    additional_txn_fee_ofrd: float | None = None
    additional_txn_fee_pub: float | None = None
    pg_charge: float | None = Field(None, alias="PGCharge")
    other_charges: float | None = None

    charge_bu: list[KeyValue] | None = None

    discount: float | None = None
    published_fare: float | None = None
    commission_earned: float | None = None
    plb_earned: float | None = Field(None, alias="PLBEarned")
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


#  BAGGAGE MODEL
class Baggage(BaseSchema):
    airline_code: str
    flight_number: str
    way_type: int
    code: str
    description: str | int
    weight: float
    currency: str
    price: float
    origin: str
    destination: str
    text: str | None = None  # extra in non-lcc??


#  MEAL MODEL
class Meal(BaseSchema):
    airline_code: str
    flight_number: str
    way_type: int
    code: str
    description: str | int
    airline_description: str | None = None
    quantity: int | None = None
    currency: str | None = None
    price: float | None = None
    origin: str | None = None
    destination: str | None = None


#  SEAT MODEL
class Seat(BaseSchema):
    airline_code: str
    flight_number: str
    craft_type: str
    origin: str
    destination: str
    availablity_type: int
    description: str | int
    code: str
    row_no: str
    seat_no: str | None = None
    seat_type: int
    seat_way_type: int
    compartment: int
    deck: int
    currency: str
    price: float
    text: str | None = None  # extra in non-lcc??


#  ROW STRUCTURE (each row has seats)
class RowSeats(BaseSchema):
    seats: list[Seat]


#  SEGMENT STRUCTURE (each segment has rows)
class SegmentSeat(BaseSchema):
    row_seats: list[RowSeats]


#  SEATDYNAMIC STRUCTURE (each segment seat belongs to one flight leg)
class SeatDynamic(BaseSchema):
    segment_seat: list[SegmentSeat]
