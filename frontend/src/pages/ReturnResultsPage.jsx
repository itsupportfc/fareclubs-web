import React, { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useFlightStore from "../store/useFlightStore";
import Navbar from "../components/Home/Navbar";
import SmallSearch from "../components/search/SmallSearch";
import Sidebar from "../components/search/Sidebar";
import LoaderOverlay from "../components/common/LoaderOverlay";
import ReturnFareModal from "../components/search/ReturnFareModal";

/* ================= HELPERS ================= */
const getLowestFare = (flight) =>
  flight?.fares?.find(f => f.totalPrice === flight.lowestPrice) ||
  flight?.fares?.[0];

const getLegs = (flight) =>
  getLowestFare(flight)?.segments?.[0] || [];

const formatTime = (t) =>
  new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const formatDuration = (m = 0) =>
  `${Math.floor(m / 60)}h ${m % 60}m`;

const getFlightBaggage = (flight) => {
  const legs = getLegs(flight);
  const first = legs[0];
  return {
    cabin: first?.cabinBaggage || 0,
    checkin: first?.checkedBaggage || 0,
  };
};

/* ================= PAGE ================= */
export default function ReturnResultsPage() {
  const navigate = useNavigate();
  const flightStore = useFlightStore();

  const {
    outboundFlights = [],
    inboundFlights = [],
    adults,
    children,
    infants,
    isLoading,
    isInternationalReturn,
    getSelectedFlight,
    setSelectedFlight,
  } = flightStore;

  const farePassengers = adults + children;

  // sync selected flights with store for persistence
  const [selectedOutbound, setSelectedOutboundState] = useState(getSelectedFlight()?.outbound || null);
  const [selectedInbound, setSelectedInboundState] = useState(getSelectedFlight()?.inbound || null);
  const [showFareModal, setShowFareModal] = useState(false);
  const [detailsFlight, setDetailsFlight] = useState(null);
  const [detailsTab, setDetailsTab] = useState("itinerary");

  // persist selections in store cache
  const setSelectedOutbound = (flight) => {
    setSelectedOutboundState(flight);
    setSelectedFlight({ outbound: flight, inbound: selectedInbound });
  };

  const setSelectedInbound = (flight) => {
    setSelectedInboundState(flight);
    setSelectedFlight({ outbound: selectedOutbound, inbound: flight });
  };

  const totalPrice = useMemo(() => {
    const out = selectedOutbound?.lowestPrice || 0;
    const ret = selectedInbound?.lowestPrice || 0;
    return (out + ret) * farePassengers;
  }, [selectedOutbound, selectedInbound, farePassengers]);

  if (isLoading) return <LoaderOverlay />;

  return (
    <div className="min-h-screen bg-gray-50 mt-16 pb-40">
      <Navbar />

      {/* Header */}
      <div className="bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white">
        <div className="max-w-7xl mx-auto px-4 py-5">
          <SmallSearch />
          <h1 className="text-2xl font-bold mt-2">Round-trip Flights</h1>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-10 flex gap-6">
        <div className="hidden md:block w-72">
          <Sidebar
            outboundFlights={outboundFlights}
            inboundFlights={inboundFlights}
          />
        </div>

        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
          <FlightColumn
            title="Departure"
            flights={outboundFlights}
            selected={selectedOutbound}
            onSelect={setSelectedOutbound}
            onDetails={setDetailsFlight}
            farePassengers={farePassengers}
          />

          <FlightColumn
            title="Return"
            flights={inboundFlights}
            selected={selectedInbound}
            onSelect={setSelectedInbound}
            onDetails={setDetailsFlight}
            farePassengers={farePassengers}
          />
        </div>
      </div>

      {/* ================= STICKY FOOTER ================= */}
      {(selectedOutbound || selectedInbound) && (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#0B1D33] text-white px-6 py-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex gap-6">
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
            </div>

            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-2xl font-bold">
                  ₹{totalPrice.toLocaleString("en-IN")}
                </div>
                <div className="text-sm text-gray-300">
                  for {farePassengers} passenger{farePassengers > 1 ? "s" : ""}
                  {infants > 0 && ` + ${infants} infant`}
                </div>
              </div>

              {/* Disable BOOK NOW if seats not assigned for all passengers */}
              <button
                onClick={() => setShowFareModal(true)}
                className={`px-8 py-3 rounded-full font-semibold ${
                  selectedOutbound && selectedInbound
                    ? "bg-blue-500"
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

      {/* ================= DETAILS MODAL ================= */}
      {detailsFlight && (
        <FlightDetailsModal
          flight={detailsFlight}
          tab={detailsTab}
          setTab={setDetailsTab}
          farePassengers={farePassengers}
          onClose={() => setDetailsFlight(null)}
        />
      )}

      {/* ================= FARE MODAL ================= */}
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
function FlightColumn({ title, flights, selected, onSelect, onDetails, farePassengers }) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      {flights.map(f => (
        <FlightCard
          key={f.groupId}
          flight={f}
          isSelected={selected?.groupId === f.groupId}
          onSelect={onSelect}
          onShowDetails={onDetails}
          farePassengers={farePassengers}
        />
      ))}
    </div>
  );
}

/* ================= FLIGHT CARD ================= */
function FlightCard({ flight, isSelected, onSelect, onShowDetails, farePassengers }) {
  const legs = getLegs(flight);
  const first = legs[0];
  const last = legs[legs.length - 1];

  return (
    <div
      onClick={() => onSelect(flight)}
      className={`p-4 mb-4 rounded-xl border cursor-pointer ${
        isSelected ? "border-blue-500 bg-blue-50" : "bg-white"
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
              {formatTime(first.departureTime)} → {formatTime(last.arrivalTime)}
            </div>
            <div className="text-sm text-gray-600">
              {first.departure.code} → {last.arrival.code} ·{" "}
              {flight.noOfStops === 0 ? "Non-stop" : `${flight.noOfStops} stop`}
            </div>
            <div className="text-xs text-gray-500">
              {first.carrier.name} · {first.flightNumber}
            </div>
          </div>
        </div>

        <div className="font-bold">
          ₹{(flight.lowestPrice * farePassengers).toLocaleString("en-IN")}
        </div>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          onShowDetails(flight);
        }}
        className="text-blue-600 text-sm mt-2 underline"
      >
        Flight Details
      </button>
    </div>
  );
}

/* ================= FOOTER FLIGHT ================= */
function FooterFlight({ title, flight, onShowDetails }) {
  const legs = getLegs(flight);
  const first = legs[0];
  const last = legs[legs.length - 1];

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
          {formatTime(first.departureTime)} → {formatTime(last.arrivalTime)}
        </div>
        <button
          onClick={() => onShowDetails(flight)}
          className="text-blue-400 text-sm underline"
        >
          Flight Details
        </button>
      </div>
    </div>
  );
}

/* ================= DETAILS MODAL ================= */
function FlightDetailsModal({ flight, tab, setTab, farePassengers, onClose }) {
  const fare = getLowestFare(flight);
  const legs = getLegs(flight);

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex justify-center items-center">
      <div className="bg-white max-w-3xl w-full rounded-xl overflow-hidden">
        <div className="flex justify-between p-4 border-b">
          <h2 className="font-bold">
            {flight.origin} → {flight.destination}
          </h2>
          <button onClick={onClose}>✕</button>
        </div>

        <div className="flex border-b">
          {["itinerary", "fare", "cancellation"].map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-3 font-semibold ${
                tab === t ? "border-b-2 border-blue-600 text-blue-600" : ""
              }`}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        <div className="p-4 max-h-96 overflow-y-auto">
          {tab === "itinerary" &&
            legs.map((l, i) => (
              <div key={i} className="border rounded-lg p-4 mb-3">
                <div className="font-semibold">
                  {l.departure.city} → {l.arrival.city}
                </div>
                <div className="text-sm text-gray-600">
                  {l.carrier.name} · {l.flightNumber}
                </div>
                <div className="text-sm">
                  {formatTime(l.departureTime)} – {formatTime(l.arrivalTime)}
                </div>
                <div className="text-xs text-gray-500">
                  Baggage: {l.checkedBaggage}kg · Cabin: {l.cabinBaggage}kg
                </div>
                {l.layoverMinutes > 0 && (
                  <div className="text-xs text-orange-600 mt-1">
                    Layover: {formatDuration(l.layoverMinutes)}
                  </div>
                )}
              </div>
            ))}

          {tab === "fare" && (
            <>
              <p>Base Fare: ₹{fare.baseFare * farePassengers}</p>
              <p>Taxes: ₹{fare.taxes * farePassengers}</p>
              <p className="font-semibold mt-2">
                Total: ₹{fare.totalPrice * farePassengers}
              </p>
            </>
          )}

          {tab === "cancellation" && (
            <p className="text-gray-600">
              {fare.refundable ? "Refundable" : "Non-refundable"} as per airline policy
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
