import asyncio
import logging
import traceback
from dataclasses import dataclass
from enum import IntEnum
from uuid import uuid4

import httpx
from app.api.v1.auth import get_current_user, get_optional_current_user
from app.api.v1.dependencies import get_end_user_ip, get_tbo_client, get_tbo_transformer
from app.clients.exceptions import ExternalProviderError
from app.clients.tbo_client import TBOClient, TBOParseError
from app.config import settings
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.internal.booking import (
    BookingConfirmRequest,
    BookingConfirmResponse,
    BookingCreateOrderRequest,
    BookingCreateOrderResponse,
)
from app.schemas.internal.fare_quote import (
    FareQuoteFlags,
    FareQuoteRequest,
    FareQuoteResponse,
    FlightPriceDetail,
    PerPassengerFare,
)
from app.schemas.internal.fare_rule import FareRulesResponse
from app.schemas.internal.flight import FlightSearchRequest, FlightSearchResponse
from app.schemas.internal.ssr import SsrRequest, SsrResponse
from app.schemas.tbo import (
    TBOFareQuoteRequest,
    TBOFareRuleRequest,
    TBOGetBookingDetailsRequest,
    TBOGetBookingDetailsResponse,
    TBOSSRRequest,
    TBOTicketNonLCCRequest,
    TBOTicketResponse,
)
from app.schemas.tbo.ssr import TBOSSRResponse
from app.services.booking_service import BookingService
from app.transformers.tbo_transformer import TBOTransformer
from app.utils import razorpay_utils
from app.utils.cache import get_flight_cache
from app.utils.email import (
    build_booking_attention_email,
    build_booking_failure_email,
    send_customer_eticket_email,
    send_staff_alert_email,
)
from app.utils.eticket_pdf import generate_eticket_pdf
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flights", tags=["Flights"])
limiter = Limiter(key_func=get_remote_address)


# ==============================================================================
# SEARCH
# ==============================================================================


@router.post("/search", response_model=FlightSearchResponse)
async def search_flights(
    payload: FlightSearchRequest,
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    cache=Depends(get_flight_cache),
):
    try:
        tbo_request = await transformer.trasform_search_request(request=payload)
        tbo_response = await client.search(tbo_request)
        response = await transformer.transform_search_response(
            tbo_response, payload, cache
        )
        return response
    except ExternalProviderError as e:
        if "No result found" in str(e):
            return FlightSearchResponse(
                search_id="",
                trip_type=payload.trip_type,
                origin=payload.origin,
                destination=payload.destination,
                departure_date=payload.departure_date,
                return_date=payload.return_date,
                passengers={
                    "adults": payload.adults,
                    "children": payload.children,
                    "infants": payload.infants,
                },
                cabin_class=payload.cabin_class,
                outbound_flights=[],
                inbound_flights=[],
                is_international_return=False,
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Flight provider error: {str(e)}",
        )


# ==============================================================================
# FARE RULES
# ==============================================================================


@router.get("/fare-rules/{fare_id}", response_model=FareRulesResponse)
async def get_fare_rules(
    fare_id: str,
    end_user_ip: str = Depends(get_end_user_ip),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    cache=Depends(get_flight_cache),
):
    cached_data = await cache.get(fare_id)
    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Your session has expired. Please search again to get updated fares.",
        )

    tbo_request = TBOFareRuleRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=cached_data["TraceId"],
        ResultIndex=cached_data["ResultIndex"],
    )
    tbo_response = await client.get_fare_rule(tbo_request)
    return transformer.transform_fare_rule_response(tbo_response)


# ==============================================================================
# FARE QUOTE (Steps 3 & 4: flags + per-passenger fares)
# ==============================================================================


def _extract_per_passenger_fares(itinerary) -> list[PerPassengerFare]:
    """Divide TBO FareBreakdown aggregate fares by PassengerCount to get per-head."""
    results = []
    for fb in itinerary.FareBreakdown:
        count = fb.PassengerCount or 1
        results.append(
            PerPassengerFare(
                pax_type=fb.PassengerType,
                currency=fb.Currency,
                base_fare=round(fb.BaseFare / count, 2),
                tax=round(fb.Tax / count, 2),
                yq_tax=round(fb.YQTax / count, 2),
                other_charges=0,
                additional_txn_fee_ofrd=round(
                    (fb.AdditionalTxnFeeOfrd or 0) / count, 2
                ),
                additional_txn_fee_pub=round((fb.AdditionalTxnFeePub or 0) / count, 2),
                pg_charge=round((fb.PGCharge or 0) / count, 2),
            )
        )
    return results


def _extract_flags(itinerary) -> FareQuoteFlags:
    """Extract compliance requirement flags from TBO FareQuote Itinerary."""
    return FareQuoteFlags(
        is_pan_required=itinerary.IsPanRequiredAtBook or False,
        is_passport_required=(
            (itinerary.IsPassportRequiredAtBook or False)
            or (itinerary.IsPassportRequiredAtTicket or False)
        ),
        # is_passport_full_detail_required=itinerary.IsPassportRequiredAtTicket or False,
        is_gst_allowed=itinerary.GSTAllowed or False,
        is_lcc=itinerary.IsLCC,
    )


@router.post("/fare-quote", response_model=FareQuoteResponse)
async def get_fare_quote(
    payload: FareQuoteRequest,
    end_user_ip: str = Depends(get_end_user_ip),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    cache=Depends(get_flight_cache),
):
    outbound_cached = await cache.get(payload.fare_id_outbound)
    if not outbound_cached:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Your session has expired. Please search again to get updated fares.",
        )

    tasks = []
    outbound_req = TBOFareQuoteRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=outbound_cached["TraceId"],
        ResultIndex=outbound_cached["ResultIndex"],
    )
    tasks.append(client.get_fare_quote(outbound_req))

    inbound_cached = None
    # International return: one fareId covers both directions — skip inbound TBO call
    if (
        payload.trip_type == "roundtrip"
        and payload.fare_id_inbound
        and not payload.is_international_return
    ):
        inbound_cached = await cache.get(payload.fare_id_inbound)
        if not inbound_cached:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Your session has expired. Please search again to get updated fares.",
            )
        inbound_req = TBOFareQuoteRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=inbound_cached["TraceId"],
            ResultIndex=inbound_cached["ResultIndex"],
        )
        tasks.append(client.get_fare_quote(inbound_req))

    tbo_responses = await asyncio.gather(*tasks)
    outbound_tbo_response = tbo_responses[0]
    inbound_tbo_response = tbo_responses[1] if len(tbo_responses) > 1 else None

    # Extract per-passenger fares and flags
    outbound_itinerary = outbound_tbo_response.Response.Results
    per_pax_outbound = _extract_per_passenger_fares(outbound_itinerary)
    flags_outbound = _extract_flags(outbound_itinerary)

    # Cache flags for use during booking confirmation
    await cache.set(
        f"flags_{payload.fare_id_outbound}", flags_outbound.model_dump(), ttl=900
    )

    # Cache verified total fare for price validation at order creation
    verified_outbound_total = (
        outbound_tbo_response.Response.Results.Fare.BaseFare
        + outbound_tbo_response.Response.Results.Fare.Tax
    )
    await cache.set(
        f"verified_price_{payload.fare_id_outbound}",
        verified_outbound_total,
        ttl=900,
    )

    per_pax_inbound: list[PerPassengerFare] = []
    flags_inbound = None
    is_time_changed_inbound = False

    if payload.is_international_return:
        # International return: single TBO fare covers both directions.
        # Duplicate outbound data as inbound so frontend has per-pax fares
        # for both directions (needed by SSR modal, booking page, etc.).
        per_pax_inbound = per_pax_outbound
        flags_inbound = flags_outbound
        is_time_changed_inbound = (
            getattr(outbound_tbo_response.Response, "IsTimeChanged", False) or False
        )

    elif inbound_tbo_response:
        # Domestic return: separate inbound TBO response
        inbound_itinerary = inbound_tbo_response.Response.Results
        per_pax_inbound = _extract_per_passenger_fares(inbound_itinerary)
        flags_inbound = _extract_flags(inbound_itinerary)
        is_time_changed_inbound = (
            getattr(inbound_tbo_response.Response, "IsTimeChanged", False) or False
        )
        if payload.fare_id_inbound:
            await cache.set(
                f"flags_{payload.fare_id_inbound}",
                flags_inbound.model_dump(),
                ttl=900,
            )
            verified_inbound_total = (
                inbound_tbo_response.Response.Results.Fare.BaseFare
                + inbound_tbo_response.Response.Results.Fare.Tax
            )
            await cache.set(
                f"verified_price_{payload.fare_id_inbound}",
                verified_inbound_total,
                ttl=900,
            )

    # Check price changes
    outbound_price_changed = False
    outbound_detail = None
    if outbound_tbo_response.Response.IsPriceChanged:
        new_outbound_price = (
            outbound_tbo_response.Response.Results.Fare.BaseFare
            + outbound_tbo_response.Response.Results.Fare.Tax
        )
        if new_outbound_price >= payload.initial_price_outbound + 50:
            outbound_price_changed = True
            outbound_detail = FlightPriceDetail(
                original_price=payload.initial_price_outbound,
                new_price=new_outbound_price,
                difference=new_outbound_price - payload.initial_price_outbound,
            )

    inbound_price_changed = False
    inbound_detail = None
    if inbound_tbo_response and payload.initial_price_inbound is not None:
        if inbound_tbo_response.Response.IsPriceChanged:
            new_inbound_price = (
                inbound_tbo_response.Response.Results.Fare.BaseFare
                + inbound_tbo_response.Response.Results.Fare.Tax
            )
            if new_inbound_price >= payload.initial_price_inbound + 50:
                inbound_price_changed = True
                inbound_detail = FlightPriceDetail(
                    original_price=payload.initial_price_inbound,
                    new_price=new_inbound_price,
                    difference=new_inbound_price - payload.initial_price_inbound,
                )

    is_price_changed = outbound_price_changed or inbound_price_changed
    message = ""
    if is_price_changed:
        changes = []
        if outbound_price_changed and outbound_detail:
            changes.append(f"Outbound increased by ₹{outbound_detail.difference:.2f}")
        if inbound_price_changed and inbound_detail:
            changes.append(f"Inbound increased by ₹{inbound_detail.difference:.2f}")
        message = " | ".join(changes)

    return FareQuoteResponse(
        is_price_changed=is_price_changed,
        outbound=outbound_detail,
        inbound=inbound_detail,
        message=message,
        per_passenger_fares_outbound=per_pax_outbound,
        per_passenger_fares_inbound=per_pax_inbound,
        flags_outbound=flags_outbound,
        flags_inbound=flags_inbound,
        is_time_changed_outbound=getattr(
            outbound_tbo_response.Response, "IsTimeChanged", False
        )
        or False,
        is_time_changed_inbound=is_time_changed_inbound,
    )


# ==============================================================================
# SSR
# ==============================================================================


@router.post("/ssr")
async def get_ssr_details(
    payload: SsrRequest,
    cache=Depends(get_flight_cache),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    end_user_ip: str = Depends(get_end_user_ip),
):
    outbound_provider_ref = await cache.get(payload.fare_id_outbound)
    if not outbound_provider_ref:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Your session has expired. Please search again to get updated fares.",
        )

    is_lcc_outbound = outbound_provider_ref.get("IsLCC", False)
    is_lcc_inbound = False

    tasks = []
    out_req = TBOSSRRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=outbound_provider_ref["TraceId"],
        ResultIndex=outbound_provider_ref["ResultIndex"],
    )
    tasks.append(client.get_ssr(out_req))

    if payload.trip_type == "roundtrip" and not payload.is_international_return:
        inbound_provider_ref = await cache.get(payload.fare_id_inbound)
        if not inbound_provider_ref:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Your session has expired. Please search again to get updated fares.",
            )
        is_lcc_inbound = inbound_provider_ref.get("IsLCC", False)
        in_req = TBOSSRRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=inbound_provider_ref["TraceId"],
            ResultIndex=inbound_provider_ref["ResultIndex"],
        )
        tasks.append(client.get_ssr(in_req))

    try:
        tbo_responses = await asyncio.gather(*tasks)
        outbound_ssr_response = tbo_responses[0]
        # Store as Pydantic model for correct round-trip serialization
        await cache.set_model(
            f"raw_ssr_{payload.fare_id_outbound}", outbound_ssr_response
        )

        if payload.is_international_return:
            if is_lcc_outbound:  # in this case inbound is also LCC, since it's the same fare with linked fares
                outbound_view = transformer.transform_lcc_ssr_response(
                    baggage_options=outbound_ssr_response.Response.Baggage[0]
                    if outbound_ssr_response.Response.Baggage
                    else [],
                    meal_options=outbound_ssr_response.Response.MealDynamic[0]
                    if outbound_ssr_response.Response.MealDynamic
                    else [],
                    seat_options=outbound_ssr_response.Response.SeatDynamic[0]
                    if outbound_ssr_response.Response.SeatDynamic
                    else None,
                )
                inbound_view = transformer.transform_lcc_ssr_response(
                    baggage_options=outbound_ssr_response.Response.Baggage[1]
                    if len(outbound_ssr_response.Response.Baggage or []) > 1
                    else [],
                    meal_options=outbound_ssr_response.Response.MealDynamic[1]
                    if len(outbound_ssr_response.Response.MealDynamic or []) > 1
                    else [],
                    seat_options=outbound_ssr_response.Response.SeatDynamic[1]
                    if len(outbound_ssr_response.Response.SeatDynamic or []) > 1
                    else None,
                )
            else:
                outbound_view = transformer.transform_non_lcc_ssr_response(
                    baggage_options=outbound_ssr_response.Response.Baggage[0]
                    if outbound_ssr_response.Response.Baggage
                    else [],
                    meal_options=outbound_ssr_response.Response.Meal,
                    seat_options=outbound_ssr_response.Response.SeatDynamic[0]
                    if outbound_ssr_response.Response.SeatDynamic
                    else None,
                )
                inbound_view = transformer.transform_non_lcc_ssr_response(
                    baggage_options=outbound_ssr_response.Response.Baggage[1]
                    if len(outbound_ssr_response.Response.Baggage or []) > 1
                    else [],
                    meal_options=outbound_ssr_response.Response.Meal,
                    seat_options=outbound_ssr_response.Response.SeatDynamic[1]
                    if len(outbound_ssr_response.Response.SeatDynamic or []) > 1
                    else None,
                )
        else:
            if is_lcc_outbound:
                outbound_view = transformer.transform_lcc_ssr_response(
                    baggage_options=outbound_ssr_response.Response.Baggage[0]
                    if outbound_ssr_response.Response.Baggage
                    else [],
                    meal_options=outbound_ssr_response.Response.MealDynamic[0]
                    if outbound_ssr_response.Response.MealDynamic
                    else [],
                    seat_options=outbound_ssr_response.Response.SeatDynamic[0]
                    if outbound_ssr_response.Response.SeatDynamic
                    else None,
                )
            else:
                outbound_view = transformer.transform_non_lcc_ssr_response(
                    baggage_options=outbound_ssr_response.Response.Baggage[0]
                    if outbound_ssr_response.Response.Baggage
                    else [],
                    meal_options=outbound_ssr_response.Response.Meal,
                    seat_options=outbound_ssr_response.Response.SeatDynamic[0]
                    if outbound_ssr_response.Response.SeatDynamic
                    else None,
                )

            inbound_view = None
            if len(tbo_responses) > 1:
                inbound_ssr_response = tbo_responses[1]
                await cache.set_model(
                    f"raw_ssr_{payload.fare_id_inbound}", inbound_ssr_response
                )

                if is_lcc_inbound:
                    inbound_view = transformer.transform_lcc_ssr_response(
                        baggage_options=inbound_ssr_response.Response.Baggage[0]
                        if inbound_ssr_response.Response.Baggage
                        else [],
                        meal_options=inbound_ssr_response.Response.MealDynamic[0]
                        if inbound_ssr_response.Response.MealDynamic
                        else [],
                        seat_options=inbound_ssr_response.Response.SeatDynamic[0]
                        if inbound_ssr_response.Response.SeatDynamic
                        else None,
                    )
                else:
                    inbound_view = transformer.transform_non_lcc_ssr_response(
                        baggage_options=inbound_ssr_response.Response.Baggage[0]
                        if inbound_ssr_response.Response.Baggage
                        else [],
                        meal_options=inbound_ssr_response.Response.Meal,
                        seat_options=inbound_ssr_response.Response.SeatDynamic[0]
                        if inbound_ssr_response.Response.SeatDynamic
                        else None,
                    )

        return SsrResponse(outbound=outbound_view, inbound=inbound_view)
    except (ExternalProviderError, Exception):
        return SsrResponse(outbound=None, inbound=None)


# ==============================================================================
# BOOKING — 2-step flow: create-order → confirm
# ==============================================================================


@router.post("/booking/create-order", response_model=BookingCreateOrderResponse)
@limiter.limit("5/minute")  # ← rate limit: 5 order attempts per IP per minute
async def create_booking_order(
    request: Request,  # required by slowapi to read client IP
    payload: BookingCreateOrderRequest,
    cache=Depends(get_flight_cache),
    current_user: User | None = Depends(get_optional_current_user),
):
    req_id = uuid4().hex[:8]
    # Log differently for guests vs logged-in users — both are valid
    user_label = f"user_id={current_user.id}" if current_user else "guest"
    logger.info(
        "[%s] create_booking_order : %s, fare_id_outbound=%s, fare_id_inbound=%s, total_amount=₹%.2f",
        req_id,
        user_label,
        payload.fare_id_outbound,
        payload.fare_id_inbound,
        payload.total_amount,
    )
    cached = await cache.get(payload.fare_id_outbound)
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Your session has expired. Please search again to get updated fares.",
        )

    # Verify total_amount matches the fare confirmed by fare-quote
    verified_outbound = await cache.get(f"verified_price_{payload.fare_id_outbound}")
    if verified_outbound is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fare quote has not been completed. Please complete fare verification before booking.",
        )

    expected_total = verified_outbound
    if payload.fare_id_inbound:
        verified_inbound = await cache.get(f"verified_price_{payload.fare_id_inbound}")
        if verified_inbound is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inbound fare quote has not been completed. Please complete fare verification before booking.",
            )
        expected_total += verified_inbound

    # 3. Amount check — round to avoid floating-point precision issues
    #    Principle: Never compare floats with ==. Round both sides to 2 decimal places.
    #    We allow a small tolerance (₹1) to handle rounding differences between
    #    frontend and backend, but the client must NOT underpay by more than that.
    submitted = round(payload.total_amount, 2)
    expected = round(expected_total, 2)
    if submitted < expected - 1.0:
        logger.warning(
            "[%s] Amount mismatch: submitted=%.2f expected=%.2f",
            req_id,
            submitted,
            expected,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Amount mismatch: submitted ₹{submitted}, expected ₹{expected}. Please refresh fares.",
        )

    try:
        order = razorpay_utils.create_order(
            amount_paise=int(expected * 100),
            receipt=payload.fare_id_outbound,
        )
    except Exception as e:
        logger.error("[%s] Razorpay order creation failed: %s", req_id, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment gateway is temporarily unavailable. Please try again.",
            # ← never leak str(e) — internal error details stay in logs
        )

    logger.info(
        "[%s] create_booking_order: Razorpay order created (order_id=%s, amount_paise=%d)",
        req_id,
        order["id"],
        order["amount"],
    )

    return BookingCreateOrderResponse(
        razorpay_order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        verified_amount=expected,
    )


class TicketStatus(IntEnum):
    FAILED = 0
    CONFIRMED = 1
    IN_PROGRESS = 2
    UNAVAILABLE = 3
    SYSTEM_ERROR = 4
    PENDING = 5
    ISSUED = 6
    PRICE_CHANGED = 8
    PROVIDER_ERROR = 9


class BookStatus(IntEnum):
    NOT_SET = 0
    SUCCESSFUL = 1
    FAILED = 2
    OTHER_FARE = 3
    OTHER_CLASS = 4
    BOOKED_OTHER = 5
    NOT_CONFIRMED = 6


_FAILED_TICKET_STATUSES = {
    TicketStatus.FAILED,
    TicketStatus.UNAVAILABLE,
    TicketStatus.SYSTEM_ERROR,
    TicketStatus.PROVIDER_ERROR,
}
_SOFT_TICKET_STATUSES = {TicketStatus.IN_PROGRESS, TicketStatus.PENDING}
_SUCCESS_TICKET_STATUSES = {TicketStatus.CONFIRMED, TicketStatus.ISSUED}

_BOOK_STATUS_TO_TICKET_STATUS = {
    BookStatus.NOT_SET: TicketStatus.PENDING,
    BookStatus.SUCCESSFUL: TicketStatus.CONFIRMED,
    BookStatus.FAILED: TicketStatus.FAILED,
    BookStatus.OTHER_FARE: TicketStatus.PRICE_CHANGED,
    BookStatus.OTHER_CLASS: TicketStatus.PRICE_CHANGED,
    BookStatus.BOOKED_OTHER: TicketStatus.ISSUED,
    BookStatus.NOT_CONFIRMED: TicketStatus.PENDING,
}


def _ticket_status_from_booking_status(booking_status: int | None) -> int:
    if booking_status is None:
        return TicketStatus.PENDING
    return _BOOK_STATUS_TO_TICKET_STATUS.get(booking_status, TicketStatus.PENDING)


def _mark_pending_with_support(
    resp: BookingConfirmResponse,
    payload: BookingConfirmRequest,
    error_message: str,
) -> BookingConfirmResponse:
    resp.status = "pending"
    resp.support_phone = settings.SUPPORT_PHONE or None
    resp.support_email = settings.SUPPORT_EMAIL or None
    resp.error_message = error_message
    resp.razorpay_payment_id = payload.razorpay_payment_id
    resp.razorpay_order_id = payload.razorpay_order_id
    return resp


async def _send_eticket_background(provider_raw: dict, pnr: str) -> None:
    """Generate PDF and email e-ticket to the lead passenger. Used as a background task."""
    try:
        from app.utils.eticket_pdf import _extract_itinerary

        itinerary = _extract_itinerary(provider_raw)
        if not itinerary:
            logger.warning("Cannot send e-ticket email: no itinerary in provider_raw")
            return

        passengers = itinerary.get("Passenger", [])
        lead_pax = next(
            (p for p in passengers if p.get("IsLeadPax")),
            passengers[0] if passengers else None,
        )
        if not lead_pax or not lead_pax.get("Email"):
            logger.info("No lead passenger email — skipping e-ticket email")
            return

        pdf_bytes = generate_eticket_pdf(provider_raw)
        passenger_name = (
            f"{lead_pax.get('FirstName', '')} {lead_pax.get('LastName', '')}".strip()
        )
        await send_customer_eticket_email(
            to_email=lead_pax["Email"],
            passenger_name=passenger_name,
            pnr=pnr,
            pdf_bytes=pdf_bytes,
        )
    except Exception:
        logger.exception("Background e-ticket email failed for PNR %s", pnr)


def _decorate_response(
    resp: BookingConfirmResponse,
    payload: BookingConfirmRequest,
    background_tasks: BackgroundTasks,
    ticket_provider_raw: dict | None = None,
) -> BookingConfirmResponse:
    ts = resp.ticket_status

    if ts in _SUCCESS_TICKET_STATUSES:
        resp.status = "confirmed"
        if ticket_provider_raw:
            background_tasks.add_task(
                _send_eticket_background, ticket_provider_raw, resp.pnr
            )
        return resp

    if ts in _SOFT_TICKET_STATUSES:
        resp = _mark_pending_with_support(
            resp,
            payload,
            "Your booking is currently being verified with the airline. Our team will confirm shortly.",
        )
        subject, html = build_booking_attention_email(
            payload,
            f"TicketStatus={ts} (in progress/verification)",
            payload.razorpay_payment_id,
            payload.razorpay_order_id,
        )
        background_tasks.add_task(send_staff_alert_email, subject, html)
        return resp

    if ts == TicketStatus.PRICE_CHANGED:
        resp = _mark_pending_with_support(
            resp,
            payload,
            "Fare changed during ticketing. Our team has been notified to resolve this quickly.",
        )
        subject, html = build_booking_attention_email(
            payload,
            "TicketStatus=8 (price changed)",
            payload.razorpay_payment_id,
            payload.razorpay_order_id,
        )
        background_tasks.add_task(send_staff_alert_email, subject, html)
        return resp

    if ts in _FAILED_TICKET_STATUSES:
        resp = _mark_pending_with_support(
            resp,
            payload,
            (
                "Your payment was successful but ticket issuance encountered an issue. "
                "Our team has been notified and will resolve this shortly."
            ),
        )
        subject, html = build_booking_failure_email(
            payload,
            f"TicketStatus={ts} (failed)",
            payload.razorpay_payment_id,
            payload.razorpay_order_id,
        )
        background_tasks.add_task(send_staff_alert_email, subject, html)
        return resp

    resp = _mark_pending_with_support(
        resp,
        payload,
        "Your booking status is under verification. Our team has been notified.",
    )
    subject, html = build_booking_failure_email(
        payload,
        f"TicketStatus={ts} (unknown)",
        payload.razorpay_payment_id,
        payload.razorpay_order_id,
    )
    background_tasks.add_task(send_staff_alert_email, subject, html)
    return resp


async def _ticket_single_leg(
    *,
    direction: str = "outbound",
    is_lcc: bool,
    payload: BookingConfirmRequest,
    cached_data: dict,
    end_user_ip: str,
    raw_ssr: TBOSSRResponse | None,
    client: TBOClient,
    transformer: TBOTransformer,
) -> TBOTicketResponse:
    """Book and ticket a single flight leg (LCC or non-LCC)."""
    if is_lcc:
        lcc_req = transformer.transform_ticket_lcc_request(
            payload,
            cached_data,
            end_user_ip,
            raw_ssr,
            direction=direction,
        )
        return await client.generate_ticket_lcc(lcc_req)

    book_req = transformer.transform_book_request(
        payload,
        cached_data,
        end_user_ip,
        raw_ssr,
        direction=direction,
    )
    book_resp = await client.book_flight(book_req)
    book_inner = book_resp.Response.Response
    if not book_inner:
        raise ExternalProviderError(
            provider_code="BOOK_FAILED",
            http_status=502,
            message="TBO Book did not return booking details.",
        )

    nonlcc_req = TBOTicketNonLCCRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=cached_data["TraceId"],
        PNR=book_inner.PNR,
        BookingId=book_inner.BookingId,
        IsPriceChangeAccepted=True,
    )
    return await client.generate_ticket_nonlcc(nonlcc_req)


# ==============================================================================
# LegResult pattern — partial-failure-safe booking confirmation
# ==============================================================================


@dataclass
class LegResult:
    """Encapsulates the outcome of processing a single flight leg.

    Internal-only, never serialized. Holds ticket response OR recovery
    response OR error in one object. The `succeeded` property gives a clean boolean.
    """

    direction: str  # "outbound" | "inbound"
    is_lcc: bool
    cached_data: dict

    # Exactly one of these will be populated:
    ticket_response: TBOTicketResponse | None = None
    recovery_response: TBOGetBookingDetailsResponse | None = None
    recovered_ticket_status: int | None = None
    error: Exception | None = None

    # Set after persistence:
    booking: object | None = None  # Booking model instance

    @property
    def succeeded(self) -> bool:
        return self.ticket_response is not None or self.recovery_response is not None

    @property
    def provider_raw(self) -> dict | None:
        if self.ticket_response:
            return self.ticket_response.model_dump(mode="json")
        if self.recovery_response:
            return self.recovery_response.model_dump(mode="json")
        return None


async def _process_single_leg(
    *,
    direction: str,
    is_lcc: bool,
    payload: BookingConfirmRequest,
    cached_data: dict,
    end_user_ip: str,
    raw_ssr: TBOSSRResponse | None,
    client: TBOClient,
    transformer: TBOTransformer,
    req_id: str = "",
) -> LegResult:
    """Process one flight leg: ticket it, recover on timeout, capture errors.

    Never raises — all errors captured into LegResult. This ensures
    asyncio.gather never cancels the sibling task on roundtrip.
    """
    result = LegResult(direction=direction, is_lcc=is_lcc, cached_data=cached_data)
    try:
        logger.info(
            "[%s] _process_single_leg: about to ticket %s leg", req_id, direction
        )
        result.ticket_response = await _ticket_single_leg(
            direction=direction,
            is_lcc=is_lcc,
            payload=payload,
            cached_data=cached_data,
            end_user_ip=end_user_ip,
            raw_ssr=raw_ssr,
            client=client,
            transformer=transformer,
        )
    except httpx.TimeoutException as timeout_err:
        logger.warning(
            "TBO Book/Ticket timed out for %s leg (razorpay_payment_id=%s): %s",
            direction,
            payload.razorpay_payment_id,
            str(timeout_err),
        )
        try:
            lead_pax = next(
                (p for p in payload.passengers if p.is_lead_pax),
                payload.passengers[0],
            )
            details_resp = await client.get_booking_details_with_retry(
                end_user_ip=end_user_ip,
                trace_id=cached_data.get("TraceId"),
                first_name=lead_pax.first_name,
                last_name=lead_pax.last_name,
            )
            if details_resp and details_resp.Response.FlightItinerary:
                itin = details_resp.Response.FlightItinerary
                result.recovery_response = details_resp
                result.recovered_ticket_status = _ticket_status_from_booking_status(
                    itin.Status
                )
                logger.info(
                    "Recovered %s booking via GetBookingDetails (pnr=%s)",
                    direction,
                    itin.PNR,
                )
            else:
                result.error = Exception(
                    f"TBO timeout on {direction} leg, recovery found no booking"
                )
        except Exception as recovery_err:
            logger.error(
                "Recovery lookup failed for %s leg: %s", direction, recovery_err
            )
            result.error = timeout_err
    except Exception as e:
        result.error = e
    return result


async def _persist_leg_result(
    result: LegResult,
    *,
    booking_service: BookingService,
    user_id: int | None,
    payment,
    trip_type: str,
    is_lcc: bool,
    linked_booking_id: int | None = None,
) -> None:
    """Persist a LegResult to DB. Mutates result.booking in place.

    Errors are caught here so that if outbound persistence succeeds but
    inbound throws, the outbound booking survives.
    """
    try:
        if result.ticket_response is not None:
            result.booking = await booking_service.save_booking(
                user_id=user_id,
                payment=payment,
                provider="tbo",
                ticket_response=result.ticket_response,
                direction=result.direction,
                trip_type=trip_type,
                is_lcc=result.is_lcc,
                linked_booking_id=linked_booking_id,
            )
        elif result.recovery_response is not None:
            result.booking = await booking_service.save_booking_from_details(
                user_id=user_id,
                payment=payment,
                provider="tbo",
                details_response=result.recovery_response,
                direction=result.direction,
                trip_type=trip_type,
                is_lcc=result.is_lcc,
                ticket_status=result.recovered_ticket_status,
                linked_booking_id=linked_booking_id,
            )
        else:
            error_msg = str(result.error) if result.error else "Unknown error"
            result.booking = await booking_service.save_failed_booking(
                user_id=user_id,
                payment=payment,
                provider="tbo",
                direction=result.direction,
                trip_type=trip_type,
                is_lcc=result.is_lcc,
                error_message=error_msg,
            )
            if isinstance(result.error, TBOParseError) and hasattr(
                result.error, "raw_response"
            ):
                result.booking.provider_raw = result.error.raw_response
                result.booking.status = "needs_attention"
    except Exception as persist_err:
        logger.error(
            "Failed to persist %s leg: %s\n%s",
            result.direction,
            persist_err,
            traceback.format_exc(),
        )
        if result.succeeded:
            result.error = persist_err


def _send_leg_alerts(
    result: LegResult,
    payload: BookingConfirmRequest,
    background_tasks: BackgroundTasks,
) -> None:
    """Send staff alert for a failed leg."""
    if result.succeeded:
        return
    error_msg = str(result.error) if result.error else "Unknown error"
    label = result.direction.upper()
    if isinstance(result.error, TBOParseError):
        subject, html = build_booking_attention_email(
            payload,
            f"[{label}] TBO parse error: {error_msg}",
            payload.razorpay_payment_id,
            payload.razorpay_order_id,
        )
    else:
        subject, html = build_booking_failure_email(
            payload,
            f"[{label}] {error_msg}",
            payload.razorpay_payment_id,
            payload.razorpay_order_id,
        )
    background_tasks.add_task(send_staff_alert_email, subject, html)


def _build_response_from_legs(
    *,
    outbound: LegResult,
    inbound: LegResult | None,
    payload: BookingConfirmRequest,
    background_tasks: BackgroundTasks,
    transformer: TBOTransformer,
) -> BookingConfirmResponse:
    """Build final API response from LegResult(s).

    Handles all permutations: both succeed, one fails (partial),
    both fail (pending), oneway (inbound=None).
    """
    # --- Build outbound portion of response ---
    if outbound.succeeded:
        if outbound.ticket_response:
            resp = transformer.transform_booking_confirm_response(
                outbound.ticket_response,
                outbound.is_lcc,
            )
        else:
            itin = outbound.recovery_response.Response.FlightItinerary
            resp = BookingConfirmResponse(
                pnr=itin.PNR,
                booking_id=itin.BookingId,
                is_lcc=outbound.is_lcc,
                ticket_status=outbound.recovered_ticket_status,
                ssr_denied=False,
                invoice_no=itin.InvoiceNo,
                invoice_amount=itin.InvoiceAmount,
            )
        resp.booking_id = outbound.booking.id if outbound.booking else 0
    else:
        # Outbound failed
        _send_leg_alerts(outbound, payload, background_tasks)
        resp = BookingConfirmResponse(
            pnr="PENDING",
            booking_id=outbound.booking.id if outbound.booking else 0,
            is_lcc=outbound.is_lcc,
            ticket_status=TicketStatus.PENDING,
            ssr_denied=False,
            status="pending",
            support_phone=settings.SUPPORT_PHONE or None,
            support_email=settings.SUPPORT_EMAIL or None,
            error_message=(
                "Your payment was successful but we encountered an issue completing your booking. "
                "Our team has been notified and will contact you shortly."
            ),
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_order_id=payload.razorpay_order_id,
        )

    # --- Attach inbound portion (roundtrip only) ---
    if inbound is not None:
        if inbound.succeeded:
            if inbound.ticket_response:
                resp_in = transformer.transform_booking_confirm_response(
                    inbound.ticket_response,
                    inbound.is_lcc,
                )
                resp.pnr_inbound = resp_in.pnr
            else:
                resp.pnr_inbound = (
                    inbound.recovery_response.Response.FlightItinerary.PNR
                )
            resp.booking_id_inbound = inbound.booking.id if inbound.booking else 0
            resp.inbound_status = "confirmed"
        else:
            _send_leg_alerts(inbound, payload, background_tasks)
            resp.pnr_inbound = "PENDING"
            resp.booking_id_inbound = inbound.booking.id if inbound.booking else 0
            resp.inbound_status = "failed"
            resp.inbound_error_message = (
                "Your return flight encountered an issue. "
                "Our team has been notified and will resolve this shortly."
            )

    # --- Determine overall status ---
    if inbound is not None:
        if outbound.succeeded and not inbound.succeeded:
            resp.status = "partial"
        elif not outbound.succeeded and inbound.succeeded:
            resp.status = "partial"
            resp.error_message = (
                "Your outbound flight encountered an issue but your return flight is confirmed. "
                "Our team has been notified and will resolve this shortly."
            )

    # --- Decorate (e-ticket dispatch, soft-status alerts) for successful outbound ---
    if outbound.succeeded:
        return _decorate_response(
            resp,
            payload,
            background_tasks,
            ticket_provider_raw=outbound.provider_raw,
        )
    return resp


@router.post("/booking/confirm", response_model=BookingConfirmResponse)
async def confirm_booking(
    payload: BookingConfirmRequest,
    background_tasks: BackgroundTasks,
    cache=Depends(get_flight_cache),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    end_user_ip: str = Depends(get_end_user_ip),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    req_id = uuid4().hex[:8]
    logger.info(
        "[%s] confirm_booking START: razorpay_payment_id=%s, is_international_return=%s, fare_id_outbound=%s, fare_id_inbound=%s",
        req_id,
        payload.razorpay_payment_id,
        payload.is_international_return,
        payload.fare_id_outbound,
        payload.fare_id_inbound,
    )

    # 1. Validate cache
    cached_data = await cache.get(payload.fare_id_outbound)
    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Your session has expired. Please search again to get updated fares.",
        )

    # 2. Verify Razorpay payment signature
    if not razorpay_utils.verify_payment_signature(
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment verification failed — invalid signature",
        )

    is_lcc: bool = cached_data.get("IsLCC", False)
    # why only outbound?
    raw_ssr = await cache.get_model(
        f"raw_ssr_{payload.fare_id_outbound}", TBOSSRResponse
    )
    # wrong message
    if is_lcc and not raw_ssr:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Seat and meal options have expired. Please refresh SSR and try booking again.",
        )

    is_domestic_return = (
        payload.trip_type == "roundtrip"
        and payload.fare_id_inbound is not None
        and not payload.is_international_return
    )

    # check the model schema!
    # 3. Save payment to DB
    booking_service = BookingService(db)
    payment = await booking_service.save_payment(
        user_id=current_user.id if current_user else None,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
        amount_paise=int(payload.total_amount * 100),
    )

    # Phase 1: Build legs list
    legs_to_process = [
        {
            "direction": "outbound",
            "is_lcc": is_lcc,
            "payload": payload,
            "cached_data": cached_data,
            "end_user_ip": end_user_ip,
            "raw_ssr": raw_ssr,
            "client": client,
            "transformer": transformer,
            "req_id": req_id,
        }
    ]

    cached_inbound = None
    is_lcc_inbound = False
    if is_domestic_return:
        cached_inbound = await cache.get(payload.fare_id_inbound)
        if not cached_inbound:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Your session has expired. Please search again to get updated fares.",
            )
        raw_ssr_in = await cache.get_model(
            f"raw_ssr_{payload.fare_id_inbound}", TBOSSRResponse
        )
        is_lcc_inbound = cached_inbound.get("IsLCC", False)
        if is_lcc_inbound and not raw_ssr_in:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Seat and meal options for return flight have expired. Please refresh SSR and try booking again.",
            )
        legs_to_process.append(
            {
                "direction": "inbound",
                "is_lcc": is_lcc_inbound,
                "payload": payload,
                "cached_data": cached_inbound,
                "end_user_ip": end_user_ip,
                "raw_ssr": raw_ssr_in,
                "client": client,
                "transformer": transformer,
                "req_id": req_id,
            }
        )

    logger.info(
        "[%s] confirm_booking: legs_to_process=%d, is_domestic_return=%s, directions=%s",
        req_id,
        len(legs_to_process),
        is_domestic_return,
        [leg["direction"] for leg in legs_to_process],
    )

    # Phase 2: Process all legs concurrently (_process_single_leg never raises)
    leg_results = await asyncio.gather(
        *[_process_single_leg(**leg) for leg in legs_to_process]
    )

    # Phase 3: Persist sequentially (outbound first for linked_booking_id)
    user_id = current_user.id if current_user else None
    outbound_result: LegResult = leg_results[0]
    await _persist_leg_result(
        outbound_result,
        booking_service=booking_service,
        user_id=user_id,
        payment=payment,
        trip_type=payload.trip_type,
        is_lcc=is_lcc,
    )

    inbound_result: LegResult | None = None
    if len(leg_results) > 1:
        inbound_result = leg_results[1]
        linked_id = outbound_result.booking.id if outbound_result.booking else None
        await _persist_leg_result(
            inbound_result,
            booking_service=booking_service,
            user_id=user_id,
            payment=payment,
            trip_type=payload.trip_type,
            is_lcc=is_lcc_inbound,
            linked_booking_id=linked_id,
        )

    # Phase 4: Single commit
    try:
        await db.commit()
    except Exception as commit_err:
        logger.error(
            "DB commit failed after booking (razorpay_payment_id=%s): %s\n%s",
            payload.razorpay_payment_id,
            commit_err,
            traceback.format_exc(),
        )
        subject, html = build_booking_failure_email(
            payload,
            f"DB commit error: {commit_err}",
            payload.razorpay_payment_id,
            payload.razorpay_order_id,
        )
        background_tasks.add_task(send_staff_alert_email, subject, html)
        return BookingConfirmResponse(
            pnr="PENDING",
            booking_id=0,
            is_lcc=is_lcc,
            ticket_status=TicketStatus.PENDING,
            ssr_denied=False,
            status="pending",
            support_phone=settings.SUPPORT_PHONE or None,
            support_email=settings.SUPPORT_EMAIL or None,
            error_message=(
                "Your payment was successful but we encountered an issue completing your booking. "
                "Our team has been notified and will contact you shortly."
            ),
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_order_id=payload.razorpay_order_id,
        )

    # Phase 5: Build response
    return _build_response_from_legs(
        outbound=outbound_result,
        inbound=inbound_result,
        payload=payload,
        background_tasks=background_tasks,
        transformer=transformer,
    )


@router.get("/booking/{booking_id}/eticket")
async def download_eticket(
    booking_id: int,
    pnr: str,
    db: AsyncSession = Depends(get_db),
):
    """Download e-ticket PDF for a confirmed booking (verified by PNR)."""
    logger.info("download_eticket called: booking_id=%s, pnr=%s", booking_id, pnr)
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id_and_pnr(booking_id, pnr)
    if not booking:
        logger.warning(
            "E-ticket: booking not found (booking_id=%s, pnr=%s)", booking_id, pnr
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    if booking.status != "confirmed":
        logger.warning(
            "E-ticket: booking status is '%s', not 'confirmed' (booking_id=%s)",
            booking.status,
            booking_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-ticket is only available for confirmed bookings.",
        )
    if not booking.provider_raw:
        logger.warning("E-ticket: provider_raw is missing (booking_id=%s)", booking_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking data not available for e-ticket generation.",
        )

    try:
        logger.info("E-ticket: generating PDF for booking_id=%s", booking_id)
        pdf_bytes = generate_eticket_pdf(booking.provider_raw)
    except Exception as e:
        logger.exception("Failed to generate e-ticket PDF for booking %s", booking_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate e-ticket PDF.",
        )

    logger.info(
        "E-ticket: PDF generated successfully for booking_id=%s, size=%d bytes",
        booking_id,
        len(pdf_bytes),
    )
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=FareClubs_ETicket_{booking.pnr}.pdf"
        },
    )


@router.post("/booking/details")
async def get_booking_details(
    payload: TBOGetBookingDetailsRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        tbo_client = TBOClient()
        response = await tbo_client.get_booking_details(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
