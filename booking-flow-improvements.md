# Booking Flow Improvements — Detailed Code Changes

---

## Change 1: Add `IntEnum` import

**File:** `backend/app/api/v1/flight.py` — Line 1

Add to imports:

```python
from enum import IntEnum
```

---

## Change 2: Replace status constants with IntEnum classes

**File:** `backend/app/api/v1/flight.py` — Replace lines 497-523

**Remove:**

```python
_FAILED_TICKET_STATUSES = {0, 3, 4, 9}
_SOFT_TICKET_STATUSES = {2, 5}
_SUCCESS_TICKET_STATUSES = {1, 6}

_BOOK_STATUS_NOT_SET = 0
_BOOK_STATUS_SUCCESSFUL = 1
_BOOK_STATUS_FAILED = 2
_BOOK_STATUS_OTHER_FARE = 3
_BOOK_STATUS_OTHER_CLASS = 4
_BOOK_STATUS_BOOKED_OTHER = 5
_BOOK_STATUS_NOT_CONFIRMED = 6

_BOOK_STATUS_TO_TICKET_STATUS = {
    _BOOK_STATUS_NOT_SET: 5,
    _BOOK_STATUS_SUCCESSFUL: 1,
    _BOOK_STATUS_FAILED: 0,
    _BOOK_STATUS_OTHER_FARE: 8,
    _BOOK_STATUS_OTHER_CLASS: 8,
    _BOOK_STATUS_BOOKED_OTHER: 6,
    _BOOK_STATUS_NOT_CONFIRMED: 5,
}


def _ticket_status_from_booking_status(booking_status: int | None) -> int:
    if booking_status is None:
        return 5
    return _BOOK_STATUS_TO_TICKET_STATUS.get(booking_status, 5)
```

**Replace with:**

```python
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
```

Also update `_decorate_response` line 566 — change `if ts == 8:` to:

```python
    if ts == TicketStatus.PRICE_CHANGED:
```

And in the error handler blocks (lines 1015, 1078), change `ticket_status=5` to:

```python
        ticket_status=TicketStatus.PENDING,
```

---

## Change 3: Cache verified price in `fare_quote` endpoint

**File:** `backend/app/api/v1/flight.py` — After line 224 (after `await cache.set(f"flags_{...}`)

**Add after line 224:**

```python
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
```

**Add inside the `if inbound_tbo_response:` block, after line 243 (after `await cache.set(f"flags_{...}`):**

```python
        verified_inbound_total = (
            inbound_tbo_response.Response.Results.Fare.BaseFare
            + inbound_tbo_response.Response.Results.Fare.Tax
        )
        await cache.set(
            f"verified_price_{payload.fare_id_inbound}",
            verified_inbound_total,
            ttl=900,
        )
```

---

## Change 4: Verify price in `create_booking_order`

**File:** `backend/app/api/v1/flight.py` — In `create_booking_order`, after line 477 (after the session-expired check), before the `try: order = ...` block

**Add after line 477:**

```python
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

    if abs(payload.total_amount - expected_total) > 1.0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Price mismatch: submitted ₹{payload.total_amount}, verified ₹{expected_total}. Please refresh fares.",
        )
```

---

## Change 5: Delete `_generate_lcc_ticket_with_seat_retry`

**File:** `backend/app/api/v1/flight.py` — Delete lines 613-680

**Remove the entire function:**

```python
# remove this for now
async def _generate_lcc_ticket_with_seat_retry(
    *,
    payload: BookingConfirmRequest,
    cached_data: dict,
    fare_id: str,
    end_user_ip: str,
    raw_ssr: TBOSSRResponse,
    cache,
    client: TBOClient,
    transformer: TBOTransformer,
) -> TBOTicketResponse:
    ... entire function body ...
```

---

## Change 6: Add `_ticket_single_leg` helper

**File:** `backend/app/api/v1/flight.py` — Add where `_generate_lcc_ticket_with_seat_retry` was (after `_decorate_response`)

```python
async def _ticket_single_leg(
    *,
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
            payload, cached_data, end_user_ip, raw_ssr,
        )
        return await client.generate_ticket_lcc(lcc_req)

    book_req = transformer.transform_book_request(
        payload, cached_data, end_user_ip, raw_ssr,
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
```

---

## Change 7: Rewrite domestic roundtrip booking logic

**File:** `backend/app/api/v1/flight.py` — Replace lines 761-836 (the `if is_lcc and is_lcc_inbound:` / `else:` branches)

**Remove:**

```python
            # if both inbound and outbound are LCC
            if is_lcc and is_lcc_inbound:
                inbound_fare_id = payload.fare_id_inbound
                if not  inbound_fare_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Inbound fare id is required for roundtrip booking.",
                    )
                ticket_out, ticket_in = await asyncio.gather(
                    _generate_lcc_ticket_with_seat_retry(
                        payload=payload,
                        cached_data=cached_data,
                        fare_id=payload.fare_id_outbound,
                        end_user_ip=end_user_ip,
                        raw_ssr=raw_ssr,
                        cache=cache,
                        client=client,
                        transformer=transformer,
                    ),
                    _generate_lcc_ticket_with_seat_retry(
                        payload=payload,
                        cached_data=cached_inbound,
                        fare_id=inbound_fare_id,
                        end_user_ip=end_user_ip,
                        raw_ssr=raw_ssr_in,
                        cache=cache,
                        client=client,
                        transformer=transformer,
                    ),
                )
            # WRONG: what if one is LCC?
            else:
                book_req_out = transformer.transform_book_request(
                    payload, cached_data, end_user_ip, raw_ssr
                )
                book_req_in = transformer.transform_book_request(
                    payload, cached_inbound, end_user_ip, raw_ssr_in
                )
                book_out, book_in = await asyncio.gather(
                    client.book_flight(book_req_out),
                    client.book_flight(book_req_in),
                )
                book_out_inner = book_out.Response.Response
                book_in_inner = book_in.Response.Response
                if not book_out_inner or not book_in_inner:
                    raise ExternalProviderError(
                        provider_code="BOOK_FAILED",
                        http_status=502,
                        message="TBO Book did not return booking details for one or more legs.",
                    )

                pnr_out = book_out_inner.PNR
                bid_out = book_out_inner.BookingId
                pnr_in = book_in_inner.PNR
                bid_in = book_in_inner.BookingId

                nonlcc_out = TBOTicketNonLCCRequest(
                    EndUserIp=end_user_ip,
                    TokenId="",
                    TraceId=cached_data["TraceId"],
                    PNR=pnr_out,
                    BookingId=bid_out,
                    IsPriceChangeAccepted=True,
                )
                nonlcc_in = TBOTicketNonLCCRequest(
                    EndUserIp=end_user_ip,
                    TokenId="",
                    TraceId=cached_inbound["TraceId"],
                    PNR=pnr_in,
                    BookingId=bid_in,
                    IsPriceChangeAccepted=True,
                )
                ticket_out, ticket_in = await asyncio.gather(
                    client.generate_ticket_nonlcc(nonlcc_out),
                    client.generate_ticket_nonlcc(nonlcc_in),
                )
```

**Replace with:**

```python
            ticket_out, ticket_in = await asyncio.gather(
                _ticket_single_leg(
                    is_lcc=is_lcc,
                    payload=payload,
                    cached_data=cached_data,
                    end_user_ip=end_user_ip,
                    raw_ssr=raw_ssr,
                    client=client,
                    transformer=transformer,
                ),
                _ticket_single_leg(
                    is_lcc=is_lcc_inbound,
                    payload=payload,
                    cached_data=cached_inbound,
                    end_user_ip=end_user_ip,
                    raw_ssr=raw_ssr_in,
                    client=client,
                    transformer=transformer,
                ),
            )
```

---

## Change 8: Simplify oneway/international booking path

**File:** `backend/app/api/v1/flight.py` — Replace lines 869-962 (the `else:` oneway block)

**Remove:**

```python
        else:
            # Oneway or international return: single booking call
            pnr = None
            booking_id = None

            try:
                if is_lcc:
                    ticket_resp = await _generate_lcc_ticket_with_seat_retry(
                        payload=payload,
                        cached_data=cached_data,
                        fare_id=payload.fare_id_outbound,
                        end_user_ip=end_user_ip,
                        raw_ssr=raw_ssr,
                        cache=cache,
                        client=client,
                        transformer=transformer,
                    )
                else:
                    book_req = transformer.transform_book_request(
                        payload, cached_data, end_user_ip, raw_ssr
                    )
                    book_resp = await client.book_flight(book_req)
                    book_inner = book_resp.Response.Response
                    if not book_inner:
                        raise ExternalProviderError(
                            provider_code="BOOK_FAILED",
                            http_status=502,
                            message="TBO Book did not return booking details.",
                        )

                    pnr = book_inner.PNR
                    booking_id = book_inner.BookingId

                    nonlcc_ticket_req = TBOTicketNonLCCRequest(
                        EndUserIp=end_user_ip,
                        TokenId="",
                        TraceId=cached_data["TraceId"],
                        PNR=pnr,
                        BookingId=booking_id,
                        IsPriceChangeAccepted=True,
                    )
                    ticket_resp = await client.generate_ticket_nonlcc(nonlcc_ticket_req)

            except httpx.TimeoutException as timeout_err:
                # Step 6: Timeout recovery — poll GetBookingDetails
                logger.warning(
                    "TBO Book/Ticket timed out (razorpay_payment_id=%s): %s",
                    payload.razorpay_payment_id,
                    str(timeout_err),
                )
                # Only possible for Non-LCC where we got PNR from Book response
                if not is_lcc and pnr and booking_id:
                    details_resp = await client.get_booking_details_with_retry(
                        pnr=pnr,
                        booking_id=booking_id,
                        end_user_ip=end_user_ip,
                    )
                    if details_resp:
                        itin = details_resp.Response.FlightItinerary
                        recovered_ticket_status = _ticket_status_from_booking_status(
                            itin.Status
                        )
                        logger.info(
                            "Recovered booking via GetBookingDetails (pnr=%s, booking_id=%s, booking_status=%s, ticket_status=%s)",
                            itin.PNR,
                            itin.BookingId,
                            itin.Status,
                            recovered_ticket_status,
                        )
                        resp = BookingConfirmResponse(
                            pnr=itin.PNR,
                            booking_id=itin.BookingId,
                            is_lcc=is_lcc,
                            ticket_status=recovered_ticket_status,
                            ssr_denied=False,
                            invoice_no=itin.InvoiceNo,
                            invoice_amount=itin.InvoiceAmount,
                        )
                        await booking_service.save_booking_from_details(
                            user_id=current_user.id if current_user else None,
                            payment=payment,
                            provider="tbo",
                            details_response=details_resp,
                            direction="outbound",
                            trip_type=payload.trip_type,
                            is_lcc=is_lcc,
                            ticket_status=recovered_ticket_status,
                        )
                        await db.commit()
                        return _decorate_response(resp, payload, background_tasks)

                raise Exception(
                    f"TBO request timed out: {timeout_err}"
                ) from timeout_err
```

**Replace with:**

```python
        else:
            # Oneway or international return: single booking call
            try:
                ticket_resp = await _ticket_single_leg(
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
                    "TBO Book/Ticket timed out (razorpay_payment_id=%s): %s",
                    payload.razorpay_payment_id,
                    str(timeout_err),
                )
                # Attempt recovery via GetBookingDetails using TraceId
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
                if details_resp:
                    itin = details_resp.Response.FlightItinerary
                    recovered_ticket_status = _ticket_status_from_booking_status(
                        itin.Status
                    )
                    logger.info(
                        "Recovered booking via GetBookingDetails (pnr=%s, booking_id=%s, booking_status=%s, ticket_status=%s)",
                        itin.PNR,
                        itin.BookingId,
                        itin.Status,
                        recovered_ticket_status,
                    )
                    resp = BookingConfirmResponse(
                        pnr=itin.PNR,
                        booking_id=itin.BookingId,
                        is_lcc=is_lcc,
                        ticket_status=recovered_ticket_status,
                        ssr_denied=False,
                        invoice_no=itin.InvoiceNo,
                        invoice_amount=itin.InvoiceAmount,
                    )
                    await booking_service.save_booking_from_details(
                        user_id=current_user.id if current_user else None,
                        payment=payment,
                        provider="tbo",
                        details_response=details_resp,
                        direction="outbound",
                        trip_type=payload.trip_type,
                        is_lcc=is_lcc,
                        ticket_status=recovered_ticket_status,
                    )
                    await db.commit()
                    return _decorate_response(resp, payload, background_tasks)

                raise Exception(
                    f"TBO request timed out: {timeout_err}"
                ) from timeout_err
```

---

## Change 9: Update `TBOGetBookingDetailsRequest` schema

**File:** `backend/app/schemas/tbo/booking_details.py` — Replace lines 19-26

**Remove:**

```python
class TBOGetBookingDetailsRequest(TBOBaseSchema):
    """TBO GetBookingDetails API request"""

    EndUserIp: str
    TokenId: str
    PNR: str
    BookingId: int
```

**Replace with:**

```python
class TBOGetBookingDetailsRequest(TBOBaseSchema):
    """TBO GetBookingDetails API request.

    Supports multiple lookup patterns per TBO docs:
      - BookingId (+ optional PNR)
      - PNR + FirstName/LastName
      - TraceId
    """

    EndUserIp: str
    TokenId: str
    BookingId: int | None = None
    PNR: str | None = None
    TraceId: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
```

---

## Change 10: Update `get_booking_details_with_retry` in TBO client

**File:** `backend/app/clients/tbo_client.py` — Replace lines 543-615

**Remove:**

```python
    async def get_booking_details_with_retry(
        self,
        pnr: str,
        booking_id: int,
        end_user_ip: str,
        max_retries: int = 12,
        interval_seconds: float = 12.0,
    ) -> TBOGetBookingDetailsResponse | None:
        """Poll GetBookingDetails after a timeout to check if booking succeeded.

        When TBO Book/Ticket times out, the booking may have actually succeeded.
        We poll up to max_retries times at interval_seconds apart.
        Returns the first response that has a concrete itinerary/status,
        and keeps polling only while provider reports "booking under process".
        """
        token = await self.authenticate()

        for attempt in range(1, max_retries + 1):
            logger.info(
                "GetBookingDetails retry %d/%d for PNR=%s BookingId=%d",
                attempt,
                max_retries,
                pnr,
                booking_id,
            )
            if attempt > 1:
                await asyncio.sleep(interval_seconds)

            try:
                payload = TBOGetBookingDetailsRequest(
                    EndUserIp=end_user_ip,
                    TokenId=token,
                    PNR=pnr,
                    BookingId=booking_id,
                )
                response = await self.get_booking_details(payload)
                error_message = (
                    response.Response.Error.ErrorMessage
                    if response.Response.Error and response.Response.Error.ErrorMessage
                    else ""
                )
                if "booking under process" in error_message.lower():
                    logger.info(
                        "GetBookingDetails still under process on attempt %d for PNR=%s",
                        attempt,
                        pnr,
                    )
                    continue

                itin = response.Response.FlightItinerary
                if itin:
                    logger.info(
                        "GetBookingDetails resolved on attempt %d: PNR=%s status=%s",
                        attempt,
                        pnr,
                        itin.Status,
                    )
                    return response
                logger.info(
                    "GetBookingDetails did not return itinerary on attempt %d for PNR=%s",
                    attempt,
                    pnr,
                )
            except Exception as e:
                logger.warning("GetBookingDetails retry %d failed: %s", attempt, str(e))
                continue

        logger.warning(
            "GetBookingDetails gave up after %d retries for PNR=%s",
            max_retries,
            pnr,
        )
        return None
```

**Replace with:**

```python
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
```

---

## Summary of files changed

| File                                         | Changes                                                                                                                                                                                                                                                                     |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/app/api/v1/flight.py`               | Add `IntEnum` import, replace status constants, cache verified price in `fare_quote`, add price check in `create_booking_order`, delete `_generate_lcc_ticket_with_seat_retry`, add `_ticket_single_leg`, rewrite roundtrip + oneway booking logic, update timeout recovery |
| `backend/app/schemas/tbo/booking_details.py` | Make `PNR`/`BookingId` optional, add `TraceId`/`FirstName`/`LastName`                                                                                                                                                                                                       |
| `backend/app/clients/tbo_client.py`          | Update `get_booking_details_with_retry` to accept flexible lookup params                                                                                                                                                                                                    |
