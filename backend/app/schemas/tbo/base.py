"""
TBO Base Schema

Uses EXACT field names from TBO JSON (PascalCase).
No alias_generator - fields match TBO API exactly.
"""

from pydantic import BaseModel, ConfigDict


class TBOBaseSchema(BaseModel):
    """
    Base schema for all TBO API models.

    - Field names match TBO JSON exactly (PascalCase)
    - extra="ignore": TBO may add new fields, don't break
    - populate_by_name=True: Accept both PascalCase and lowercase
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        from_attributes=True,
    )


class TBOError(TBOBaseSchema):
    """TBO API error structure"""

    ErrorCode: int
    ErrorMessage: str
