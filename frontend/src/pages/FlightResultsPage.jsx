import { useState } from "react";
import useFlightStore from "../store/useFlightStore";
import Navbar from "../components/Home/Navbar";
import Sidebar from "../components/search/Sidebar";
import SmallSearch from "../components/search/SmallSearch";
import FlightPriceCard from "../components/search/FlightPriceCard";
import Offers from "../components/search/Offers";
import LoaderOverlay from "../components/common/LoaderOverlay";
import FareModal from "../components/search/FareModal";

export default function FlightResultsPage() {
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

  /* -------------------------------------------
     HANDLE FARE VIEW (STORE SELECTED FLIGHT)
  -------------------------------------------- */
  const handleViewFares = (flight) => {
    setSelectedFlight(flight);

    // ✅ cache selected flight
    setCache("selectedFlight", flight);
  };

  if (isLoading) return <LoaderOverlay />;

  return (
    <div className="min-h-screen bg-gray-50 mt-16">
      <Navbar />

      {/* HEADER */}
      <div className="bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white">
        <div className="max-w-7xl mx-auto px-4 py-5 space-y-2">
          <SmallSearch />
          <h1 className="text-2xl md:text-3xl font-bold">
            Flights from {origin} → {destination}
          </h1>
          <p className="text-orange-100 text-sm">
            {outboundFlights.length} flights found
          </p>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="max-w-7xl mx-auto px-4 py-10 grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-1">
          <Sidebar />
        </div>

        <div className="lg:col-span-3 space-y-4">
          {outboundFlights.length === 0 ? (
            <div className="text-center py-24 text-gray-500">
              No outbound flights available
            </div>
          ) : (
            outboundFlights.map((flight) => (
              <FlightPriceCard
                key={flight.groupId}
                flight={flight}
                onViewFares={handleViewFares} // ✅ cached here
              />
            ))
          )}
        </div>

        <div className="lg:col-span-1 hidden lg:block">
          <Offers />
        </div>
      </div>

      {/* FARE MODAL */}
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
