import hashlib
import uuid
from datetime import datetime
from typing import Optional, cast

from app.clients.exceptions import ExternalProviderError
from app.schemas.internal.booking import (
    BookingConfirmRequest,
    BookingConfirmResponse,
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
    BaggageSelection,
    BookPassenger,
    MealSelection,
    PassengerFare,
    SeatDynamicSelection,
    TBOBookRequest,
)
from app.schemas.tbo.common import (
    Baggage,
    Meal,
    Seat,
    SeatDynamic,
    SimpleMeal,
)
from app.schemas.tbo.enums import BaggageDescriptionEnum, FlightCabinClass, JourneyType
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
from app.utils.cache import FlightCache

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
                                    seat.AvailablityType, "available"
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

        # BAGGAGE
        for b in baggage_options or []:
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
                    for_full_journey=b.WayType == 2,
                )
            )

        # MEAL
        meal_prefs = [
            MealPreference(code=m.Code, description=m.Description)
            for m in meal_options or []
        ]

        return NonLccSsrView(
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
                                    seat.AvailablityType, "available"
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

        # BAGGAGE
        for b in baggage_options or []:
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
                    for_full_journey=b.WayType == 2,
                )
            )

        # MEAL
        for m in meal_options or []:
            if m.Code == "NoMeal":
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
                    for_full_journey=m.WayType == 2,
                )
            )

        return LccSsrView(segments=list(segment_map.values()))

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
    # BOOKING TRANSFORMERS
    # ------------------------------------------------------------------

    def transform_book_request(
        self,
        request: BookingConfirmRequest,
        cached_data: dict,
        end_user_ip: str,
        raw_ssr: Optional[TBOSSRResponse] = None,
    ) -> TBOBookRequest:
        """Build TBO Book request for Non-LCC flights."""
        free_ssr = self._find_free_ssr(raw_ssr)

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

            fare = PassengerFare(
                Currency=p.fare.currency,
                BaseFare=p.fare.base_fare,
                Tax=p.fare.tax,
                YQTax=p.fare.yq_tax or 0,
                AdditionalTxnFeeOfrd=p.fare.additional_txn_fee_ofrd or 0,
                AdditionalTxnFeePub=p.fare.additional_txn_fee_pub or 0,
                PGCharge=p.fare.pg_charge or 0,
                OtherCharges=p.fare.other_charges,
            )

            meal = None
            seat_pref = None
            baggage = None
            if p.ssr:
                if p.ssr.meal_code:
                    meal = MealSelection(Code=p.ssr.meal_code, Description=2)
                if p.ssr.seat_code:
                    seat_pref = SeatDynamicSelection(
                        Code=p.ssr.seat_code, Description=2
                    )
                if p.ssr.baggage_code:
                    baggage = BaggageSelection(Code=p.ssr.baggage_code, Description=2)

            # Auto-assign free SSR if user didn't select
            if not meal and free_ssr["free_meal_code"]:
                meal = MealSelection(Code=free_ssr["free_meal_code"], Description=1)
            if p.pax_type != 3:  # not infant
                if not baggage and free_ssr["free_baggage"]:
                    baggage = BaggageSelection(
                        Code=free_ssr["free_baggage"].Code,
                        Description=1,
                    )

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
                    SeatDynamic=seat_pref,
                    Baggage=baggage,
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
    ) -> TBOTicketLCCRequest:
        """Build TBO Ticket request for LCC flights."""
        free_ssr = self._find_free_ssr(raw_ssr)

        # Build lookup maps from cached SSR
        baggage_map: dict[str, Baggage] = {}
        meal_map: dict[str, Meal] = {}
        seat_map: dict[str, Seat] = {}
        free_meals_by_segment: list[Meal] = []
        no_seat_list: list[Seat] = []

        if raw_ssr and raw_ssr.Response:
            if raw_ssr.Response.Baggage:
                for seg_options in raw_ssr.Response.Baggage:
                    for b in seg_options or []:
                        baggage_map[b.Code] = b

            if raw_ssr.Response.SeatDynamic:
                for sd in raw_ssr.Response.SeatDynamic:
                    if sd.SegmentSeat:
                        for seg in sd.SegmentSeat:
                            reference_seat: Seat | None = None
                            if seg.RowSeats:
                                for row in seg.RowSeats:
                                    for seat in row.Seats:
                                        if reference_seat is None:
                                            reference_seat = seat
                                        if seat.Code and seat.Code != "NoSeat":
                                            seat_map[seat.Code] = seat
                            if reference_seat:
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

            if raw_ssr.Response.MealDynamic:
                for seg_options in raw_ssr.Response.MealDynamic:
                    for m in seg_options or []:
                        if m.Code == "NoMeal":
                            continue
                        meal_map[m.Code] = m
                    free_meal = next(
                        (meal for meal in (seg_options or []) if meal.Price == 0 and meal.Code != "NoMeal"),
                        None,
                    )
                    if free_meal:
                        free_meals_by_segment.append(free_meal)

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

            fare = PassengerFareSmall(
                BaseFare=p.fare.base_fare,
                Tax=p.fare.tax,
                YQTax=p.fare.yq_tax or 0,
                AdditionalTxnFeeOfrd=p.fare.additional_txn_fee_ofrd or 0,
                AdditionalTxnFeePub=p.fare.additional_txn_fee_pub or 0,
                PGCharge=p.fare.pg_charge or 0,
            )

            baggage_list: list[Baggage] | None = None
            meal_list: list[Meal] | None = None

            if p.ssr:
                if p.ssr.baggage_code and p.ssr.baggage_code in baggage_map:
                    baggage_list = [baggage_map[p.ssr.baggage_code]]
                if p.ssr.meal_code and p.ssr.meal_code in meal_map:
                    meal_list = [meal_map[p.ssr.meal_code]]

            # Auto-assign free SSR if user didn't select
            if not meal_list and free_meals_by_segment:
                meal_list = list(free_meals_by_segment)
            elif not meal_list and free_ssr["free_meal_lcc"]:
                meal_list = [free_ssr["free_meal_lcc"]]
            if p.pax_type != 3:  # not infant
                if not baggage_list and free_ssr["free_baggage"]:
                    baggage_list = [free_ssr["free_baggage"]]

            seat_dynamic: list[Seat] | None = None
            if p.pax_type != 3:
                if (
                    not force_no_seat_selection
                    and p.ssr
                    and p.ssr.seat_code
                    and p.ssr.seat_code in seat_map
                ):
                    seat_dynamic = [seat_map[p.ssr.seat_code]]
                elif no_seat_list:
                    seat_dynamic = list(no_seat_list)

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
                    Baggage=baggage_list,
                    MealDynamic=meal_list,
                    SeatDynamic=seat_dynamic,
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
            search_id=uuid.uuid4().hex[:8],
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

        fare_id = uuid.uuid4().hex[:4]
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
                            name=seg.Airline.AirlineName,
                        ),
                        flight_number=seg.Airline.FlightNumber,
                        operating_carrier=seg.Airline.AirlineName,
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
