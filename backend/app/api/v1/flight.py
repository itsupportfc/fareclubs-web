from app.api.v1.auth import get_current_user
from app.clients.tbo_client import TBOClient
from app.db.models.user import User
from app.schemas.tbo import TBOSearchRequest, TBOSearchResponse
from app.schemas.tbo_book import TBOBookRequest, TBOBookResponse
from app.schemas.tbo_booking_details import (
    TBOGetBookingDetailsRequest,
    TBOGetBookingDetailsResponse,
)
from app.schemas.tbo_fare_quote import TBOFareQuoteRequest, TBOFareQuoteResponse
from app.schemas.tbo_farerule import TBOFareRuleRequest, TBOFareRuleResponse
from app.schemas.tbo_ssr import TBOSSRRequest, TBOSSRResponse
from app.schemas.tbo_ticket import (
    TBOTicketRequestLCC,
    TBOTicketRequestNonLCC,
    TBOTicketResponse,
)
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.post("/search", response_model=TBOSearchResponse)
async def search_flights(
    payload: TBOSearchRequest,
    # current_user: User = Depends(get_current_user),  # this makes api endpoint protected
):
    # print("Received payload:", payload)
    client = TBOClient()
    try:
        response = await client.search(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/fare-rules", response_model=TBOFareRuleResponse)
async def get_fare_rules(
    payload: TBOFareRuleRequest,
    current_user: User = Depends(get_current_user),
):
    client = TBOClient()
    try:
        response = await client.get_fare_rule(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/fare-quote", response_model=TBOFareQuoteResponse)
async def get_fare_quote(
    payload: TBOFareQuoteRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        client = TBOClient()
        response = await client.get_fare_quote(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/ssr", response_model=TBOSSRResponse)
async def get_ssr_details(
    payload: TBOSSRRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        client = TBOClient()
        response = await client.get_ssr(payload)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
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
    payload: TBOTicketRequestLCC,
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
    payload: TBOTicketRequestNonLCC,
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
