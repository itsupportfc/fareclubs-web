from datetime import datetime

from app.schemas.internal.base import InternalBaseSchema


class FareRule(InternalBaseSchema):
    airline: str
    # departure_time: datetime | None = None
    destination: str
    fare_basis_code: str
    fare_inclusions: list[str] | None = None
    fare_restriction: str | None = None
    fare_rule_detail: str
    flight_id: int | None = None
    origin: str
    # return_date: datetime | None = None


class FareRulesResponse(InternalBaseSchema):
    fare_rules: list[FareRule]
