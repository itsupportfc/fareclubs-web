import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from enum import IntEnum
from typing import Optional

import httpx
from app.clients.exceptions import ExternalProviderError
from app.config import settings
from app.core.logging import sanitize_for_logging, truncate_for_logging
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
from app.schemas.tbo.search import Itinerary
from pydantic import ValidationError

# Dedicated logger name routes to the tbo_file handler in logging config
logger = logging.getLogger("app.integrations.tbo")


class TBOParseError(Exception):
    """Raised when TBO response JSON is valid but doesn't match our schema."""

    def __init__(self, message: str, raw_response: dict):
        super().__init__(message)
        self.raw_response = raw_response


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

_SEAT_UNAVAILABLE_MARKERS = (
    "selected seat has already been reserved",
    "seat has already been reserved",
    "seat unavailable",
)

_MEAL_REQUIRED_MARKERS = (
    "meal selection is mandatory",
    "meal is mandatory",
    "meal selection required",
)


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
            "Accept-Encoding": "gzip",
        }

    def _log_tbo_request(self, *, operation: str, url: str, payload: dict) -> None:
        log_payload: dict = {
            "event": "tbo.request",
            "operation": operation,
            "url": url,
        }
        if settings.ENABLE_TBO_BODY_LOGGING:
            log_payload["payload"] = sanitize_for_logging(payload)
        logger.info(json.dumps(log_payload, default=str))

    def _log_tbo_response(
        self,
        *,
        operation: str,
        url: str,
        status_code: int,
        elapsed_ms: float,
        response_data: dict | None = None,
        raw_text: str | None = None,
    ) -> None:
        # Always log metadata at INFO
        log_meta = {
            "event": "tbo.response",
            "operation": operation,
            "url": url,
            "status_code": status_code,
            "duration_ms": round(elapsed_ms, 2),
        }
        logger.info(json.dumps(log_meta, default=str))

        # Log response body at DEBUG only (can be very large for search responses)
        if settings.ENABLE_TBO_BODY_LOGGING and logger.isEnabledFor(logging.DEBUG):
            body_payload: dict = {"event": "tbo.response.body", "operation": operation}
            if response_data is not None:
                body_payload["body"] = sanitize_for_logging(response_data)
            elif raw_text is not None:
                body_payload["body"] = truncate_for_logging(
                    raw_text, settings.LOG_MAX_BODY_CHARS
                )
            logger.debug(json.dumps(body_payload, default=str))

    async def _post_tbo_json(
        self,
        *,
        operation: str,
        url: str,
        payload_data: dict,
        timeout: float,
    ) -> dict:
        self._log_tbo_request(operation=operation, url=url, payload=payload_data)

        async with httpx.AsyncClient(timeout=timeout) as client:
            started = time.perf_counter()
            resp = await client.post(url, json=payload_data, headers=self.headers)
            elapsed_ms = (time.perf_counter() - started) * 1000

        if resp.status_code != 200:
            self._log_tbo_response(
                operation=operation,
                url=url,
                status_code=resp.status_code,
                elapsed_ms=elapsed_ms,
                raw_text=resp.text,
            )
            raise ExternalProviderError(
                provider_code=f"{operation.upper()}_HTTP_{resp.status_code}",
                message="Flight provider returned an error. Please try again.",
                http_status=502,
            )

        try:
            data = resp.json()
        except Exception as e:
            self._log_tbo_response(
                operation=operation,
                url=url,
                status_code=resp.status_code,
                elapsed_ms=elapsed_ms,
                raw_text=resp.text,
            )
            logger.exception("Invalid or unexpected JSON in %s response", operation)
            raise ExternalProviderError(
                provider_code=f"{operation.upper()}_INVALID_RESPONSE",
                message="Received an invalid response from the flight provider. Please try again.",
                http_status=502,
            ) from e

        self._log_tbo_response(
            operation=operation,
            url=url,
            status_code=resp.status_code,
            elapsed_ms=elapsed_ms,
            response_data=data,
        )
        return data

    async def _call_tbo_api(
        self,
        *,
        operation: str,
        endpoint: str,
        payload,
        response_model: type,
        timeout: float,
        check_status: bool = True,
        critical: bool = False,
    ):
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        payload_data["TokenId"] = token

        data = await self._post_tbo_json(
            operation=operation,
            url=f"{self.air_base_url}/{endpoint}",
            payload_data=payload_data,
            timeout=timeout,
        )

        if check_status:
            self._check_response_status(data, context=operation)

        try:
            return response_model(**data)
        except Exception as e:
            logger.exception("Failed to parse %s response", operation)
            if critical:
                raise TBOParseError(
                    "Unexpected response structure from TBO", raw_response=data
                ) from e
            raise ExternalProviderError(
                provider_code=f"{operation.upper().replace(' ', '_')}_PARSE_ERROR",
                message="Received an invalid response from the flight provider.",
                http_status=502,
            ) from e

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
            payload_data = payload.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            )
            data = await self._post_tbo_json(
                operation="TBO Authenticate",
                url=f"{self.shared_base_url}/Authenticate",
                payload_data=payload_data,
                timeout=30,
            )

            try:
                parsed = TBOAuthResponse(**data)
            except Exception as e:
                logger.exception("Invalid or unexpected JSON in TBO auth response")
                raise ExternalProviderError(
                    provider_code="AUTH_PARSE_ERROR",
                    message="Received an invalid response from the flight provider.",
                    http_status=502,
                ) from e

            # Successful = 1
            if parsed.Status != 1 or not parsed.TokenId:
                error_msg = (
                    parsed.Error.ErrorMessage
                    if parsed.Error
                    else "Unknown authentication error"
                )
                logger.error("TBO Auth failed: %s", error_msg)
                raise ExternalProviderError(
                    provider_code="AUTH_FAILED",
                    message=f"TBO Auth Error: {error_msg}",
                    http_status=502,
                )

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
            raise ExternalProviderError(
                provider_code="LOGOUT_NO_SESSION",
                message="No active TBO session.",
                http_status=400,
            )

        payload = TBOLogoutRequest(
            ClientId=settings.TBO_CLIENT_ID,
            EndUserIp=settings.TBO_END_USER_IP,
            TokenAgencyId=self._cached_agency_id,  # type: ignore
            TokenMemberId=self._cached_member_id,  # type: ignore
            TokenId=self._cached_token,  # type: ignore
        )
        payload_data = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        data = await self._post_tbo_json(
            operation="TBO Logout",
            url=f"{self.shared_base_url}/Logout",
            payload_data=payload_data,
            timeout=30,
        )

        try:
            parsed = TBOLogoutResponse(**data)
        except Exception as e:
            logger.exception("Failed to parse TBO Logout response")
            raise ExternalProviderError(
                provider_code="LOGOUT_PARSE_ERROR",
                message="Received an invalid response from the flight provider.",
                http_status=502,
            ) from e

        if parsed.Status != 1 or parsed.Error.ErrorCode != 0:
            error_msg = parsed.Error.ErrorMessage or "Unknown logout error"
            logger.error("TBO Logout failed: %s", error_msg)
            raise ExternalProviderError(
                provider_code="LOGOUT_FAILED",
                message=f"TBO Logout Error: {error_msg}",
                http_status=502,
            )

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

        normalized_msg = (error_msg or "").lower()
        if any(marker in normalized_msg for marker in _SEAT_UNAVAILABLE_MARKERS):
            provider_code = "SEAT_UNAVAILABLE"
            http_status = 409
        elif any(marker in normalized_msg for marker in _MEAL_REQUIRED_MARKERS):
            provider_code = "MEAL_REQUIRED"
            http_status = 400
        else:
            provider_code, http_status = ERROR_CODE_MAP.get(
                error_code, ("UNKNOWN_ERROR", 500)
            )

        logger.error(
            "%s ERROR (%s): %s",
            context,
            provider_code,
            error_msg,
        )
        logger.error("Full TBO error response: %s", json.dumps(tbo_response, indent=2))
        raise ExternalProviderError(
            provider_code=provider_code,
            http_status=http_status,
            message=f"{context} Error: {error_msg}",
        )

    async def search(self, payload: TBOSearchRequest) -> TBOSearchResponse:
        """Perform flight search"""
        token = await self.authenticate()
        payload_data = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        payload_data["TokenId"] = token

        data = await self._post_tbo_json(
            operation="TBO Search",
            url=f"{self.air_base_url}/Search",
            payload_data=payload_data,
            timeout=360,
        )
        self._check_response_status(data, context="TBO Search")

        # Parse results individually — skip malformed itineraries instead of
        # failing the entire search.
        try:
            raw_results = data.get("Response", {}).get("Results", [])
            filtered_results: list[list[dict]] = []

            for direction_idx, direction_list in enumerate(raw_results):
                valid_items: list[dict] = []
                for item_idx, item in enumerate(direction_list):
                    try:
                        Itinerary(**item)
                        valid_items.append(item)
                    except (ValidationError, Exception) as ve:
                        logger.warning(
                            "Skipping malformed result [%d][%d] (ResultIndex=%s): %s",
                            direction_idx,
                            item_idx,
                            item.get("ResultIndex", "?"),
                            ve,
                        )
                filtered_results.append(valid_items)

            skipped = sum(
                len(raw) - len(filt) for raw, filt in zip(raw_results, filtered_results)
            )
            if skipped:
                logger.warning(
                    "TBO Search: skipped %d malformed results out of %d total",
                    skipped,
                    sum(len(d) for d in raw_results),
                )

            data["Response"]["Results"] = filtered_results
            return TBOSearchResponse(**data)
        except Exception as e:
            logger.exception("Failed to validate TBO search response")
            raise ExternalProviderError(
                provider_code="TBO_SEARCH_PARSE_ERROR",
                message="Received an invalid response from the flight provider.",
                http_status=502,
            ) from e

    async def get_fare_rule(self, payload: TBOFareRuleRequest) -> TBOFareRuleResponse:
        return await self._call_tbo_api(
            operation="TBO FareRule", endpoint="FareRule",
            payload=payload, response_model=TBOFareRuleResponse, timeout=60,
        )

    async def get_fare_quote(self, payload: TBOFareQuoteRequest) -> TBOFareQuoteResponse:
        return await self._call_tbo_api(
            operation="TBO FareQuote", endpoint="FareQuote",
            payload=payload, response_model=TBOFareQuoteResponse, timeout=60,
        )

    async def get_ssr(self, payload: TBOSSRRequest) -> TBOSSRResponse:
        return await self._call_tbo_api(
            operation="TBO SSR", endpoint="SSR",
            payload=payload, response_model=TBOSSRResponse, timeout=60,
        )

    async def book_flight(self, payload: TBOBookRequest) -> TBOBookResponse:
        return await self._call_tbo_api(
            operation="TBO Book", endpoint="Book",
            payload=payload, response_model=TBOBookResponse, timeout=300,
            critical=True,
        )

    async def generate_ticket_lcc(self, payload: TBOTicketLCCRequest) -> TBOTicketResponse:
        return await self._call_tbo_api(
            operation="TBO TicketLCC", endpoint="Ticket",
            payload=payload, response_model=TBOTicketResponse, timeout=300,
            critical=True,
        )

    async def generate_ticket_nonlcc(self, payload: TBOTicketNonLCCRequest) -> TBOTicketResponse:
        return await self._call_tbo_api(
            operation="TBO TicketNonLCC", endpoint="Ticket",
            payload=payload, response_model=TBOTicketResponse, timeout=300,
            critical=True,
        )

    async def get_booking_details_with_retry(
        self,
        end_user_ip: str,
        *,
        pnr: str | None = None,
        booking_id: int | None = None,
        trace_id: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        max_retries: int = 12,
        interval_seconds: float = 12.0,
    ) -> TBOGetBookingDetailsResponse | None:
        """Poll GetBookingDetails after a timeout to check if booking succeeded.

        When TBO Book/Ticket times out, the booking may have actually succeeded.
        Supports multiple lookup patterns: BookingId, PNR+Name, or TraceId.
        Polls up to max_retries times at interval_seconds apart.
        """
        token = await self.authenticate()
        lookup_desc = f"PNR={pnr} BookingId={booking_id} TraceId={trace_id}"

        for attempt in range(1, max_retries + 1):
            logger.info(
                "GetBookingDetails retry %d/%d for %s",
                attempt,
                max_retries,
                lookup_desc,
            )
            if attempt > 1:
                await asyncio.sleep(interval_seconds)

            try:
                payload = TBOGetBookingDetailsRequest(
                    EndUserIp=end_user_ip,
                    TokenId=token,
                    PNR=pnr,
                    BookingId=booking_id,
                    TraceId=trace_id,
                    FirstName=first_name,
                    LastName=last_name,
                )
                response = await self.get_booking_details(payload)
                error_message = (
                    response.Response.Error.ErrorMessage
                    if response.Response.Error and response.Response.Error.ErrorMessage
                    else ""
                )
                if "booking under process" in error_message.lower():
                    logger.info(
                        "GetBookingDetails still under process on attempt %d for %s",
                        attempt,
                        lookup_desc,
                    )
                    continue

                itin = response.Response.FlightItinerary
                if itin:
                    logger.info(
                        "GetBookingDetails resolved on attempt %d: PNR=%s status=%s",
                        attempt,
                        itin.PNR,
                        itin.Status,
                    )
                    return response
                logger.info(
                    "GetBookingDetails did not return itinerary on attempt %d for %s",
                    attempt,
                    lookup_desc,
                )
            except Exception as e:
                logger.warning("GetBookingDetails retry %d failed: %s", attempt, str(e))
                continue

        logger.warning(
            "GetBookingDetails gave up after %d retries for %s",
            max_retries,
            lookup_desc,
        )
        return None

    async def get_booking_details(self, payload: TBOGetBookingDetailsRequest) -> TBOGetBookingDetailsResponse:
        return await self._call_tbo_api(
            operation="TBO GetBookingDetails", endpoint="GetBookingDetails",
            payload=payload, response_model=TBOGetBookingDetailsResponse, timeout=60,
            check_status=False,
        )
