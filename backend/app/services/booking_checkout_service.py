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
from app.core.exceptions import SsrExpiredError, SsrValidationError
from app.db.models.user import User
from app.domain.booking_enums import (
    SUCCESS_TICKET_STATUSES,
    BookingLegStatus,
    BookingOverallStatus,
    BookingRecordStatus,
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
    SsrSelection,
)
from app.schemas.tbo import (
    TBOFareQuoteResponse,
    TBOGetBookingDetailsResponse,
    TBOTicketNonLCCRequest,
    TBOTicketResponse,
)
from app.schemas.tbo.ssr import TBOSSRResponse
from app.services.booking_service import BookingService
from app.services.ssr_validation_service import SsrValidationService
from app.transformers.booking_transformer import (
    BookingConfirmationTransformer,
    BookingLegTransformResult,
)
from app.transformers.tbo_transformer import TBOTransformer
from app.utils import razorpay_utils
from app.utils.cache import FlightCache
from app.utils.money import paise_to_rupees, rupees_to_paise
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
    fare_quote: TBOFareQuoteResponse


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
    # injects all the dependencies, makes it testable
    def __init__(
        self,
        *,
        cache: FlightCache,
        client: TBOClient,
        request_transformer: TBOTransformer,
        response_transformer: BookingConfirmationTransformer,
        booking_service: BookingService,
        ssr_validator: SsrValidationService | None = None,
    ):
        self.cache = cache
        self.client = client
        self.request_transformer = request_transformer
        self.response_transformer = response_transformer
        self.booking_service = booking_service
        self.ssr_validator = ssr_validator or SsrValidationService(cache)

    @staticmethod
    def _is_price_changed(response: TBOTicketResponse) -> bool:
        """Safe accessor — defensive against malformed responses."""
        inner = getattr(response.Response, "Response", None)
        if inner is None:
            return False
        return inner.TicketStatus == TicketStatus.PRICE_CHANGED

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
        # check cache => validate payment amount => return Razorpay order details
        await self._require_cached_fare(payload.fare_id_outbound)
        # FAIL CLOSED: never charge a customer for a SSR mix we can't book.
        try:
            await self.ssr_validator.validate(
                fare_id_outbound=payload.fare_id_outbound,
                fare_id_inbound=payload.fare_id_inbound,
                ssr_selections_outbound=payload.ssr_selections_outbound or [],
                ssr_selections_inbound=payload.ssr_selections_inbound or [],
                journey_ssr_outbound=payload.journey_ssr_outbound or [],
                journey_ssr_inbound=payload.journey_ssr_inbound or [],
                is_international_return=payload.is_international_return,
            )
        except SsrExpiredError as exc:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "code": "SSR_EXPIRED",
                    "message": "Add-ons expired. Please re-confirm your selections.",
                },
            ) from exc
        except SsrValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "SSR_INVALID",
                    "message": "Some add-ons are no longer available.",
                    "missing": exc.missing,
                },
            ) from exc
        verified_total_paise = await self._compute_verified_total_paise(
            fare_id_outbound=payload.fare_id_outbound,
            fare_id_inbound=payload.fare_id_inbound,
            ssr_selections_outbound=payload.ssr_selections_outbound,
            ssr_selections_inbound=payload.ssr_selections_inbound,
            journey_ssr_outbound=payload.journey_ssr_outbound,
            journey_ssr_inbound=payload.journey_ssr_inbound,
            is_international_return=payload.is_international_return,
        )
        self._validate_client_total_paise(
            client_total_amount=payload.client_total_amount,
            verified_total_paise=verified_total_paise,
        )

        try:
            razorpay_order = razorpay_utils.create_order(
                amount_paise=verified_total_paise,
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
            verified_total_amount=paise_to_rupees(verified_total_paise),
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
        # Defense-in-depth: re-verify even though Razorpay already enforced the
        # order amount — catches a tampered confirm payload or a fare-cache
        # rotation between order and confirm.
        outbound_cached_fare = await self._require_cached_fare(payload.fare_id_outbound)
        ssr_outbound = [
            sel for p in payload.passengers for sel in (p.ssr_segments_outbound or [])
        ]
        ssr_inbound = [
            sel for p in payload.passengers for sel in (p.ssr_segments_inbound or [])
        ]
        journey_outbound = [p.journey_ssr_outbound for p in payload.passengers]
        journey_inbound = [p.journey_ssr_inbound for p in payload.passengers]
        verified_total_paise = await self._compute_verified_total_paise(
            fare_id_outbound=payload.fare_id_outbound,
            fare_id_inbound=payload.fare_id_inbound,
            ssr_selections_outbound=ssr_outbound,
            ssr_selections_inbound=ssr_inbound,
            journey_ssr_outbound=journey_outbound,
            journey_ssr_inbound=journey_inbound,
            is_international_return=payload.is_international_return,
        )
        self._validate_client_total_paise(
            client_total_amount=payload.client_total_amount,
            verified_total_paise=verified_total_paise,
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
            amount_paise=verified_total_paise,
        )

        if not was_created:
            existing_bookings = await self.booking_service.get_bookings_by_payment(
                payment.id
            )
            if existing_bookings:
                terminal_statuses = {
                    BookingRecordStatus.CONFIRMED.value,
                    BookingRecordStatus.NEEDS_ATTENTION.value,
                    BookingRecordStatus.FAILED.value,
                }
                all_terminal = all(
                    b.status in terminal_statuses for b in existing_bookings
                )
                if all_terminal:
                    logger.warning(
                        "[%s] duplicate confirm request for payment_order_id=%s "
                        "(existing statuses=%s) — replaying stored response",
                        request_id,
                        payload.payment_order_id,
                        [b.status for b in existing_bookings],
                    )
                    return self._build_response_from_existing_bookings(
                        bookings=existing_bookings,
                        payload=payload,
                    )
                # Non-terminal (e.g. PENDING from a crashed prior run): fall
                # through and re-attempt the TBO Book/Ticket cycle. PNR uniqueness
                # at the DB layer protects us from creating duplicate rows.
                logger.info(
                    "[%s] duplicate confirm but existing booking(s) non-terminal "
                    "(statuses=%s) — re-running TBO cycle",
                    request_id,
                    [b.status for b in existing_bookings],
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
        outbound_cached_fare: dict,  # why only this is required?
    ) -> list[LegWorkItem]:
        # outbound_cached_fare == provider_ref dict of this fare_id
        outbound_is_lcc = outbound_cached_fare.get("IsLCC", False)
        outbound_raw_ssr = await self.cache.get_model(
            f"raw_ssr_{payload.fare_id_outbound}", TBOSSRResponse
        )
        # checking that SSR options exist in cache?
        # why only for lcc?
        if outbound_is_lcc and not outbound_raw_ssr:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Seat and meal options for the outbound flight expired. Please refresh SSR and try again.",
            )

        outbound_fare_quote = await self._require_fare_quote(payload.fare_id_outbound)

        work_items = [
            LegWorkItem(
                direction=LegDirection.OUTBOUND,
                is_lcc=outbound_is_lcc,
                cached_fare=outbound_cached_fare,
                raw_ssr=outbound_raw_ssr,
                fare_quote=outbound_fare_quote,
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

        inbound_fare_quote = await self._require_fare_quote(payload.fare_id_inbound)

        work_items.append(
            LegWorkItem(
                direction=LegDirection.INBOUND,
                is_lcc=inbound_is_lcc,
                cached_fare=inbound_cached_fare,
                raw_ssr=inbound_raw_ssr,
                fare_quote=inbound_fare_quote,
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
        self, *, item: LegWorkItem, payload: BookingConfirmRequest, end_user_ip: str
    ) -> TBOTicketResponse:
        """
        Issue the ticket for one leg.
        TBO's ticket call is effectively two-phase when it detects a fare delta:
        the first call returns TicketStatus=PRICE_CHANGED as a checkpoint and
        does NOT issue, even when IsPriceChangeAccepted=True is set. Retrying
        once with the same args lets TBO commit at the new price.

        We retry exactly once. If the second call also returns PRICE_CHANGED,
        something else is going on (rare TBO quirk, or a delta we genuinely
        cannot accept) and we let the caller persist as NEEDS_ATTENTION.
        """

        if item.is_lcc:
            lcc_request = self.request_transformer.transform_ticket_lcc_request(
                request=payload,
                cached_data=item.cached_fare,
                end_user_ip=end_user_ip,
                raw_ssr=item.raw_ssr,
                direction=item.direction.value,
                fare_quote=item.fare_quote,
            )
            response = await self.client.generate_ticket_lcc(lcc_request)
            if self._is_price_changed(response):
                logger.info(
                    "TBO returned PRICE_CHANGED on first LCC Ticket; retrying once "
                    "(IsPriceChangeAccepted=True, trace_id=%s)",
                    item.cached_fare.get("TraceId"),
                )
                response = await self.client.generate_ticket_lcc(lcc_request)

            return response

        # non-LCC
        book_request = self.request_transformer.transform_book_request(
            request=payload,
            cached_data=item.cached_fare,
            end_user_ip=end_user_ip,
            raw_ssr=item.raw_ssr,
            direction=item.direction.value,
            fare_quote=item.fare_quote,
        )
        book_response = await self.client.book_flight(book_request)
        book_inner = book_response.Response.Response
        if not book_inner:
            raise ExternalProviderError(
                provider_code="BOOK_FAILED",
                http_status=502,
                message="Booking failed: empty response from provider",
            )

        non_lcc_ticket_request = TBOTicketNonLCCRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=item.cached_fare["TraceId"],
            PNR=book_inner.PNR,
            BookingId=book_inner.BookingId,
            IsPriceChangeAccepted=True,
        )
        response = await self.client.generate_ticket_nonlcc(non_lcc_ticket_request)
        if self._is_price_changed(response):
            logger.info(
                "TBO returned PRICE_CHANGED on first NonLCC Ticket; retrying once "
                "(PNR=%s, BookingId=%s)",
                book_inner.PNR,
                book_inner.BookingId,
            )
            response = await self.client.generate_ticket_nonlcc(non_lcc_ticket_request)
        return response

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
            logger.critical(
                "TICKET ISSUED BUT NOT SAVED — %s leg: provider_raw exists=%s, error=%s\n%s",
                result.direction.value,
                result.provider_raw is not None,
                persist_error,
                traceback.format_exc(),
            )
            # DO NOT overwrite result.error when the ticket was successfully issued.
            # The customer must see "confirmed" because the airline DID confirm it.
            # The persist failure is an internal issue that staff must resolve manually.
            if not result.succeeded:
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

    async def _require_fare_quote(self, fare_id: str | None) -> TBOFareQuoteResponse:
        """Load the cached FareQuote required to build provider passenger fares.

        Any cache-miss on a TBO TraceId-bound key means the session is no longer
        recoverable — the user must re-search. We use the same 410 detail string
        as `_require_cached_fare` so the frontend's existing "session has expired"
        handler routes the user to /search without any new error-routing logic.
        """
        if not fare_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing fare ID.",
            )
        fare_quote = await self.cache.get_model(
            f"fare_quote_{fare_id}", TBOFareQuoteResponse
        )
        if fare_quote is None:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Your session has expired. Please search again to get updated fares.",
            )
        return fare_quote

    def _compute_ssr_total_paise_for_direction(
        self,
        *,
        raw_ssr: TBOSSRResponse | None,
        selections: list["SsrSelection | None"] | None,
        leg_index: int,
        is_international_return: bool,
    ) -> int:
        """Sum the price of all SSR codes selected for one direction (in paise).

        `selections` is a flat list (already flattened across passengers and
        segments — order doesn't matter for summation).

        - Domestic round-trip: each direction has its own raw_ssr cache, `leg_index=0`.
        - International round-trip: both directions share the outbound raw_ssr cache;
          `leg_index=0` reads outbound blocks, `leg_index=1` reads inbound blocks.

        Returns int paise to keep arithmetic exact across many add-ons.
        Missing codes are logged and skipped — Issue 6 will tighten this to
        raise once SSR validation runs first.
        """
        if not selections or not raw_ssr or not raw_ssr.Response:
            return 0

        response = raw_ssr.Response

        def _pick_blocks(blocks):
            if blocks is None:
                return []
            if is_international_return:
                return [blocks[leg_index]] if leg_index < len(blocks) else []
            return list(blocks)

        seat_price_paise_by_code: dict[str, int] = {}
        for sd in _pick_blocks(response.SeatDynamic):
            if not sd or not sd.SegmentSeat:
                continue
            for seg in sd.SegmentSeat:
                if not seg.RowSeats:
                    continue
                for row in seg.RowSeats:
                    for seat in row.Seats or []:
                        if seat.Code and seat.Code != "NoSeat":
                            seat_price_paise_by_code[seat.Code] = rupees_to_paise(
                                seat.Price
                            )

        baggage_price_paise_by_code: dict[str, int] = {}
        for block in _pick_blocks(response.Baggage):
            for b in block or []:
                if b.Code:
                    baggage_price_paise_by_code[b.Code] = rupees_to_paise(b.Price)

        # MealDynamic = LCC priced meals. Non-LCC `Meal` (SimpleMeal) has no
        # Price field, so non-LCC meals cost ₹0 and are not added.
        meal_price_paise_by_code: dict[str, int] = {}
        for block in _pick_blocks(response.MealDynamic):
            for m in block or []:
                if m.Code:
                    meal_price_paise_by_code[m.Code] = rupees_to_paise(m.Price)

        total_paise = 0
        for sel in selections:
            if sel is None:
                continue
            if sel.meal_code:
                price = meal_price_paise_by_code.get(sel.meal_code)
                if price is None:
                    logger.warning(
                        "SSR pricing: meal_code=%s not found in cached SSR (leg_index=%d) — skipping",
                        sel.meal_code,
                        leg_index,
                    )
                else:
                    total_paise += price
            if sel.baggage_code:
                price = baggage_price_paise_by_code.get(sel.baggage_code)
                if price is None:
                    logger.warning(
                        "SSR pricing: baggage_code=%s not found in cached SSR (leg_index=%d) — skipping",
                        sel.baggage_code,
                        leg_index,
                    )
                else:
                    total_paise += price
            if sel.seat_code:
                price = seat_price_paise_by_code.get(sel.seat_code)
                if price is None:
                    logger.warning(
                        "SSR pricing: seat_code=%s not found in cached SSR (leg_index=%d) — skipping",
                        sel.seat_code,
                        leg_index,
                    )
                else:
                    total_paise += price
        return total_paise

    async def _compute_verified_total_paise(
        self,
        *,
        fare_id_outbound: str,
        fare_id_inbound: str | None,
        ssr_selections_outbound: list["SsrSelection | None"] | None = None,
        ssr_selections_inbound: list["SsrSelection | None"] | None = None,
        journey_ssr_outbound: list["SsrSelection | None"] | None = None,
        journey_ssr_inbound: list["SsrSelection | None"] | None = None,
        is_international_return: bool = False,
    ) -> int:
        """Compute the total amount the customer pays, in integer paise.

        Reads `verified_price_paise_{fare_id}` (cached at fare-quote time from
        `Fare.PublishedFare`) and adds SSR totals (also paise). int + int is
        exact — no float drift can sneak into the Razorpay handoff.

        SSR has TWO selection layers:
        - per-segment: `ssr_selections_*` (one entry per pax × segment), used
          for seat / segment-meal / segment-baggage prices.
        - journey-level: `journey_ssr_*` (one entry per pax), used for
          full-journey baggage / meal prices that apply once over the trip.
        """
        verified_outbound_paise = await self.cache.get(
            f"verified_price_paise_{fare_id_outbound}"
        )
        if verified_outbound_paise is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fare quote must be completed before checkout.",
            )

        verified_total_paise = int(verified_outbound_paise)
        if fare_id_inbound:
            verified_inbound_paise = await self.cache.get(
                f"verified_price_paise_{fare_id_inbound}"
            )
            if verified_inbound_paise is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inbound fare quote must be completed before checkout.",
                )
            verified_total_paise += int(verified_inbound_paise)

        has_outbound_ssr = bool(ssr_selections_outbound) and any(
            s is not None for s in ssr_selections_outbound
        )
        has_inbound_ssr = bool(ssr_selections_inbound) and any(
            s is not None for s in ssr_selections_inbound
        )
        has_outbound_journey = bool(journey_ssr_outbound) and any(
            s is not None for s in journey_ssr_outbound
        )
        has_inbound_journey = bool(journey_ssr_inbound) and any(
            s is not None for s in journey_ssr_inbound
        )
        needs_outbound_cache = (
            has_outbound_ssr
            or has_outbound_journey
            or ((has_inbound_ssr or has_inbound_journey) and is_international_return)
        )
        needs_inbound_cache = (
            has_inbound_ssr or has_inbound_journey
        ) and not is_international_return

        if needs_outbound_cache or needs_inbound_cache:
            outbound_raw_ssr = await self.cache.get_model(
                f"raw_ssr_{fare_id_outbound}", TBOSSRResponse
            )
            if needs_outbound_cache and outbound_raw_ssr is None:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Your session has expired. Please search again to get updated fares.",
                )

            if has_outbound_ssr:
                verified_total_paise += self._compute_ssr_total_paise_for_direction(
                    raw_ssr=outbound_raw_ssr,
                    selections=ssr_selections_outbound,
                    leg_index=0,
                    is_international_return=is_international_return,
                )
            if has_outbound_journey:
                verified_total_paise += self._compute_ssr_total_paise_for_direction(
                    raw_ssr=outbound_raw_ssr,
                    selections=journey_ssr_outbound,
                    leg_index=0,
                    is_international_return=is_international_return,
                )

            if has_inbound_ssr or has_inbound_journey:
                if is_international_return:
                    inbound_raw_ssr = outbound_raw_ssr
                else:
                    if not fare_id_inbound:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Inbound SSR selections received without an inbound fare.",
                        )
                    inbound_raw_ssr = await self.cache.get_model(
                        f"raw_ssr_{fare_id_inbound}", TBOSSRResponse
                    )
                    if inbound_raw_ssr is None:
                        raise HTTPException(
                            status_code=status.HTTP_410_GONE,
                            detail="Your session has expired. Please search again to get updated fares.",
                        )
                if has_inbound_ssr:
                    verified_total_paise += self._compute_ssr_total_paise_for_direction(
                        raw_ssr=inbound_raw_ssr,
                        selections=ssr_selections_inbound,
                        leg_index=1 if is_international_return else 0,
                        is_international_return=is_international_return,
                    )
                if has_inbound_journey:
                    verified_total_paise += self._compute_ssr_total_paise_for_direction(
                        raw_ssr=inbound_raw_ssr,
                        selections=journey_ssr_inbound,
                        leg_index=1 if is_international_return else 0,
                        is_international_return=is_international_return,
                    )

        return verified_total_paise

    def _validate_client_total_paise(
        self,
        *,
        client_total_amount: float,
        verified_total_paise: int,
    ) -> None:
        """Compare client-supplied rupees to verified paise. Tolerance: ₹10."""
        client_total_paise = rupees_to_paise(client_total_amount)
        # ₹10 tolerance = 1000 paise. Same UX threshold, expressed in paise.
        if abs(client_total_paise - verified_total_paise) > 1000:
            verified_rupees = paise_to_rupees(verified_total_paise)
            logger.warning(
                "Amount mismatch: submitted=%.2f, expected=%.2f, diff_paise=%d",
                client_total_amount,
                verified_rupees,
                client_total_paise - verified_total_paise,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Amount mismatch: submitted ₹{client_total_amount:.2f}, "
                    f"expected ₹{verified_rupees:.2f}. Please refresh fares."
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
