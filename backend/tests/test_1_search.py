"""
TEST PHASE 1: Search API Tests
Tests only the flight search endpoint with validation and basic functionality
"""

import time
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

# Test Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/flights"
DEV_PREFIX = "/dev"


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
        print(
            f"\nTimer {self.name}: {self.duration:.3f}s ({self.duration * 1000:.0f}ms)"
        )


@pytest.fixture
async def async_client():
    """Async HTTP client for testing"""
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        yield ac


# ============================================================================
# SEARCH VALIDATION TESTS
# ============================================================================


class TestSearchValidation:
    """Test input validation for flight search"""

    @pytest.mark.asyncio
    async def test_missing_trip_type(self, async_client):
        """Test search with missing trip_type field"""
        payload = {
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_trip_type(self, async_client):
        """Test search with invalid trip_type value"""
        payload = {
            "trip_type": "invalid_type",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_past_departure_date(self, async_client):
        """Test search with past departure date"""
        payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_zero_adults(self, async_client):
        """Test search with 0 adults"""
        payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 0,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_same_origin_destination(self, async_client):
        """Test search with same origin and destination"""
        payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "DEL",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_roundtrip_missing_return_date(self, async_client):
        """Test roundtrip search without return_date"""
        payload = {
            "trip_type": "roundtrip",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_return_date_before_departure(self, async_client):
        """Test roundtrip with return_date before departure_date"""
        payload = {
            "trip_type": "roundtrip",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=10)).strftime(
                "%Y-%m-%d"
            ),
            "return_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        assert response.status_code == 422


# ============================================================================
# SEARCH FUNCTIONALITY TESTS
# ============================================================================


class TestSearchFunctionality:
    """Test search API functionality and response structure"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "origin,destination,route_name",
        [
            ("DEL", "BOM", "Delhi to Mumbai"),
            # ("DEL", "MAA", "Delhi to Chennai"),
            # ("DEL", "BLR", "Delhi to Bangalore"),
        ],
    )
    async def test_oneway_search(self, async_client, origin, destination, route_name):
        """Test oneway flight search"""
        payload = {
            "trip_type": "oneway",
            "origin": origin,
            "destination": destination,
            "departure_date": (datetime.now() + timedelta(days=14)).strftime(
                "%Y-%m-%d"
            ),
            "adults": 1,
            "children": 0,
            "infants": 0,
        }

        with ResponseTimer(f"Search: {origin} -> {destination}") as timer:
            response = await async_client.post(f"{API_PREFIX}/search", json=payload)

        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()

        # Validate response structure (camelCase from InternalBaseSchema)
        assert "searchId" in data, "Missing 'searchId' in response"
        assert "tripType" in data, "Missing 'tripType' in response"
        assert "outboundFlights" in data, "Missing 'outboundFlights' in response"
        assert isinstance(data["outboundFlights"], list), (
            "'outboundFlights' should be a list"
        )

        print(
            f"Found {len(data['outboundFlights'])} outbound flight groups for {route_name}"
        )

        if data["outboundFlights"]:
            flight_group = data["outboundFlights"][0]

            # Validate flight group structure
            assert "groupId" in flight_group, "Missing 'groupId'"
            assert "fares" in flight_group, "Missing 'fares' array"
            assert isinstance(flight_group["fares"], list), "'fares' should be a list"

            if flight_group["fares"]:
                fare = flight_group["fares"][0]
                # Validate fare structure
                assert "fareId" in fare, "Missing 'fareId'"
                assert "totalPrice" in fare, "Missing 'totalPrice'"
                assert "segments" in fare, "Missing 'segments'"

        # Performance logging (no failure, just info)
        if timer.duration < 30:
            print(f"✓ Good performance: {timer.duration:.2f}s")
        else:
            print(
                f"\033[91m⚠ Slow response: {timer.duration:.2f}s (expected < 30s)\033[0m"
            )

    @pytest.mark.asyncio
    async def test_cache_inspection_after_search(self, async_client):
        """Test cache contains is_lcc flag after search"""
        search_payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=14)).strftime(
                "%Y-%m-%d"
            ),
            "adults": 1,
        }

        with ResponseTimer("Search") as timer:
            search_response = await async_client.post(
                f"{API_PREFIX}/search", json=search_payload
            )

        assert search_response.status_code == 200
        search_data = search_response.json()

        if not search_data["outboundFlights"]:
            pytest.skip("No flights found to test cache")

        # Get first fare_id from first flight group's fares array
        first_flight_group = search_data["outboundFlights"][0]
        if not first_flight_group.get("fares"):
            pytest.skip("No fares found in first flight group")

        fare_id = first_flight_group["fares"][0]["fareId"]

        # Inspect cache
        with ResponseTimer("Cache Inspect") as timer:
            cache_response = await async_client.get(f"{DEV_PREFIX}/cache-inspect")

        assert cache_response.status_code == 200, (
            f"Cache inspect failed: {cache_response.text}"
        )
        cache_data = cache_response.json()

        print(f"Cache has {len(cache_data)} entries")

        # Check if our fare_id exists in cache
        if fare_id in cache_data:
            cached_entry = cache_data[fare_id]
            print(
                f"Cache entry for {fare_id}: TraceId={cached_entry.get('TraceId')}, is_lcc={cached_entry.get('is_lcc')}"
            )

            # Validate cache structure
            assert "TraceId" in cached_entry, "Missing 'TraceId' in cache"
            assert "ResultIndex" in cached_entry, "Missing 'ResultIndex' in cache"
            assert "is_lcc" in cached_entry, "Missing 'is_lcc' flag in cache"
            assert isinstance(cached_entry["is_lcc"], bool), (
                "'is_lcc' should be boolean"
            )

            print("Cache structure validated")
        else:
            pytest.fail(f"fare_id {fare_id} not found in cache")

    @pytest.mark.asyncio
    async def test_fare_id_uniqueness(self, async_client):
        """Test that all fare_ids in search results are unique"""
        payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        response = await async_client.post(f"{API_PREFIX}/search", json=payload)
        data = response.json()

        # Extract all fareIds from all flight groups and their fares
        fare_ids = []
        for flight_group in data.get("outboundFlights", []):
            for fare in flight_group.get("fares", []):
                fare_ids.append(fare["fareId"])

        unique_fare_ids = set(fare_ids)

        print(f"Total fare_ids: {len(fare_ids)}, Unique: {len(unique_fare_ids)}")

        assert len(fare_ids) == len(unique_fare_ids), "Duplicate fare_ids found!"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestSearchPerformance:
    """Test search API performance"""

    @pytest.mark.asyncio
    async def test_search_response_time(self, async_client):
        """Test search response time and log performance metrics"""
        payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        with ResponseTimer("Search Performance") as timer:
            response = await async_client.post(f"{API_PREFIX}/search", json=payload)

        assert response.status_code == 200

        # Performance benchmarks (log only, no failure)
        if timer.duration < 10:
            print(f"✓ Excellent performance: {timer.duration:.2f}s")
        elif timer.duration < 30:
            print(f"✓ Good performance: {timer.duration:.2f}s")
        else:
            # Log in red but don't fail - slower responses are acceptable
            print(
                f"\033[91m⚠ Slow response: {timer.duration:.2f}s (expected < 30s)\033[0m"
            )

    @pytest.mark.asyncio
    async def test_concurrent_searches(self, async_client):
        """Test handling of concurrent search requests"""
        payload = {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
        }

        import asyncio

        with ResponseTimer("3 Concurrent Searches") as timer:
            tasks = [
                async_client.post(f"{API_PREFIX}/search", json=payload)
                for _ in range(3)
            ]
            responses = await asyncio.gather(*tasks)

        success_count = sum(1 for r in responses if r.status_code == 200)
        avg_time = timer.duration / 3

        print(
            f"Successful: {success_count}/3, Average time: {avg_time:.2f}s per request"
        )

        # Performance logging for concurrent requests
        if avg_time < 30:
            print("✓ Good concurrent performance")
        else:
            print(f"\033[91m⚠ Slow concurrent response: {avg_time:.2f}s avg\033[0m")

        assert success_count == 3, f"Only {success_count}/3 requests succeeded"


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PHASE 1: SEARCH API TESTS")
    print("=" * 80)
    print("\nRun with: pytest tests/test_1_search.py -v -s")
    print("\nTest Categories:")
    print("  1. Search Validation - Input validation tests")
    print("  2. Search Functionality - Response structure and cache tests")
    print("  3. Search Performance - Response time and concurrency")
    print("=" * 80 + "\n")
