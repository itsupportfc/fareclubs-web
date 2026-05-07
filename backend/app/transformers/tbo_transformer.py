import hashlib
import logging
import secrets
import uuid
from datetime import datetime
from typing import Optional, cast

from app.clients.exceptions import ExternalProviderError
from app.core.exceptions import SsrValidationError
from app.schemas.internal.booking import (
    BookingConfirmRequest,
    BookingConfirmResponse,
    ConfirmPassengerInfo,
    FareBreakdownInfo,
    MiniFareRuleInfo,
    PassengerFareInfo,
    SegmentBaggageInfo,
    SsrSelection,
)
from app.schemas.internal.fare_quote import FareQuoteResponse
from app.schemas.internal.fare_rule import FareRule, FareRulesResponse
from app.schemas.internal.flight import (
    Airline,
    Airport,
    CabinClass,
    Direction,
    FareOption,
    FlightGroup,
    FlightSearchRequest,
    FlightSearchResponse,
    FlightSegment,
    PassengerType,
    TripType,
)
from app.schemas.internal.ssr import (
    BaggageOptions,
    LccMealOptions,
    LccSegmentSsrView,
    LccSsrView,
    MealPreference,
    NonLccSegmentSsrView,
    NonLccSsrView,
    SeatOptions,
    SeatRow,
    SeatStatus,
    SeatType,
)
from app.schemas.tbo.book import (
    BookPassenger,
    PassengerFare,
    TBOBookRequest,
)
from app.schemas.tbo.common import (
    Baggage,
    Meal,
    Seat,
    SeatDynamic,
    SimpleMeal,
)
from app.schemas.tbo.enums import (
    BaggageDescriptionEnum,
    FlightCabinClass,
    JourneyType,
    SeatAvailabilityTypeEnum,
)
from app.schemas.tbo.enums import PassengerType as TBOPassengerType
from app.schemas.tbo.fare_quote import TBOFareQuoteResponse
from app.schemas.tbo.fare_rule import TBOFareRuleRequest, TBOFareRuleResponse
from app.schemas.tbo.search import (
    Itinerary,
    SearchSegment,
    Segment,
    TBOSearchRequest,
    TBOSearchResponse,
)
from app.schemas.tbo.ssr import TBOSSRResponse
from app.schemas.tbo.ticket import (
    PassengerFareSmall,
    TBOTicketLCCRequest,
    TBOTicketResponse,
    TicketPassengerRequest,
)
from app.transformers._fare_breakdown import build_fare_breakdown
from app.utils.cache import FlightCache
from app.utils.money import divide_money, money_to_float

logger = logging.getLogger(__name__)

# MAPPINGS
CABIN_CLASS_MAP: dict[int, CabinClass] = {
    FlightCabinClass.ECONOMY: "economy",
    FlightCabinClass.PREMIUM_ECONOMY: "premium_economy",
    FlightCabinClass.BUSINESS: "business",
    FlightCabinClass.FIRST: "first",
    FlightCabinClass.ALL: "economy",
    FlightCabinClass.UNKNOWN: "economy",
}

PASSENGER_TYPE_MAP: dict[int, PassengerType] = {
    TBOPassengerType.ADULT: "adult",
    TBOPassengerType.CHILD: "child",
    TBOPassengerType.INFANT: "infant",
}

SEAT_STATUS_MAP: dict[int, SeatStatus] = {
    1: "available",
    3: "occupied",
    4: "blocked",
    5: "space",
}

SEAT_TYPE_MAP: dict[int, str] = {
    1: "window",
    4: "window",
    5: "window",
    6: "window",
    7: "window",
    8: "window",
    9: "window",
    22: "window",
    25: "window",
    26: "window",
    27: "window",
    42: "window",
    43: "window",
    2: "aisle",
    10: "aisle",
    11: "aisle",
    12: "aisle",
    13: "aisle",
    14: "aisle",
    15: "aisle",
    23: "aisle",
    31: "aisle",
    32: "aisle",
    33: "aisle",
    46: "aisle",
    47: "aisle",
    3: "middle",
    16: "middle",
    17: "middle",
    18: "middle",
    19: "middle",
    20: "middle",
    21: "middle",
    24: "middle",
    28: "middle",
    29: "middle",
    30: "middle",
    44: "middle",
    45: "middle",
    34: "middle",
    35: "middle",
    36: "middle",
    37: "middle",
    38: "middle",
    39: "middle",
    40: "middle",
    41: "middle",
    0: "middle",
}


class TBOTransformer:
    """Transform TBO API responses to internal schemas."""

    # ------------------------------------------------------------------
    # SSR TRANSFORMERS
    # ------------------------------------------------------------------

    def transform_non_lcc_ssr_response(
        self,
        baggage_options: list[Baggage] | None,
        meal_options: list[SimpleMeal] | None,
        seat_options: Optional[SeatDynamic],
    ) -> NonLccSsrView:
        segment_map: dict[str, NonLccSegmentSsrView] = {}
        # Full-journey items live at trip level — deduped by code.
        journey_baggage: dict[str, BaggageOptions] = {}

        # SEAT
        if seat_options and seat_options.SegmentSeat:
            for segment in seat_options.SegmentSeat:
                if not segment.RowSeats:
                    continue
                sample_seat = segment.RowSeats[0].Seats[0]
                key = f"{sample_seat.FlightNumber}_{sample_seat.Origin}"
                if key not in segment_map:
                    segment_map[key] = NonLccSegmentSsrView(
                        flight_number=sample_seat.FlightNumber,
                        origin=sample_seat.Origin,
                        destination=sample_seat.Destination,
                    )
                segment_map[key].seat_options = [
                    SeatRow(
                        row_number=rows.Seats[0].RowNo,
                        seats=[
                            SeatOptions(
                                code=seat.Code,
                                price=seat.Price,
                                status=SEAT_STATUS_MAP.get(
                                    seat.AvailablityType, "occupied"
                                ),
                                type=cast(SeatType, SEAT_TYPE_MAP[seat.SeatType]),
                            )
                            for seat in rows.Seats
                            if seat.Code != "NoSeat" and seat.SeatType in SEAT_TYPE_MAP
                        ],
                    )
                    for rows in segment.RowSeats
                    if rows.Seats
                ]

        # BAGGAGE — split into journey-level (WayType=2) vs segment-specific.
        for b in baggage_options or []:
            if b.WayType == 2:
                journey_baggage.setdefault(
                    b.Code,
                    BaggageOptions(
                        code=b.Code,
                        weight=b.Weight,
                        price=b.Price,
                        for_full_journey=True,
                    ),
                )
                continue
            key = f"{b.FlightNumber}_{b.Origin}"
            if key not in segment_map:
                segment_map[key] = NonLccSegmentSsrView(
                    flight_number=b.FlightNumber,
                    origin=b.Origin,
                    destination=b.Destination,
                )
            segment_map[key].baggage_options.append(
                BaggageOptions(
                    code=b.Code,
                    weight=b.Weight,
                    price=b.Price,
                    for_full_journey=False,
                )
            )

        # MEAL
        meal_prefs = [
            MealPreference(code=m.Code, description=m.Description)
            for m in meal_options or []
        ]

        return NonLccSsrView(
            journey_baggage=list(journey_baggage.values()),
            segments=list(segment_map.values()),
            meal_preferences=meal_prefs,
        )

    def transform_lcc_ssr_response(
        self,
        baggage_options: list[Baggage] | None,
        meal_options: list[Meal] | None,
        seat_options: Optional[SeatDynamic],
    ) -> LccSsrView:
        segment_map: dict[str, LccSegmentSsrView] = {}
        # Full-journey items live at trip level — deduped by code.
        journey_baggage: dict[str, BaggageOptions] = {}
        journey_meals: dict[str, LccMealOptions] = {}

        # SEAT
        if seat_options and seat_options.SegmentSeat:
            for segment in seat_options.SegmentSeat:
                if not segment.RowSeats:
                    continue
                sample_seat = segment.RowSeats[0].Seats[0]
                key = f"{sample_seat.FlightNumber}_{sample_seat.Origin}"
                if key not in segment_map:
                    segment_map[key] = LccSegmentSsrView(
                        flight_number=sample_seat.FlightNumber,
                        origin=sample_seat.Origin,
                        destination=sample_seat.Destination,
                    )
                segment_map[key].seat_options = [
                    SeatRow(
                        row_number=rows.Seats[0].RowNo,
                        seats=[
                            SeatOptions(
                                code=seat.Code,
                                price=seat.Price,
                                status=SEAT_STATUS_MAP.get(
                                    seat.AvailablityType, "occupied"
                                ),
                                type=cast(SeatType, SEAT_TYPE_MAP[seat.SeatType]),
                            )
                            for seat in rows.Seats
                            if seat.Code != "NoSeat" and seat.SeatType in SEAT_TYPE_MAP
                        ],
                    )
                    for rows in segment.RowSeats
                    if rows.Seats
                ]

        # BAGGAGE — split into journey-level (WayType=2) vs segment-specific.
        for b in baggage_options or []:
            if b.WayType == 2:
                journey_baggage.setdefault(
                    b.Code,
                    BaggageOptions(
                        code=b.Code,
                        weight=b.Weight,
                        price=b.Price,
                        for_full_journey=True,
                    ),
                )
                continue
            key = f"{b.FlightNumber}_{b.Origin}"
            if key not in segment_map:
                segment_map[key] = LccSegmentSsrView(
                    flight_number=b.FlightNumber,
                    origin=b.Origin,
                    destination=b.Destination,
                )
            segment_map[key].baggage_options.append(
                BaggageOptions(
                    code=b.Code,
                    weight=b.Weight,
                    price=b.Price,
                    for_full_journey=False,
                )
            )

        # MEAL — same split.
        for m in meal_options or []:
            if m.Code == "NoMeal":
                continue
            if m.WayType == 2:
                journey_meals.setdefault(
                    m.Code,
                    LccMealOptions(
                        code=m.Code,
                        description=m.AirlineDescription or "",
                        price=m.Price,
                        for_full_journey=True,
                    ),
                )
                continue
            key = f"{m.FlightNumber}_{m.Origin}"
            if key not in segment_map:
                segment_map[key] = LccSegmentSsrView(
                    flight_number=m.FlightNumber,
                    origin=m.Origin,
                    destination=m.Destination,
                )
            segment_map[key].meal_options.append(
                LccMealOptions(
                    code=m.Code,
                    description=m.AirlineDescription or "",
                    price=m.Price,
                    for_full_journey=False,
                )
            )

        return LccSsrView(
            journey_baggage=list(journey_baggage.values()),
            journey_meals=list(journey_meals.values()),
            segments=list(segment_map.values()),
        )

    def transform_fare_rule_response(
        self, tbo_response: TBOFareRuleResponse
    ) -> FareRulesResponse:
        tbo_fare_rules = tbo_response.Response.FareRules or []
        internal_fare_rules = [
            FareRule(
                airline=rule.Airline,
                destination=rule.Destination,
                fare_basis_code=rule.FareBasisCode,
                fare_inclusions=rule.FareInclusions,
                fare_restriction=rule.FareRestriction,
                fare_rule_detail=rule.FareRuleDetail,
                flight_id=rule.FlightId,
                origin=rule.Origin,
            )
            for rule in tbo_fare_rules
        ]
        return FareRulesResponse(fare_rules=internal_fare_rules)

    # ------------------------------------------------------------------
    # FREE SSR AUTO-SELECTION (Step 7)
    # ------------------------------------------------------------------

    def _find_free_ssr(self, raw_ssr: Optional[TBOSSRResponse]) -> dict:
        """Find free (Price=0) SSR items from cached SSR response.

        TBO may have free meals/baggage that MUST be selected for the booking
        to succeed. If user doesn't pick anything, we auto-select these.
        """
        result = {
            "free_baggage": None,
            "free_meal_lcc": None,
            "free_meal_code": None,
        }
        if not raw_ssr or not raw_ssr.Response:
            return result

        # Free baggage: Description=1 (Included) + Price=0
        if raw_ssr.Response.Baggage:
            for seg_options in raw_ssr.Response.Baggage:
                for b in seg_options or []:
                    if b.Price == 0 and b.Description == 1:
                        result["free_baggage"] = b
                        break
                if result["free_baggage"]:
                    break

        # Free LCC meal (MealDynamic): Price=0
        if raw_ssr.Response.MealDynamic:
            for seg_options in raw_ssr.Response.MealDynamic:
                for m in seg_options or []:
                    if m.Price == 0 and m.Code != "NoMeal":
                        result["free_meal_lcc"] = m
                        break
                if result["free_meal_lcc"]:
                    break

        # Non-LCC meal (Meal): these are just dietary preference codes, typically free
        if raw_ssr.Response.Meal:
            for m in raw_ssr.Response.Meal:
                if m.Code:
                    result["free_meal_code"] = m.Code
                    break

        return result

    # ------------------------------------------------------------------
    # FARE-QUOTE → PROVIDER PASSENGER FARE HELPERS
    # ------------------------------------------------------------------

    def _fare_breakdown_for_pax_type(
        self, fare_quote: TBOFareQuoteResponse, pax_type: int
    ):
        """Return the FareBreakdown row matching this passenger type.

        TBO's FareBreakdown is aggregated by pax type (e.g. one row for all
        adults), so callers must divide by PassengerCount to get per-head values.
        """
        for fb in fare_quote.Response.Results.FareBreakdown or []:
            if int(fb.PassengerType) == int(pax_type):
                return fb
        raise ExternalProviderError(
            provider_code="FARE_BREAKDOWN_MISSING",
            http_status=502,
            message=f"FareQuote has no FareBreakdown for pax_type={pax_type}",
        )

    def _passenger_fare_from_fare_quote(
        self, *, fare_quote: TBOFareQuoteResponse, pax_type: int,
    ) -> PassengerFareInfo:
        """Build a per-head PassengerFareInfo from cached FareQuote.

        OtherCharges is itinerary-level in TBO; FareBreakdown does not carry it
        per-pax-type. We reconcile via PublishedFare for the customer total
        (Razorpay), so the per-pax provider block uses 0 here.
        """
        fb = self._fare_breakdown_for_pax_type(fare_quote, pax_type)
        n = fb.PassengerCount or 1
        return PassengerFareInfo(
            currency=fb.Currency or "INR",
            base_fare=money_to_float(divide_money(fb.BaseFare, n)),
            tax=money_to_float(divide_money(fb.Tax, n)),
            yq_tax=money_to_float(divide_money(fb.YQTax or 0, n)),
            other_charges=0,
            additional_txn_fee_ofrd=money_to_float(
                divide_money(fb.AdditionalTxnFeeOfrd or 0, n)
            ),
            additional_txn_fee_pub=money_to_float(
                divide_money(fb.AdditionalTxnFeePub or 0, n)
            ),
            pg_charge=money_to_float(divide_money(fb.PGCharge or 0, n)),
        )

    # ------------------------------------------------------------------
    # BOOKING TRANSFORMERS
    # ------------------------------------------------------------------

    def transform_book_request(
        self,
        request: BookingConfirmRequest,
        cached_data: dict,
        end_user_ip: str,
        raw_ssr: Optional[TBOSSRResponse] = None,
        direction: str = "outbound",
        fare_quote: TBOFareQuoteResponse | None = None,
    ) -> TBOBookRequest:
        """Build TBO Book request for Non-LCC flights."""
        if fare_quote is None:
            raise ExternalProviderError(
                provider_code="FARE_QUOTE_MISSING",
                http_status=410,
                message="FareQuote expired. Please verify fare again before booking.",
            )
        free_ssr = self._find_free_ssr(raw_ssr)

        # Build per-segment lookup maps from cached SSR (mirrors LCC approach)
        seat_maps: list[dict[str, Seat]] = []
        baggage_maps: list[dict[str, Baggage]] = []
        journey_baggage_maps: list[dict[str, Baggage]] = []
        meal_map: dict[str, SimpleMeal] = {}  # non-LCC meals are a flat list
        segment_keys: list[tuple[str, str]] = []  # (Origin, FlightNumber) per segment

        if raw_ssr and raw_ssr.Response:
            # Seats — per segment
            if raw_ssr.Response.SeatDynamic:
                for sd in raw_ssr.Response.SeatDynamic:
                    if sd.SegmentSeat:
                        for seg in sd.SegmentSeat:
                            seg_seats: dict[str, Seat] = {}
                            reference_seat: Seat | None = None
                            if seg.RowSeats:
                                for row in seg.RowSeats:
                                    for seat in row.Seats:
                                        if reference_seat is None:
                                            reference_seat = seat
                                        if (
                                            seat.Code
                                            and seat.Code != "NoSeat"
                                            and seat.AvailablityType
                                            == SeatAvailabilityTypeEnum.AVAILABLE
                                        ):
                                            seg_seats[seat.Code] = seat
                            seat_maps.append(seg_seats)
                            if reference_seat:
                                segment_keys.append(
                                    (reference_seat.Origin, reference_seat.FlightNumber)
                                )

            # Baggage — group by (Origin, FlightNumber) to match segment order
            if raw_ssr.Response.Baggage:
                for seg_options in raw_ssr.Response.Baggage:
                    grouped: dict[tuple[str, str], dict[str, Baggage]] = {}
                    for b in seg_options or []:
                        key = (b.Origin, b.FlightNumber)
                        if key not in grouped:
                            grouped[key] = {}
                        grouped[key][b.Code] = b
                    seen: set[tuple[str, str]] = set()
                    for sk in segment_keys:
                        if sk in grouped and sk not in seen:
                            seen.add(sk)
                            baggage_maps.append(grouped[sk])
                    for gk, gv in grouped.items():
                        if gk not in seen:
                            baggage_maps.append(gv)

            # Per-leg journey baggage maps (WayType==2 — full direction).
            # See the LCC build site above for rationale: an international
            # roundtrip's outbound and inbound copies of the same code must
            # not collapse onto one segment.
            for seg_options in raw_ssr.Response.Baggage:
                leg_bag: dict[str, Baggage] = {}
                for b in seg_options or []:
                    if b.WayType == 2:
                        leg_bag.setdefault(b.Code, b)
                journey_baggage_maps.append(leg_bag)

            # Meal — flat list for non-LCC (SimpleMeal: Code + Description string)
            if raw_ssr.Response.Meal:
                for m in raw_ssr.Response.Meal:
                    if m.Code:
                        meal_map[m.Code] = m

        passengers = []
        for p in request.passengers:
            dob = datetime.strptime(p.date_of_birth, "%Y-%m-%d")
            passport_expiry = (
                datetime.strptime(p.passport_expiry, "%Y-%m-%d")
                if p.passport_expiry
                else None
            )
            passport_issue_date = (
                datetime.strptime(p.passport_issue_date, "%Y-%m-%d")
                if p.passport_issue_date
                else None
            )

            pax_fare = self._passenger_fare_from_fare_quote(
                fare_quote=fare_quote, pax_type=p.pax_type
            )
            fare = PassengerFare(
                Currency=pax_fare.currency,
                BaseFare=pax_fare.base_fare,
                Tax=pax_fare.tax,
                YQTax=pax_fare.yq_tax or 0,
                AdditionalTxnFeeOfrd=pax_fare.additional_txn_fee_ofrd or 0,
                AdditionalTxnFeePub=pax_fare.additional_txn_fee_pub or 0,
                PGCharge=pax_fare.pg_charge or 0,
                OtherCharges=pax_fare.other_charges or 0,
            )

            # Determine SSR segments for this direction
            if request.is_international_return:
                ssr_segments = (p.ssr_segments_outbound or []) + (
                    p.ssr_segments_inbound or []
                )
            elif direction == "inbound":
                ssr_segments = p.ssr_segments_inbound or []
            else:
                ssr_segments = p.ssr_segments_outbound or []

            meal: SimpleMeal | None = None
            seat_list: list[Seat] = []
            baggage_list: list[Baggage] = []

            for seg_idx, seg_ssr in enumerate(ssr_segments):
                if seg_ssr is None:
                    continue

                # Meal — single selection for non-LCC; use first valid hit across segments
                if not meal and seg_ssr.meal_code:
                    if not meal_map or seg_ssr.meal_code in meal_map:
                        desc = (
                            meal_map[seg_ssr.meal_code].Description
                            if seg_ssr.meal_code in meal_map
                            else (seg_ssr.meal_description or seg_ssr.meal_code)
                        )
                        meal = SimpleMeal(Code=seg_ssr.meal_code, Description=desc)

                # Seat — one full Seat object per segment.
                # SSR validation already ran upstream — any miss here means the
                # cache rotated between validate() and now: surface as 422.
                if p.pax_type != 3:  # not infant
                    s_map = seat_maps[seg_idx] if seg_idx < len(seat_maps) else {}
                    if seg_ssr.seat_code:
                        if seg_ssr.seat_code not in s_map:
                            raise SsrValidationError([{
                                "leg": direction,
                                "segment": seg_idx,
                                "pax": p.pax_type,
                                "type": "seat",
                                "code": seg_ssr.seat_code,
                            }])
                        seat_list.append(s_map[seg_ssr.seat_code])

                # Baggage — one per segment
                if seg_ssr.baggage_code:
                    b_map = baggage_maps[seg_idx] if seg_idx < len(baggage_maps) else {}
                    if seg_ssr.baggage_code not in b_map:
                        raise SsrValidationError([{
                            "leg": direction,
                            "segment": seg_idx,
                            "pax": p.pax_type,
                            "type": "baggage",
                            "code": seg_ssr.baggage_code,
                        }])
                    baggage_list.append(b_map[seg_ssr.baggage_code])

            # Journey-level SSR (WayType==2 — one entry per trip direction).
            # See LCC version for rationale: pair selections with leg index so
            # baggage carries the correct Origin/Destination/FlightNumber.
            if request.is_international_return:
                j_ssr_pairs: list[tuple[SsrSelection, int]] = []
                if p.journey_ssr_outbound:
                    j_ssr_pairs.append((p.journey_ssr_outbound, 0))
                if p.journey_ssr_inbound:
                    j_ssr_pairs.append((p.journey_ssr_inbound, 1))
            elif direction == "inbound":
                j_ssr_pairs = (
                    [(p.journey_ssr_inbound, 0)] if p.journey_ssr_inbound else []
                )
            else:
                j_ssr_pairs = (
                    [(p.journey_ssr_outbound, 0)] if p.journey_ssr_outbound else []
                )

            for j_ssr, leg_idx in j_ssr_pairs:
                bag_map = (
                    journey_baggage_maps[leg_idx]
                    if leg_idx < len(journey_baggage_maps)
                    else {}
                )
                leg_label = "outbound" if leg_idx == 0 else "inbound"
                if j_ssr.baggage_code:
                    if j_ssr.baggage_code not in bag_map:
                        raise SsrValidationError([{
                            "leg": leg_label,
                            "segment": "journey",
                            "pax": p.pax_type,
                            "type": "baggage",
                            "code": j_ssr.baggage_code,
                        }])
                    baggage_list.append(bag_map[j_ssr.baggage_code])
                # Non-LCC: TBO accepts a single Meal preference per PNR, so we
                # honour outbound first. If the inbound leg picks a different
                # meal, log it (the request body will only carry the outbound
                # one) so QA can see the asymmetry rather than silently
                # dropping it as the previous `if not meal` short-circuit did.
                if j_ssr.meal_code and j_ssr.meal_code in meal_map:
                    if not meal:
                        desc = meal_map[j_ssr.meal_code].Description
                        meal = SimpleMeal(Code=j_ssr.meal_code, Description=desc)
                    elif meal.Code != j_ssr.meal_code:
                        logger.warning(
                            "Non-LCC journey meal: ignoring %s leg pick %s; "
                            "PNR keeps %s",
                            leg_label,
                            j_ssr.meal_code,
                            meal.Code,
                        )

            # Auto-assign free SSR if user didn't select anything
            if not meal and free_ssr["free_meal_code"]:
                free_meal_obj = meal_map.get(free_ssr["free_meal_code"])
                meal = SimpleMeal(
                    Code=free_ssr["free_meal_code"],
                    Description=free_meal_obj.Description
                    if free_meal_obj
                    else free_ssr["free_meal_code"],
                )
            if p.pax_type != 3:  # not infant
                if not baggage_list and free_ssr["free_baggage"]:
                    baggage_list = [free_ssr["free_baggage"]]

            passengers.append(
                BookPassenger(
                    Title=p.title,
                    FirstName=p.first_name,
                    LastName=p.last_name,
                    PaxType=p.pax_type,
                    DateOfBirth=dob,
                    Gender=p.gender,
                    AddressLine1=p.address_line1
                    if p.address_line1 and p.address_line1.strip() not in ("", "N/A")
                    else "123, Test",
                    AddressLine2=p.address_line2,
                    City=p.city
                    if p.city and p.city.strip() not in ("", "N/A")
                    else "New Delhi",
                    CountryCode=p.country_code,
                    CountryName=p.country_name,
                    Nationality=p.nationality,
                    ContactNo=p.contact_no,
                    Email=p.email,
                    IsLeadPax=p.is_lead_pax,
                    PassportNo=p.passport_no,
                    PassportExpiry=passport_expiry,
                    PassportIssueDate=passport_issue_date,
                    PassportIssueCountryCode=p.passport_issue_country_code,
                    PAN=p.pan,
                    GSTCompanyName=p.gst.gst_company_name if p.gst else None,
                    GSTNumber=p.gst.gst_number if p.gst else None,
                    GSTCompanyAddress=p.gst.gst_company_address if p.gst else None,
                    GSTCompanyContactNumber=p.gst.gst_company_contact_number
                    if p.gst
                    else None,
                    GSTCompanyEmail=p.gst.gst_company_email if p.gst else None,
                    Fare=fare,
                    MealDynamic=meal,
                    SeatDynamic=seat_list or None,
                    Baggage=baggage_list or None,
                )
            )

        return TBOBookRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=cached_data["TraceId"],
            ResultIndex=cached_data["ResultIndex"],
            Passengers=passengers,
        )

    def transform_ticket_lcc_request(
        self,
        request: BookingConfirmRequest,
        cached_data: dict,
        end_user_ip: str,
        raw_ssr: Optional[TBOSSRResponse] = None,
        force_no_seat_selection: bool = False,
        direction: str = "outbound",
        fare_quote: TBOFareQuoteResponse | None = None,
    ) -> TBOTicketLCCRequest:
        """Build TBO Ticket request for LCC flights."""
        if fare_quote is None:
            raise ExternalProviderError(
                provider_code="FARE_QUOTE_MISSING",
                http_status=410,
                message="FareQuote expired. Please verify fare again before booking.",
            )
        free_ssr = self._find_free_ssr(raw_ssr)

        # Build per-segment lookup maps from cached SSR
        seat_maps: list[dict[str, Seat]] = []
        baggage_maps: list[dict[str, Baggage]] = []
        meal_maps: list[dict[str, Meal]] = []
        free_meals_by_segment: list[Meal] = []
        no_seat_list: list[Seat] = []
        segment_keys: list[tuple[str, str]] = []  # (Origin, FlightNumber) per segment

        if raw_ssr and raw_ssr.Response:
            # Process seats FIRST to establish segment ordering
            if raw_ssr.Response.SeatDynamic:
                for sd in raw_ssr.Response.SeatDynamic:
                    if sd.SegmentSeat:
                        for seg in sd.SegmentSeat:
                            seg_seats: dict[str, Seat] = {}
                            reference_seat: Seat | None = None
                            if seg.RowSeats:
                                for row in seg.RowSeats:
                                    for seat in row.Seats:
                                        if reference_seat is None:
                                            reference_seat = seat
                                        if (
                                            seat.Code
                                            and seat.Code != "NoSeat"
                                            and seat.AvailablityType
                                            == SeatAvailabilityTypeEnum.AVAILABLE
                                        ):
                                            seg_seats[seat.Code] = seat
                            seat_maps.append(seg_seats)
                            if reference_seat:
                                segment_keys.append(
                                    (reference_seat.Origin, reference_seat.FlightNumber)
                                )
                                no_seat_list.append(
                                    Seat(
                                        AirlineCode=reference_seat.AirlineCode,
                                        FlightNumber=reference_seat.FlightNumber,
                                        CraftType=reference_seat.CraftType,
                                        Origin=reference_seat.Origin,
                                        Destination=reference_seat.Destination,
                                        AvailablityType=0,
                                        Description=2,
                                        Code="NoSeat",
                                        RowNo="0",
                                        SeatNo=None,
                                        SeatType=0,
                                        SeatWayType=2,
                                        Compartment=0,
                                        Deck=0,
                                        Currency=reference_seat.Currency,
                                        Price=0.0,
                                    )
                                )

            # Baggage — group by (Origin, FlightNumber) to split merged direction arrays
            if raw_ssr.Response.Baggage:
                for seg_options in raw_ssr.Response.Baggage:
                    grouped: dict[tuple[str, str], dict[str, Baggage]] = {}
                    for b in seg_options or []:
                        key = (b.Origin, b.FlightNumber)
                        if key not in grouped:
                            grouped[key] = {}
                        grouped[key][b.Code] = b

                    seen: set[tuple[str, str]] = set()
                    for sk in segment_keys:
                        if sk in grouped and sk not in seen:
                            seen.add(sk)
                            baggage_maps.append(grouped[sk])
                    for gk, gv in grouped.items():
                        if gk not in seen:
                            baggage_maps.append(gv)

            # Meals — group by (Origin, FlightNumber) to split merged direction arrays
            if raw_ssr.Response.MealDynamic:
                for seg_options in raw_ssr.Response.MealDynamic:
                    grouped_meals: dict[tuple[str, str], dict[str, Meal]] = {}
                    free_per_group: dict[tuple[str, str], Meal | None] = {}
                    for m in seg_options or []:
                        if m.Code == "NoMeal":
                            continue
                        key = (m.Origin, m.FlightNumber)
                        if key not in grouped_meals:
                            grouped_meals[key] = {}
                        grouped_meals[key][m.Code] = m
                        if m.Price == 0 and key not in free_per_group:
                            free_per_group[key] = m

                    seen_meals: set[tuple[str, str]] = set()
                    for sk in segment_keys:
                        if sk in grouped_meals and sk not in seen_meals:
                            seen_meals.add(sk)
                            meal_maps.append(grouped_meals[sk])
                            if sk in free_per_group:
                                free_meals_by_segment.append(free_per_group[sk])
                    for gk, gv in grouped_meals.items():
                        if gk not in seen_meals:
                            meal_maps.append(gv)
                            if gk in free_per_group:
                                free_meals_by_segment.append(free_per_group[gk])

        # Per-leg journey-SSR maps (WayType==2 — full direction, not per segment).
        # One map per SSR block so an international roundtrip's outbound and
        # inbound selections don't collapse onto the same segment via setdefault.
        # For domestic/oneway the transformer is called per direction with a
        # single-block raw_ssr, so the lists have length 1.
        journey_baggage_maps: list[dict[str, Baggage]] = []
        journey_meal_maps: list[dict[str, Meal]] = []
        if raw_ssr and raw_ssr.Response:
            for seg_options in raw_ssr.Response.Baggage or []:
                leg_bag: dict[str, Baggage] = {}
                for b in seg_options or []:
                    if b.WayType == 2:
                        leg_bag.setdefault(b.Code, b)
                journey_baggage_maps.append(leg_bag)
            for seg_options in raw_ssr.Response.MealDynamic or []:
                leg_meal: dict[str, Meal] = {}
                for m in seg_options or []:
                    if m.WayType == 2:
                        leg_meal.setdefault(m.Code, m)
                journey_meal_maps.append(leg_meal)

        num_segments = max(len(seat_maps), len(no_seat_list), 1)

        passengers = []
        for p in request.passengers:
            passport_expiry = (
                datetime.strptime(p.passport_expiry, "%Y-%m-%d")
                if p.passport_expiry
                else None
            )
            passport_issue_date = (
                datetime.strptime(p.passport_issue_date, "%Y-%m-%d")
                if p.passport_issue_date
                else None
            )

            pax_fare = self._passenger_fare_from_fare_quote(
                fare_quote=fare_quote, pax_type=p.pax_type
            )
            fare = PassengerFareSmall(
                BaseFare=pax_fare.base_fare,
                Tax=pax_fare.tax,
                YQTax=pax_fare.yq_tax or 0,
                AdditionalTxnFeeOfrd=pax_fare.additional_txn_fee_ofrd or 0,
                AdditionalTxnFeePub=pax_fare.additional_txn_fee_pub or 0,
                PGCharge=pax_fare.pg_charge or 0,
            )

            # Determine SSR segments for this passenger based on direction
            if request.is_international_return:
                ssr_segments = (p.ssr_segments_outbound or []) + (
                    p.ssr_segments_inbound or []
                )
            elif direction == "inbound":
                ssr_segments = p.ssr_segments_inbound or []
            else:
                ssr_segments = p.ssr_segments_outbound or []

            # Build per-segment SSR lists
            baggage_list: list[Baggage] = []
            meal_list: list[Meal] = []
            seat_dynamic: list[Seat] = []

            for seg_idx in range(num_segments):
                seg_ssr = ssr_segments[seg_idx] if seg_idx < len(ssr_segments) else None

                # Baggage. SSR validation already ran upstream — any miss here
                # means the cache rotated; raise so the user is asked to refresh.
                if seg_ssr and seg_ssr.baggage_code:
                    bag_map = (
                        baggage_maps[seg_idx] if seg_idx < len(baggage_maps) else {}
                    )
                    if seg_ssr.baggage_code not in bag_map:
                        raise SsrValidationError([{
                            "leg": direction,
                            "segment": seg_idx,
                            "pax": p.pax_type,
                            "type": "baggage",
                            "code": seg_ssr.baggage_code,
                        }])
                    baggage_list.append(bag_map[seg_ssr.baggage_code])

                # Meals
                if seg_ssr and seg_ssr.meal_code:
                    m_map = meal_maps[seg_idx] if seg_idx < len(meal_maps) else {}
                    if seg_ssr.meal_code not in m_map:
                        raise SsrValidationError([{
                            "leg": direction,
                            "segment": seg_idx,
                            "pax": p.pax_type,
                            "type": "meal",
                            "code": seg_ssr.meal_code,
                        }])
                    meal_list.append(m_map[seg_ssr.meal_code])

                # Seats (skip infants)
                if p.pax_type != 3:
                    s_map = seat_maps[seg_idx] if seg_idx < len(seat_maps) else {}
                    if (
                        not force_no_seat_selection
                        and seg_ssr
                        and seg_ssr.seat_code
                    ):
                        if seg_ssr.seat_code not in s_map:
                            raise SsrValidationError([{
                                "leg": direction,
                                "segment": seg_idx,
                                "pax": p.pax_type,
                                "type": "seat",
                                "code": seg_ssr.seat_code,
                            }])
                        seat_dynamic.append(s_map[seg_ssr.seat_code])
                    elif seg_idx < len(no_seat_list):
                        seat_dynamic.append(no_seat_list[seg_idx])

            # Journey-level SSR (WayType==2 — one entry per trip direction).
            # Pair each user-side selection with its leg index so the looked-up
            # Baggage/Meal carries the right Origin/Destination/FlightNumber.
            # International return: outbound→0, inbound→1 against the shared
            # raw_ssr. Domestic/oneway: leg_idx is always 0 because each
            # transformer call sees a single-block raw_ssr.
            if request.is_international_return:
                j_ssr_pairs: list[tuple[SsrSelection, int]] = []
                if p.journey_ssr_outbound:
                    j_ssr_pairs.append((p.journey_ssr_outbound, 0))
                if p.journey_ssr_inbound:
                    j_ssr_pairs.append((p.journey_ssr_inbound, 1))
            elif direction == "inbound":
                j_ssr_pairs = (
                    [(p.journey_ssr_inbound, 0)] if p.journey_ssr_inbound else []
                )
            else:
                j_ssr_pairs = (
                    [(p.journey_ssr_outbound, 0)] if p.journey_ssr_outbound else []
                )

            for j_ssr, leg_idx in j_ssr_pairs:
                bag_map = (
                    journey_baggage_maps[leg_idx]
                    if leg_idx < len(journey_baggage_maps)
                    else {}
                )
                meal_map_j = (
                    journey_meal_maps[leg_idx]
                    if leg_idx < len(journey_meal_maps)
                    else {}
                )
                leg_label = "outbound" if leg_idx == 0 else "inbound"
                if j_ssr.baggage_code:
                    if j_ssr.baggage_code not in bag_map:
                        raise SsrValidationError([{
                            "leg": leg_label,
                            "segment": "journey",
                            "pax": p.pax_type,
                            "type": "baggage",
                            "code": j_ssr.baggage_code,
                        }])
                    baggage_list.append(bag_map[j_ssr.baggage_code])
                if j_ssr.meal_code:
                    if j_ssr.meal_code not in meal_map_j:
                        raise SsrValidationError([{
                            "leg": leg_label,
                            "segment": "journey",
                            "pax": p.pax_type,
                            "type": "meal",
                            "code": j_ssr.meal_code,
                        }])
                    meal_list.append(meal_map_j[j_ssr.meal_code])

            # Auto-assign free SSR if user didn't select anything
            if not meal_list and free_meals_by_segment:
                meal_list = list(free_meals_by_segment)
            elif not meal_list and free_ssr["free_meal_lcc"]:
                meal_list = [free_ssr["free_meal_lcc"]]
            if p.pax_type != 3:
                if not seat_dynamic and no_seat_list:
                    seat_dynamic = list(no_seat_list)
                if not baggage_list and free_ssr["free_baggage"]:
                    baggage_list = [free_ssr["free_baggage"]]

            dob = (
                p.date_of_birth
                if "T" in p.date_of_birth
                else p.date_of_birth + "T00:00:00"
            )

            passengers.append(
                TicketPassengerRequest(
                    Title=p.title,
                    FirstName=p.first_name,
                    LastName=p.last_name,
                    PaxType=p.pax_type,
                    Gender=p.gender,
                    DateOfBirth=dob,
                    AddressLine1=p.address_line1
                    if p.address_line1 and p.address_line1.strip() not in ("", "N/A")
                    else "123, Test",
                    AddressLine2=p.address_line2,
                    City=p.city
                    if p.city and p.city.strip() not in ("", "N/A")
                    else "New Delhi",
                    CountryCode=p.country_code,
                    CountryName=p.country_name or "India",
                    ContactNo=p.contact_no,
                    Email=p.email,
                    IsLeadPax=p.is_lead_pax,
                    Nationality=p.nationality,
                    IsPassportRequired=p.is_passport_required,
                    PassportNo=p.passport_no,
                    PassportExpiry=passport_expiry,
                    PassportIssueDate=passport_issue_date,
                    PassportIssueCountryCode=p.passport_issue_country_code,
                    PAN=p.pan,
                    GSTCompanyName=p.gst.gst_company_name if p.gst else None,
                    GSTNumber=p.gst.gst_number if p.gst else None,
                    GSTCompanyAddress=p.gst.gst_company_address if p.gst else None,
                    GSTCompanyContactNumber=p.gst.gst_company_contact_number
                    if p.gst
                    else None,
                    GSTCompanyEmail=p.gst.gst_company_email if p.gst else None,
                    Fare=fare,
                    Baggage=baggage_list or None,
                    MealDynamic=meal_list or None,
                    SeatDynamic=seat_dynamic or None,
                )
            )

        return TBOTicketLCCRequest(
            EndUserIp=end_user_ip,
            TokenId="",
            TraceId=cached_data["TraceId"],
            ResultIndex=cached_data["ResultIndex"],
            Passengers=passengers,
        )

    def transform_booking_confirm_response(
        self,
        ticket_response: TBOTicketResponse,
        is_lcc: bool,
    ) -> BookingConfirmResponse:
        inner = ticket_response.Response.Response
        if inner is None:
            error = ticket_response.Response.Error
            raise ExternalProviderError(
                provider_code="TICKET_FAILED",
                http_status=502,
                message=f"TBO ticketing failed: {error.ErrorMessage if error else 'Unknown error'}",
            )
        itinerary = inner.FlightItinerary

        # Build passenger info (including confirmed seat numbers per segment)
        passengers_info = []
        for pax in itinerary.Passenger:
            seat_numbers: list[str | None] | None = None
            if pax.SegmentAdditionalInfo:
                seat_numbers = [
                    seg.Seat or None for seg in pax.SegmentAdditionalInfo
                ]
            passengers_info.append(
                ConfirmPassengerInfo(
                    title=pax.Title,
                    first_name=pax.FirstName,
                    last_name=pax.LastName,
                    pax_type=pax.PaxType,
                    ticket_number=pax.Ticket.TicketNumber if pax.Ticket else None,
                    email=pax.Email,
                    contact_no=pax.ContactNo,
                    seat_numbers=seat_numbers,
                )
            )

        # Build segment baggage/meal info from first passenger's SegmentAdditionalInfo
        segment_baggage = []
        first_pax = itinerary.Passenger[0] if itinerary.Passenger else None
        if first_pax and first_pax.SegmentAdditionalInfo:
            for seg_info in first_pax.SegmentAdditionalInfo:
                segment_baggage.append(
                    SegmentBaggageInfo(
                        fare_basis=seg_info.FareBasis,
                        baggage=seg_info.Baggage,
                        cabin_baggage=seg_info.CabinBaggage,
                        meal=seg_info.Meal or None,
                    )
                )

        # Build fare breakdown — shared with Non-LCC path via build_fare_breakdown.
        fare_breakdown = build_fare_breakdown(itinerary.Fare)

        # Build mini fare rules
        mini_fare_rules = []
        if itinerary.MiniFareRules:
            for rule_list in itinerary.MiniFareRules:
                if isinstance(rule_list, list):
                    for rule in rule_list:
                        if isinstance(rule, dict):
                            mini_fare_rules.append(
                                MiniFareRuleInfo(
                                    journey_points=rule.get("JourneyPoints", ""),
                                    type=rule.get("Type", ""),
                                    details=rule.get("Details"),
                                )
                            )
                elif isinstance(rule_list, dict):
                    mini_fare_rules.append(
                        MiniFareRuleInfo(
                            journey_points=rule_list.get("JourneyPoints", ""),
                            type=rule_list.get("Type", ""),
                            details=rule_list.get("Details"),
                        )
                    )

        return BookingConfirmResponse(
            pnr=inner.PNR,
            booking_id=inner.BookingId,
            is_lcc=is_lcc,
            ticket_status=inner.TicketStatus,
            ssr_denied=inner.SSRDenied,
            ssr_message=inner.SSRMessage,
            invoice_no=itinerary.InvoiceNo,
            invoice_amount=itinerary.InvoiceAmount,
            is_price_changed=inner.IsPriceChanged,
            is_time_changed=inner.IsTimeChanged,
            passengers=passengers_info or None,
            segment_baggage=segment_baggage or None,
            fare_breakdown=fare_breakdown,
            mini_fare_rules=mini_fare_rules or None,
        )

    # ------------------------------------------------------------------
    # SEARCH TRANSFORMERS
    # ------------------------------------------------------------------

    async def trasform_search_request(
        self, request: FlightSearchRequest
    ) -> TBOSearchRequest:
        segments = []
        segments.append(
            SearchSegment(
                Origin=request.origin,
                Destination=request.destination,
                FlightCabinClass=FlightCabinClass[request.cabin_class.upper()],
                PreferredDepartureTime=datetime.combine(
                    request.departure_date, datetime.min.time()
                ),
                PreferredArrivalTime=None,
            )
        )
        if request.trip_type == "roundtrip" and request.return_date:
            segments.append(
                SearchSegment(
                    Origin=request.destination,
                    Destination=request.origin,
                    FlightCabinClass=FlightCabinClass[request.cabin_class.upper()],
                    PreferredDepartureTime=datetime.combine(
                        request.return_date, datetime.min.time()
                    ),
                    PreferredArrivalTime=None,
                )
            )
        return TBOSearchRequest(
            EndUserIp="0.0.0.0",
            TokenId="",
            AdultCount=request.adults,
            ChildCount=request.children,
            InfantCount=request.infants,
            DirectFlight=request.direct_only,
            OneStopFlight=False,
            JourneyType=(
                JourneyType.RETURN
                if request.trip_type == "roundtrip"
                else JourneyType.ONEWAY
            ),
            PreferredAirlines=None,
            Segments=segments,
            Sources=None,
        )

    async def transform_search_response(
        self,
        tbo_response: TBOSearchResponse,
        request: FlightSearchRequest,
        cache: FlightCache,
    ) -> FlightSearchResponse:
        response = tbo_response.Response
        trace_id = response.TraceId
        results = response.Results or []

        outbound_groups: list[FlightGroup] = []
        inbound_groups: list[FlightGroup] = []
        is_international_return: bool = False

        if request.trip_type == "oneway":
            outbound_groups = await self._group_flights(
                itineraries=results[0],
                trace_id=trace_id,
                cache=cache,
            )
        else:
            if len(results) == 2:
                outbound_groups = await self._group_flights(
                    itineraries=results[0],
                    trace_id=trace_id,
                    cache=cache,
                )
                inbound_groups = await self._group_flights(
                    itineraries=results[1],
                    trace_id=trace_id,
                    cache=cache,
                )
            else:
                is_international_return = True
                outbound_groups = await self._group_flights(
                    itineraries=results[0],
                    trace_id=trace_id,
                    cache=cache,
                )

        all_groups = outbound_groups + inbound_groups

        return FlightSearchResponse(
            search_id=secrets.token_urlsafe(12),
            trip_type=request.trip_type,
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            passengers={
                "adults": request.adults,
                "children": request.children,
                "infants": request.infants,
            },
            cabin_class=request.cabin_class,
            outbound_flights=outbound_groups,
            inbound_flights=inbound_groups,
            is_international_return=is_international_return,
            available_airlines=self._get_all_airlines(all_groups),
            price_range=self._get_price_range(all_groups),
            stops_available=sorted({g.no_of_stops for g in all_groups}),
        )

    def _get_price_range(self, groups: list[FlightGroup]) -> dict:
        if not groups:
            return {"min": 0, "max": 0}
        min_price = float("inf")
        max_price = float("-inf")
        found_any = False
        for group in groups:
            if group.fares:
                found_any = True
                min_price = min(min_price, float(group.fares[0].total_price))
                max_price = max(max_price, float(group.fares[-1].total_price))
        if not found_any:
            return {"min": 0, "max": 0}
        return {"min": min_price, "max": max_price}

    def _get_all_airlines(self, groups: list[FlightGroup]) -> list[str]:
        return list(
            {
                segment.carrier.name
                for group in groups
                for fare in group.fares
                for segment_list in fare.segments
                for segment in segment_list
            }
        )

    async def _group_flights(
        self,
        itineraries: list[Itinerary],
        trace_id: str,
        cache: FlightCache,
    ) -> list[FlightGroup]:
        flight_groups: dict[str, list[Itinerary]] = {}
        for itinerary in itineraries:
            group_id = self._build_group_id(itinerary)
            if group_id not in flight_groups:
                flight_groups[group_id] = []
            flight_groups[group_id].append(itinerary)

        result: list[FlightGroup] = []

        for group_id, group_of_itineraries in flight_groups.items():
            # _build_fare_options is now async because cache.set is async
            fares = [
                await self._build_fare_options(itin, trace_id, cache)
                for itin in group_of_itineraries
            ]
            fares.sort(key=lambda f: f.total_price)

            first_itin = group_of_itineraries[0]
            first_seg = first_itin.Segments[0][0]
            last_seg = first_itin.Segments[0][-1]

            no_of_stops = len(first_itin.Segments[0]) - 1
            if no_of_stops > 0:
                stop_airports = [
                    seg.Destination.Airport.AirportCode
                    for seg in first_itin.Segments[0][:-1]
                ]
                total_duration = last_seg.AccumulatedDuration or 0
            else:
                stop_airports = []
                total_duration = first_seg.Duration

            result.append(
                FlightGroup(
                    group_id=group_id,
                    total_duration_minutes=total_duration,
                    no_of_stops=no_of_stops,
                    stop_airports=stop_airports,
                    departure_time=first_seg.Origin.DepTime,
                    arrival_time=last_seg.Destination.ArrTime,
                    origin=first_seg.Origin.Airport.AirportCode,
                    destination=last_seg.Destination.Airport.AirportCode,
                    fares=fares,
                    lowest_price=fares[0].total_price,
                    currency=fares[0].currency,
                )
            )

        result.sort(key=lambda g: g.lowest_price)
        return result

    async def _build_fare_options(
        self,
        itinerary: Itinerary,
        trace_id: str,
        cache: FlightCache,
    ) -> FareOption:
        fare = itinerary.Fare
        segments = self._build_segments(itinerary.Segments)

        outbound_segments = itinerary.Segments[0]
        inbound_segments = itinerary.Segments[1] if len(itinerary.Segments) > 1 else []

        fare_type = None
        for seg in outbound_segments:
            if seg.SupplierFareClass:
                fare_type = seg.SupplierFareClass
                break
        if inbound_segments:
            for seg in inbound_segments:
                if seg.SupplierFareClass:
                    if fare_type is not None:
                        fare_type = fare_type + "|" + seg.SupplierFareClass
                    else:
                        fare_type = seg.SupplierFareClass
                    break
        if fare_type is None:
            fare_type = "Saver"

        fare_id = secrets.token_urlsafe(16)
        provider_ref = {
            "TraceId": trace_id,
            "ResultIndex": itinerary.ResultIndex,
            "IsLCC": itinerary.IsLCC,
            "provider": "tbo",
        }
        await cache.set(fare_id=fare_id, data=provider_ref, ttl=900)

        return FareOption(
            fare_id=fare_id,
            segments=segments,
            fare_type=fare_type,
            currency=fare.Currency,
            base_fare=float(str(fare.BaseFare)),
            taxes=float(str(fare.Tax)),
            total_price=float(str(fare.PublishedFare)),
            refundable=itinerary.IsRefundable,
            meal_included=itinerary.IsFreeMealAvailable or False,
            passport_required=itinerary.IsPassportRequiredAtTicket or False,
        )

    def _build_segments(
        self,
        tbo_nested_segments: list[list[Segment]],
    ) -> list[list[FlightSegment]]:
        all_flight_segments: list[list[FlightSegment]] = []
        for segment_list in tbo_nested_segments:
            flight_segments: list[FlightSegment] = []
            for seg in segment_list:
                flight_segments.append(
                    FlightSegment(
                        departure=Airport(
                            code=seg.Origin.Airport.AirportCode,
                            name=seg.Origin.Airport.AirportName,
                            city=seg.Origin.Airport.CityName,
                            country=seg.Origin.Airport.CountryName,
                            terminal=seg.Origin.Airport.Terminal or None,
                        ),
                        arrival=Airport(
                            code=seg.Destination.Airport.AirportCode,
                            name=seg.Destination.Airport.AirportName,
                            city=seg.Destination.Airport.CityName,
                            country=seg.Destination.Airport.CountryName,
                            terminal=seg.Destination.Airport.Terminal or None,
                        ),
                        departure_time=seg.Origin.DepTime,
                        arrival_time=seg.Destination.ArrTime,
                        carrier=Airline(
                            code=seg.Airline.AirlineCode,
                            name=seg.Airline.AirlineName or seg.Airline.AirlineCode,
                        ),
                        flight_number=seg.Airline.FlightNumber,
                        operating_carrier=seg.Airline.AirlineName
                        or seg.Airline.AirlineCode,
                        aircraft=seg.Craft or None,
                        duration_minutes=seg.Duration,
                        layover_minutes=seg.GroundTime,
                        checked_baggage=seg.Baggage,
                        cabin_baggage=seg.CabinBaggage,
                        cabin_class=CABIN_CLASS_MAP.get(seg.CabinClass, "economy"),
                        booking_class=seg.Airline.FareClass,
                        seats_available=seg.NoOfSeatAvailable,
                    )
                )
            all_flight_segments.append(flight_segments)
        return all_flight_segments

    def _build_group_id(self, itinerary: Itinerary) -> str:
        def seg_key(seg):
            return (
                f"{seg.Airline.AirlineCode}{seg.Airline.FlightNumber}_"
                f"{seg.Origin.Airport.AirportCode}-"
                f"{seg.Destination.Airport.AirportCode}_"
                f"{seg.Origin.DepTime}"
            )

        parts = []
        for leg in itinerary.Segments:
            for seg in leg:
                parts.append(seg_key(seg))
        composite_key = "|".join(parts)
        digest = hashlib.blake2s(
            composite_key.encode("utf-8"),
            digest_size=6,
        ).hexdigest()
        return f"ITI_{digest}"
