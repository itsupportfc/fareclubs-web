import asyncio
import logging

from app.api.v1.dependencies import get_end_user_ip, get_tbo_client, get_tbo_transformer
from app.clients.exceptions import ExternalProviderError
from app.clients.tbo_client import TBOClient
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
    TBOSSRRequest,
)
from app.transformers.tbo_transformer import TBOTransformer
from app.utils.cache import get_flight_cache
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

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
