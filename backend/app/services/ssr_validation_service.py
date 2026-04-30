"""Validate user-selected SSR codes against the canonical cached TBO SSR response.

Called from BookingCheckoutService.create_payment_order — BEFORE Razorpay
order creation — so we never charge a customer for a SSR mix that won't book.
"""

from __future__ import annotations

from app.core.exceptions import SsrExpiredError, SsrValidationError
from app.schemas.tbo.ssr import TBOSSRResponse
from app.utils.cache import FlightCache


class SsrValidationService:
    def __init__(self, cache: FlightCache):
        self.cache = cache

    async def validate(
        self,
        *,
        fare_id_outbound: str,
        fare_id_inbound: str | None,
        ssr_selections_outbound: list,
        ssr_selections_inbound: list,
        is_international_return: bool,
    ) -> None:
        """Raise SsrValidationError or SsrExpiredError; otherwise return None."""
        if not (ssr_selections_outbound or ssr_selections_inbound):
            return  # no SSR to validate

        # Outbound raw SSR — also covers inbound for international return
        outbound_raw = await self.cache.get_model(
            f"raw_ssr_{fare_id_outbound}", TBOSSRResponse
        )
        if outbound_raw is None:
            raise SsrExpiredError()

        missing: list[dict] = []
        if ssr_selections_outbound:
            missing.extend(
                self._check(
                    raw=outbound_raw,
                    selections=ssr_selections_outbound,
                    leg="outbound",
                    leg_index=0,
                    is_intl=is_international_return,
                )
            )

        if ssr_selections_inbound:
            if is_international_return:
                inbound_raw = outbound_raw
                inbound_leg_index = 1
            else:
                inbound_raw = await self.cache.get_model(
                    f"raw_ssr_{fare_id_inbound}", TBOSSRResponse
                )
                if inbound_raw is None:
                    raise SsrExpiredError()
                inbound_leg_index = 0
            missing.extend(
                self._check(
                    raw=inbound_raw,
                    selections=ssr_selections_inbound,
                    leg="inbound",
                    leg_index=inbound_leg_index,
                    is_intl=is_international_return,
                )
            )

        if missing:
            raise SsrValidationError(missing)

    def _check(
        self,
        *,
        raw: TBOSSRResponse,
        selections: list,
        leg: str,
        leg_index: int,
        is_intl: bool,
    ) -> list[dict]:
        """Build lookup sets for the given leg and check each selection."""
        response = raw.Response

        def _pick(blocks):
            if blocks is None:
                return []
            if is_intl:
                return [blocks[leg_index]] if leg_index < len(blocks) else []
            return list(blocks)

        seat_codes: set[str] = set()
        for sd in _pick(response.SeatDynamic):
            if not sd or not sd.SegmentSeat:
                continue
            for seg in sd.SegmentSeat:
                for row in seg.RowSeats or []:
                    for seat in row.Seats or []:
                        if seat.Code and seat.Code != "NoSeat":
                            seat_codes.add(seat.Code)

        baggage_codes = {
            b.Code
            for block in _pick(response.Baggage)
            for b in (block or [])
            if b.Code
        }
        meal_codes = {
            m.Code
            for block in _pick(response.MealDynamic)
            for m in (block or [])
            if m.Code
        }
        # Non-LCC dietary meals
        meal_codes |= {m.Code for m in (response.Meal or []) if m.Code}

        missing: list[dict] = []
        for seg_idx, sel in enumerate(selections or []):
            if sel is None:
                continue
            if sel.seat_code and sel.seat_code not in seat_codes:
                missing.append(
                    {
                        "leg": leg,
                        "segment": seg_idx,
                        "type": "seat",
                        "code": sel.seat_code,
                    }
                )
            if sel.baggage_code and sel.baggage_code not in baggage_codes:
                missing.append(
                    {
                        "leg": leg,
                        "segment": seg_idx,
                        "type": "baggage",
                        "code": sel.baggage_code,
                    }
                )
            if sel.meal_code and sel.meal_code not in meal_codes:
                missing.append(
                    {
                        "leg": leg,
                        "segment": seg_idx,
                        "type": "meal",
                        "code": sel.meal_code,
                    }
                )
        return missing
