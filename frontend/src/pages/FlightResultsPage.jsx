import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Plane } from "lucide-react";
import useFlightStore from "../store/useFlightStore";
import Navbar from "../components/Home/Navbar";
import Sidebar from "../components/search/Sidebar";
import SmallSearch from "../components/search/SmallSearch";
import FlightPriceCard from "../components/search/FlightPriceCard";
import Offers from "../components/search/Offers";
import FareModal from "../components/search/FareModal";
import FlightSearchLoader from "../components/common/FlightSearchLoader";
import { filterFlights } from "../utils/flightFilters";
import { useShallow } from "zustand/react/shallow";
export default function FlightResultsPage() {
    const {
        outboundFlights,
        origin,
        destination,
        adults,
        children,
        infants,
        isLoading,
        filters,
        setCache,
    } = useFlightStore(
        useShallow((s) => ({
            outboundFlights: s.outboundFlights,
            origin: s.origin,
            destination: s.destination,
            adults: s.adults,
            children: s.children,
            infants: s.infants,
            isLoading: s.isLoading,
            filters: s.filters,
            setCache: s.setCache,
        })),
    );

    const passengers = { adults, children, infants };
    const [selectedFlight, setSelectedFlight] = useState(null);

    const handleViewFares = (flight) => {
        setSelectedFlight(flight);
        if (typeof setCache === "function") {
            setCache("selectedFlight", flight);
        }
    };

    const filteredFlights = useMemo(
        () =>
            filterFlights(outboundFlights, filters.outbound, filters.maxPrice),
        [outboundFlights, filters],
    );

    // if (isLoading) return <LoaderOverlay />;

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
                    {isLoading ? (
                        <FlightSearchLoader />
                    ) : filteredFlights.length === 0 ? (
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
                        filteredFlights.map((flight) => (
                            <FlightPriceCard
                                key={flight.groupId || flight.ResultIndex}
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
