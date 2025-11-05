from pydantic import BaseModel, ConfigDict
from app.schemas.tbo_common import BaseSchema, TBOError  # your shared BaseSchema with to_pascal alias generator


#  REQUEST MODEL
class TBOSSRRequest(BaseSchema):
    end_user_ip: str
    # token_id: str | None = None
    trace_id: str
    result_index: str


#  BAGGAGE MODEL
class SSRBaggage(BaseSchema):
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
    text: str | None = None # extra in non-lcc??


#  MEAL MODEL
class SSRMeal(BaseSchema):
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
class SSRSeat(BaseSchema):
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
    text: str | None = None # extra in non-lcc??


#  ROW STRUCTURE (each row has seats)
class RowSeats(BaseSchema):
    seats: list[SSRSeat]


#  SEGMENT STRUCTURE (each segment has rows)
class SegmentSeat(BaseSchema):
    row_seats: list[RowSeats]


#  SEATDYNAMIC STRUCTURE (each segment seat belongs to one flight leg)
class SeatDynamic(BaseSchema):
    segment_seat: list[SegmentSeat]


#  RESPONSE WRAPPER MODEL
class TBOSSRResponseStructure(BaseSchema):
    response_status: int
    error: TBOError
    trace_id: str
    baggage: list[list[SSRBaggage]] | None = None
    meal_dynamic: list[list[SSRMeal]] | None = None
    seat_dynamic: list[SeatDynamic] | None = None


#  OUTER RESPONSE WRAPPER (matches full JSON)
class TBOSSRResponse(BaseSchema):
    response: TBOSSRResponseStructure
