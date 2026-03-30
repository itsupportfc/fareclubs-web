# Code Review Fixes — Complete Implementation Guide

Every fix below is **copy-paste ready**. Files are in alphabetical order within each phase. For each change: **what** to change, **why**, and exact **before → after** code.

---

## Table of Contents

- [Phase 1: Fix Critical Bugs (P0)](#phase-1-fix-critical-bugs-p0)
- [Phase 2: Security & Auth Fixes (P1)](#phase-2-security--auth-fixes-p1)
- [Phase 3: Consolidate Duplicated Code](#phase-3-consolidate-duplicated-code)
- [Phase 4: Form Validation](#phase-4-form-validation)
- [Phase 5: Production Readiness](#phase-5-production-readiness)
- [Phase 6: React Best Practices Polish](#phase-6-react-best-practices-polish)

---

## Phase 1: Fix Critical Bugs (P0)

### 1A. Fix Rules of Hooks Violation — `FlightPriceCard.jsx`

**Problem:** `useMemo` and `useFlightStore` hooks are called AFTER an early `return null` on line 34. React requires all hooks to be called unconditionally, in the same order, every render. This will crash in development mode.

**File:** `src/components/search/FlightPriceCard.jsx`

**BEFORE (lines 28–80):**
```jsx
/* ---------- COMPONENT ---------- */
export default function FlightPriceCard({ flight, onViewFares = () => {} }) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("FLIGHT");
  const [fetchedFareId, setFetchedFareId] = useState(null);

  if (!flight || !flight.fares?.length) return null;

  /* ---------- LOWEST FARE ---------- */
  const lowestFare = useMemo(
    () =>
      flight.fares.reduce(
        (min, f) => (f.totalPrice < min.totalPrice ? f : min),
        flight.fares[0]
      ),
    [flight.fares]
  );

  const fareId = lowestFare.FareId;
  const segments = lowestFare.segments?.flat() || [];
  if (!segments.length) return null;

  const firstSeg = segments[0];
  const lastSeg = segments[segments.length - 1];
  const airlineName = firstSeg.carrier.name;
  const airlineCode = firstSeg.carrier.code;

  const flightNumbers = segments
    .map((s) => `${s.carrier.code}-${s.flightNumber}`)
    .join(", ");

  const stopsCount = segments.length - 1;
  const stopsText =
    stopsCount === 0
      ? "Non-stop"
      : `${stopsCount} stop${stopsCount > 1 ? "s" : ""}`;

  const layovers = segments.slice(0, -1).map((seg, idx) => {
    const nextSeg = segments[idx + 1];
    return {
      airport: seg.destination,
      duration: formatDuration(
        diffMinutes(seg.arrivalTime, nextSeg.departureTime)
      ),
    };
  });

  /* ---------- STORE HOOKS ---------- */
  const getFareRules = useFlightStore((s) => s.getFareRules);
  const getFareQuote = useFlightStore((s) => s.getFareQuote);
  const fareData = useFlightStore((s) => s.fareData);
  const isFareLoading = useFlightStore((s) => s.isFareLoading);
  const fareError = useFlightStore((s) => s.fareError);

  const setSelectedFlight = useFlightStore((s) => s.setSelectedFlight);
```

**AFTER:**
```jsx
/* ---------- COMPONENT ---------- */
export default function FlightPriceCard({ flight, onViewFares = () => {} }) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("FLIGHT");
  const [fetchedFareId, setFetchedFareId] = useState(null);

  /* ---------- STORE HOOKS (must be above any early return) ---------- */
  const getFareRules = useFlightStore((s) => s.getFareRules);
  const getFareQuote = useFlightStore((s) => s.getFareQuote);
  const fareData = useFlightStore((s) => s.fareData);
  const isFareLoading = useFlightStore((s) => s.isFareLoading);
  const fareError = useFlightStore((s) => s.fareError);
  const setSelectedFlight = useFlightStore((s) => s.setSelectedFlight);

  /* ---------- LOWEST FARE ---------- */
  const lowestFare = useMemo(
    () =>
      flight?.fares?.length
        ? flight.fares.reduce(
            (min, f) => (f.totalPrice < min.totalPrice ? f : min),
            flight.fares[0]
          )
        : null,
    [flight?.fares]
  );

  if (!flight || !lowestFare) return null;

  const fareId = lowestFare.FareId;
  const segments = lowestFare.segments?.flat() || [];
  if (!segments.length) return null;

  const firstSeg = segments[0];
  const lastSeg = segments[segments.length - 1];
  const airlineName = firstSeg.carrier.name;
  const airlineCode = firstSeg.carrier.code;

  const flightNumbers = segments
    .map((s) => `${s.carrier.code}-${s.flightNumber}`)
    .join(", ");

  const stopsCount = segments.length - 1;
  const stopsText =
    stopsCount === 0
      ? "Non-stop"
      : `${stopsCount} stop${stopsCount > 1 ? "s" : ""}`;

  const layovers = segments.slice(0, -1).map((seg, idx) => {
    const nextSeg = segments[idx + 1];
    return {
      airport: seg.destination,
      duration: formatDuration(
        diffMinutes(seg.arrivalTime, nextSeg.departureTime)
      ),
    };
  });
```

**Key changes:**
1. All `useFlightStore` selectors and `useMemo` moved ABOVE the early return
2. `useMemo` now handles the `null` case internally (returns `null` if no fares)
3. Guard moved below hooks: `if (!flight || !lowestFare) return null`

---

### 1A (cont). Fix Rules of Hooks Violation — `FareModal.jsx`

**Problem:** `useNavigate()` is called on line 16, AFTER `if (!flight) return null` on line 14.

**File:** `src/components/search/FareModal.jsx`

**BEFORE (lines 9–23):**
```jsx
export default function FareModal({
  flight,
  passengers = { adults: 1, children: 0, infants: 0 },
  onClose,
}) {
  if (!flight) return null;

  const navigate = useNavigate();
  const [loadingFareId, setLoadingFareId] = useState(null);
  const [priceChange, setPriceChange] = useState(null);
  const [timeChanged, setTimeChanged] = useState(null);

  const actualFlight = flight.flight || flight;
  const fares = actualFlight?.fares || flight?.fares || [];
  if (!fares.length) return null;
```

**AFTER:**
```jsx
export default function FareModal({
  flight,
  passengers = { adults: 1, children: 0, infants: 0 },
  onClose,
}) {
  const navigate = useNavigate();
  const [loadingFareId, setLoadingFareId] = useState(null);
  const [priceChange, setPriceChange] = useState(null);
  const [timeChanged, setTimeChanged] = useState(null);

  if (!flight) return null;

  const actualFlight = flight.flight || flight;
  const fares = actualFlight?.fares || flight?.fares || [];
  if (!fares.length) return null;
```

**Key change:** Move `useNavigate()` and all `useState` calls ABOVE the `if (!flight) return null` guard.

---

### 1B. Fix `setCache` ReferenceError — `FlightResultsPage.jsx`

**Problem:** `handleViewFares` calls `setCache(...)` on line 30, but `setCache` was never destructured from the store. This throws a `ReferenceError` every time a user clicks "VIEW FARES".

**File:** `src/pages/FlightResultsPage.jsx`

**BEFORE (lines 13–31):**
```jsx
  const {
    outboundFlights,
    origin,
    destination,
    adults,
    children,
    infants,
    isLoading,
  } = useFlightStore();

  const passengers = { adults, children, infants };

  const [selectedFlight, setSelectedFlight] = useState(null);

  const handleViewFares = (flight) => {
    setSelectedFlight(flight);
    setCache("selectedFlight", flight);
  };
```

**AFTER:**
```jsx
  const {
    outboundFlights,
    origin,
    destination,
    adults,
    children,
    infants,
    isLoading,
    setCache,
  } = useFlightStore();

  const passengers = { adults, children, infants };

  const [selectedFlight, setSelectedFlight] = useState(null);

  const handleViewFares = (flight) => {
    setSelectedFlight(flight);
    setCache("selectedFlight", flight);
  };
```

**Key change:** Add `setCache` to the destructured store values.

---

### 1C. Fix Sidebar Store Mismatch — `Sidebar.jsx`

**Problem:** Line 15 destructures `searchResults`, `filters`, and `setFilters` from the store, but none of these exist in `useFlightStore`. This means:
- Filters don't work at all (clicking checkboxes does nothing)
- The airline list is hardcoded instead of derived from search results

**Recommended approach:** Add `filters` state and `setFilters` action to the store, and derive airlines from actual results.

#### Step 1: Add to `useFlightStore.js`

Add these lines inside the `create()` call (after the `travelClass` / `tripType` setters, around line 70):

```js
  // Filters
  filters: {},
  setFilters: (filters) => set({ filters }),
```

#### Step 2: Rewrite `Sidebar.jsx`

**BEFORE (full file):**
```jsx
import React, { useState, useMemo, useEffect } from "react";
import {
  Sunrise, Sun, Sunset, Moon, Clock,
  PlaneTakeoff, Filter, ArrowUp,
} from "lucide-react";
import useFlightStore from "../../store/useFlightStore";

const Sidebar = () => {
  const { searchResults, filters = {}, setFilters } = useFlightStore();
  const flights = searchResults?.Response?.Results?.[0] || [];
  const firstFlight = flights?.[0]?.Segments?.[0]?.[0];
  // ... rest of component with inline sub-components
```

**AFTER (full file):**
```jsx
import React, { useState, useMemo, useEffect } from "react";
import {
  Sunrise, Sun, Sunset, Moon, Clock,
  PlaneTakeoff, Filter, ArrowUp,
} from "lucide-react";
import useFlightStore from "../../store/useFlightStore";

/* ---- Sub-components defined OUTSIDE the parent (avoids re-creation each render) ---- */

function RouteInfoCard({ originCity, destCity, departureAirport, arrivalAirport }) {
  return (
    <div className="bg-white shadow-md p-4 rounded-xl space-y-1 border border-gray-100 hover:shadow-lg transition-all duration-200">
      <h3 className="font-display text-xl text-gray-900 flex items-center gap-2">
        <PlaneTakeoff size={20} className="text-orange-500" />
        {originCity} → {destCity}
      </h3>
      <p className="text-sm text-gray-600">
        Departure: <span className="font-medium">{departureAirport}</span>
      </p>
      <p className="text-sm text-gray-600">
        Arrival: <span className="font-medium">{arrivalAirport}</span>
      </p>
    </div>
  );
}

function FilterCard({ filters, setFilters }) {
  const handleCheckbox = (key) => setFilters({ ...filters, [key]: !filters[key] });
  return (
    <div className="bg-white shadow-md p-4 rounded-xl border border-gray-100 hover:shadow-lg transition-all duration-200">
      <h3 className="text-lg font-semibold mb-3 text-gray-900 flex items-center gap-2">
        <Filter size={18} className="text-orange-500" /> Popular Filters
      </h3>
      <div className="space-y-3 text-sm text-gray-700">
        <label className="flex items-center gap-2 cursor-pointer hover:text-orange-500 transition-colors duration-200">
          <input
            type="checkbox"
            checked={!!filters.nonStop}
            onChange={() => handleCheckbox("nonStop")}
            className="accent-orange-500"
          />
          Non Stop
        </label>
        <label className="flex items-center gap-2 cursor-pointer hover:text-orange-500 transition-colors duration-200">
          <input
            type="checkbox"
            checked={!!filters.oneStop}
            onChange={() => handleCheckbox("oneStop")}
            className="accent-orange-500"
          />
          1 Stop
        </label>
      </div>
    </div>
  );
}

function TimeSlotCard({ filters, setFilters }) {
  const timeSlots = [
    { label: "Early Morning", key: "earlyMorning", range: "00:00 - 08:00", icon: <Sunrise size={18} /> },
    { label: "Morning", key: "morning", range: "08:00 - 12:00", icon: <Sun size={18} /> },
    { label: "Afternoon", key: "afternoon", range: "12:00 - 18:00", icon: <Sunset size={18} /> },
    { label: "Evening", key: "evening", range: "18:00 - 24:00", icon: <Moon size={18} /> },
  ];

  const handleTimeSlotChange = (key) => {
    setFilters({
      ...filters,
      timeSlots: { ...filters.timeSlots, [key]: !filters.timeSlots?.[key] },
    });
  };

  return (
    <div className="bg-white shadow-md p-4 rounded-xl border border-gray-100 hover:shadow-lg transition-all duration-200">
      <h3 className="text-lg font-semibold mb-3 text-gray-900 flex items-center gap-2">
        <Clock size={18} className="text-orange-500" /> Departure Time
      </h3>
      <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 space-y-2">
        {timeSlots.map((slot) => (
          <label
            key={slot.key}
            className="flex items-center justify-between text-sm cursor-pointer hover:text-orange-600 transition-colors duration-200"
          >
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!filters.timeSlots?.[slot.key]}
                onChange={() => handleTimeSlotChange(slot.key)}
                className="accent-orange-500"
              />
              <span className="flex items-center gap-1 font-medium text-gray-800">
                {slot.icon} {slot.label}
              </span>
            </div>
            <span className="text-xs text-gray-500">{slot.range}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function AirlinesCard({ airlines, filters, setFilters }) {
  const handleCheckbox = (airline) => {
    const selected = filters.airlines || [];
    if (selected.includes(airline)) {
      setFilters({ ...filters, airlines: selected.filter((a) => a !== airline) });
    } else {
      setFilters({ ...filters, airlines: [...selected, airline] });
    }
  };

  return (
    <div className="bg-white shadow-md p-4 rounded-xl border border-gray-100 hover:shadow-lg transition-all duration-200">
      <h3 className="text-lg font-semibold mb-3 text-gray-900">Airlines</h3>
      <div className="space-y-2 text-sm text-gray-700">
        {airlines.map((airline) => (
          <label key={airline} className="flex items-center gap-2 cursor-pointer hover:text-orange-500 transition-colors duration-200">
            <input
              type="checkbox"
              checked={filters.airlines?.includes(airline) || false}
              onChange={() => handleCheckbox(airline)}
              className="accent-orange-500"
            />
            {airline}
          </label>
        ))}
      </div>
    </div>
  );
}

/* ---- Main Sidebar ---- */

const Sidebar = () => {
  const { outboundFlights, filters = {}, setFilters } = useFlightStore();

  // Derive airline names from actual search results
  const airlines = useMemo(() => {
    const names = new Set();
    (outboundFlights || []).forEach((flight) => {
      const seg = flight.fares?.[0]?.segments?.[0]?.[0]
        || flight.fares?.[0]?.segments?.flat()?.[0];
      if (seg?.carrier?.name) names.add(seg.carrier.name);
    });
    return [...names].sort();
  }, [outboundFlights]);

  // Derive route info from first flight
  const firstFlight = outboundFlights?.[0];
  const firstSeg = firstFlight?.fares?.[0]?.segments?.[0]?.[0]
    || firstFlight?.fares?.[0]?.segments?.flat()?.[0];
  const originCity = firstSeg?.departure?.city || firstFlight?.origin || "Origin";
  const destCity = firstSeg?.arrival?.city || firstFlight?.destination || "Destination";
  const departureAirport = firstSeg?.departure?.name || "";
  const arrivalAirport = firstSeg?.arrival?.name || "";

  // Scroll to Top Button
  const [showTop, setShowTop] = useState(false);
  useEffect(() => {
    const handleScroll = () => setShowTop(window.scrollY > 300);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <div className="relative">
        <aside className="hidden md:block col-span-1 space-y-4 sticky top-5">
          <RouteInfoCard
            originCity={originCity}
            destCity={destCity}
            departureAirport={departureAirport}
            arrivalAirport={arrivalAirport}
          />
          <FilterCard filters={filters} setFilters={setFilters} />
          <TimeSlotCard filters={filters} setFilters={setFilters} />
          <AirlinesCard airlines={airlines} filters={filters} setFilters={setFilters} />
        </aside>
      </div>

      {showTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="fixed bottom-5 right-5 bg-orange-500 text-white p-3 rounded-full shadow-lg hover:bg-orange-600 transition-colors duration-200"
        >
          <ArrowUp size={20} />
        </button>
      )}
    </>
  );
};

export default Sidebar;
```

**Key changes:**
1. Read `outboundFlights` instead of non-existent `searchResults`
2. Read `filters` and `setFilters` from store (after adding them in step 1)
3. Derive airline list from actual `outboundFlights` data via `useMemo`
4. Move all sub-components OUTSIDE the `Sidebar` function — fixes re-creation on every render (also covers Phase 3D)
5. Pass `filters`/`setFilters` as props to sub-components instead of relying on closure

---

### 1D. Fix `getFareQuote` Signature Mismatch — `useFlightStore.js`

**Problem:** The store's `getFareQuote` action (line 222) accepts `{ fareId, initialPrice }` and passes it directly to `getFareQuoteAPI`. But `getFareQuoteAPI` expects `{ tripType, fareIdOutbound, initialPriceOutbound, ... }`. This means the cancellation tab in `FlightPriceCard` sends the wrong payload and the API call fails.

**File:** `src/store/useFlightStore.js`

**BEFORE (lines 222–247):**
```js
  getFareQuote: async ({ fareId, initialPrice }) => {
    if (!fareId) throw new Error("fareId is required");

    set({ isFareLoading: true, fareError: null });

    try {
      const payload = { fareId, initialPrice };
      const response = await getFareQuoteAPI(payload);

      set((state) => ({
        fareData: {
          ...state.fareData,
          [fareId]: {
            ...(state.fareData[fareId] || {}),
            fareQuote: response,
          },
        },
        isFareLoading: false,
      }));

      return response;
    } catch (err) {
      set({ isFareLoading: false, fareError: err.message });
      throw err;
    }
  },
```

**AFTER:**
```js
  getFareQuote: async ({ fareId, initialPrice }) => {
    if (!fareId) throw new Error("fareId is required");

    set({ isFareLoading: true, fareError: null });

    try {
      // Map to the shape getFareQuoteAPI expects
      const payload = {
        tripType: "oneway",
        fareIdOutbound: fareId,
        initialPriceOutbound: initialPrice,
        fareIdInbound: null,
        initialPriceInbound: null,
      };
      const response = await getFareQuoteAPI(payload);

      set((state) => ({
        fareData: {
          ...state.fareData,
          [fareId]: {
            ...(state.fareData[fareId] || {}),
            fareQuote: response,
          },
        },
        isFareLoading: false,
      }));

      return response;
    } catch (err) {
      set({ isFareLoading: false, fareError: err.message });
      throw err;
    }
  },
```

**Key change:** Transform the simple `{ fareId, initialPrice }` into the full payload shape that `getFareQuoteAPI` requires.

---

### 1E. Fix ReturnFareModal Missing `onClose`

**Problem:** `ReturnResultsPage.jsx` passes `onClose={() => setShowFareModal(false)}` to `ReturnFareModal` (line 186), but the component never destructures `onClose`. Instead, it calls `navigate(-1)` on the X button (line 139), which navigates the user away from the page entirely.

**File:** `src/components/search/ReturnFareModal.jsx`

**BEFORE (lines 10–16):**
```jsx
export default function ReturnFareModal({
  outboundFlight,
  returnFlight,
  outboundBaggage,
  returnBaggage,
  isInternationalReturn = false,
}) {
```

**AFTER:**
```jsx
export default function ReturnFareModal({
  outboundFlight,
  returnFlight,
  outboundBaggage,
  returnBaggage,
  isInternationalReturn = false,
  onClose,
}) {
```

**BEFORE (lines 138–143):**
```jsx
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors duration-200"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
```

**AFTER:**
```jsx
          <button
            onClick={() => onClose?.()}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors duration-200"
            aria-label="Close fare modal"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
```

---

## Phase 2: Security & Auth Fixes (P1)

### 2A. Implement Actual Logout — `WalletProfile.jsx`

**Problem:** `handleLogout` (line 26) only shows a toast and closes the dropdown. It never clears the auth token or user info, so the user remains "logged in".

**File:** `src/components/Home/WalletProfile.jsx`

**BEFORE (lines 1–4, 26–30):**
```jsx
import React, { useState, useRef, useEffect } from "react";
import { Home, Printer, Phone, Lock, LogOut, ChevronDown } from "lucide-react";
import { toast } from "sonner";

// ...

    const handleLogout = () => {
        toast.success("Logged out successfully!");
        setOpen(false);
        // Add your logout logic here
    };
```

**AFTER:**
```jsx
import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Home, Printer, Phone, Lock, LogOut, ChevronDown } from "lucide-react";
import { toast } from "sonner";

// ... (add inside component, before handleLogout):

    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("userName");
        toast.success("Logged out successfully!");
        setOpen(false);
        navigate("/");
    };
```

Also **delete the inline `<style>` tag** at lines 102–117:

```jsx
            {/* DELETE THIS ENTIRE BLOCK */}
            <style>{`
        @keyframes slideDown {
          0% { opacity: 0; transform: translateY(-5px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animate-slide-down {
          animation: slideDown 0.15s ease-out;
        }
      `}</style>
```

In the dropdown div's className, remove `animate-slide-down` — the `transition-all duration-200` already present handles the animation.

---

### 2B. Remove Console Statements — Create `utils/logger.js`

**Problem:** 23+ `console.log/error/group/groupEnd` calls in `flight.js` alone, plus 10+ in other files. These leak internal data in production.

**New File:** `src/utils/logger.js`

```js
const isDev = import.meta.env.DEV;

export const log = (...args) => {
  if (isDev) console.log(...args);
};

export const logError = (...args) => {
  if (isDev) console.error(...args);
};

export const logGroup = (label, fn) => {
  if (isDev) {
    console.group(label);
    fn();
    console.groupEnd();
  }
};
```

**Then rewrite `src/components/api/flight.js` (full file):**

```js
import { log, logError } from "../../utils/logger";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// ===============================
// Search Flights API
// ===============================
export async function searchFlightsAPI(payload) {
  const body = {
    tripType: payload.tripType,
    origin: payload.origin,
    destination: payload.destination,
    departureDate: payload.departureDate,
    adults: payload.adults,
    children: payload.children,
    infants: payload.infants,
    cabinClass: payload.cabinClass,
  };

  if (payload.tripType === "roundtrip" && payload.returnDate) {
    body.returnDate = payload.returnDate;
  }

  log("[Search] Request:", body);

  const response = await fetch(`${API_BASE_URL}/flights/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    logError("[Search] Error:", data);
    throw new Error(data?.detail || "Flight search failed");
  }

  log("[Search] Response:", response.status);
  return data;
}

// ===============================
// Fare Quote API
// ===============================
export async function getFareQuoteAPI({
  tripType,
  fareIdOutbound,
  initialPriceOutbound,
  fareIdInbound = null,
  initialPriceInbound = null,
}) {
  const payload = {
    tripType,
    fareIdOutbound,
    initialPriceOutbound,
    fareIdInbound,
    initialPriceInbound,
  };

  if (!fareIdOutbound) {
    throw new Error("fareIdOutbound is required");
  }

  if (tripType === "roundtrip" && !fareIdInbound) {
    throw new Error("fareIdInbound is required for roundtrip");
  }

  log("[FareQuote] Request:", payload);

  const response = await fetch(`${API_BASE_URL}/flights/fare-quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    logError("[FareQuote] Error:", data);
    if (Array.isArray(data?.detail)) {
      throw new Error(data.detail.map((e) => e.msg).join(", "));
    }
    throw new Error(data?.detail || "Failed to fetch fare quote");
  }

  return data;
}

// ===============================
// Fare Rules API
// ===============================
export async function getFareRulesAPI({ fareId }) {
  if (!fareId) {
    throw new Error("fareId is required for fare rules");
  }

  const payload = { fareId };
  log("[FareRules] Request:", payload);

  const response = await fetch(`${API_BASE_URL}/flights/fare-rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    logError("[FareRules] Error:", data);
    throw new Error(data?.detail || "Failed to fetch fare rules");
  }

  return data;
}

// ===============================
// SSR API (Seats, Meals)
// ===============================
export async function getSSRAPI(payload) {
  if (!payload.fareIdOutbound) {
    throw new Error("fareIdOutbound is required for SSR");
  }

  log("[SSR] Request:", payload);

  try {
    const response = await fetch(`${API_BASE_URL}/flights/ssr`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      logError("[SSR] Error:", data);
      throw new Error(data?.detail || "SSR API failed");
    }

    return data;
  } catch (err) {
    logError("[SSR] Exception:", err?.message || err);
    throw err;
  }
}

// ===============================
// Download E-Ticket PDF
// ===============================
export async function downloadEticketAPI(bookingId, pnr) {
  const response = await fetch(
    `${API_BASE_URL}/flights/booking/${bookingId}/eticket?pnr=${encodeURIComponent(pnr)}`,
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err?.detail || "Failed to download e-ticket");
  }

  return response.blob();
}
```

**Also replace `console.error` calls in these other files:**

| File | Line | Replace with |
|------|------|-------------|
| `FlightPriceCard.jsx` | 95-96 | `.catch(console.error)` → `.catch(logError)` — add `import { logError } from "../../utils/logger"` |
| `FareModal.jsx` | 116 | `console.error(...)` → `logError(...)` |
| `ReturnFareModal.jsx` | 113 | `console.error(...)` → `logError(...)` |
| `useFlightStore.js` | 214 | `console.error(...)` → `logError(...)` |
| `BookingPage.jsx` | 230 | `console.error(...)` → `logError(...)` |
| `BookingConfirmationPage.jsx` | 148 | `console.error(...)` → `logError(...)` |
| `SearchPanel.jsx` | 106 | `console.error(err)` → `logError(err)` |

---

### 2C. Add Route Protection

**New File:** `src/components/common/ProtectedRoute.jsx`

```jsx
import { Navigate } from "react-router-dom";
import { toast } from "sonner";

export default function ProtectedRoute({ children }) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    toast.error("Please log in to continue.");
    return <Navigate to="/" replace />;
  }

  return children;
}
```

**File:** `src/router/AppRouter.jsx`

**BEFORE:**
```jsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "../components/common/DashBoard";
import FlightResultsPage from "../pages/FlightResultsPage";
import ReturnResultsPage from "../pages/ReturnResultsPage";
import BookingPage from "../pages/BookingPage";
import BookingConfirmationPage from "../pages/BookingConfirmationPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/flights/results" element={<FlightResultsPage />} />
        <Route path="/return/results" element={<ReturnResultsPage />} />
        <Route path="/booking" element={<BookingPage />} />
        <Route path="/booking/confirmation" element={<BookingConfirmationPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**AFTER:**
```jsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "../components/common/DashBoard";
import FlightResultsPage from "../pages/FlightResultsPage";
import ReturnResultsPage from "../pages/ReturnResultsPage";
import BookingPage from "../pages/BookingPage";
import BookingConfirmationPage from "../pages/BookingConfirmationPage";
import ProtectedRoute from "../components/common/ProtectedRoute";
import NotFoundPage from "../pages/NotFoundPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/flights/results" element={<FlightResultsPage />} />
        <Route path="/return/results" element={<ReturnResultsPage />} />
        <Route
          path="/booking"
          element={
            <ProtectedRoute>
              <BookingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/booking/confirmation"
          element={
            <ProtectedRoute>
              <BookingConfirmationPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

Note: `NotFoundPage` is created in Phase 5F below.

---

## Phase 3: Consolidate Duplicated Code

### 3A. Centralize Utility Functions — `utils/formatters.js`

**Problem:** `formatTime`, `formatDate`, `formatDuration`, and `diffMinutes` are defined in 5+ files with slight variations.

**File:** `src/utils/formatters.js`

**BEFORE (lines 1-24):**
```js
export const formatTime = (t) =>
    t
        ? new Date(t).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
          })
        : "--";

export const formatDate = (t) =>
    t
        ? new Date(t).toLocaleDateString([], {
              day: "2-digit",
              month: "short",
              year: "numeric",
          })
        : "--";

export const currencyFmt = (n) =>
    Number(n || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 0,
    });

export const getAirlineLogo = (code) =>
    code ? `https://pics.avs.io/60/60/${code}.png` : "";
```

**AFTER:**
```js
export const formatTime = (t) =>
    t
        ? new Date(t).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
          })
        : "--";

export const formatDate = (t) =>
    t
        ? new Date(t).toLocaleDateString("en-IN", {
              day: "2-digit",
              month: "short",
              year: "numeric",
          })
        : "--";

export const formatDuration = (mins = 0) => {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h}h ${m}m`;
};

export const diffMinutes = (a, b) =>
    Math.max(0, Math.round((new Date(b) - new Date(a)) / 60000));

export const currencyFmt = (n) =>
    Number(n || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 0,
    });

export const getAirlineLogo = (code) =>
    code ? `https://pics.avs.io/60/60/${code}.png` : "";
```

**Then remove duplicate definitions and add imports:**

#### `FlightPriceCard.jsx` — Remove lines 7-26, add import:

**BEFORE (lines 1-6):**
```jsx
import React, { useMemo, useState, useEffect } from "react";
import { Plane } from "lucide-react";
import { motion } from "framer-motion";
import useFlightStore from "../../store/useFlightStore";

/* ---------- HELPERS ---------- */
const formatTime = (dt) => ...
const formatDate = (dt) => ...
const formatDuration = (mins = 0) => ...
const diffMinutes = (a, b) => ...
```

**AFTER:**
```jsx
import React, { useMemo, useState, useEffect } from "react";
import { Plane } from "lucide-react";
import { motion } from "framer-motion";
import useFlightStore from "../../store/useFlightStore";
import { formatTime, formatDate, formatDuration, diffMinutes, getAirlineLogo } from "../../utils/formatters";
```

#### `FareModal.jsx` — Delete inline `formatTime`/`formatDate` (lines 39-52), add import:

```jsx
import { formatTime, formatDate } from "../../utils/formatters";
``

#### `ReturnFareModal.jsx` — Delete inline `formatTime` (lines 37-38), add import:

```jsx
import { formatTime } from "../../utils/formatters";
```

#### `ReturnResultsPage.jsx` — Delete lines 19-23, add import:

```jsx
import { formatTime, formatDuration, getAirlineLogo } from "../utils/formatters";
```

#### `BookingConfirmationPage.jsx` — Delete local `formatTime`/`formatDate` (lines 36-48), update import:

**BEFORE:**
```jsx
import { currencyFmt } from "../utils/formatters";
```

**AFTER:**
```jsx
import { currencyFmt, formatTime, formatDate } from "../utils/formatters";
```

---

### 3B. Centralize Airline Logo URL

**Problem:** `https://pics.avs.io/60/60/${code}.png` is hardcoded in 5 files. `getAirlineLogo` already exists in `formatters.js` but isn't used.

Replace all hardcoded URLs with `getAirlineLogo(code)` and add `onError` fallback:

| File | Line(s) | Before | After |
|------|---------|--------|-------|
| `FlightPriceCard.jsx` | 143 | `` src={`https://pics.avs.io/60/60/${airlineCode}.png`} `` | `src={getAirlineLogo(airlineCode)}` + add `onError={(e) => (e.target.style.display = "none")}` |
| `FareModal.jsx` | 156 | `` src={`https://pics.avs.io/60/60/${firstSegment.carrier.code}.png`} `` | Already has `onError` — just change src to `src={getAirlineLogo(firstSegment.carrier.code)}` |
| `ReturnResultsPage.jsx` | 242, 286 | `` src={`https://pics.avs.io/60/60/${first.carrier.code}.png`} `` | `src={getAirlineLogo(first.carrier.code)}` + add `onError` |
| `ReturnFlightcard.jsx` | 66 | `` src={`https://pics.avs.io/60/60/${data.airlineCode}.png`} `` | `src={getAirlineLogo(data.airlineCode)}` + add `onError` |

Add `import { getAirlineLogo } from "..."` to each file.

---

### 3C. Extract Shared FareCard Component

**Problem:** `ReturnFareModal.jsx` has a `FareCard` component (lines 216-250) and `FareModal.jsx` has similar fare card rendering. Near-identical code.

**New File:** `src/components/search/FareCard.jsx`

```jsx
import React from "react";
import { motion } from "framer-motion";

export default function FareCard({
  fare,
  isSelected,
  onSelect,
  farePassengers = 1,
  baggage,
  showBaggage = false,
  index = 0,
}) {
  const displayPrice = fare.totalPrice * farePassengers;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className={`min-w-[300px] border rounded-2xl p-5 flex flex-col transition-all duration-200 hover:shadow-lg ${
        isSelected
          ? "border-blue-500 ring-1 ring-blue-500 bg-blue-50/30"
          : "border-gray-200 hover:border-gray-300"
      }`}
    >
      <p className="font-display text-2xl font-bold text-center">
        ₹{displayPrice.toLocaleString("en-IN")}
      </p>

      {farePassengers > 1 && (
        <p className="text-center text-sm text-gray-500">
          ₹{fare.totalPrice} × {farePassengers} passenger
          {farePassengers > 1 ? "s" : ""}
        </p>
      )}

      <p className="mt-2 text-center font-semibold uppercase">
        {fare.fareType}
      </p>

      {showBaggage && baggage && (
        <div className="text-xs text-gray-500 text-center mt-1">
          Baggage: {baggage.checkin}kg · Cabin: {baggage.cabin}kg
        </div>
      )}

      <div className="my-4 border-t" />

      <button
        onClick={onSelect}
        className={`mt-auto w-full py-2.5 rounded-xl text-white font-semibold transition-colors duration-200 ${
          isSelected ? "bg-pink-800" : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {isSelected ? "SELECTED" : "SELECT"}
      </button>
    </motion.div>
  );
}
```

**Then in `ReturnFareModal.jsx`:**
- Delete the local `FareCard` function (lines 216-250)
- Add `import FareCard from "./FareCard";` at the top
- Update usage to pass `showBaggage={true}`:

```jsx
<FareCard
  key={fare.fareId}
  fare={fare}
  baggage={activeBaggage}
  showBaggage={true}
  isSelected={selected?.fareId === fare.fareId}
  onSelect={() => handleSelectFare(fare)}
  farePassengers={farePassengers}
  index={idx}
/>
```

---

### 3D. Move Inline Components Out of Render Bodies

**Already handled in 1C** for `Sidebar.jsx` — all sub-components moved outside `Sidebar`.

**File:** `ReturnResultsPage.jsx` — `FlightColumn`, `FlightCard`, `FooterFlight`, `FlightDetailsModal` are already defined outside the `ReturnResultsPage` function. **No change needed.**

---

## Phase 4: Form Validation

### 4A. Create Validation Utilities

**New File:** `src/utils/validators.js`

```js
const ageDiff = (dob) => {
  const birth = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const m = now.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) age--;
  return age;
};

export const isValidName = (s) => /^[a-zA-Z\s'-]{2,50}$/.test(s?.trim());

export const isValidEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);

export const isValidPhone = (s) => /^\d{10,15}$/.test(s?.replace(/\D/g, ""));

export const isValidPAN = (s) => /^[A-Z]{5}[0-9]{4}[A-Z]$/.test(s);

export const isValidPassport = (s) => /^[A-Z0-9]{6,12}$/.test(s);

export const isAdult = (dob) => ageDiff(dob) >= 12;

export const isChild = (dob) => {
  const a = ageDiff(dob);
  return a >= 2 && a < 12;
};

export const isInfant = (dob) => ageDiff(dob) < 2;

export const isFutureDate = (d) => new Date(d) > new Date();
```

---

### 4B. Add Validation to `travellersComplete` — `BookingPage.jsx`

**File:** `src/pages/BookingPage.jsx`

Add import at top:
```jsx
import {
    isValidName, isValidEmail, isValidPhone,
    isValidPAN, isValidPassport,
    isAdult, isChild, isInfant, isFutureDate,
} from "../utils/validators";
```

**BEFORE (lines 131-154):**
```jsx
    const travellersComplete = useMemo(() => {
        if (!travellers.length) return false;
        const basicOk = travellers.every(
            (t) =>
                t.title &&
                t.firstName &&
                t.lastName &&
                t.dateOfBirth &&
                t.gender,
        );
        const leadOk = !!(travellers[0]?.email && travellers[0]?.contactNo);
        const panOk =
            !fareQuoteFlags?.isPanRequired || travellers.every((t) => t.pan);
        const passportOk =
            !fareQuoteFlags?.isPassportRequired ||
            travellers.every(
                (t) =>
                    t.passportNo &&
                    t.passportExpiry &&
                    (!fareQuoteFlags?.isPassportFullDetailRequired ||
                        (t.passportIssueDate && t.passportIssueCountryCode)),
            );
        return basicOk && leadOk && panOk && passportOk;
    }, [travellers, fareQuoteFlags]);
```

**AFTER:**
```jsx
    const travellersComplete = useMemo(() => {
        if (!travellers.length) return false;

        const basicOk = travellers.every(
            (t) =>
                t.title &&
                isValidName(t.firstName) &&
                isValidName(t.lastName) &&
                t.dateOfBirth &&
                t.gender,
        );

        // Validate DOB matches pax type
        const dobOk = travellers.every((t) => {
            if (!t.dateOfBirth) return false;
            if (t.type === "Adult") return isAdult(t.dateOfBirth);
            if (t.type === "Child") return isChild(t.dateOfBirth);
            if (t.type === "Infant") return isInfant(t.dateOfBirth);
            return true;
        });

        const leadOk = !!(
            travellers[0]?.email &&
            isValidEmail(travellers[0].email) &&
            travellers[0]?.contactNo &&
            isValidPhone(travellers[0].contactNo)
        );

        const panOk =
            !fareQuoteFlags?.isPanRequired ||
            travellers.every((t) => isValidPAN(t.pan));

        const passportOk =
            !fareQuoteFlags?.isPassportRequired ||
            travellers.every(
                (t) =>
                    isValidPassport(t.passportNo) &&
                    t.passportExpiry &&
                    isFutureDate(t.passportExpiry) &&
                    (!fareQuoteFlags?.isPassportFullDetailRequired ||
                        (t.passportIssueDate && t.passportIssueCountryCode)),
            );

        return basicOk && dobOk && leadOk && panOk && passportOk;
    }, [travellers, fareQuoteFlags]);
```

---

### 4C. Add Field-Level Error Display — `TravellerForm.jsx`

**File:** `src/components/booking/TravellerForm.jsx`

Add imports:
```jsx
import React, { useState } from "react";
import { motion } from "framer-motion";
import { isValidName, isValidPAN, isValidPassport, isValidEmail, isValidPhone, isFutureDate } from "../../utils/validators";
```

Add error state and validation inside the component (after the `update` function):

```jsx
export default function TravellerForm({ travellers, setTravellers, fareQuoteFlags }) {
    const [errors, setErrors] = useState({});

    const update = (i, k, v) => {
        const copy = [...travellers];
        copy[i] = { ...copy[i], [k]: v };
        setTravellers(copy);
    };

    const validateField = (i, k, v) => {
        const key = `${i}-${k}`;
        let msg = "";

        switch (k) {
            case "firstName":
            case "lastName":
                if (v && !isValidName(v)) msg = "Letters only, 2-50 characters";
                break;
            case "pan":
                if (v && !isValidPAN(v)) msg = "Invalid PAN format (e.g. ABCDE1234F)";
                break;
            case "passportNo":
                if (v && !isValidPassport(v)) msg = "Invalid passport number";
                break;
            case "passportExpiry":
                if (v && !isFutureDate(v)) msg = "Must be a future date";
                break;
            case "email":
                if (v && !isValidEmail(v)) msg = "Invalid email address";
                break;
            case "contactNo":
                if (v && !isValidPhone(v)) msg = "10-15 digits required";
                break;
        }

        setErrors((prev) => ({ ...prev, [key]: msg }));
    };

    const fieldError = (i, k) => errors[`${i}-${k}`];
```

Then wrap each input with error display. Example for firstName:

**BEFORE:**
```jsx
<InputLabel label="First Name" required>
    <input
        className={inputBase}
        placeholder="As on ID"
        value={t.firstName}
        onChange={(e) => update(i, "firstName", e.target.value)}
    />
</InputLabel>
```

**AFTER:**
```jsx
<InputLabel label="First Name" required>
    <input
        className={`${inputBase} ${fieldError(i, "firstName") ? "border-red-400 focus:ring-red-300 focus:border-red-400" : ""}`}
        placeholder="As on ID"
        value={t.firstName}
        onChange={(e) => update(i, "firstName", e.target.value)}
        onBlur={(e) => validateField(i, "firstName", e.target.value)}
    />
    {fieldError(i, "firstName") && (
        <p className="text-xs text-red-500 mt-1">{fieldError(i, "firstName")}</p>
    )}
</InputLabel>
```

Apply the same pattern to: `lastName`, `pan`, `passportNo`, `passportExpiry`, `email`, `contactNo`.

---

### 4D. Add Passenger Count Limits — `SearchPanel.jsx`

**Problem:** No limit on passenger count. Airlines cap at 9 total, and infants must not exceed adults.

**File:** `src/components/Home/SearchPanel.jsx`

**BEFORE (the "+" button, around line 220-230):**
```jsx
                                            <button
                                                type="button"
                                                onClick={() =>
                                                    useFlightStore.setState({
                                                        [key]: value + 1,
                                                    })
                                                }
                                                className="px-3 py-1 border rounded hover:bg-gray-100 transition-colors duration-200"
                                            >
                                                +
                                            </button>
```

**AFTER:**
```jsx
                                            <button
                                                type="button"
                                                disabled={
                                                    totalPassengers >= 9 ||
                                                    (key === "infants" && value >= adults)
                                                }
                                                onClick={() =>
                                                    useFlightStore.setState({
                                                        [key]: value + 1,
                                                    })
                                                }
                                                className="px-3 py-1 border rounded hover:bg-gray-100 transition-colors duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                                            >
                                                +
                                            </button>
```

Add validation messages below the passenger rows (before the `<select>` for travel class):

```jsx
{totalPassengers >= 9 && (
    <p className="text-xs text-red-500 mb-2">Maximum 9 passengers allowed</p>
)}
{infants > adults && (
    <p className="text-xs text-red-500 mb-2">Infants cannot exceed number of adults</p>
)}
```

---

## Phase 5: Production Readiness

### 5A. Fix SEO / HTML Head — `index.html`

**File:** `frontend/index.html`

**BEFORE:**
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>frontend</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**AFTER:**
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" href="/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FareClubs — Cheap Flight Tickets & Booking</title>
    <meta name="description" content="Book cheap domestic and international flight tickets on FareClubs. Compare fares across airlines and save on every trip." />
    <meta property="og:title" content="FareClubs — Cheap Flight Tickets & Booking" />
    <meta property="og:description" content="Book cheap domestic and international flight tickets. Compare fares across airlines." />
    <meta property="og:type" content="website" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**Note:** Place your brand favicon at `frontend/public/favicon.png`.

---

### 5B. Airline Logo Fallback Strategy

**Recommended: Option C — keep external, add fallback.** Already addressed in Phase 3B. Every `<img>` using `getAirlineLogo()` should have `onError` handler.

**Optional better UX — create `src/components/common/AirlineLogo.jsx`:**

```jsx
import { useState } from "react";
import { getAirlineLogo } from "../../utils/formatters";

export default function AirlineLogo({ code, name, className = "w-10 h-10" }) {
  const [failed, setFailed] = useState(false);

  if (failed || !code) {
    return (
      <div className={`${className} rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500`}>
        {(code || "??").slice(0, 2)}
      </div>
    );
  }

  return (
    <img
      src={getAirlineLogo(code)}
      alt={name || code}
      className={`${className} object-contain`}
      onError={() => setFailed(true)}
    />
  );
}
```

---

### 5C. Move SearchPanel Carousel Images

**File:** `src/components/Home/SearchPanel.jsx`

**BEFORE (lines 8-12):**
```jsx
const images = [
    "https://www.fareclubs.com/nav/file/2/Zero",
    "https://www.fareclubs.com/nav/file/2/Ebix",
    "https://www.fareclubs.com/nav/file/2/fataka",
];
```

**AFTER:**
```jsx
const images = [
    "/banners/banner-1.webp",
    "/banners/banner-2.webp",
    "/banners/banner-3.webp",
];
```

**Action:** Download the current images and save them to `frontend/public/banners/`. Convert to WebP for better performance.

---

### 5D. Add `.env.example`

**New File:** `frontend/.env.example`

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

### 5E. Add Error Boundary

**New File:** `src/components/common/ErrorBoundary.jsx`

```jsx
import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error("ErrorBoundary caught:", error, info);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">
            Something went wrong
          </h1>
          <p className="text-gray-500 mb-6">
            An unexpected error occurred. Please try again.
          </p>
          <a
            href="/"
            className="px-6 py-3 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-full font-semibold hover:shadow-lg transition-all"
          >
            Go Home
          </a>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**File:** `src/App.jsx`

**BEFORE:**
```jsx
import React from "react";
import { Toaster } from "sonner";
import AppRouter from "./router/AppRouter";

export default function App() {
  return (
    <>
      <Toaster position="top-center" richColors />
      <AppRouter />
    </>
  );
}
```

**AFTER:**
```jsx
import React from "react";
import { Toaster } from "sonner";
import AppRouter from "./router/AppRouter";
import ErrorBoundary from "./components/common/ErrorBoundary";

export default function App() {
  return (
    <ErrorBoundary>
      <Toaster position="top-center" richColors />
      <AppRouter />
    </ErrorBoundary>
  );
}
```

---

### 5F. Add 404 Catch-All Route

**New File:** `src/pages/NotFoundPage.jsx`

```jsx
import { Link } from "react-router-dom";
import { Home } from "lucide-react";
import Navbar from "../components/Home/Navbar";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex flex-col items-center justify-center pt-32 px-4">
        <h1 className="font-display text-6xl font-bold text-gray-200 mb-4">
          404
        </h1>
        <p className="text-gray-500 text-lg mb-6">Page not found</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-full font-semibold hover:shadow-lg transition-all"
        >
          <Home className="w-4 h-4" />
          Go Home
        </Link>
      </div>
    </div>
  );
}
```

Route already added in Phase 2C (`AppRouter.jsx` update).

---

### 5G. Remove Dead Code/Files

| Action | File | Reason |
|--------|------|--------|
| **Delete** | `src/pages/internal-search.jsonc` | 391KB test data — not imported anywhere |
| **Delete** | `src/components/search/ViewDetails.jsx` | Empty/unused component (verify with `grep -r "ViewDetails" src/`) |
| **Remove** | Inline `<style>` in `WalletProfile.jsx` | Already covered in Phase 2A |
| **Uninstall** | `axios` from `package.json` | Unused — entire codebase uses `fetch`. Run `npm uninstall axios` if present |

---

### 5H. Persist BookingPage State Across Refresh

**Problem:** If a user refreshes the booking page, all `location.state` is lost and the page becomes blank/broken.

**File:** `src/pages/BookingPage.jsx`

**BEFORE (lines 43-61):**
```jsx
export default function BookingPage() {
    const { state } = useLocation();
    const navigate = useNavigate();

    const {
        outboundFlight,
        returnFlight,
        outboundSelectedFare,
        returnSelectedFare,
        passengers = { adults: 1, children: 0, infants: 0 },
        isInternationalReturn = false,
        perPassengerFares,
        fareQuoteFlags: fareQuoteFlagsOneway,
        perPassengerFaresOutbound,
        perPassengerFaresInbound,
        fareQuoteFlagsOutbound,
        fareQuoteFlagsInbound,
    } = state || {};
```

**AFTER:**
```jsx
export default function BookingPage() {
    const { state } = useLocation();
    const navigate = useNavigate();

    // Restore from sessionStorage if page was refreshed (location.state is lost)
    const pageState = useMemo(() => {
        if (state) {
            try {
                sessionStorage.setItem("fc_booking_state", JSON.stringify(state));
            } catch {}
            return state;
        }
        try {
            const stored = sessionStorage.getItem("fc_booking_state");
            if (stored) return JSON.parse(stored);
        } catch {}
        return {};
    }, [state]);

    const {
        outboundFlight,
        returnFlight,
        outboundSelectedFare,
        returnSelectedFare,
        passengers = { adults: 1, children: 0, infants: 0 },
        isInternationalReturn = false,
        perPassengerFares,
        fareQuoteFlags: fareQuoteFlagsOneway,
        perPassengerFaresOutbound,
        perPassengerFaresInbound,
        fareQuoteFlagsOutbound,
        fareQuoteFlagsInbound,
    } = pageState;

    // Guard: no flight data at all
    if (!outboundFlight && !outboundSelectedFare) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
                <Navbar />
                <p className="text-gray-500 mt-32">
                    No booking data found. Please search for flights first.
                </p>
                <button
                    onClick={() => navigate("/")}
                    className="mt-4 px-6 py-2.5 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-full font-semibold"
                >
                    Search Flights
                </button>
            </div>
        );
    }
```

---

## Phase 6: React Best Practices Polish

### 6A. Fix Key Props — `TravellerForm.jsx`

**File:** `src/components/booking/TravellerForm.jsx` line 34

**BEFORE:**
```jsx
                    key={i}
```

**AFTER:**
```jsx
                    key={`${t.type}-${i}`}
```

---

### 6B. Accessibility Quick Wins

#### Add `aria-label` to icon-only close buttons:

**`FareModal.jsx` (line 137):**
```jsx
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors duration-200"
            aria-label="Close fare options"
          >
```

**`ReturnFareModal.jsx`** — already updated in Phase 1E.

#### Add Escape key handler to all modals:

Add this hook inside `FareModal`, `ReturnFareModal`, and `SSRModal`:

```jsx
  useEffect(() => {
    const handleEsc = (e) => { if (e.key === "Escape") onClose?.(); };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [onClose]);
```

#### Add `role="dialog"` and `aria-modal="true"` to modal wrappers:

```jsx
<div className="fixed inset-0 z-50 ..." role="dialog" aria-modal="true">
```

#### `AirportAutocomplete` — add roles to dropdown:

```jsx
<ul role="listbox">
  {results.map((airport) => (
    <li key={airport.code} role="option" aria-selected={selectedCode === airport.code}>
```

---

### 6C. ESLint Tightening — `eslint.config.js`

**File:** `frontend/eslint.config.js`

**BEFORE (lines 25-27):**
```js
    rules: {
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
    },
```

**AFTER:**
```js
    rules: {
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      'no-console': 'warn',
    },
```

Optionally add `eslint-plugin-jsx-a11y`:
```bash
npm install -D eslint-plugin-jsx-a11y
```

Then update config:
```js
import jsxA11y from 'eslint-plugin-jsx-a11y';

// Add to extends array:
jsxA11y.configs.recommended,
```

---

## Summary of New Files

| File | Purpose |
|------|---------|
| `src/utils/logger.js` | Dev-only console wrapper |
| `src/utils/validators.js` | Form field validators |
| `src/components/common/ProtectedRoute.jsx` | Auth guard for routes |
| `src/components/common/ErrorBoundary.jsx` | React error boundary |
| `src/components/common/AirlineLogo.jsx` | Logo with fallback (optional) |
| `src/components/search/FareCard.jsx` | Shared fare card component |
| `src/pages/NotFoundPage.jsx` | 404 page |
| `frontend/.env.example` | Environment variable template |

## Files to Delete

| File | Reason |
|------|--------|
| `src/pages/internal-search.jsonc` | 391KB test data, not imported |
| `src/components/search/ViewDetails.jsx` | Empty/unused component |

---

## Execution Order

| Step | Phase | Effort | Risk |
|------|-------|--------|------|
| 1 | 1A-1E: Fix critical bugs | ~1 hr | Low |
| 2 | 2A-2C: Security fixes | ~1 hr | Low |
| 3 | 3A-3B: Centralize utils + logos | ~30 min | Low |
| 4 | 3C-3D: Extract shared components | ~1 hr | Medium |
| 5 | 4A-4D: Form validation | ~1.5 hr | Medium |
| 6 | 5A-5H: Production readiness | ~1.5 hr | Low |
| 7 | 6A-6C: React best practices | ~45 min | Low |

**Total: ~7-8 hours of implementation**

---

## Verification Checklist

After each phase:

1. `npm run build` — must succeed with no errors
2. `npm run lint` — should pass
3. Manual test flows:
   - Home → search one-way → view fares → book → payment
   - Home → search roundtrip → select both → view fares → book → payment
   - Refresh on booking page → data should persist
   - Logout → verify token cleared → try accessing /booking → should redirect
   - Enter invalid traveller data → verify inline errors appear
4. Browser console — should be clean in production build
5. Network tab — verify airline logo fallbacks work
