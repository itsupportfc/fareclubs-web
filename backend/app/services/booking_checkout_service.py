"""Checkout orchestration service.

This is the piece that keeps the FastAPI route thin:
- validate cache and payment inputs
- call provider APIs
- persist legs
- build the final response
- schedule alerts / e-ticket email
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from dataclasses import dataclass
from uuid import uuid4

import httpx
from app.clients.exceptions import ExternalProviderError
from app.clients.tbo_client import TBOClient, TBOParseError
from app.config import settings
from app.db.models.user import User
from app.domain.booking_enums import (
    SUCCESS_TICKET_STATUSES,
    BookingLegStatus,
    BookingOverallStatus,
    BookStatus,
    LegDirection,
    TicketStatus,
    TripType,
    derive_overall_booking_status,
)
from app.schemas.internal.booking import (
    BookingConfirmRequest,
    BookingConfirmResponse,
    BookingCreateOrderRequest,
    BookingCreateOrderResponse,
)
from app.schemas.tbo import (
    TBOGetBookingDetailsResponse,
    TBOTicketNonLCCRequest,
    TBOTicketResponse,
)
from app.schemas.tbo.ssr import TBOSSRResponse
from app.services.booking_service import BookingService
from app.transformers.booking_transformer import (
    BookingConfirmationTransformer,
    BookingLegTransformResult,
)
from app.transformers.tbo_transformer import TBOTransformer
from app.utils import razorpay_utils
from app.utils.cache import FlightCache
from app.utils.email import (
    build_booking_attention_email,
    build_booking_failure_email,
    send_customer_eticket_email,
    send_staff_alert_email,
)
from app.utils.eticket_pdf import generate_eticket_pdf
from fastapi import BackgroundTasks, HTTPException, status

logger = logging.getLogger(__name__)


@dataclass
class LegWorkItem:
    direction: LegDirection
    is_lcc: bool
    cached_fare: dict
    raw_ssr: TBOSSRResponse | None


@dataclass
class LegExecutionResult:
    direction: LegDirection
    is_lcc: bool
    cached_fare: dict
    ticket_response: TBOTicketResponse | None = None
    recovery_response: TBOGetBookingDetailsResponse | None = None
    recovered_ticket_status: int | None = None
    error: Exception | None = None
    booking_record = None

    @property
    def succeeded(self) -> bool:
        return self.ticket_response is not None or self.recovery_response is not None

    @property
    def provider_raw(self) -> dict | None:
        if self.ticket_response is not None:
            return self.ticket_response.model_dump(mode="json")
        if self.recovery_response is not None:
            return self.recovery_response.model_dump(mode="json")
        return None


class BookingCheckoutService:
    def __init__(
        self,
        *,
        cache: FlightCache,
        client: TBOClient,
        request_transformer: TBOTransformer,
        response_transformer: BookingConfirmationTransformer,
        booking_service: BookingService,
    ):
        self.cache = cache
        self.client = client
        self.request_transformer = request_transformer
        self.response_transformer = response_transformer
        self.booking_service = booking_service

    async def create_payment_order(
        self,
        *,
        payload: BookingCreateOrderRequest,
        current_user: User | None,
    ) -> BookingCreateOrderResponse:
        request_id = uuid4().hex[:8]
        user_label = f"user_id={current_user.id}" if current_user else "guest"
        logger.info(
            "[%s] create_payment_order start (%s, outbound=%s, inbound=%s)",
            request_id,
            user_label,
            payload.fare_id_outbound,
            payload.fare_id_inbound,
        )

        await self._require_cached_fare(payload.fare_id_outbound)
        verified_total_amount = await self._compute_verified_total_amount(
            fare_id_outbound=payload.fare_id_outbound,
            fare_id_inbound=payload.fare_id_inbound,
        )
        self._validate_client_total_amount(
            client_total_amount=payload.client_total_amount,
            verified_total_amount=verified_total_amount,
        )

        try:
            razorpay_order = razorpay_utils.create_order(
                amount_paise=int(round(verified_total_amount, 2) * 100),
                receipt=payload.fare_id_outbound,
            )
        except Exception as exc:
            logger.exception("[%s] Razorpay order creation failed", request_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment gateway is temporarily unavailable. Please try again.",
            ) from exc

        return BookingCreateOrderResponse(
            payment_order_id=razorpay_order["id"],
            payment_amount_paise=razorpay_order["amount"],
            payment_currency=razorpay_order["currency"],
            razorpay_public_key=settings.RAZORPAY_KEY_ID,
            verified_total_amount=round(verified_total_amount, 2),
        )

    async def confirm_booking(
        self,
        *,
        payload: BookingConfirmRequest,
        background_tasks: BackgroundTasks,
        end_user_ip: str,
        current_user: User | None,
    ) -> BookingConfirmResponse:
        request_id = uuid4().hex[:8]
        logger.info(
            "[%s] confirm_booking start payment_id=%s outbound=%s inbound=%s",
            request_id,
            payload.payment_id,
            payload.fare_id_outbound,
            payload.fare_id_inbound,
        )

        outbound_cached_fare = await self._require_cached_fare(payload.fare_id_outbound)
        verified_total_amount = await self._compute_verified_total_amount(
            fare_id_outbound=payload.fare_id_outbound,
            fare_id_inbound=payload.fare_id_inbound,
        )
        self._validate_client_total_amount(
            client_total_amount=payload.client_total_amount,
            verified_total_amount=verified_total_amount,
        )

        self._verify_payment_signature(payload)

        work_items = await self._build_leg_work_items(payload, outbound_cached_fare)

        (
            payment,
            was_created,
        ) = await self.booking_service.get_or_create_captured_payment(
            user_id=current_user.id if current_user else None,
            razorpay_order_id=payload.payment_order_id,
            razorpay_payment_id=payload.payment_id,
            razorpay_signature=payload.payment_signature,
            amount_paise=int(round(verified_total_amount, 2) * 100),
        )

        if not was_created:
            existing_bookings = await self.booking_service.get_bookings_by_payment(
                payment.id
            )
            if existing_bookings:
                logger.warning(
                    "[%s] duplicate confirm request for payment_order_id=%s",
                    request_id,
                    payload.payment_order_id,
                )
                return self._build_response_from_existing_bookings(
                    bookings=existing_bookings,
                    payload=payload,
                )

        execution_results = await asyncio.gather(
            *[
                self._process_single_leg(
                    item=item,
                    payload=payload,
                    end_user_ip=end_user_ip,
                    request_id=request_id,
                )
                for item in work_items
            ]
        )

        outbound_result = execution_results[0]
        await self._persist_leg_result(
            result=outbound_result,
            payload=payload,
            payment=payment,
            current_user=current_user,
            linked_booking_id=None,
        )

        inbound_result = execution_results[1] if len(execution_results) > 1 else None
        if inbound_result is not None:
            await self._persist_leg_result(
                result=inbound_result,
                payload=payload,
                payment=payment,
                current_user=current_user,
                linked_booking_id=(
                    outbound_result.booking_record.id
                    if outbound_result.booking_record
                    else None
                ),
            )

        try:
            await self.booking_service.db.commit()
        except Exception as commit_error:
            logger.error(
                "DB commit failed after booking payment_id=%s: %s\n%s",
                payload.payment_id,
                commit_error,
                traceback.format_exc(),
            )
            subject, html = build_booking_failure_email(
                payload,
                f"DB commit error: {commit_error}",
                payload.payment_id,
                payload.payment_order_id,
            )
            background_tasks.add_task(send_staff_alert_email, subject, html)
            return self._build_commit_failure_response(payload, work_items[0].is_lcc)

        return self._build_final_response(
            payload=payload,
            outbound_result=outbound_result,
            inbound_result=inbound_result,
            background_tasks=background_tasks,
        )

    async def _build_leg_work_items(
        self,
        payload: BookingConfirmRequest,
        outbound_cached_fare: dict,
    ) -> list[LegWorkItem]:
        outbound_is_lcc = outbound_cached_fare.get("IsLCC", False)
        outbound_raw_ssr = await self.cache.get_model(
            f"raw_ssr_{payload.fare_id_outbound}", TBOSSRResponse
        )
        if outbound_is_lcc and not outbound_raw_ssr:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Seat and meal options for the outbound flight expired. Please refresh SSR and try again.",
            )

        work_items = [
            LegWorkItem(
                direction=LegDirection.OUTBOUND,
                is_lcc=outbound_is_lcc,
                cached_fare=outbound_cached_fare,
                raw_ssr=outbound_raw_ssr,
            )
        ]

        is_domestic_roundtrip = (
            payload.trip_type == TripType.ROUNDTRIP
            and payload.fare_id_inbound is not None
            and not payload.is_international_return
        )
        if not is_domestic_roundtrip:
            return work_items

        inbound_cached_fare = await self._require_cached_fare(payload.fare_id_inbound)
        inbound_is_lcc = inbound_cached_fare.get("IsLCC", False)
        inbound_raw_ssr = await self.cache.get_model(
            f"raw_ssr_{payload.fare_id_inbound}", TBOSSRResponse
        )
        if inbound_is_lcc and not inbound_raw_ssr:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Seat and meal options for the return flight expired. Please refresh SSR and try again.",
            )

        work_items.append(
            LegWorkItem(
                direction=LegDirection.INBOUND,
                is_lcc=inbound_is_lcc,
                cached_fare=inbound_cached_fare,
                raw_ssr=inbound_raw_ssr,
            )
        )
        return work_items

    async def _process_single_leg(
        self,
        *,
        item: LegWorkItem,
        payload: BookingConfirmRequest,
        end_user_ip: str,
        request_id: str,
    ) -> LegExecutionResult:
        result = LegExecutionResult(
            direction=item.direction,
            is_lcc=item.is_lcc,
            cached_fare=item.cached_fare,
        )
        try:
            result.ticket_response = await self._ticket_single_leg(
                item=item,
                payload=payload,
                end_user_ip=end_user_ip,
            )
            return result
        except httpx.TimeoutException as timeout_error:
            logger.warning(
                "[%s] provider timeout while ticketing %s leg for payment_id=%s",
                request_id,
                item.direction.value,
                payload.payment_id,
            )
            try:
                lead_passenger = next(
                    (
                        passenger
                        for passenger in payload.passengers
                        if passenger.is_lead_pax
                    ),
                    payload.passengers[0],
                )
                details_response = await self.client.get_booking_details_with_retry(
                    end_user_ip=end_user_ip,
                    trace_id=item.cached_fare.get("TraceId"),
                    first_name=lead_passenger.first_name,
                    last_name=lead_passenger.last_name,
                )
                if details_response and details_response.Response.FlightItinerary:
                    itinerary = details_response.Response.FlightItinerary
                    result.recovery_response = details_response
                    result.recovered_ticket_status = int(
                        BookStatus.to_ticket_status(itinerary.Status)
                    )
                    return result
                result.error = Exception(
                    f"Provider timeout while ticketing {item.direction.value} leg; recovery found no booking"
                )
                return result
            except Exception as recovery_error:
                logger.error(
                    "[%s] recovery lookup failed for %s leg: %s",
                    request_id,
                    item.direction.value,
                    recovery_error,
                )
                result.error = timeout_error
                return result
        except Exception as exc:
            result.error = exc
            return result

    async def _ticket_single_leg(
        self,
        *,
        item: LegWorkItem,
        payload: BookingConfirmRequest,
        end_user_ip: str,
    ) -> TBOTicketResponse:
        if item.is_lcc:
            lcc_request = self.request_transformer.transform_ticket_lcc_request(
                payload,
                item.cached_fare,
                end_user_ip,
                item.raw_ssr,
                direction=item.direction.value,
            )
            return await self.client.generate_ticket_lcc(lcc_request)

        book_request = self.request_transformer.transform_book_request(
            payload,
            item.cached_fare,
            end_user_ip,
            item.raw_ssr,
            direction=item.direction.value,
        )
        book_response = await self.client.book_flight(book_request)
        book_inner = book_response.Response.Response
        if not book_inner:
            raise ExternalProviderError(
                provider_code="BOOK_FAILED",
                http_status=502,
                message="TBO Book did not return booking details.",
            )

        non_lcc_ticket_request = TBOTicketNonLCCRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=item.cached_fare["TraceId"],
            PNR=book_inner.PNR,
            BookingId=book_inner.BookingId,
            IsPriceChangeAccepted=True,
        )
        return await self.client.generate_ticket_nonlcc(non_lcc_ticket_request)

    async def _persist_leg_result(
        self,
        *,
        result: LegExecutionResult,
        payload: BookingConfirmRequest,
        payment,
        current_user: User | None,
        linked_booking_id: int | None,
    ) -> None:
        user_id = current_user.id if current_user else None
        try:
            if result.ticket_response is not None:
                result.booking_record = await self.booking_service.save_ticketed_leg(
                    user_id=user_id,
                    payment=payment,
                    provider="tbo",
                    ticket_response=result.ticket_response,
                    direction=result.direction.value,
                    trip_type=payload.trip_type,
                    linked_booking_id=linked_booking_id,
                )
                return

            if result.recovery_response is not None:
                result.booking_record = await self.booking_service.save_recovered_leg(
                    user_id=user_id,
                    payment=payment,
                    provider="tbo",
                    details_response=result.recovery_response,
                    direction=result.direction.value,
                    trip_type=payload.trip_type,
                    provider_ticket_status=result.recovered_ticket_status
                    or int(TicketStatus.PENDING),
                    is_lcc=result.is_lcc,
                    linked_booking_id=linked_booking_id,
                )
                return

            parse_error_raw = (
                result.error.raw_response
                if isinstance(result.error, TBOParseError)
                and hasattr(result.error, "raw_response")
                else None
            )
            result.booking_record = await self.booking_service.save_failed_leg(
                user_id=user_id,
                payment=payment,
                provider="tbo",
                direction=result.direction.value,
                trip_type=payload.trip_type,
                is_lcc=result.is_lcc,
                error_message=str(result.error or "Unknown error"),
                is_domestic=result.cached_fare.get("IsDomestic", True),
                parse_error_raw=parse_error_raw,
            )
        except Exception as persist_error:
            logger.error(
                "Failed to persist %s leg: %s\n%s",
                result.direction.value,
                persist_error,
                traceback.format_exc(),
            )
            if result.succeeded:
                result.error = persist_error

    def _build_final_response(
        self,
        *,
        payload: BookingConfirmRequest,
        outbound_result: LegExecutionResult,
        inbound_result: LegExecutionResult | None,
        background_tasks: BackgroundTasks,
    ) -> BookingConfirmResponse:
        support_needed = False

        outbound_transform = self._transform_leg_result(
            result=outbound_result,
            success_message=None,
            failure_message=(
                "Your payment was successful but we could not complete the outbound ticket immediately. "
                "Our team has been notified and will contact you shortly."
            ),
        )
        if outbound_transform.leg.leg_status != BookingLegStatus.CONFIRMED:
            support_needed = True
            self._queue_leg_alert(
                result=outbound_result,
                payload=payload,
                background_tasks=background_tasks,
            )

        inbound_transform = None
        if inbound_result is not None:
            inbound_transform = self._transform_leg_result(
                result=inbound_result,
                success_message=None,
                failure_message=(
                    "Your return flight encountered an issue. Our team has been notified and will resolve this shortly."
                ),
            )
            if inbound_transform.leg.leg_status != BookingLegStatus.CONFIRMED:
                support_needed = True
                self._queue_leg_alert(
                    result=inbound_result,
                    payload=payload,
                    background_tasks=background_tasks,
                )

        outbound_leg_status = outbound_transform.leg.leg_status
        inbound_leg_status = (
            inbound_transform.leg.leg_status if inbound_transform else None
        )
        logger.debug(
            "deriving overall_status: outbound_leg=%s (type=%s), inbound_leg=%s",
            outbound_leg_status,
            type(outbound_leg_status).__name__,
            inbound_leg_status,
        )
        overall_status = derive_overall_booking_status(
            outbound_leg_status,
            inbound_leg_status,
        )
        logger.debug("derived overall_status=%s", overall_status)

        if (
            overall_status == BookingOverallStatus.CONFIRMED
            and outbound_result.provider_raw
            and outbound_transform.leg.provider_pnr
        ):
            background_tasks.add_task(
                self._send_eticket_background,
                outbound_result.provider_raw,
                outbound_transform.leg.provider_pnr,
            )

        primary_passengers = outbound_transform.passengers or (
            inbound_transform.passengers if inbound_transform else None
        )
        response = BookingConfirmResponse(
            overall_status=overall_status,
            outbound_leg=outbound_transform.leg,
            inbound_leg=inbound_transform.leg if inbound_transform else None,
            passengers=primary_passengers,
            support_phone=settings.SUPPORT_PHONE or None if support_needed else None,
            support_email=settings.SUPPORT_EMAIL or None if support_needed else None,
            payment_order_id=payload.payment_order_id,
            payment_id=payload.payment_id,
        )

        if (
            overall_status == BookingOverallStatus.PARTIAL
            and inbound_transform is not None
            and outbound_transform.leg.leg_status != BookingLegStatus.CONFIRMED
            and inbound_transform.leg.leg_status == BookingLegStatus.CONFIRMED
            and not outbound_transform.leg.customer_message
        ):
            response.outbound_leg.customer_message = (
                "Your return flight is confirmed, but the outbound leg still needs attention. "
                "Our team has already been notified."
            )

        return response

    def _build_response_from_existing_bookings(
        self,
        *,
        bookings: list,
        payload: BookingConfirmRequest,
    ) -> BookingConfirmResponse:
        bookings_by_direction = {booking.direction: booking for booking in bookings}
        outbound_booking = bookings_by_direction.get(LegDirection.OUTBOUND.value)
        if outbound_booking is None:
            logger.error(
                "duplicate confirm: no outbound booking found for payment_order_id=%s",
                payload.payment_order_id,
            )
            return self._build_commit_failure_response(
                payload, bookings[0].is_lcc if bookings else False
            )
        outbound_transform = self.response_transformer.build_from_booking_record(
            booking=outbound_booking
        )

        inbound_booking = bookings_by_direction.get(LegDirection.INBOUND.value)
        inbound_transform = (
            self.response_transformer.build_from_booking_record(booking=inbound_booking)
            if inbound_booking is not None
            else None
        )
        overall_status = derive_overall_booking_status(
            outbound_transform.leg.leg_status,
            inbound_transform.leg.leg_status if inbound_transform else None,
        )
        support_needed = overall_status != BookingOverallStatus.CONFIRMED
        return BookingConfirmResponse(
            overall_status=overall_status,
            outbound_leg=outbound_transform.leg,
            inbound_leg=inbound_transform.leg if inbound_transform else None,
            passengers=outbound_transform.passengers
            or (inbound_transform.passengers if inbound_transform else None),
            support_phone=settings.SUPPORT_PHONE or None if support_needed else None,
            support_email=settings.SUPPORT_EMAIL or None if support_needed else None,
            payment_order_id=payload.payment_order_id,
            payment_id=payload.payment_id,
        )

    def _build_commit_failure_response(
        self,
        payload: BookingConfirmRequest,
        outbound_is_lcc: bool,
    ) -> BookingConfirmResponse:
        outbound_transform = self.response_transformer.build_failed_leg(
            leg_direction=LegDirection.OUTBOUND,
            booking_record_id=None,
            provider_is_lcc=outbound_is_lcc,
            provider_ticket_status=int(TicketStatus.PENDING),
            customer_message=(
                "Your payment was successful but we encountered an internal issue while saving the booking. "
                "Our team has been notified and will contact you shortly."
            ),
        )
        return BookingConfirmResponse(
            overall_status=BookingOverallStatus.PENDING,
            outbound_leg=outbound_transform.leg,
            inbound_leg=None,
            passengers=None,
            support_phone=settings.SUPPORT_PHONE or None,
            support_email=settings.SUPPORT_EMAIL or None,
            payment_order_id=payload.payment_order_id,
            payment_id=payload.payment_id,
        )

    def _transform_leg_result(
        self,
        *,
        result: LegExecutionResult,
        success_message: str | None,
        failure_message: str,
    ) -> BookingLegTransformResult:
        if result.ticket_response is not None:
            transformed = self.response_transformer.build_from_ticket_response(
                ticket_response=result.ticket_response,
                leg_direction=result.direction,
                booking_record_id=(
                    result.booking_record.id
                    if result.booking_record is not None
                    else None
                ),
            )
            if success_message:
                transformed.leg.customer_message = success_message
            return transformed

        if result.recovery_response is not None:
            transformed = self.response_transformer.build_from_booking_details_response(
                details_response=result.recovery_response,
                leg_direction=result.direction,
                provider_ticket_status=result.recovered_ticket_status
                or int(TicketStatus.PENDING),
                provider_is_lcc=result.is_lcc,
                booking_record_id=(
                    result.booking_record.id
                    if result.booking_record is not None
                    else None
                ),
            )
            if success_message:
                transformed.leg.customer_message = success_message
            return transformed

        return self.response_transformer.build_failed_leg(
            leg_direction=result.direction,
            booking_record_id=(
                result.booking_record.id if result.booking_record is not None else None
            ),
            provider_is_lcc=result.is_lcc,
            provider_ticket_status=(
                int(result.booking_record.ticket_status)
                if result.booking_record is not None
                else int(TicketStatus.PENDING)
            ),
            customer_message=failure_message,
        )

    async def _require_cached_fare(self, fare_id: str | None) -> dict:
        if not fare_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing fare ID.",
            )
        cached_fare = await self.cache.get(fare_id)
        if not cached_fare:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Your session has expired. Please search again to get updated fares.",
            )
        return cached_fare

    async def _compute_verified_total_amount(
        self,
        *,
        fare_id_outbound: str,
        fare_id_inbound: str | None,
    ) -> float:
        verified_outbound_amount = await self.cache.get(
            f"verified_price_{fare_id_outbound}"
        )
        if verified_outbound_amount is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fare quote must be completed before checkout.",
            )

        verified_total_amount = float(verified_outbound_amount)
        if fare_id_inbound:
            verified_inbound_amount = await self.cache.get(
                f"verified_price_{fare_id_inbound}"
            )
            if verified_inbound_amount is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inbound fare quote must be completed before checkout.",
                )
            verified_total_amount += float(verified_inbound_amount)
        return verified_total_amount

    def _validate_client_total_amount(
        self,
        *,
        client_total_amount: float,
        verified_total_amount: float,
    ) -> None:
        submitted = round(client_total_amount, 2)
        expected = round(verified_total_amount, 2)
        if submitted < expected - 1.0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Amount mismatch: submitted ₹{submitted}, expected ₹{expected}. "
                    "Please refresh fares."
                ),
            )

    def _verify_payment_signature(self, payload: BookingConfirmRequest) -> None:
        if not razorpay_utils.verify_payment_signature(
            order_id=payload.payment_order_id,
            payment_id=payload.payment_id,
            signature=payload.payment_signature,
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment verification failed — invalid signature.",
            )

    def _queue_leg_alert(
        self,
        *,
        result: LegExecutionResult,
        payload: BookingConfirmRequest,
        background_tasks: BackgroundTasks,
    ) -> None:
        if result.error is None:
            if result.ticket_response is not None:
                ticket_status = result.ticket_response.Response.Response.TicketStatus
                subject, html = build_booking_attention_email(
                    payload,
                    f"[{result.direction.value.upper()}] soft provider status={ticket_status}",
                    payload.payment_id,
                    payload.payment_order_id,
                )
            elif result.recovery_response is not None:
                subject, html = build_booking_attention_email(
                    payload,
                    f"[{result.direction.value.upper()}] recovered provider status={result.recovered_ticket_status}",
                    payload.payment_id,
                    payload.payment_order_id,
                )
            else:
                return
            background_tasks.add_task(send_staff_alert_email, subject, html)
            return

        error_message = str(result.error)
        label = result.direction.value.upper()
        if isinstance(result.error, TBOParseError):
            subject, html = build_booking_attention_email(
                payload,
                f"[{label}] provider parse error: {error_message}",
                payload.payment_id,
                payload.payment_order_id,
            )
        else:
            subject, html = build_booking_failure_email(
                payload,
                f"[{label}] {error_message}",
                payload.payment_id,
                payload.payment_order_id,
            )
        background_tasks.add_task(send_staff_alert_email, subject, html)

    async def _send_eticket_background(
        self, provider_raw: dict, provider_pnr: str
    ) -> None:
        """Generate and email the e-ticket in the background.

        We only do this after a confirmed outbound leg because that is the minimum
        happy-path customer experience already used in the current product.
        """

        try:
            from app.utils.eticket_pdf import _extract_itinerary

            itinerary = _extract_itinerary(provider_raw)
            if not itinerary:
                logger.warning(
                    "Cannot send e-ticket email: itinerary missing in provider_raw"
                )
                return

            passengers = itinerary.get("Passenger", [])
            lead_passenger = next(
                (passenger for passenger in passengers if passenger.get("IsLeadPax")),
                passengers[0] if passengers else None,
            )
            if not lead_passenger or not lead_passenger.get("Email"):
                logger.info(
                    "No lead passenger email available; skipping e-ticket email"
                )
                return

            pdf_bytes = generate_eticket_pdf(provider_raw)
            passenger_name = (
                f"{lead_passenger.get('FirstName', '')} {lead_passenger.get('LastName', '')}"
            ).strip()
            await send_customer_eticket_email(
                to_email=lead_passenger["Email"],
                passenger_name=passenger_name,
                pnr=provider_pnr,
                pdf_bytes=pdf_bytes,
            )
        except Exception:
            logger.exception(
                "Background e-ticket email failed for PNR %s", provider_pnr
            )
