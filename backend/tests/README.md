# Flight Booking API - Test Suite

Phased approach to testing flight booking endpoints. Tests validate API contracts, not internal implementation.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r tests/requirements-test.txt
```

### 2. Start Server (Terminal 1)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Run Tests (Terminal 2)

```bash
cd backend
pytest tests/test_1_search.py -v -s
```

---

## Test Phases

### Phase 1: Search API (test_1_search.py)

**Status:** Ready to run

Tests the `/api/v1/flights/search` endpoint.

**Test Classes:**

1. **TestSearchValidation** - Input validation (7 tests)
    - Missing/invalid fields, past dates, passenger count validation
2. **TestSearchFunctionality** - Core functionality (5 tests)
    - Oneway search for different routes
    - Cache inspection (is_lcc flag verification)
    - LCC/Non-LCC distribution
    - Response consistency and uniqueness
3. **TestSearchPerformance** - Performance checks (2 tests)
    - Response time < 10s
    - Concurrent request handling

**Run:**

```bash
# All tests
pytest tests/test_1_search.py -v -s

# Specific test class
pytest tests/test_1_search.py::TestSearchValidation -v -s
pytest tests/test_1_search.py::TestSearchFunctionality -v -s
pytest tests/test_1_search.py::TestSearchPerformance -v -s
```

-   GDS data parity
-   IATA code compliance
-   Currency consistency
-   Special assistance requests
-   Baggage allowance clarity
-   Fare family differentiation

### 6. Data Integrity Tests (`TestDataIntegrity`)

-   Search results consistency across multiple calls
-   Fare ID uniqueness validation

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r tests/requirements-test.txt
```

### 2. Environment Setup

Ensure your `.env` file has test credentials:

```bash
# TBO API credentials
TBO_API_URL=https://api.tbo.com/
TBO_USERNAME=your_username
TBO_PASSWORD=your_password

# Database (if using test database)
DATABASE_URL=postgresql://user:pass@localhost/fareclubs_test
```

### 3. Start the API Server

```bash
# Terminal 1: Start backend server
cd backend
uvicorn app.main:app --reload --port 8000
```

## Running Tests

### Run All Tests

```bash
pytest tests/test_flight_flow.py -v -s
```

### Run Specific Test Categories

```bash
# Validation tests only
pytest tests/test_flight_flow.py::TestFlightSearchValidation -v -s

# LCC flow tests only
pytest tests/test_flight_flow.py::TestFlightBookingFlow::test_oneway_lcc_flow -v -s

# Non-LCC flow tests only
pytest tests/test_flight_flow.py::TestFlightBookingFlow::test_oneway_non_lcc_flow -v -s

# Performance tests only
pytest tests/test_flight_flow.py::TestPerformance -v -s

# Industry standard tests only
pytest tests/test_flight_flow.py::TestFlightDomainStandards -v -s
```

### Run Tests for Specific Route

```bash
# DEL to BOM only
pytest tests/test_flight_flow.py -k "BOM" -v -s

# DEL to MAA only
pytest tests/test_flight_flow.py -k "MAA" -v -s
```

### Run with Coverage

```bash
pytest tests/test_flight_flow.py --cov=app --cov-report=html --cov-report=term
```

### Run in Parallel

```bash
pytest tests/test_flight_flow.py -n auto
```

## Test Output

The tests include detailed output with:

-   ⏱️ Response time for each API call
-   ✅ Success indicators
-   ❌ Validation error details
-   📌 Selected flight information
-   ℹ️ Information messages for skipped/conceptual tests

Example output:

```
================================================================================
🧪 Testing LCC Flow: Delhi to Mumbai
================================================================================

⏱️  Step 1: Search Flights (DEL → BOM): 2.345s (2345ms)
✅ Search successful - Found 45 flights
📌 Selected LCC Flight: IndiGo - ₹4500

⏱️  Step 2: Fare Rules: 0.856s (856ms)
✅ Fare Rules retrieved - 5 rules

⏱️  Step 3: Fare Quote: 1.234s (1234ms)
✅ Price unchanged - ₹4500

⏱️  Step 4: SSR Details (LCC): 1.567s (1567ms)
✅ LCC SSR retrieved - 12 meal options, 3 baggage options
   Sample meal: Veg Sandwich - ₹400

================================================================================
✅ LCC Flow Complete: Delhi to Mumbai
================================================================================
```

## Key Validation Points

### LCC vs Non-LCC Differences

**LCC (Low Cost Carrier)**

-   SSR type: `"lcc"`
-   Meals: Priced options at segment level
-   Structure: `segments[0].meal_options[].price` (required)

**Non-LCC (Full Service)**

-   SSR type: `"non_lcc"`
-   Meals: Dietary preferences at journey level (free)
-   Structure: `meal_preferences[]` (no price field)

### Price Tolerance

-   Fare quote accepts price changes < ₹50
-   Price changes ≥ ₹50 trigger `is_price_changed: true`
-   Separate tolerance for outbound and inbound (roundtrip)

### Cache Handling

-   Invalid fare_id returns 410 Gone
-   Cache should be checked before all TBO API calls
-   fare-rules, fare-quote, and ssr all depend on cached data

## Industry Best Practices Covered

1. **Regulatory Compliance**: IATA code validation, PNR generation
2. **Transparency**: Fare breakup, cancellation policies, baggage rules
3. **User Safety**: Duplicate booking prevention, time limits
4. **Data Quality**: GDS parity, consistency checks
5. **Accessibility**: Special assistance handling
6. **Performance**: Response time SLAs, concurrent handling

## Troubleshooting

### Tests Skip with "No LCC/Non-LCC flights found"

-   TBO API may not return both carrier types for all routes
-   Try different routes or date ranges
-   Check TBO inventory availability

### 410 Gone Errors

-   Cache may have expired (default TTL)
-   Ensure sufficient time between search and subsequent calls
-   Check cache implementation in `get_flight_cache()`

### Timeout Errors

-   TBO API may be slow for certain routes
-   Increase timeout in pytest.ini
-   Check network connectivity to TBO API

## Future Enhancements

-   [ ] Mock TBO API responses for deterministic testing
-   [ ] Add roundtrip flow tests
-   [ ] Add international flight tests
-   [ ] Add load testing scenarios
-   [ ] Add security/authentication tests
-   [ ] Add database transaction rollback for booking tests
-   [ ] Add contract testing with TBO API schemas

## Notes

-   Tests require active internet connection to TBO API
-   Some tests may fail if TBO inventory is limited
-   Response times vary based on TBO API performance
-   Tests are designed to be idempotent (safe to run multiple times)
