from datetime import datetime
from typing import List, Optional
from urllib import response

from app.schemas.tbo_common import BaseSchema, TBOError


class TBOFareRuleRequest(BaseSchema):
    end_user_ip: str
    # token_id: str
    trace_id: str
    result_index: str


class FareRule(BaseSchema):
    Airline: str
    DepartureTime: Optional[datetime]
    Destination: str
    FareBasisCode: str
    FareInclusions: Optional[List[str]]
    FareRestriction: Optional[List[str]]
    FareRuleDetail: str  # HTML content
    FlightId: Optional[int]
    Origin: str
    ReturnDate: Optional[datetime]


class ResponseStructure(BaseSchema):
    error: TBOError
    fare_rules: List[FareRule]
    response_status: int
    trace_id: str


class TBOFareRuleResponse(BaseSchema):
    response: ResponseStructure
