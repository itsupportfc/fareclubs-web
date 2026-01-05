"""
Internal Base Schema

Base for all frontend-facing schemas.
Uses camelCase for JSON serialization (JavaScript convention).
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class InternalBaseSchema(BaseModel):
    """
    Base schema for all internal/frontend-facing models.

    - Python code uses snake_case
    - JSON output uses camelCase (for JavaScript frontend)
    - Strict validation (no unknown fields)
    """

    model_config = ConfigDict(
        alias_generator=to_camel,  # snake_case → camelCase for JSON
        populate_by_name=True,  # Accept both cases as input
        extra="forbid",  # Reject unknown fields (strict API)
        from_attributes=True,  # Allow ORM conversion
        validate_default=True,  # Validate default values
        str_strip_whitespace=True,  # Trim whitespace from strings
        use_enum_values=True,  # Serialize enums as values
    )
