import React, { useState, useEffect, useMemo } from "react";
import {
  Sunrise, Sun, Sunset, Moon, Clock,
  PlaneTakeoff, Filter, ArrowUp, IndianRupee,
} from "lucide-react";
import useFlightStore from "../../store/useFlightStore";
import { resolveTripConfig } from "../../config/tripConfig";

/* ─────────────────────────────────────────────────────────────
   deriveAirlines
   Scans a flight list and returns a sorted array of unique airline names.
   Called inside DirectionFilterSection so each direction gets its own list.
───────────────────────────────────────────────────────────────── */
function deriveAirlines(flightGroups = []) {
  const names = new Set();
  flightGroups.forEach((flightGroup) => {
    // Same path as getAirlineName: fares[0].segments[0][0].carrier.name
    const name = flightGroup?.fares?.[0]?.segments?.[0]?.[0]?.carrier?.name;
    if (name) names.add(name);
  });
  return [...names].sort();
}

/* ─────────────────────────────────────────────────────────────
   RouteInfoCard — decorative, not a filter
───────────────────────────────────────────────────────────────── */
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

/* ─────────────────────────────────────────────────────────────
   PriceSlider
   Global filter — applies to both outbound and inbound.
   Hidden when priceRange.max is 0 (backend hasn't sent data yet).

   The slider value is:  maxPrice (user's choice) ?? rangeMax (full range = no filter)
   Dragging all the way right = no filter (same as null).
   "Clear" button explicitly sets maxPrice back to null.
───────────────────────────────────────────────────────────────── */
function PriceSlider({ priceRange, maxPrice, setMaxPrice }) {
  const rangeMin     = priceRange?.min || 0;
  const rangeMax     = priceRange?.max || 0;
  const currentValue = maxPrice ?? rangeMax;

  if (rangeMax === 0) return null;

  return (
    <div className="bg-white shadow-md p-4 rounded-xl border border-gray-100 hover:shadow-lg transition-all duration-200">
      <h3 className="text-lg font-semibold mb-3 text-gray-900 flex items-center gap-2">
        <IndianRupee size={18} className="text-orange-500" /> Price Range
      </h3>
      <div className="flex justify-between text-sm text-gray-600 mb-1">
        <span>₹{rangeMin.toLocaleString("en-IN")}</span>
        <span className="font-semibold text-gray-800">
          up to ₹{currentValue.toLocaleString("en-IN")}
        </span>
      </div>
      <input
        type="range"
        min={rangeMin}
        max={rangeMax}
        value={currentValue}
        onChange={(e) => setMaxPrice(Number(e.target.value))}
        className="w-full accent-orange-500"
      />
      {maxPrice !== null && (
        <button
          onClick={() => setMaxPrice(null)}
          className="text-xs text-orange-500 mt-2 underline hover:text-orange-600 transition-colors"
        >
          Clear price filter
        </button>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   StopsCard
   Renders Non Stop / 1 Stop checkboxes.
   onChange receives a flat patch: { nonStop: true } or { oneStop: false }
───────────────────────────────────────────────────────────────── */
function StopsCard({ filters, onChange }) {
  const options = [
    { key: "nonStop", label: "Non Stop" },
    { key: "oneStop", label: "1 Stop"   },
  ];

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-600 mb-2 flex items-center gap-1">
        <Filter size={14} className="text-orange-500" /> Stops
      </h4>
      <div className="space-y-2 text-sm text-gray-700">
        {options.map(({ key, label }) => (
          <label
            key={key}
            className="flex items-center gap-2 cursor-pointer hover:text-orange-500 transition-colors duration-200"
          >
            <input
              type="checkbox"
              checked={!!filters?.[key]}
              onChange={() => onChange({ [key]: !filters?.[key] })}
              className="accent-orange-500"
            />
            {label}
          </label>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   TimeSlotCard
   onChange receives a nested patch: { timeSlots: { morning: true } }
   The store's setFilters deep-merges timeSlots so only the toggled key changes.
───────────────────────────────────────────────────────────────── */
function TimeSlotCard({ filters, onChange }) {
  const slots = [
    { label: "Early Morning", key: "earlyMorning", range: "00:00–08:00", icon: <Sunrise size={14} /> },
    { label: "Morning",       key: "morning",      range: "08:00–12:00", icon: <Sun     size={14} /> },
    { label: "Afternoon",     key: "afternoon",    range: "12:00–18:00", icon: <Sunset  size={14} /> },
    { label: "Evening",       key: "evening",      range: "18:00–24:00", icon: <Moon    size={14} /> },
  ];

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-600 mb-2 flex items-center gap-1">
        <Clock size={14} className="text-orange-500" /> Departure Time
      </h4>
      <div className="bg-gray-50 border border-gray-100 rounded-xl p-2 space-y-2">
        {slots.map((slot) => (
          <label
            key={slot.key}
            className="flex items-center justify-between text-xs cursor-pointer hover:text-orange-600 transition-colors duration-200"
          >
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!filters?.timeSlots?.[slot.key]}
                onChange={() =>
                  onChange({ timeSlots: { [slot.key]: !filters?.timeSlots?.[slot.key] } })
                }
                className="accent-orange-500"
              />
              <span className="flex items-center gap-1 font-medium text-gray-800">
                {slot.icon} {slot.label}
              </span>
            </div>
            <span className="text-gray-400">{slot.range}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   AirlinesCard
   airlines prop is derived from the relevant flight list (not from store.availableAirlines)
   so each direction shows only the airlines that actually appear in that direction's results.
   Returns null if no airlines found (avoids rendering an empty card).
───────────────────────────────────────────────────────────────── */
function AirlinesCard({ airlines, filters, onChange }) {
  if (!airlines.length) return null;

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-600 mb-2">Airlines</h4>
      <div className="space-y-2 text-sm text-gray-700">
        {airlines.map((airline) => (
          <label
            key={airline}
            className="flex items-center gap-2 cursor-pointer hover:text-orange-500 transition-colors duration-200"
          >
            <input
              type="checkbox"
              checked={filters?.airlines?.includes(airline) || false}
              onChange={() => {
                const selected = filters?.airlines || [];
                const exists   = selected.includes(airline);
                onChange({
                  airlines: exists
                    ? selected.filter((a) => a !== airline)
                    : [...selected, airline],
                });
              }}
              className="accent-orange-500"
            />
            {airline}
          </label>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   DirectionFilterSection
   Composes StopsCard + TimeSlotCard + AirlinesCard for one direction.
   title = null on one-way (no heading rendered).

   Why this wrapper exists:
   The two sections ("Onward Journey" / "Return Journey") have identical structure
   but different data (different filters object, different onChange, different flights).
   This component captures that shared structure once.
───────────────────────────────────────────────────────────────── */
function DirectionFilterSection({ title, filters, onChange, flights }) {
  const airlines = useMemo(() => deriveAirlines(flights), [flights]);

  return (
    <div className="bg-white shadow-md p-4 rounded-xl border border-gray-100 hover:shadow-lg transition-all duration-200 space-y-4">
      {title && (
        <h3 className="text-base font-bold text-blue-700 border-b border-blue-100 pb-2">
          {title}
        </h3>
      )}
      <StopsCard    filters={filters} onChange={onChange} />
      <TimeSlotCard filters={filters} onChange={onChange} />
      <AirlinesCard airlines={airlines} filters={filters} onChange={onChange} />
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   Sidebar (main)
   Reads tripType + isInternationalReturn from the store and resolves
   hasSeparateLists via resolveTripConfig — the same source of truth
   used by ReturnResultsPage to decide its column layout.

   hasSeparateLists = true  → domestic return → two direction sections
   hasSeparateLists = false → one-way or international return → one section
───────────────────────────────────────────────────────────────── */
const Sidebar = ({
  outboundFlights: outboundFlightsProp,
  inboundFlights:  inboundFlightsProp,
}) => {
  const {
    outboundFlights: storeOutboundFlights,
    inboundFlights:  storeInboundFlights,
    tripType,
    isInternationalReturn,
    filters = {},
    priceRange,
    setFilters,
    setMaxPrice,
  } = useFlightStore();

  const outboundFlights = outboundFlightsProp || storeOutboundFlights || [];
  const inboundFlights  = inboundFlightsProp  || storeInboundFlights  || [];

  const { hasSeparateLists } = resolveTripConfig({ tripType, isInternationalReturn });

  const firstFlight = outboundFlights[0] || inboundFlights[0];
  // segments[0][0] = first leg of the outbound direction (internal schema, always this shape)
  const firstSeg = firstFlight?.fares?.[0]?.segments?.[0]?.[0];

  const originCity       = firstSeg?.departure?.city || firstFlight?.origin      || "Origin";
  const destCity         = firstSeg?.arrival?.city   || firstFlight?.destination || "Destination";
  const departureAirport = firstSeg?.departure?.name || "";
  const arrivalAirport   = firstSeg?.arrival?.name   || "";

  const [showTop, setShowTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => setShowTop(window.scrollY > 300);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <aside className="hidden md:block col-span-1 space-y-4 sticky top-5">

        <RouteInfoCard
          originCity={originCity}
          destCity={destCity}
          departureAirport={departureAirport}
          arrivalAirport={arrivalAirport}
        />

        {/* Price slider is always shown (global, not per-direction) */}
        <PriceSlider
          priceRange={priceRange}
          maxPrice={filters.maxPrice}
          setMaxPrice={setMaxPrice}
        />

        {hasSeparateLists ? (
          // Domestic return: show separate filter sections per direction
          <>
            <DirectionFilterSection
              title="Onward Journey"
              filters={filters.outbound}
              onChange={(patch) => setFilters("outbound", patch)}
              flights={outboundFlights}
            />
            <DirectionFilterSection
              title="Return Journey"
              filters={filters.inbound}
              onChange={(patch) => setFilters("inbound", patch)}
              flights={inboundFlights}
            />
          </>
        ) : (
          // One-way or international return: single filter section, no direction heading
          <DirectionFilterSection
            title={null}
            filters={filters.outbound}
            onChange={(patch) => setFilters("outbound", patch)}
            flights={outboundFlights}
          />
        )}

      </aside>

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
