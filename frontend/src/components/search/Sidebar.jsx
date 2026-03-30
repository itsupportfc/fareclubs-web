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