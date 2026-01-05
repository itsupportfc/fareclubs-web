import asyncio
import json
import logging
from datetime import datetime, timezone
from enum import IntEnum
from typing import Optional

import httpx
from app.clients.exceptions import ExternalProviderError
from app.config import settings
from app.schemas.tbo import (
    # Auth
    TBOAuthRequest,
    TBOAuthResponse,
    # Book
    TBOBookRequest,
    TBOBookResponse,
    # Fare Quote
    TBOFareQuoteRequest,
    TBOFareQuoteResponse,
    # Fare Rule
    TBOFareRuleRequest,
    TBOFareRuleResponse,
    # Booking Details
    TBOGetBookingDetailsRequest,
    TBOGetBookingDetailsResponse,
    TBOLogoutRequest,
    TBOLogoutResponse,
    # Search
    TBOSearchRequest,
    TBOSearchResponse,
    # SSR
    TBOSSRRequest,
    TBOSSRResponse,
    # Ticket
    TBOTicketLCCRequest,
    TBOTicketNonLCCRequest,
    TBOTicketResponse,
)

logger = logging.getLogger(__name__)


class TBOResponseStatus(IntEnum):
    NOT_SET = 0
    SUCCESS = 1
    FAILED = 2
    INVALID_REQUEST = 3
    SESSION_EXPIRED = 4
    AUTH_FAILED = 5


ERROR_CODE_MAP = {
    TBOResponseStatus.NOT_SET: ("NOT_SET", 502),
    TBOResponseStatus.FAILED: ("FAILED", 502),
    TBOResponseStatus.INVALID_REQUEST: ("INVALID_REQUEST", 400),
    TBOResponseStatus.SESSION_EXPIRED: ("SESSION_EXPIRED", 401),
    TBOResponseStatus.AUTH_FAILED: ("AUTH_FAILED", 401),
}


class TBOClient:
    """Client to interact with TBO API."""

    _cached_token: Optional[str] = None
    _cached_agency_id: Optional[int] = None
    _cached_member_id: Optional[int] = None
    _cached_date: Optional[str] = None  # YYYY-MM-DD
    _token_lock = asyncio.Lock()  # ensure only one auth call at a time

    def __init__(self) -> None:
        self.shared_base_url = settings.TBO_SHARED_BASE_URL.rstrip("/")
        self.air_base_url = settings.TBO_AIR_BASE_URL.rstrip("/")

        self.headers = {
            "Content-Type": "application/json",
        }

    async def authenticate(self) -> str:
        """
        Authenticates with TBO and caches token until midnight.
        Returns: TokenId (str)
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Reuse cached token if still valid today
        if self._cached_token and self._cached_date == today:
            logger.info("Using cached TBO token")
            return self._cached_token

        async with self._token_lock:
            # Double-check after acquiring lock (race-safe)
            if self._cached_token and self._cached_date == today:
                return self._cached_token

            payload = TBOAuthRequest(
                ClientId=settings.TBO_CLIENT_ID,
                UserName=settings.TBO_USERNAME,
                Password=settings.TBO_PASSWORD,
                EndUserIp=settings.TBO_END_USER_IP,
            )

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.shared_base_url}/Authenticate",
                    json=payload.model_dump(by_alias=True),
                    headers=self.headers,
                )

            # --- Handle errors ---
            if resp.status_code != 200:
                logger.error(f"TBO Auth HTTP {resp.status_code}: {resp.text}")
                raise Exception(f"TBO authentication failed (HTTP {resp.status_code})")

            try:
                data = resp.json()
                parsed = TBOAuthResponse(**data)
            except Exception as e:
                logger.exception("Invalid or unexpected JSON in TBO response")
                raise Exception("Invalid or unexpected response from TBO") from e

            # Successful = 1
            if parsed.Status != 1 or not parsed.TokenId:
                error_msg = (
                    parsed.Error.ErrorMessage
                    if parsed.Error
                    else "Unknown authentication error"
                )
                logger.error(f"TBO Auth failed: {error_msg}")
                raise Exception(f"TBO Auth Error: {error_msg}")

            # --- Cache the token until midnight ---
            self._cached_token = parsed.TokenId
            self._cached_date = today
            self._cached_agency_id = parsed.Member.AgencyId if parsed.Member else None
            self._cached_member_id = parsed.Member.MemberId if parsed.Member else None
            logger.info("TBO token cached successfully until midnight UTC")

            return self._cached_token

    async def get_token(self) -> str:
        """Public method to fetch (or reuse) a valid token."""
        return await self.authenticate()

    async def logout(self) -> bool:
        """Logout current TBO session."""
        if not all(
            [
                self._cached_agency_id,
                self._cached_date,
                self._cached_member_id,
                self._cached_token,
            ]
        ):
            raise Exception("No active TBO session")

        payload = TBOLogoutRequest(
            ClientId=settings.TBO_CLIENT_ID,
            EndUserIp=settings.TBO_END_USER_IP,
            TokenAgencyId=self._cached_agency_id,  # type: ignore
            TokenMemberId=self._cached_member_id,  # type: ignore
            TokenId=self._cached_token,  # type: ignore
        )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.shared_base_url}/Logout",
                json=payload.model_dump(by_alias=True),
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO Logout HTTP {resp.status_code}:{resp.text}")
            raise Exception(f"TBO logout failed (HTTP {resp.status_code})")

        try:
            parsed = TBOLogoutResponse(**resp.json())
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO logout response")
            raise Exception("Invalid logout response from TBO") from e

        if parsed.Status != 1 or parsed.Error.ErrorCode != 0:
            error_msg = parsed.Error.ErrorMessage or "Unknown logout error"
            logger.error(f"TBO Logout failed: {error_msg}")
            raise Exception(f"TBO Logout Error: {error_msg}")

        # clear cached data
        self._cached_token = None
        self._cached_agency_id = None
        self._cached_member_id = None
        self._cached_date = None

        return True

    def _check_response_status(self, tbo_response, context="TBO API"):
        """Check standard response status from TBO API responses."""

        response_status = tbo_response.get("Response", {}).get("ResponseStatus")

        if response_status == TBOResponseStatus.SUCCESS:
            return  # all good

        error_code = tbo_response.get("Response", {}).get("Error", {}).get("ErrorCode")
        error_msg = (
            tbo_response.get("Response", {}).get("Error", {}).get("ErrorMessage")
        )

        provider_code, http_status = ERROR_CODE_MAP.get(
            error_code, ("UNKNOWN_ERROR", 500)
        )

        logger.error(
            "%s ERROR (%s): %s",
            context,
            provider_code,
            error_msg,
        )
        raise ExternalProviderError(
            provider_code=provider_code,
            http_status=http_status,
            message=f"{context} Error: {error_msg}",
        )

    async def search(self, payload: TBOSearchRequest) -> TBOSearchResponse:
        """Perform flight search"""
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/Search"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO Search HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO search failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly

        # try to parse the response
        try:
            data = resp.json()
            # print("TBO Search Response Data:", data)
            self._check_response_status(data, context="TBO Search")
            parsed = TBOSearchResponse(**data)
            return parsed
        except ExternalProviderError:
            # Bubble up provider errors so the API layer can decide how to respond
            raise
        except Exception as e:
            logger.exception("Failed to validate TBO search response")
            raise Exception("Unexpected response structure from TBO") from e

    async def get_fare_rule(self, payload: TBOFareRuleRequest) -> TBOFareRuleResponse:
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/FareRule"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO FareRule HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO FareRule failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO FareRule response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            self._check_response_status(data, context="TBO FareRule")

            parsed = TBOFareRuleResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO FareRule response")
            raise Exception("Unexpected response structure from TBO") from e

    async def get_fare_quote(
        self, payload: TBOFareQuoteRequest
    ) -> TBOFareQuoteResponse:
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/FareQuote"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO FareQuote HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO FareQuote failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO FareQuote response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            self._check_response_status(data, context="TBO FareQuote")
            parsed = TBOFareQuoteResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO FareQuote response")
            raise Exception("Unexpected response structure from TBO") from e

    async def get_ssr(self, payload: TBOSSRRequest) -> TBOSSRResponse:
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/SSR"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO SSR HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO SSR failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO SSR response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            print(payload_data)
            print("TBO SSR Response Data:", data)
            self._check_response_status(data, context="TBO SSR")

            # dump data for debugging
            with open("ssr.jsonc", "a", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            parsed = TBOSSRResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO SSR response")
            raise Exception("Unexpected response structure from TBO") from e

    async def book_flight(self, payload: TBOBookRequest) -> TBOBookResponse:
        """Only non-LCC"""
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/Book"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO Book HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO Book failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO Book response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            # print(data)
            parsed = TBOBookResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO Book response")
            raise Exception("Unexpected response structure from TBO") from e

    async def generate_ticket_lcc(
        self, payload: TBOTicketLCCRequest
    ) -> TBOTicketResponse:
        """Generate ticket for LCC flights"""
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/Ticket"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO TicketLCC HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO TicketLCC failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO TicketLCC response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            # print(data)
            parsed = TBOTicketResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO TicketLCC response")
            raise Exception("Unexpected response structure from TBO") from e

    async def generate_ticket_nonlcc(
        self, payload: TBOTicketNonLCCRequest
    ) -> TBOTicketResponse:
        """Generate ticket for non-LCC flights"""
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/Ticket"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO TicketNonLCC HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO TicketNonLCC failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO TicketNonLCC response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            # print(data)
            parsed = TBOTicketResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO TicketNonLCC response")
            raise Exception("Unexpected response structure from TBO") from e

    async def get_booking_details(
        self, payload: TBOGetBookingDetailsRequest
    ) -> TBOGetBookingDetailsResponse:
        """Get booking details by PNR and Booking ID"""
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, mode="json")
        payload_data["TokenId"] = token

        url = f"{self.air_base_url}/GetBookingDetails"
        self.headers["Accept-Encoding"] = "gzip"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload_data,
                headers=self.headers,
            )

        if resp.status_code != 200:
            logger.error(f"TBO GetPNRDetails HTTP {resp.status_code}: {resp.text}")
            raise Exception(f"TBO GetPNRDetails failed (HTTP {resp.status_code})")

        # httpx automatically decompresses gzip, so just parse JSON directly
        try:
            data = resp.json()
        except Exception as e:
            logger.exception("Invalid or unexpected JSON in TBO GetPNRDetails response")
            raise Exception("Invalid response from TBO") from e

        # try to parse the response
        try:
            # print(data)
            parsed = TBOGetBookingDetailsResponse(**data)
            return parsed
        except Exception as e:
            logger.exception("Failed to parse TBO GetPNRDetails response")
            raise Exception("Unexpected response structure from TBO") from e
