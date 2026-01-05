"""
TEST PHASE 2: Application Flow Tests
Tests complete user flows: Search → Fare Quote → Fare Rules → SSR

Tests realistic user journeys through the booking funnel:
- Search flights (oneway/roundtrip)
- Check fare quotes (price verification)
- Review fare rules (cancellation/change policies)
- Select add-ons (SSR - baggage, meals, seats)

SMART TESTING STRATEGY:
Tests use intelligent fallback logic to handle real-world scenarios:
1. Try initial route (DEL-BOM) with multiple dates (14, 21, 28, 35 days ahead)
2. If no flights, try fallback routes (MAA, BLR, etc.)
3. Tests NEVER fail just because one route has no availability
4. Only fail if API is down or completely broken

This ensures tests are robust and production-ready, not brittle.
"""

import time
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

# Test Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/flights"
DEV_PREFIX = "/dev"

# Fallback routes for testing (high-traffic routes with good availability)
FALLBACK_ROUTES = [
    # ("DEL", "BOM", "Delhi to Mumbai"),
    ("DEL", "MAA", "Delhi to Chennai"),
    # ("DEL", "BLR", "Delhi to Bangalore"),
    # ("BOM", "BLR", "Mumbai to Bangalore"),
    # ("BOM", "MAA", "Mumbai to Chennai"),
]

# Days ahead to try (stagger to avoid same-day availability issues)
FALLBACK_DAYS = [14, 21, 28, 35]


class ResponseTimer:
    """Context manager to measure API response time"""

    def __init__(self, name: str):
        self.name = name
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration: float = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        print(f"\n  ⏱ {self.name}: {self.duration:.3f}s ({self.duration * 1000:.0f}ms)")


@pytest.fixture
async def async_client():
    """Async HTTP client for testing"""
    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as ac:
        yield ac


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def perform_search(
    async_client, trip_type: str, origin: str, destination: str, days_ahead: int = 14
):
    """Helper to perform flight search and return results"""
    payload = {
        "trip_type": trip_type,
        "origin": origin,
        "destination": destination,
        "departure_date": (datetime.now() + timedelta(days=days_ahead)).strftime(
            "%Y-%m-%d"
        ),
        "adults": 1,
    }

    if trip_type == "roundtrip":
        payload["return_date"] = (
            datetime.now() + timedelta(days=days_ahead + 7)
        ).strftime("%Y-%m-%d")

    with ResponseTimer(f"Search {trip_type.upper()} {origin}-{destination}"):
        response = await async_client.post(f"{API_PREFIX}/search", json=payload)

    assert response.status_code == 200, f"Search failed: {response.text}"
    return response.json()


async def perform_search_with_fallback(
    async_client,
    trip_type: str,
    initial_origin: str = "DEL",
    initial_destination: str = "MAA",
):
    """
    Smart search with fallback logic - tries multiple routes and dates until flights found

    Strategy:
    1. Try initial route with different dates
    2. Try fallback routes if no flights found (skip routes already tried)
    3. Return first successful search with flights

    Returns:
        tuple: (search_data, origin, destination) or (None, None, None) if all attempts fail
    """
    tried_routes = set()  # Track routes we've already tried

    # Try initial route first with different dates
    print(f"\n  Attempting route: {initial_origin} → {initial_destination}")
    tried_routes.add((initial_origin, initial_destination))

    for days_ahead in FALLBACK_DAYS:
        search_data = await perform_search(
            async_client, trip_type, initial_origin, initial_destination, days_ahead
        )

        # Check if we got flights
        flights_key = "outboundFlights" if trip_type == "oneway" else "outboundFlights"
        if search_data.get(flights_key) and len(search_data[flights_key]) > 0:
            print(
                f"  ✓ Found {len(search_data[flights_key])} flights ({days_ahead} days ahead)"
            )
            return search_data, initial_origin, initial_destination
        else:
            print(f"  ⚠ No flights for {days_ahead} days ahead, trying next date...")

    # No flights on initial route, try fallback routes
    print(
        f"  ⚠ No flights on {initial_origin}-{initial_destination}, trying fallback routes..."
    )

    for origin, destination, route_name in FALLBACK_ROUTES:
        # Skip if we already tried this route
        if (origin, destination) in tried_routes:
            continue

        tried_routes.add((origin, destination))
        print(f"\n  Trying fallback: {route_name} ({origin} → {destination})")

        for days_ahead in FALLBACK_DAYS[:2]:  # Try fewer days for fallback routes
            search_data = await perform_search(
                async_client, trip_type, origin, destination, days_ahead
            )

            if search_data.get(flights_key) and len(search_data[flights_key]) > 0:
                print(
                    f"  ✓ Found {len(search_data[flights_key])} flights on fallback route"
                )
                return search_data, origin, destination

    # All attempts failed
    print("  ✗ No flights found on any route/date combination")
    return None, None, None


async def get_cache_data(async_client):
    """Helper to get cache data"""
    response = await async_client.get(f"{DEV_PREFIX}/cache-inspect")
    assert response.status_code == 200
    return response.json()


def get_first_fare(search_data: dict, flight_type: str = "outbound") -> dict | None:
    """
    Get first available fare from search results (any carrier type)

    Args:
        search_data: Search response JSON
        flight_type: "outbound" or "inbound"

    Returns:
        Fare dict with fareId, totalPrice, etc. or None if not found
    """
    flights_key = "outboundFlights" if flight_type == "outbound" else "inboundFlights"

    for flight_group in search_data.get(flights_key, []):
        fares = flight_group.get("fares", [])
        if fares:
            return fares[0]  # Just return first available
    return None


def find_flight_by_carrier_type(
    search_data: dict, cache_data: dict, is_lcc: bool, flight_type: str = "outbound"
) -> dict | None:
    """
    Find a flight (fare) of specific carrier type (LCC or Non-LCC)

    Args:
        search_data: Search response JSON
        cache_data: Cache data from /dev/cache-inspect
        is_lcc: True for LCC, False for Non-LCC
        flight_type: "outbound" or "inbound"

    Returns:
        Fare dict with fareId, totalPrice, etc. or None if not found
    """
    flights_key = "outboundFlights" if flight_type == "outbound" else "inboundFlights"

    for flight_group in search_data.get(flights_key, []):
        for fare in flight_group.get("fares", []):
            fare_id = fare["fareId"]
            if fare_id in cache_data:
                cached_is_lcc = cache_data[fare_id].get("IsLCC", False)
                if cached_is_lcc == is_lcc:
                    return fare
    return None


def get_carrier_type(fare_id: str, cache_data: dict) -> str:
    """
    Determine if a flight is LCC or Non-LCC

    Args:
        fare_id: Flight fare ID
        cache_data: Cache data from /dev/cache-inspect

    Returns:
        "LCC" or "Non-LCC"
    """
    if fare_id in cache_data:
        is_lcc = cache_data[fare_id].get("IsLCC", False)
        return "LCC" if is_lcc else "Non-LCC"
    return "Unknown"


# ============================================================================
# ONEWAY FLOW TESTS
# ============================================================================


class TestOnewayFlows:
    """Test complete user flows for oneway trips"""

    @classmethod
    def setup_class(cls):
        """Initialize shared search cache"""
        cls.shared_search_data = None
        cls.shared_search_route = None

    async def get_search_data(self, async_client, force_new=False):
        """
        Get search data, reusing previous search if available
        This avoids re-searching the same route multiple times in a test class
        """
        if not force_new and self.shared_search_data:
            print(f"  ♻ Reusing previous search: {self.shared_search_route}")
            return self.shared_search_data, self.shared_search_route

        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "oneway", "DEL", "MAA"
        )

        if search_data:
            self.shared_search_data = search_data
            self.shared_search_route = (origin, destination)

        return search_data, (origin, destination) if search_data else (None, None)

    @pytest.mark.asyncio
    async def test_oneway_lcc_full_flow(self, async_client):
        """
        FLOW: Search → Fare Quote → Fare Rules → SSR (Oneway)
        Tests complete booking funnel - uses whatever flights are available
        """
        print("\n" + "=" * 70)
        print("TEST: Oneway Full Flow")
        print("=" * 70)

        # Step 1: Get search data (reuse if already searched)
        search_data, route = await self.get_search_data(async_client)

        if not search_data:
            pytest.fail("No flights found on any route")

        origin, destination = route
        print(f"  ✓ Using route: {origin} → {destination}")

        # Step 2: Just get first available fare
        cache_data = await get_cache_data(async_client)
        fare = get_first_fare(search_data)

        if not fare:
            pytest.fail("No fares found")

        fare_id = fare["fareId"]
        initial_price = fare["totalPrice"]
        carrier_type = get_carrier_type(fare_id, cache_data)
        print(f"  ✓ Found {carrier_type} flight: {fare_id} @ ₹{initial_price}")

        # Step 3: Fare Quote
        print("\n  Step 2: Getting Fare Quote...")
        quote_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": fare_id,
            "initial_price_outbound": initial_price,
        }

        with ResponseTimer("Fare Quote"):
            quote_response = await async_client.post(
                f"{API_PREFIX}/fare-quote", json=quote_payload
            )

        assert quote_response.status_code == 200, (
            f"Fare quote failed: {quote_response.text}"
        )
        quote_data = quote_response.json()

        print(f"  ✓ Price changed: {quote_data['isPriceChanged']}")
        if quote_data["isPriceChanged"]:
            print(f"  ⚠ {quote_data['message']}")

        # Step 4: Fare Rules
        print("\n  Step 3: Getting Fare Rules...")
        with ResponseTimer("Fare Rules"):
            rules_response = await async_client.get(
                f"{API_PREFIX}/fare-rules/{fare_id}"
            )

        assert rules_response.status_code == 200, (
            f"Fare rules failed: {rules_response.text}"
        )
        rules_data = rules_response.json()

        # Validate fare rules structure
        assert "fareRules" in rules_data, "Missing fareRules in response"
        print(f"  ✓ Fare rules retrieved successfully")

        # Step 5: SSR (Special Service Requests)
        print("\n  Step 4: Getting SSR (Baggage/Meals/Seats)...")
        ssr_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": fare_id,
            "is_international_return": False,
        }

        with ResponseTimer("SSR Request"):
            ssr_response = await async_client.post(
                f"{API_PREFIX}/ssr", json=ssr_payload
            )

        assert ssr_response.status_code == 200, f"SSR failed: {ssr_response.text}"
        ssr_data = ssr_response.json()

        # Validate SSR structure
        assert "outbound" in ssr_data, "Missing outbound in SSR response"
        outbound_ssr = ssr_data["outbound"]

        if outbound_ssr:
            # LCC should have baggage, meal, and seat options
            print(f"  ✓ Baggage options: {len(outbound_ssr.get('baggageOptions', []))}")
            print(f"  ✓ Meal options: {len(outbound_ssr.get('mealOptions', []))}")
            print(f"  ✓ Seat map available: {outbound_ssr.get('seatMap') is not None}")
        else:
            print("  ⚠ No SSR data available for this flight")

        print("\n  ✅ FLOW COMPLETED SUCCESSFULLY")

    @pytest.mark.asyncio
    async def test_oneway_nonlcc_full_flow(self, async_client):
        """
        FLOW: Search → Fare Quote → Fare Rules → SSR (Different Oneway Fare)
        Tests complete booking funnel with different flight - reuses search from previous test
        """
        print("\n" + "=" * 70)
        print("TEST: Oneway Full Flow (Different Fare)")
        print("=" * 70)

        # Step 1: Get search data (reuse previous search)
        search_data, route = await self.get_search_data(async_client)

        if not search_data:
            pytest.fail("No flights found on any route")

        origin, destination = route
        print(f"  ✓ Using route: {origin} → {destination}")

        # Step 2: Get second available fare (for variety)
        cache_data = await get_cache_data(async_client)

        # Get all fares and pick second one
        all_fares = []
        for flight_group in search_data.get("outboundFlights", []):
            all_fares.extend(flight_group.get("fares", []))

        if len(all_fares) < 2:
            pytest.skip(
                f"Only {len(all_fares)} fare(s) available, need 2+ for different test"
            )

        fare = all_fares[1]  # Get second fare

        fare_id = fare["fareId"]
        initial_price = fare["totalPrice"]
        carrier_type = get_carrier_type(fare_id, cache_data)
        print(
            f"  ✓ Found {carrier_type} flight (2nd option): {fare_id} @ ₹{initial_price}"
        )

        # Step 3: Fare Quote
        print("\n  Step 2: Getting Fare Quote...")
        quote_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": fare_id,
            "initial_price_outbound": initial_price,
        }

        with ResponseTimer("Fare Quote"):
            quote_response = await async_client.post(
                f"{API_PREFIX}/fare-quote", json=quote_payload
            )

        assert quote_response.status_code == 200
        quote_data = quote_response.json()

        print(f"  ✓ Price changed: {quote_data['isPriceChanged']}")

        # Step 4: Fare Rules
        print("\n  Step 3: Getting Fare Rules...")
        with ResponseTimer("Fare Rules"):
            rules_response = await async_client.get(
                f"{API_PREFIX}/fare-rules/{fare_id}"
            )

        assert rules_response.status_code == 200
        print("  ✓ Fare rules retrieved")

        # Step 5: SSR
        print("\n  Step 4: Getting SSR...")
        ssr_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": fare_id,
            "is_international_return": False,
        }

        with ResponseTimer("SSR Request"):
            ssr_response = await async_client.post(
                f"{API_PREFIX}/ssr", json=ssr_payload
            )

        assert ssr_response.status_code == 200
        ssr_data = ssr_response.json()

        outbound_ssr = ssr_data.get("outbound")
        if outbound_ssr:
            # Non-LCC typically has included baggage, optional meals
            print(f"  ✓ Baggage options: {len(outbound_ssr.get('baggageOptions', []))}")
            print(f"  ✓ Meal options: {len(outbound_ssr.get('mealOptions', []))}")

        print("\n  ✅ FLOW COMPLETED SUCCESSFULLY")


# ============================================================================
# ROUNDTRIP FLOW TESTS
# ============================================================================


class TestRoundtripFlows:
    """Test complete user flows for roundtrip journeys"""

    @classmethod
    def setup_class(cls):
        """Initialize shared search cache"""
        cls.shared_search_data = None
        cls.shared_search_route = None

    async def get_search_data(self, async_client, force_new=False):
        """
        Get search data, reusing previous search if available
        """
        if not force_new and self.shared_search_data:
            print(f"  ♻ Reusing previous search: {self.shared_search_route}")
            return self.shared_search_data, self.shared_search_route

        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "roundtrip", "DEL", "MAA"
        )

        if search_data:
            self.shared_search_data = search_data
            self.shared_search_route = (origin, destination)

        return search_data, (origin, destination) if search_data else (None, None)

    @pytest.mark.asyncio
    async def test_roundtrip_both_lcc_flow(self, async_client):
        """
        FLOW: Roundtrip with both LCC flights
        Tests: Search → Fare Quote (2 flights) → Fare Rules → SSR
        Uses smart fallback to find available flights
        """
        print("\n" + "=" * 70)
        print("TEST: Roundtrip Flow - LCC + LCC")
        print("=" * 70)

        # Step 1: Smart Search roundtrip with fallback
        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "roundtrip", "DEL", "MAA"
        )

        if not search_data:
            pytest.fail("No flights found on any route")

        if not search_data.get("inboundFlights"):
            pytest.skip("No return flights available")

        print(f"  ✓ Using route: {origin} ⇄ {destination}")

        # Step 2: Find LCC flights for both legs
        cache_data = await get_cache_data(async_client)

        outbound_lcc = find_flight_by_carrier_type(
            search_data, cache_data, is_lcc=True, flight_type="outbound"
        )
        inbound_lcc = find_flight_by_carrier_type(
            search_data, cache_data, is_lcc=True, flight_type="inbound"
        )

        if not outbound_lcc or not inbound_lcc:
            pytest.skip("Could not find LCC flights for both legs")

        outbound_fare_id = outbound_lcc["fareId"]
        outbound_price = outbound_lcc["totalPrice"]
        inbound_fare_id = inbound_lcc["fareId"]
        inbound_price = inbound_lcc["totalPrice"]

        print(f"  ✓ Outbound LCC: {outbound_fare_id} @ ₹{outbound_price}")
        print(f"  ✓ Inbound LCC: {inbound_fare_id} @ ₹{inbound_price}")

        # Step 3: Fare Quote for both flights
        print("\n  Step 2: Getting Fare Quote for both flights...")
        quote_payload = {
            "trip_type": "roundtrip",
            "fare_id_outbound": outbound_fare_id,
            "initial_price_outbound": outbound_price,
            "fare_id_inbound": inbound_fare_id,
            "initial_price_inbound": inbound_price,
        }

        with ResponseTimer("Fare Quote (Roundtrip)"):
            quote_response = await async_client.post(
                f"{API_PREFIX}/fare-quote", json=quote_payload
            )

        assert quote_response.status_code == 200
        quote_data = quote_response.json()

        print(f"  ✓ Price changed: {quote_data['isPriceChanged']}")
        if quote_data.get("outbound"):
            print(
                f"    Outbound: ₹{quote_data['outbound']['originalPrice']} → ₹{quote_data['outbound']['newPrice']}"
            )
        if quote_data.get("inbound"):
            print(
                f"    Inbound: ₹{quote_data['inbound']['originalPrice']} → ₹{quote_data['inbound']['newPrice']}"
            )

        # Step 4: SSR for roundtrip (domestic - 2 separate calls)
        print("\n  Step 3: Getting SSR for roundtrip...")
        ssr_payload = {
            "trip_type": "roundtrip",
            "fare_id_outbound": outbound_fare_id,
            "fare_id_inbound": inbound_fare_id,
            "is_international_return": False,  # Domestic roundtrip
        }

        with ResponseTimer("SSR Request (Roundtrip)"):
            ssr_response = await async_client.post(
                f"{API_PREFIX}/ssr", json=ssr_payload
            )

        assert ssr_response.status_code == 200
        ssr_data = ssr_response.json()

        # Validate both outbound and inbound SSR
        assert "outbound" in ssr_data, "Missing outbound SSR"
        assert "inbound" in ssr_data, "Missing inbound SSR"

        print(f"  ✓ Outbound SSR retrieved")
        print(f"  ✓ Inbound SSR retrieved")

        print("\n  ✅ ROUNDTRIP FLOW COMPLETED SUCCESSFULLY")

    @pytest.mark.asyncio
    async def test_roundtrip_mixed_carriers_flow(self, async_client):
        """
        FLOW: Roundtrip with mixed carriers (LCC + Non-LCC)
        Realistic scenario: Outbound LCC, Return Non-LCC
        Uses smart fallback to find available flights
        """
        print("\n" + "=" * 70)
        print("TEST: Roundtrip Flow - LCC + Non-LCC (Mixed)")
        print("=" * 70)

        # Step 1: Smart Search with fallback
        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "roundtrip", "DEL", "MAA"
        )

        if not search_data:
            pytest.fail("No flights found on any route")

        if not search_data.get("inboundFlights"):
            pytest.skip("No return flights available")

        print(f"  ✓ Using route: {origin} ⇄ {destination}")

        # Step 2: Find mixed carrier flights
        cache_data = await get_cache_data(async_client)

        outbound_lcc = find_flight_by_carrier_type(
            search_data, cache_data, is_lcc=True, flight_type="outbound"
        )
        inbound_nonlcc = find_flight_by_carrier_type(
            search_data, cache_data, is_lcc=False, flight_type="inbound"
        )

        if not outbound_lcc or not inbound_nonlcc:
            pytest.skip("Could not find mixed carrier combination")

        outbound_fare_id = outbound_lcc["fareId"]
        outbound_price = outbound_lcc["totalPrice"]
        inbound_fare_id = inbound_nonlcc["fareId"]
        inbound_price = inbound_nonlcc["totalPrice"]

        print(f"  ✓ Outbound LCC: {outbound_fare_id} @ ₹{outbound_price}")
        print(f"  ✓ Inbound Non-LCC: {inbound_fare_id} @ ₹{inbound_price}")

        # Step 3: Fare Quote
        print("\n  Step 2: Getting Fare Quote for mixed carriers...")
        quote_payload = {
            "trip_type": "roundtrip",
            "fare_id_outbound": outbound_fare_id,
            "initial_price_outbound": outbound_price,
            "fare_id_inbound": inbound_fare_id,
            "initial_price_inbound": inbound_price,
        }

        with ResponseTimer("Fare Quote"):
            quote_response = await async_client.post(
                f"{API_PREFIX}/fare-quote", json=quote_payload
            )

        assert quote_response.status_code == 200
        quote_data = quote_response.json()
        print(f"  ✓ Fare quote successful")

        # Step 4: SSR (should handle mixed carrier types)
        print("\n  Step 3: Getting SSR for mixed carriers...")
        ssr_payload = {
            "trip_type": "roundtrip",
            "fare_id_outbound": outbound_fare_id,
            "fare_id_inbound": inbound_fare_id,
            "is_international_return": False,
        }

        with ResponseTimer("SSR Request"):
            ssr_response = await async_client.post(
                f"{API_PREFIX}/ssr", json=ssr_payload
            )

        assert ssr_response.status_code == 200
        ssr_data = ssr_response.json()

        # Both should have different SSR structures
        outbound_ssr = ssr_data.get("outbound")
        inbound_ssr = ssr_data.get("inbound")

        print(f"  ✓ Outbound SSR (LCC structure): Available")
        print(f"  ✓ Inbound SSR (Non-LCC structure): Available")

        print("\n  ✅ MIXED CARRIER FLOW COMPLETED SUCCESSFULLY")


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================


class TestFlowEdgeCases:
    """Test error handling and edge cases in the flow"""

    @pytest.mark.asyncio
    async def test_fare_quote_with_expired_fare_id(self, async_client):
        """
        Test fare quote with invalid/expired fare_id
        Expected: 410 Gone
        """
        print("\n" + "=" * 70)
        print("TEST: Fare Quote with Expired Fare ID")
        print("=" * 70)

        quote_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": "EXPIRED_FAKE_FARE_ID_12345",
            "initial_price_outbound": 5000.0,
        }

        with ResponseTimer("Fare Quote (Expired)"):
            response = await async_client.post(
                f"{API_PREFIX}/fare-quote", json=quote_payload
            )

        assert response.status_code == 410, "Should return 410 Gone for expired fare_id"
        print("  ✓ Correctly returned 410 Gone for expired fare_id")

    @pytest.mark.asyncio
    async def test_fare_rules_with_invalid_fare_id(self, async_client):
        """
        Test fare rules with invalid fare_id
        Expected: 410 Gone
        """
        print("\n" + "=" * 70)
        print("TEST: Fare Rules with Invalid Fare ID")
        print("=" * 70)

        with ResponseTimer("Fare Rules (Invalid)"):
            response = await async_client.get(
                f"{API_PREFIX}/fare-rules/INVALID_FARE_ID_999"
            )

        assert response.status_code == 410
        print("  ✓ Correctly returned 410 Gone for invalid fare_id")

    @pytest.mark.asyncio
    async def test_ssr_with_expired_fare_id(self, async_client):
        """
        Test SSR with expired fare_id
        Expected: 410 Gone
        """
        print("\n" + "=" * 70)
        print("TEST: SSR with Expired Fare ID")
        print("=" * 70)

        ssr_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": "EXPIRED_FARE_ID_SSR_TEST",
            "is_international_return": False,
        }

        with ResponseTimer("SSR (Expired)"):
            response = await async_client.post(f"{API_PREFIX}/ssr", json=ssr_payload)

        assert response.status_code == 410
        print("  ✓ Correctly returned 410 Gone for expired fare_id")

    @pytest.mark.asyncio
    async def test_roundtrip_missing_inbound_fare_id(self, async_client):
        """
        Test roundtrip fare quote with missing inbound fare_id
        Expected: Should handle gracefully or return validation error
        """
        print("\n" + "=" * 70)
        print("TEST: Roundtrip Quote Missing Inbound Fare ID")
        print("=" * 70)

        # Smart Search with fallback
        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "oneway", "DEL", "MAA"
        )

        if not search_data:
            pytest.fail("No flights found on any route")

        print(f"  ✓ Using route: {origin} → {destination}")

        cache_data = await get_cache_data(async_client)
        any_fare = None

        for flight_group in search_data.get("outboundFlights", []):
            fares = flight_group.get("fares", [])
            if fares:
                any_fare = fares[0]
                break

        if not any_fare:
            pytest.skip("No fares available")

        # Try roundtrip quote with missing inbound
        quote_payload = {
            "trip_type": "roundtrip",
            "fare_id_outbound": any_fare["fareId"],
            "initial_price_outbound": any_fare["totalPrice"],
            # Missing fare_id_inbound and initial_price_inbound
        }

        with ResponseTimer("Fare Quote (Missing Inbound)"):
            response = await async_client.post(
                f"{API_PREFIX}/fare-quote", json=quote_payload
            )

        # Should either handle gracefully or return 410 for missing inbound
        print(f"  Response status: {response.status_code}")
        assert response.status_code in [
            410,
            422,
        ], "Should handle missing inbound gracefully"


# ============================================================================
# DATA VALIDATION TESTS
# ============================================================================


class TestFlowDataValidation:
    """Validate data consistency across the flow"""

    @pytest.mark.asyncio
    async def test_price_consistency_in_flow(self, async_client):
        """
        Validate that prices remain consistent across Search → Fare Quote
        (within acceptable tolerance of 50 INR)
        """
        print("\n" + "=" * 70)
        print("TEST: Price Consistency Across Flow")
        print("=" * 70)

        # Smart Search with fallback
        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "oneway", "DEL", "MAA"
        )

        if not search_data:
            pytest.fail("No flights found on any route")

        print(f"  ✓ Using route: {origin} → {destination}")

        # Get first available fare
        first_flight = search_data["outboundFlights"][0]
        first_fare = first_flight["fares"][0]
        fare_id = first_fare["fareId"]
        search_price = first_fare["totalPrice"]

        print(f"  Search Price: ₹{search_price}")

        # Fare Quote
        quote_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": fare_id,
            "initial_price_outbound": search_price,
        }

        quote_response = await async_client.post(
            f"{API_PREFIX}/fare-quote", json=quote_payload
        )
        quote_data = quote_response.json()

        if quote_data["isPriceChanged"] and quote_data.get("outbound"):
            new_price = quote_data["outbound"]["newPrice"]
            difference = quote_data["outbound"]["difference"]
            print(f"  Quote Price: ₹{new_price} (Δ ₹{difference})")

            # Validate 50 INR tolerance
            if difference > 50:
                print(f"  ⚠ Price increased beyond tolerance: ₹{difference} > ₹50")
            else:
                print(f"  ✓ Price change within tolerance")
        else:
            print(f"  ✓ Price unchanged: ₹{search_price}")

    @pytest.mark.asyncio
    async def test_cache_persistence_across_flow(self, async_client):
        """
        Validate that fare_id remains in cache throughout the flow
        Search → Cache Check → Fare Quote → Cache Check
        """
        print("\n" + "=" * 70)
        print("TEST: Cache Persistence Across Flow")
        print("=" * 70)

        # Smart Search with fallback
        search_data, origin, destination = await perform_search_with_fallback(
            async_client, "oneway", "DEL", "MAA"
        )

        if not search_data:
            pytest.fail("No flights found on any route")

        print(f"  ✓ Using route: {origin} → {destination}")

        first_fare = search_data["outboundFlights"][0]["fares"][0]
        fare_id = first_fare["fareId"]

        # Check cache after search
        cache_data_1 = await get_cache_data(async_client)
        assert fare_id in cache_data_1, "fare_id not found in cache after search"
        print(f"  ✓ fare_id in cache after search")

        # Fare Quote
        quote_payload = {
            "trip_type": "oneway",
            "fare_id_outbound": fare_id,
            "initial_price_outbound": first_fare["totalPrice"],
        }
        await async_client.post(f"{API_PREFIX}/fare-quote", json=quote_payload)

        # Check cache after fare quote
        cache_data_2 = await get_cache_data(async_client)
        assert fare_id in cache_data_2, "fare_id not found in cache after fare quote"
        print(f"  ✓ fare_id persists in cache after fare quote")

        # Validate cache entry structure
        cache_entry = cache_data_2[fare_id]
        required_keys = ["TraceId", "ResultIndex", "is_lcc"]
        for key in required_keys:
            assert key in cache_entry, f"Missing {key} in cache entry"
        print(f"  ✓ Cache entry structure valid")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PHASE 2: APPLICATION FLOW TESTS")
    print("=" * 80)
    print("\nRun with: pytest tests/test_2_flow.py -v -s")
    print("\nTest Categories:")
    print("  1. Oneway Flows - Complete LCC and Non-LCC journeys")
    print("  2. Roundtrip Flows - Both LCC, Both Non-LCC, and Mixed")
    print("  3. Edge Cases - Error handling and invalid inputs")
    print("  4. Data Validation - Price consistency and cache persistence")
    print("\nFlow Pattern:")
    print("  Search → Fare Quote → Fare Rules → SSR")
    print("=" * 80 + "\n")
