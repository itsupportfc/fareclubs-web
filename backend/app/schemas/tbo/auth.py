"""
TBO Authentication API Schemas

Request and response models for TBO Auth/Logout APIs.
"""

from .base import TBOBaseSchema, TBOError

# ==============================================================================
# AUTHENTICATE
# ==============================================================================


class TBOAuthRequest(TBOBaseSchema):
    """TBO Authenticate API request"""

    ClientId: str
    UserName: str
    Password: str
    EndUserIp: str


class TBOMember(TBOBaseSchema):
    """Member info from auth response"""

    FirstName: str | None = None
    LastName: str | None = None
    Email: str | None = None
    MemberId: int | None = None
    AgencyId: int | None = None
    LoginName: str | None = None
    LoginDetails: str | None = None
    IsPrimaryAgent: bool | None = None


class TBOAuthResponse(TBOBaseSchema):
    """TBO Authenticate API response"""

    Status: int
    TokenId: str | None = None
    Error: TBOError | None = None
    Member: TBOMember | None = None


# ==============================================================================
# LOGOUT
# ==============================================================================


class TBOLogoutRequest(TBOBaseSchema):
    """TBO Logout API request"""

    ClientId: str
    EndUserIp: str
    TokenAgencyId: int
    TokenMemberId: int
    TokenId: str


class TBOLogoutResponse(TBOBaseSchema):
    """TBO Logout API response"""

    Status: int
    Error: TBOError
