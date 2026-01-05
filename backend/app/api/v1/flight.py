import asyncio
import uuid
from operator import is_
from re import S

from app.api.v1.auth import get_current_user
from app.api.v1.dependencies import get_end_user_ip, get_tbo_client, get_tbo_transformer
from app.clients.exceptions import ExternalProviderError
from app.clients.tbo_client import TBOClient
from app.db.models.user import User
from app.schemas.internal.fare_quote import (
    FareQuoteRequest,
    FareQuoteResponse,
    FlightPriceDetail,
)
from app.schemas.internal.fare_rule import FareRulesResponse
from app.schemas.internal.flight import FlightSearchRequest, FlightSearchResponse
from app.schemas.internal.ssr import SsrRequest, SsrResponse
from app.schemas.tbo import (
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
from app.transformers.tbo_transformer import TBOTransformer
from app.utils.cache import get_flight_cache
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/flights", tags=["Flights"])


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
        # print("TBO Search Response:", tbo_response)
        response = await transformer.transform_search_response(
            tbo_response, payload, cache
        )
        return response
    except ExternalProviderError as e:
        # Handle "No result found" as a valid response (200 OK with empty flights)
        if "No result found" in str(e):
            # Return empty response with original request parameters
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
        # Re-raise other provider errors
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Flight provider error: {str(e)}",
        )


@router.get("/fare-rules/{fare_id}", response_model=FareRulesResponse)
async def get_fare_rules(
    fare_id: str,
    end_user_ip: str = Depends(get_end_user_ip),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    cache=Depends(get_flight_cache),
):
    # get from cache
    cached_data = cache.get(fare_id)
    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="No such flight found in cache"
        )

    tbo_request = TBOFareRuleRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=cached_data["TraceId"],
        ResultIndex=cached_data["ResultIndex"],
    )

    # tbo_request = await transformer.transform_fare_rule_request(payload, end_user_ip)
    tbo_response = await client.get_fare_rule(tbo_request)
    # print(tbo_response)
    response = transformer.transform_fare_rule_response(tbo_response)
    return response


@router.post("/fare-quote", response_model=FareQuoteResponse)
async def get_fare_quote(
    payload: FareQuoteRequest,
    end_user_ip: str = Depends(get_end_user_ip),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    cache=Depends(get_flight_cache),
):
    """Get fare quote for outbound and inbound (if roundtrip)"""

    # Get outbound from cache
    outbound_cached = cache.get(payload.fare_id_outbound)
    if not outbound_cached:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Outbound flight not found in cache",
        )

    # Build requests
    tasks = []
    outbound_req = TBOFareQuoteRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=outbound_cached["TraceId"],
        ResultIndex=outbound_cached["ResultIndex"],
    )
    tasks.append(client.get_fare_quote(outbound_req))

    inbound_cached = None
    if payload.trip_type == "roundtrip" and payload.fare_id_inbound:
        inbound_cached = cache.get(payload.fare_id_inbound)
        if not inbound_cached:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Inbound flight not found in cache",
            )
        inbound_req = TBOFareQuoteRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=inbound_cached["TraceId"],
            ResultIndex=inbound_cached["ResultIndex"],
        )
        tasks.append(client.get_fare_quote(inbound_req))

    # Call TBO API for both (or just outbound)
    tbo_responses = await asyncio.gather(*tasks)
    outbound_tbo_response = tbo_responses[0]
    inbound_tbo_response = tbo_responses[1] if len(tbo_responses) > 1 else None

    # Check outbound price
    outbound_price_changed = False
    outbound_detail = None

    if outbound_tbo_response.Response.IsPriceChanged:
        new_outbound_price = (
            outbound_tbo_response.Response.Results.Fare.BaseFare
            + outbound_tbo_response.Response.Results.Fare.Tax
        )
        # Allow 50 INR tolerance
        if new_outbound_price >= payload.initial_price_outbound + 50:
            outbound_price_changed = True
            outbound_detail = FlightPriceDetail(
                original_price=payload.initial_price_outbound,
                new_price=new_outbound_price,
                difference=new_outbound_price - payload.initial_price_outbound,
            )

    # Check inbound price (if roundtrip)
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

    # Determine overall response
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
    )


@router.post("/ssr")
async def get_ssr_details(
    payload: SsrRequest,
    cache=Depends(get_flight_cache),
    client: TBOClient = Depends(get_tbo_client),
    transformer: TBOTransformer = Depends(get_tbo_transformer),
    end_user_ip: str = Depends(get_end_user_ip),
):
    # get data from cache
    outbound_provider_ref = cache.get(payload.fare_id_outbound)
    if not outbound_provider_ref:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="No such flight found in cache"
        )

    is_lcc_outbound = outbound_provider_ref.get("IsLCC", False)
    is_lcc_inbound = False  # will check only if roundtrip

    # if international return , TBO gives everything in 1 call
    # for domestic return , call twice , once for each fare_id
    tasks = []

    out_req = TBOSSRRequest(
        EndUserIp=end_user_ip,
        TokenId="",
        TraceId=outbound_provider_ref["TraceId"],
        ResultIndex=outbound_provider_ref["ResultIndex"],
    )
    tasks.append(client.get_ssr(out_req))

    if payload.trip_type == "roundtrip" and not payload.is_international_return:
        inbound_provider_ref = cache.get(payload.fare_id_inbound)
        if not inbound_provider_ref:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="No such inbound flight found in cache",
            )
        is_lcc_inbound = inbound_provider_ref.get("IsLCC", False)
        in_req = TBOSSRRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=inbound_provider_ref["TraceId"],
            ResultIndex=inbound_provider_ref["ResultIndex"],
        )
        tasks.append(client.get_ssr(in_req))

    # call TBO API parallely
    tbo_responses = await asyncio.gather(*tasks)
    print("TBO SSR tasks:", tasks)
    outbound_ssr_response = tbo_responses[0]
    cache.set(f"raw_ssr_{payload.fare_id_outbound}", outbound_ssr_response)

    # transform  logic
    if payload.is_international_return:
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
            inbound_view = transformer.transform_lcc_ssr_response(
                baggage_options=outbound_ssr_response.Response.Baggage[1]
                if len(outbound_ssr_response.Response.Baggage) > 1
                else [],
                meal_options=outbound_ssr_response.Response.MealDynamic[1]
                if len(outbound_ssr_response.Response.MealDynamic) > 1
                else [],
                seat_options=outbound_ssr_response.Response.SeatDynamic[1]
                if len(outbound_ssr_response.Response.SeatDynamic) > 1
                else None,
            )
        else:
            # Non-LCC International Return
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
                if len(outbound_ssr_response.Response.Baggage) > 1
                else [],
                meal_options=outbound_ssr_response.Response.Meal,
                seat_options=outbound_ssr_response.Response.SeatDynamic[1]
                if len(outbound_ssr_response.Response.SeatDynamic) > 1
                else None,
            )
    else:
        # Oneway or Domestic Return
        if is_lcc_outbound:
            # OUTBOUND IS LCC
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
            # OUTBOUND IS NON-LCC
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
        # check for domestic return
        if len(tbo_responses) > 1:
            inbound_ssr_response = tbo_responses[1]
            cache.set(f"raw_ssr_{payload.fare_id_inbound}", inbound_ssr_response)

            if is_lcc_inbound:
                # INBOUND IS LCC
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
                # INBOUND IS NON-LCC
                inbound_view = transformer.transform_non_lcc_ssr_response(
                    baggage_options=inbound_ssr_response.Response.Baggage[0]
                    if inbound_ssr_response.Response.Baggage
                    else [],
                    meal_options=inbound_ssr_response.Response.Meal,
                    seat_options=inbound_ssr_response.Response.SeatDynamic[0]
                    if inbound_ssr_response.Response.SeatDynamic
                    else None,
                )

    return SsrResponse(
        outbound=outbound_view,
        inbound=inbound_view,
    )


@router.post("/book", response_model=TBOBookResponse)
async def book_flight(
    payload: TBOBookRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        client = TBOClient()
        response = await client.book_flight(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/ticket/lcc", response_model=TBOTicketResponse)
async def generate_ticket_lcc(
    payload: TBOTicketLCCRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate ticket for LCC (Low Cost Carrier) flights"""
    try:
        client = TBOClient()
        response = await client.generate_ticket_lcc(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/ticket/nonlcc", response_model=TBOTicketResponse)
async def generate_ticket_nonlcc(
    payload: TBOTicketNonLCCRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate ticket for non-LCC flights"""
    try:
        client = TBOClient()
        response = await client.generate_ticket_nonlcc(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/booking/details", response_model=TBOGetBookingDetailsResponse)
async def get_booking_details(
    payload: TBOGetBookingDetailsRequest,
    current_user: User = Depends(get_current_user),
):
    """Get booking details by PNR and Booking ID"""
    try:
        client = TBOClient()
        response = await client.get_booking_details(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
