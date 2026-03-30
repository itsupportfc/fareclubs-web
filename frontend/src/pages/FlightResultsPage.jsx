import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Plane } from "lucide-react";
import useFlightStore from "../store/useFlightStore";
import Navbar from "../components/Home/Navbar";
import Sidebar from "../components/search/Sidebar";
import SmallSearch from "../components/search/SmallSearch";
import FlightPriceCard from "../components/search/FlightPriceCard";
import Offers from "../components/search/Offers";
import LoaderOverlay from "../components/common/LoaderOverlay";
import FareModal from "../components/search/FareModal";
import { filterFlights } from "../utils/flightFilters";

const getDepartureHour = (flight) => {
  const depTime =
    flight?.departureTime ||
    flight?.fares?.[0]?.segments?.[0]?.[0]?.departureTime ||
    flight?.Segments?.[0]?.[0]?.Origin?.DepTime ||
    flight?.Segments?.[0]?.[0]?.departureTime;

  if (!depTime) return null;

  const date = new Date(depTime);
  if (Number.isNaN(date.getTime())) return null;

  return date.getHours();
};

const getStopsCount = (flight) => {
  if (typeof flight?.noOfStops === "number") return flight.noOfStops;

  const fareSegments = flight?.fares?.[0]?.segments?.[0];
  if (Array.isArray(fareSegments)) {
    return Math.max(fareSegments.length - 1, 0);
  }

  const segmentGroup = flight?.Segments?.[0] || [];
  return Math.max(segmentGroup.length - 1, 0);
};

const getAirlineName = (flight) => {
  return (
    flight?.fares?.[0]?.segments?.[0]?.[0]?.carrier?.name ||
    flight?.Segments?.[0]?.[0]?.Airline?.AirlineName ||
    ""
  );
};

const matchesTimeSlot = (hour, activeSlots) => {
  if (!activeSlots.length) return true;
  if (hour === null) return false;

  return activeSlots.some((slot) => {
    if (slot === "earlyMorning") return hour >= 0 && hour < 8;
    if (slot === "morning") return hour >= 8 && hour < 12;
    if (slot === "afternoon") return hour >= 12 && hour < 18;
    if (slot === "evening") return hour >= 18 && hour < 24;
    return false;
  });
};

export default function FlightResultsPage() {
  const {
    outboundFlights = [],
    origin,
    destination,
    adults,
    children,
    infants,
    isLoading,
    filters = {},
    setCache,
  } = useFlightStore();

  const passengers = { adults, children, infants };
  const [selectedFlight, setSelectedFlight] = useState(null);

  const handleViewFares = (flight) => {
    setSelectedFlight(flight);
    if (typeof setCache === "function") {
      setCache("selectedFlight", flight);
    }
  };

  const filteredFlights = useMemo(
    () => filterFlights(outboundFlights, filters.outbound, filters.maxPrice),
    [outboundFlights, filters]
  );

  if (isLoading) return <LoaderOverlay />;

  return (
    <div className="min-h-screen bg-gray-50 mt-16">
      <Navbar />

      <div className="bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white">
        <div className="max-w-7xl mx-auto px-4 py-5 space-y-2">
          <SmallSearch />
          <h1 className="font-display text-2xl md:text-3xl">
            Flights from {origin} → {destination}
          </h1>
          <p className="text-orange-100 text-sm">
            {filteredFlights.length} flights found
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-10 grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-1">
          <Sidebar />
        </div>

        <motion.div
          className="lg:col-span-3 space-y-4"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.06 } },
          }}
        >
          {filteredFlights.length === 0 ? (
            <div className="text-center py-24 text-gray-500">
              <Plane className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="font-display text-lg text-gray-400">
                No outbound flights available
              </p>
              <p className="text-sm mt-1">
                Try adjusting your search criteria
              </p>
            </div>
          ) : (
            filteredFlights.map((flight, index) => (
              <FlightPriceCard
                key={flight.groupId || flight.ResultIndex || index}
                flight={flight}
                onViewFares={handleViewFares}
              />
            ))
          )}
        </motion.div>

        <div className="lg:col-span-1 hidden lg:block">
          <Offers />
        </div>
      </div>

      {selectedFlight && (
        <FareModal
          flight={selectedFlight}
          passengers={passengers}
          onClose={() => setSelectedFlight(null)}
        />
      )}
    </div>
  );
}