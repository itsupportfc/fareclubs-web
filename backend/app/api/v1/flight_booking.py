"""Thin booking router.

This intentionally owns only checkout-related endpoints.
Search / fare quote / SSR can stay in the broader flight router.
"""

import logging

from app.api.v1.auth import get_optional_current_user
from app.api.v1.dependencies import get_end_user_ip, get_tbo_client, get_tbo_transformer
from app.db.database import get_db
from app.db.models.user import User
from app.domain.booking_enums import BookingRecordStatus
from app.schemas.internal.booking import (
    BookingConfirmRequest,
    BookingConfirmResponse,
    BookingCreateOrderRequest,
    BookingCreateOrderResponse,
)
from app.services.booking_checkout_service import BookingCheckoutService
from app.services.booking_service import BookingService
from app.transformers.booking_transformer import BookingConfirmationTransformer
from app.transformers.tbo_transformer import TBOTransformer
from app.utils.cache import FlightCache, get_flight_cache
from app.utils.eticket_pdf import generate_eticket_pdf
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/flights/booking", tags=["Flight Booking"])
limiter = Limiter(key_func=get_remote_address)


def _get_checkout_service(
    *,
    cache: FlightCache,
    db: AsyncSession,
    client,
    request_transformer: TBOTransformer,
) -> BookingCheckoutService:
    return BookingCheckoutService(
        cache=cache,
        client=client,
        request_transformer=request_transformer,
        response_transformer=BookingConfirmationTransformer(),
        booking_service=BookingService(db),
    )


@router.post("/create-order", response_model=BookingCreateOrderResponse)
@limiter.limit("5/minute")
async def create_booking_order(
    request: Request,
    payload: BookingCreateOrderRequest,
    cache: FlightCache = Depends(get_flight_cache),
    db: AsyncSession = Depends(get_db),
    client=Depends(get_tbo_client),
    request_transformer: TBOTransformer = Depends(get_tbo_transformer),
    current_user: User | None = Depends(get_optional_current_user),
):
    checkout_service = _get_checkout_service(
        cache=cache,
        db=db,
        client=client,
        request_transformer=request_transformer,
    )
    return await checkout_service.create_payment_order(
        payload=payload,
        current_user=current_user,
    )


@router.post("/confirm", response_model=BookingConfirmResponse)
@limiter.limit("3/minute")
async def confirm_booking(
    request: Request,
    payload: BookingConfirmRequest,
    background_tasks: BackgroundTasks,
    cache: FlightCache = Depends(get_flight_cache),
    client=Depends(get_tbo_client),
    request_transformer: TBOTransformer = Depends(get_tbo_transformer),
    end_user_ip: str = Depends(get_end_user_ip),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    checkout_service = _get_checkout_service(
        cache=cache,
        db=db,
        client=client,
        request_transformer=request_transformer,
    )
    return await checkout_service.confirm_booking(
        payload=payload,
        background_tasks=background_tasks,
        end_user_ip=end_user_ip,
        current_user=current_user,
    )


@router.get("/{booking_record_id}/eticket")
@limiter.limit("10/minute")
async def download_eticket(
    request: Request,
    booking_record_id: int,
    pnr: str,
    db: AsyncSession = Depends(get_db),
):
    booking_service = BookingService(db)
    booking = await booking_service.get_booking_by_id_and_pnr(
        booking_record_id=booking_record_id,
        pnr=pnr,
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    if booking.status != BookingRecordStatus.CONFIRMED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-ticket is only available for confirmed bookings.",
        )
    if not booking.provider_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking data is not available for e-ticket generation.",
        )

    try:
        pdf_bytes = generate_eticket_pdf(booking.provider_raw)
    except Exception as exc:
        logger.exception("Failed to generate e-ticket PDF for booking_record_id=%s", booking_record_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate e-ticket PDF.",
        ) from exc

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=FareClubs_ETicket_{booking.pnr}.pdf"
        },
    )
