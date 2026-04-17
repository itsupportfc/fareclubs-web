import React, { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import useFlightStore from "../store/useFlightStore";
import Navbar from "../components/Home/Navbar";
import SmallSearch from "../components/search/SmallSearch";
import Sidebar from "../components/search/Sidebar";
import ReturnFareModal from "../components/search/ReturnFareModal";
import FlightSearchLoader from "../components/common/FlightSearchLoader";
import { useTripConfig } from "../hooks/useTripConfig";
import { filterFlights } from "../utils/flightFilters";
import { useShallow } from "zustand/react/shallow";

/* ================= HELPERS ================= */
const getLowestFare = (flight) =>
    flight?.fares?.find((f) => f.totalPrice === flight.lowestPrice) ||
    flight?.fares?.[0];

const getLegs = (flight) => getLowestFare(flight)?.segments?.[0] || [];

const getPrimaryLegs = (flight) => getLowestFare(flight)?.segments?.[0] || [];

const getPrimarySegment = (flight) => getPrimaryLegs(flight)?.[0];

const formatTime = (t) =>
    new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const formatDuration = (m = 0) => `${Math.floor(m / 60)}h ${m % 60}m`;

const getFlightBaggage = (flight) => {
    const legs = getLegs(flight);
    const first = legs[0];
    return {
        cabin: first?.cabinBaggage || 0,
        checkin: first?.checkedBaggage || 0,
    };
};

// Extract inbound legs from a clubbed international return fare.
// For domestic flights, segments[1] doesn't exist → returns [].
const getReturnLegs = (flight) => getLowestFare(flight)?.segments?.[1] || [];

/* ================= PAGE ================= */
export default function ReturnResultsPage() {
    const {
        outboundFlights,
        inboundFlights,
        adults,
        children,
        infants,
        isLoading,
        isInternationalReturn,
        getSelectedFlight,
        setSelectedFlight,
        filters,
    } = useFlightStore(
        useShallow((s) => ({
            outboundFlights: s.outboundFlights,
            inboundFlights: s.inboundFlights,
            adults: s.adults,
            children: s.children,
            infants: s.infants,
            isLoading: s.isLoading,
            isInternationalReturn: s.isInternationalReturn,
            getSelectedFlight: s.getSelectedFlight,
            setSelectedFlight: s.setSelectedFlight,
            filters: s.filters,
        })),
    );

    const farePassengers = adults + children;

    const tripConfig = useTripConfig({
        tripType: "roundtrip",
        isInternationalReturn,
    });

    const [selectedOutbound, setSelectedOutboundState] = useState(
        getSelectedFlight()?.outbound || null,
    );
    const [selectedInbound, setSelectedInboundState] = useState(
        getSelectedFlight()?.inbound || null,
    );
    const [showFareModal, setShowFareModal] = useState(false);
    const [detailsFlight, setDetailsFlight] = useState(null);
    const [detailsTab, setDetailsTab] = useState("itinerary");

    const setSelectedOutbound = (flight) => {
        setSelectedOutboundState(flight);
        setSelectedFlight({ outbound: flight, inbound: selectedInbound });
    };

    const setSelectedInbound = (flight) => {
        setSelectedInboundState(flight);
        setSelectedFlight({ outbound: selectedOutbound, inbound: flight });
    };

    // International return: one flight = both directions.
    const handleInternationalSelect = (flight) => {
        setSelectedOutboundState(flight);
        setSelectedInboundState(flight);
        setSelectedFlight({ outbound: flight, inbound: flight });
    };

    // Pass 1: outbound filters + price (applies to all trip types)
    const outboundFiltered = useMemo(
        () =>
            filterFlights(outboundFlights, filters.outbound, filters.maxPrice),
        [outboundFlights, filters],
    );

    // Pass 2 (international return only): inbound filters on the already-filtered array.
    // Reads segments[1] for stop count / departure time / carrier via direction="inbound".
    // Price is null — already checked in pass 1.
    const filteredOutboundFlights = useMemo(
        () =>
            isInternationalReturn
                ? filterFlights(
                      outboundFiltered,
                      filters.inbound,
                      null,
                      "inbound",
                  )
                : outboundFiltered,
        [outboundFiltered, filters.inbound, isInternationalReturn],
    );

    // Domestic return: inboundFlights is an independent list, filter it separately.
    // International return: inboundFlights is always [] — nothing to filter.
    const filteredInboundFlights = useMemo(
        () =>
            isInternationalReturn
                ? []
                : filterFlights(
                      inboundFlights,
                      filters.inbound,
                      filters.maxPrice,
                  ),
        [inboundFlights, filters, isInternationalReturn],
    );

    useEffect(() => {
        if (
            selectedOutbound &&
            !filteredOutboundFlights.some(
                (f) => f.groupId === selectedOutbound.groupId,
            )
        ) {
            setSelectedOutboundState(null);

            if (tripConfig.hasSeparateLists) {
                setSelectedFlight({
                    outbound: null,
                    inbound: selectedInbound,
                });
            } else {
                setSelectedInboundState(null);
                setSelectedFlight({
                    outbound: null,
                    inbound: null,
                });
            }
        }
    }, [
        selectedOutbound,
        selectedInbound,
        filteredOutboundFlights,
        tripConfig.hasSeparateLists,
        setSelectedFlight,
    ]);

    useEffect(() => {
        if (
            tripConfig.hasSeparateLists &&
            selectedInbound &&
            !filteredInboundFlights.some(
                (f) => f.groupId === selectedInbound.groupId,
            )
        ) {
            setSelectedInboundState(null);
            setSelectedFlight({
                outbound: selectedOutbound,
                inbound: null,
            });
        }
    }, [
        tripConfig.hasSeparateLists,
        selectedInbound,
        selectedOutbound,
        filteredInboundFlights,
        setSelectedFlight,
    ]);

    const totalPrice = useMemo(() => {
        return tripConfig.getDisplayPrice(selectedOutbound, selectedInbound);
    }, [selectedOutbound, selectedInbound, tripConfig]);

    return (
        <div className="min-h-screen bg-gray-50 mt-16 pb-40">
            <Navbar />

            <div className="bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white">
                <div className="max-w-7xl mx-auto px-4 py-5">
                    <SmallSearch />
                    <h1 className="font-display text-2xl mt-2">
                        Round-trip Flights
                    </h1>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-10 flex gap-6">
                <div className="hidden md:block w-72">
                    <Sidebar
                        outboundFlights={outboundFlights}
                        inboundFlights={inboundFlights}
                    />
                </div>

                {tripConfig.hasSeparateLists ? (
                    <div className="flex-1">
                        {isLoading ? (
                            <FlightSearchLoader columns={2} />
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <FlightColumn
                                    title="Departure"
                                    flights={filteredOutboundFlights}
                                    selected={selectedOutbound}
                                    onSelect={setSelectedOutbound}
                                    onDetails={setDetailsFlight}
                                />
                                <FlightColumn
                                    title="Return"
                                    flights={filteredInboundFlights}
                                    selected={selectedInbound}
                                    onSelect={setSelectedInbound}
                                    onDetails={setDetailsFlight}
                                />
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex-1">
                        <h2 className="font-display text-xl mb-4">
                            Round-trip Flights
                        </h2>
                        {isLoading ? (
                            <FlightSearchLoader />
                        ) : (
                            <div>
                                {filteredOutboundFlights.map((f) => (
                                    <InternationalFlightCard
                                        key={f.groupId}
                                        flight={f}
                                        isSelected={
                                            selectedOutbound?.groupId === f.groupId
                                        }
                                        onSelect={handleInternationalSelect}
                                        onShowDetails={setDetailsFlight}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {(selectedOutbound || selectedInbound) && (
                <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#0B1D33] text-white px-6 py-4">
                    <div className="max-w-7xl mx-auto flex justify-between items-center">
                        <div className="flex gap-6">
                            {tripConfig.hasSeparateLists ? (
                                <>
                                    {selectedOutbound && (
                                        <FooterFlight
                                            title="Departure"
                                            flight={selectedOutbound}
                                            onShowDetails={setDetailsFlight}
                                        />
                                    )}
                                    {selectedInbound && (
                                        <FooterFlight
                                            title="Return"
                                            flight={selectedInbound}
                                            onShowDetails={setDetailsFlight}
                                        />
                                    )}
                                </>
                            ) : (
                                selectedOutbound && (
                                    <>
                                        <FooterFlight
                                            title="Departure"
                                            flight={selectedOutbound}
                                            legs={getLegs(selectedOutbound)}
                                            onShowDetails={setDetailsFlight}
                                        />
                                        <FooterFlight
                                            title="Return"
                                            flight={selectedOutbound}
                                            legs={getReturnLegs(
                                                selectedOutbound,
                                            )}
                                            onShowDetails={setDetailsFlight}
                                        />
                                    </>
                                )
                            )}
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="text-right">
                                <div className="font-display text-2xl font-bold">
                                    ₹{totalPrice.toLocaleString("en-IN")}
                                </div>
                                <div className="text-sm text-gray-300">
                                    for {farePassengers} passenger
                                    {farePassengers > 1 ? "s" : ""}
                                    {infants > 0 && ` + ${infants} infant`}
                                </div>
                            </div>

                            <button
                                onClick={() => setShowFareModal(true)}
                                className={`px-8 py-3 rounded-full font-semibold transition-colors duration-200 ${
                                    selectedOutbound && selectedInbound
                                        ? "bg-blue-500 hover:bg-blue-600"
                                        : "bg-gray-400 cursor-not-allowed"
                                }`}
                                disabled={!selectedOutbound || !selectedInbound}
                            >
                                BOOK NOW
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {detailsFlight && (
                <FlightDetailsModal
                    flight={detailsFlight}
                    tab={detailsTab}
                    setTab={setDetailsTab}
                    onClose={() => setDetailsFlight(null)}
                />
            )}

            {showFareModal && (
                <ReturnFareModal
                    outboundFlight={selectedOutbound}
                    returnFlight={selectedInbound}
                    outboundBaggage={getFlightBaggage(selectedOutbound)}
                    returnBaggage={getFlightBaggage(selectedInbound)}
                    isInternationalReturn={isInternationalReturn}
                    onClose={() => setShowFareModal(false)}
                />
            )}
        </div>
    );
}

/* ================= COLUMN ================= */
function FlightColumn({ title, flights, selected, onSelect, onDetails }) {
    return (
        <div>
            <h2 className="font-display text-xl mb-4">{title}</h2>

            {flights.length === 0 ? (
                <div className="bg-white border border-gray-100 rounded-xl p-8 text-center text-gray-500">
                    No flights match the current filters
                </div>
            ) : (
                <div>
                    {flights.map((f) => (
                        <FlightCard
                            key={f.groupId}
                            flight={f}
                            isSelected={selected?.groupId === f.groupId}
                            onSelect={onSelect}
                            onShowDetails={onDetails}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
/* ================= FLIGHT CARD ================= */
function FlightCard({ flight, isSelected, onSelect, onShowDetails }) {
    const legs = getLegs(flight);
    const first = legs[0];
    const last = legs[legs.length - 1];

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            onClick={() => onSelect(flight)}
            className={`p-4 mb-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                isSelected
                    ? "border-blue-500 bg-blue-50 shadow-md"
                    : "bg-white border-gray-100 hover:shadow-md"
            }`}
        >
            <div className="flex justify-between items-center">
                <div className="flex gap-4">
                    <img
                        src={`https://pics.avs.io/60/60/${first.carrier.code}.png`}
                        className="w-10 h-10"
                    />
                    <div>
                        <div className="font-semibold">
                            {formatTime(first.departureTime)} →{" "}
                            {formatTime(last.arrivalTime)}
                        </div>
                        <div className="text-sm text-gray-600">
                            {first.departure.code} → {last.arrival.code} ·{" "}
                            {flight.noOfStops === 0
                                ? "Non-stop"
                                : `${flight.noOfStops} stop`}
                        </div>
                        <div className="text-xs text-gray-500">
                            {first.carrier.name} · {first.flightNumber}
                        </div>
                    </div>
                </div>

                <div className="font-display font-bold text-lg">
                    ₹{flight.lowestPrice.toLocaleString("en-IN")}
                </div>
            </div>

            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onShowDetails(flight);
                }}
                className="text-blue-600 text-sm mt-2 underline hover:text-blue-700 transition-colors duration-200"
            >
                Flight Details
            </button>
        </motion.div>
    );
}

/* ================= FOOTER FLIGHT ================= */
function FooterFlight({ title, flight, legs: legsOverride, onShowDetails }) {
    const legs = legsOverride || getLegs(flight);
    const first = legs[0];
    const last = legs[legs.length - 1];
    if (!first) return null;

    return (
        <div className="flex items-center gap-4">
            <img
                src={`https://pics.avs.io/60/60/${first.carrier.code}.png`}
                className="w-10 h-10"
            />
            <div>
                <div className="text-sm text-gray-300">
                    {title} · {first.carrier.name}
                </div>
                <div className="font-semibold">
                    {formatTime(first.departureTime)} →{" "}
                    {formatTime(last.arrivalTime)}
                </div>
                <button
                    onClick={() => onShowDetails(flight)}
                    className="text-blue-400 text-sm underline hover:text-blue-300 transition-colors duration-200"
                >
                    Flight Details
                </button>
            </div>
        </div>
    );
}

/* ================= DETAILS MODAL ================= */
function FlightDetailsModal({ flight, tab, setTab, onClose }) {
    const fare = getLowestFare(flight);
    const legs = getLegs(flight);
    const returnLegs = getReturnLegs(flight);
    const hasReturn = returnLegs.length > 0;

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-50 flex justify-center items-center"
        >
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                className="bg-white max-w-3xl w-full rounded-xl overflow-hidden"
            >
                <div className="flex justify-between p-4 border-b">
                    <h2 className="font-display font-bold text-lg">
                        {flight.origin} → {flight.destination}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 rounded-full transition-colors duration-200"
                    >
                        <svg
                            className="w-5 h-5 text-gray-500"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>

                <div className="flex border-b">
                    {["itinerary", "fare", "cancellation"].map((t) => (
                        <button
                            key={t}
                            onClick={() => setTab(t)}
                            className={`flex-1 py-3 font-semibold transition-colors duration-200 ${
                                tab === t
                                    ? "border-b-2 border-blue-600 text-blue-600"
                                    : ""
                            }`}
                        >
                            {t.toUpperCase()}
                        </button>
                    ))}
                </div>

                <div className="p-4 max-h-96 overflow-y-auto">
                    {tab === "itinerary" && (
                        <>
                            {hasReturn && (
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">
                                    Departure
                                </p>
                            )}
                            {legs.map((l, i) => (
                                <div
                                    key={`out-${i}`}
                                    className="border border-gray-100 rounded-xl p-4 mb-3"
                                >
                                    <div className="font-semibold">
                                        {l.departure.city} → {l.arrival.city}
                                    </div>
                                    <div className="text-sm text-gray-600">
                                        {l.carrier.name} · {l.flightNumber}
                                    </div>
                                    <div className="text-sm">
                                        {formatTime(l.departureTime)} –{" "}
                                        {formatTime(l.arrivalTime)}
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        Baggage: {l.checkedBaggage}kg · Cabin:{" "}
                                        {l.cabinBaggage}kg
                                    </div>
                                    {l.layoverMinutes > 0 && (
                                        <div className="text-xs text-orange-600 mt-1">
                                            Layover:{" "}
                                            {formatDuration(l.layoverMinutes)}
                                        </div>
                                    )}
                                </div>
                            ))}
                            {hasReturn && (
                                <>
                                    <p className="text-xs font-semibold text-gray-400 uppercase mb-2 mt-4">
                                        Return
                                    </p>
                                    {returnLegs.map((l, i) => (
                                        <div
                                            key={`in-${i}`}
                                            className="border border-gray-100 rounded-xl p-4 mb-3"
                                        >
                                            <div className="font-semibold">
                                                {l.departure.city} →{" "}
                                                {l.arrival.city}
                                            </div>
                                            <div className="text-sm text-gray-600">
                                                {l.carrier.name} ·{" "}
                                                {l.flightNumber}
                                            </div>
                                            <div className="text-sm">
                                                {formatTime(l.departureTime)} –{" "}
                                                {formatTime(l.arrivalTime)}
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                Baggage: {l.checkedBaggage}kg ·
                                                Cabin: {l.cabinBaggage}kg
                                            </div>
                                            {l.layoverMinutes > 0 && (
                                                <div className="text-xs text-orange-600 mt-1">
                                                    Layover:{" "}
                                                    {formatDuration(
                                                        l.layoverMinutes,
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </>
                            )}
                        </>
                    )}

                    {tab === "fare" && (
                        <>
                            <p>
                                Base Fare: ₹
                                {fare.baseFare.toLocaleString("en-IN")}
                            </p>
                            <p>Taxes: ₹{fare.taxes.toLocaleString("en-IN")}</p>
                            <p className="font-semibold mt-2">
                                Total: ₹
                                {fare.totalPrice.toLocaleString("en-IN")}
                            </p>
                        </>
                    )}

                    {tab === "cancellation" && (
                        <p className="text-gray-600">
                            {fare.refundable ? "Refundable" : "Non-refundable"}{" "}
                            as per airline policy
                        </p>
                    )}
                </div>
            </motion.div>
        </motion.div>
    );
}

/* ================= INTERNATIONAL FLIGHT CARD ================= */
function InternationalFlightCard({
    flight,
    isSelected,
    onSelect,
    onShowDetails,
}) {
    const outLegs = getLegs(flight);
    const inLegs = getReturnLegs(flight);
    const outFirst = outLegs[0];
    const outLast = outLegs.at(-1);
    const inFirst = inLegs[0];
    const inLast = inLegs.at(-1);

    if (!outFirst || !outLast) return null;
    if (!inFirst || !inLast) return null;

    const outStops = outLegs.length - 1;
    const inStops = inLegs.length - 1;

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            onClick={() => onSelect(flight)}
            className={`p-4 mb-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                isSelected
                    ? "border-blue-500 bg-blue-50 shadow-md"
                    : "bg-white border-gray-100 hover:shadow-md"
            }`}
        >
            <div className="grid grid-cols-2 gap-4">
                <div className="flex gap-3">
                    <img
                        src={`https://pics.avs.io/60/60/${outFirst.carrier.code}.png`}
                        className="w-8 h-8 mt-1"
                    />
                    <div>
                        <div className="text-xs font-semibold text-gray-400 uppercase mb-1">
                            Departure
                        </div>
                        <div className="font-semibold text-sm">
                            {formatTime(outFirst.departureTime)} →{" "}
                            {formatTime(outLast.arrivalTime)}
                        </div>
                        <div className="text-xs text-gray-600">
                            {outFirst.departure.code} → {outLast.arrival.code} ·{" "}
                            {outStops === 0 ? "Non-stop" : `${outStops} stop`}
                        </div>
                        <div className="text-xs text-gray-500">
                            {outFirst.carrier.name} · {outFirst.flightNumber}
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <img
                        src={`https://pics.avs.io/60/60/${inFirst.carrier.code}.png`}
                        className="w-8 h-8 mt-1"
                    />
                    <div>
                        <div className="text-xs font-semibold text-gray-400 uppercase mb-1">
                            Return
                        </div>
                        <div className="font-semibold text-sm">
                            {formatTime(inFirst.departureTime)} →{" "}
                            {formatTime(inLast.arrivalTime)}
                        </div>
                        <div className="text-xs text-gray-600">
                            {inFirst.departure.code} → {inLast.arrival.code} ·{" "}
                            {inStops === 0 ? "Non-stop" : `${inStops} stop`}
                        </div>
                        <div className="text-xs text-gray-500">
                            {inFirst.carrier.name} · {inFirst.flightNumber}
                        </div>
                    </div>
                </div>
            </div>
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onShowDetails(flight);
                    }}
                    className="text-blue-600 text-sm underline hover:text-blue-700 transition-colors duration-200"
                >
                    Flight Details
                </button>
                <div className="font-display font-bold text-lg">
                    ₹{flight.lowestPrice.toLocaleString("en-IN")}
                </div>
            </div>
        </motion.div>
    );
}
