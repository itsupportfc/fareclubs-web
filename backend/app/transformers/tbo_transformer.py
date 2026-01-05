import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from re import L
from typing import Optional, cast

from app.schemas import tbo
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
from app.schemas.tbo.book import TBOBookRequest
from app.schemas.tbo.common import (
    Baggage,
    Meal,
    Seat,
    SeatDynamic,
    SegmentSeatModel,
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
from app.utils.cache import FlightCache

# MAPPINGS
CABIN_CLASS_MAP: dict[int, CabinClass] = {
    FlightCabinClass.ECONOMY: "economy",
    FlightCabinClass.PREMIUM_ECONOMY: "premium_economy",
    FlightCabinClass.BUSINESS: "business",
    FlightCabinClass.FIRST: "first",
    FlightCabinClass.ALL: "economy",  # default to economy
    FlightCabinClass.UNKNOWN: "economy",  # default to economy
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
    # Window types
    1: "window",  # Window
    4: "window",  # WindowRecline
    5: "window",  # WindowWing
    6: "window",  # WindowExitRow
    7: "window",  # WindowReclineWing
    8: "window",  # WindowReclineExitRow
    9: "window",  # WindowWingExitRow
    22: "window",  # WindowReclineWingExitRow
    25: "window",  # WindowBulkhead
    26: "window",  # WindowQuiet
    27: "window",  # WindowBulkheadQuiet
    42: "window",  # WindowBulkheadWing
    43: "window",  # WindowBulkheadExitRow
    # Aisle types
    2: "aisle",  # Aisle
    10: "aisle",  # AisleRecline
    11: "aisle",  # AisleWing
    12: "aisle",  # AisleExitRow
    13: "aisle",  # AisleReclineWing
    14: "aisle",  # AisleReclineExitRow
    15: "aisle",  # AisleWingExitRow
    23: "aisle",  # AisleReclineWingExitRow
    31: "aisle",  # AisleBulkhead
    32: "aisle",  # AisleQuiet
    33: "aisle",  # AisleBulkheadQuiet
    46: "aisle",  # AisleBulkheadWing
    47: "aisle",  # AisleBulkheadExitRow
    # Middle types
    3: "middle",  # Middle
    16: "middle",  # MiddleRecline
    17: "middle",  # MiddleWing
    18: "middle",  # MiddleExitRow
    19: "middle",  # MiddleReclineWing
    20: "middle",  # MiddleReclineExitRow
    21: "middle",  # MiddleWingExitRow
    24: "middle",  # MiddleReclineWingExitRow
    28: "middle",  # MiddleBulkhead
    29: "middle",  # MiddleQuiet
    30: "middle",  # MiddleBulkheadQuiet
    44: "middle",  # MiddleBulkheadWing
    45: "middle",  # MiddleBulkheadExitRow
    # Centre types (map to middle)
    34: "middle",  # CentreAisle
    35: "middle",  # CentreMiddle
    36: "middle",  # CentreAisleBulkhead
    37: "middle",  # CentreAisleQuiet
    38: "middle",  # CentreAisleBulkheadQuiet
    39: "middle",  # CentreMiddleBulkhead
    40: "middle",  # CentreMiddleQuiet
    41: "middle",  # CentreMiddleBulkheadQuiet
    # NotSet and any unknowns
    0: "middle",  # NotSet
}


class TBOTransformer:
    """
    Transform TBO API responses to internal schemas.

    Usage:
        transformer = TBOTransformer()
        response = await transformer.transform_search_response(tbo_response, request)
    """

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

                # use sample seat to identify which segment this map belongs to
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
                    destination=b.Destination,  # ERROR: baggage may have destination as final destination ratehr then the segment destination. => first assign seats
                )

            segment_map[key].baggage_options.append(
                BaggageOptions(
                    code=b.Code,
                    # description=b.Description.name,
                    weight=b.Weight,
                    price=b.Price,
                    # is_included=b.Description == 1,
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
        """Transform TBOSSRResponse of a single leg to internal SsrResponse."""
        segment_map: dict[str, LccSegmentSsrView] = {}

        # SEAT
        if seat_options and seat_options.SegmentSeat:
            for segment in seat_options.SegmentSeat:
                if not segment.RowSeats:
                    continue

                # use sample seat to identify which segment this map belongs to
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
                    destination=b.Destination,  # ERROR: baggage may have destination as final destination ratehr then the segment destination. => first assign seats
                )

            segment_map[key].baggage_options.append(
                BaggageOptions(
                    code=b.Code,
                    # description=b.Description.name,
                    weight=b.Weight,
                    price=b.Price,
                    # is_included=b.Description == 1,
                    for_full_journey=b.WayType == 2,
                )
            )

        # MEAL
        for m in meal_options or []:
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
                    description=m.AirlineDescription,
                    price=m.Price,
                    # is_included=m.Description == 1,
                    for_full_journey=b.WayType == 2,
                )
            )

        return LccSsrView(segments=list(segment_map.values()))

    # def transform_fare_quote_response(
    #     self,
    #     tbo_response: TBOFareQuoteResponse,
    #     trace_id: str,
    #     cache: FlightCache,
    #     price_increase: float,
    # ) -> FareQuoteResponse:
    #     """Transform TBOFareQuoteResponse to internal FareQuoteResponse."""
    #     new_fare_option = self._build_fare_options(
    #         itinerary=tbo_response.Response.Results,
    #         trace_id=trace_id,
    #         cache=cache,
    #     )
    #     return FareQuoteResponse(
    #         is_price_changed=True,
    #         price_increase=price_increase,
    #         new_fare_option=new_fare_option,
    #     )

    def transform_fare_rule_response(
        self, tbo_response: TBOFareRuleResponse
    ) -> FareRulesResponse:
        """Transform TBOFareRuleResponse to internal FareRulesResponse."""
        tbo_fare_rules = tbo_response.Response.FareRules or []

        internal_fare_rules = [
            FareRule(
                airline=rule.Airline,
                # departure_time=rule.DepartureTime,
                destination=rule.Destination,
                fare_basis_code=rule.FareBasisCode,
                fare_inclusions=rule.FareInclusions,
                fare_restriction=rule.FareRestriction,
                fare_rule_detail=rule.FareRuleDetail,
                flight_id=rule.FlightId,
                origin=rule.Origin,
                # return_date=rule.ReturnDate,
            )
            for rule in tbo_fare_rules
        ]

        return FareRulesResponse(fare_rules=internal_fare_rules)

    async def trasform_search_request(
        self, request: FlightSearchRequest
    ) -> TBOSearchRequest:
        """Transform internal FlightSearchRequest to TBOSearchRequest."""
        segments = []
        # Outbound segment
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
        # Return segment (for roundtrip)
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
        tbo_request = TBOSearchRequest(
            EndUserIp="0.0.0.0",  # placeholder, should be set properly
            TokenId="",  # client will set
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
        return tbo_request

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

        if not results:
            # do what?
            pass

        if request.trip_type == "oneway":
            outbound_groups = await self._group_flights(
                itineraries=results[0],
                trace_id=trace_id,
                cache=cache,
            )
        else:
            # roundtrip => domestic : 2 arrays, international = 1 array (linked)
            # Results [[],[]] => domestic return
            # Results [[]] => international return
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
                # here => Segments [ [ {del-bom} , {bom-dxb} ] , [{dxb-del}] ]

                # error => segments me incoming segment not included
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
            # total_results=len(all_groups), # needed?
            # results_valid_until=datetime.now(timezone.utc) + timedelta(minutes=14),
            available_airlines=self._get_all_airlines(all_groups),
            price_range=self._get_price_range(all_groups),
            stops_available=sorted({g.no_of_stops for g in all_groups}),
        )

    # no need to use async await for in-memory operations on a list
    # RULE OF THUMB
    #   1. use async for I/O bound operations (DB, network, file), not CPU bound operations
    #   2. If there's no await inside the function body, don't make it async
    def _get_price_range(self, groups: list[FlightGroup]) -> dict:
        """Get min and max price from all fare options in all flight groups."""
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
        """Collect unique airlines from all segments in all fares."""
        # {} creates a set in python
        return list(
            {
                segment.carrier.name
                for group in groups
                for fare in group.fares
                for segment_list in fare.segments
                for segment in segment_list
            }
        )

        # airlines_list: set[str] = set()
        # for group in groups:
        #     for fare in group.fares:
        #         for one_way_segment_list in fare.segments:
        #             for segment in one_way_segment_list:
        #                 name = segment.carrier.name
        #                 airlines_list.add(name)
        # return list(airlines_list)

    async def _group_flights(
        self,
        itineraries: list[Itinerary],
        trace_id: str,
        cache: FlightCache,
    ) -> list[FlightGroup]:
        """Group same flights with different fare types together"""
        # ditionary of flight groups
        flight_groups: dict[str, list[Itinerary]] = {}

        # collect all flights with same group_id together
        for itinerary in itineraries:
            group_id = self._build_group_id(itinerary)
            if group_id not in flight_groups:
                flight_groups[group_id] = []
            flight_groups[group_id].append(itinerary)

        result: list[FlightGroup] = []

        # now construct 1 FlightGroup for each group => different list[FareOption]
        for group_id, group_of_itineraries in flight_groups.items():
            # build fare options , each itineary in group is a fare option
            fares = [
                self._build_fare_options(itin, trace_id, cache)
                for itin in group_of_itineraries
            ]

            # sort fares by price ( cheapest first )
            fares.sort(key=lambda f: f.total_price)

            # all the fare options will have same itineraries except things like baggage, fareclass etc
            first_itin = group_of_itineraries[0]
            first_seg = first_itin.Segments[0][0]
            last_seg = first_itin.Segments[0][-1]

            no_of_stops = len(first_itin.Segments[0]) - 1
            if no_of_stops > 0:
                # iterate over segments except last one and get the destination airport codes
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

    def _build_fare_options(
        self,
        itinerary: Itinerary,
        trace_id: str,
        # direction: Direction,
        cache: FlightCache,
    ) -> FareOption:
        """Itinerary( basically one result element with ResultIndex) -> FareOption"""
        fare = itinerary.Fare

        # tranform segments

        # HERE => passing just his first array itineray.Segments == [[],[]]
        segments = self._build_segments(itinerary.Segments)
        # segments = self._build_segments(itinerary.Segments[0])

        # # get fare type from the first segment's SupplierFareCLass
        # # as Segments: list[list[Segment]]
        # if itinerary.Segments[0] and itinerary.Segments[0][0].SupplierFareClass:
        #     fare_type = itinerary.Segments[0][0].SupplierFareClass
        # else:
        #     fare_type = None

        # fare_type = itinerary.ResultFareType

        outbound_segments = itinerary.Segments[0]
        inbound_segments = itinerary.Segments[1] if len(itinerary.Segments) > 1 else []

        # take SupplierFareClass from 1st flight of outbound segments
        fare_type = None
        for seg in outbound_segments:
            if seg.SupplierFareClass:
                fare_type = seg.SupplierFareClass
                break

        # append SupplierFareClass from 1st flight of inbound segments(if present)
        if inbound_segments:
            for seg in inbound_segments:
                if seg.SupplierFareClass:
                    if fare_type is not None:
                        fare_type = fare_type + "|" + seg.SupplierFareClass
                    else:
                        fare_type = seg.SupplierFareClass
                    break

        # De-duplication ?
        # if null => fare_type = Saver
        if fare_type is None:
            fare_type = "Saver"

        # cache
        fare_id = uuid.uuid4().hex[:4]
        provider_ref = {
            "TraceId": trace_id,
            "ResultIndex": itinerary.ResultIndex,
            # "Source": itinerary.Source, # needed?
            "IsLCC": itinerary.IsLCC,
            "provider": "tbo",
        }
        cache.set(fare_id=fare_id, data=provider_ref, ttl=900)

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
            # is_lcc=itinerary.IsLCC,
            passport_required=itinerary.IsPassportRequiredAtTicket or False,
        )

        # get fare per passenger --

    def _build_segments(
        self,
        tbo_nested_segments: list[list[Segment]],
        # direction: Direction,
    ) -> list[list[FlightSegment]]:
        """Build internal segments from TBO segments."""
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
        # deterministic hasing, same input => same output
        digest = hashlib.blake2s(
            composite_key.encode("utf-8"),
            digest_size=6,  # 48-bit hash
        ).hexdigest()

        return f"ITI_{digest}"
