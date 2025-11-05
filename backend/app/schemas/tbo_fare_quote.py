from pydantic import BaseModel

from app.schemas.tbo import Fare, Itinerary
from app.schemas.tbo_common import BaseSchema, TBOError


class TBOFareQuoteRequest(BaseSchema):
    end_user_ip: str
    # token_id: str  # from auth response
    trace_id: str  # from search response
    result_index: str  # from search response


class TBOFareQuoteResponseStructure(BaseSchema):
    error: TBOError
    is_price_changed: bool
    itinerary_change_list: list
    response_status: int
    results: Itinerary
    trace_id: str

class TBOFareQuoteResponse(BaseSchema):
    response: TBOFareQuoteResponseStructure