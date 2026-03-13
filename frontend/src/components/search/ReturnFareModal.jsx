import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { getFareQuoteAPI } from "../api/flight";
import { toast } from "sonner";
import useFlightStore from "../../store/useFlightStore";
import FareQuoteOverlay from "../common/FareQuoteOverlay";

export default function ReturnFareModal({
  outboundFlight,
  returnFlight,
  outboundBaggage,
  returnBaggage,
  isInternationalReturn = false,
}) {
  const navigate = useNavigate();
  const { adults, children, infants, setCache, getCache } = useFlightStore();

  const farePassengers = adults + children;

  const cachedSelectedFare = getCache("selectedFare") || { outbound: null, return: null };
  const [activeTab, setActiveTab] = useState("outbound");
  const [selectedFare, setSelectedFare] = useState(cachedSelectedFare);
  const [loading, setLoading] = useState(false);

  const getFares = (flight) => Array.isArray(flight?.fares) ? flight.fares : [];

  const outboundFares = getFares(outboundFlight);
  const returnFares = getFares(returnFlight);

  const fares = activeTab === "outbound" ? outboundFares : returnFares;
  const selected = activeTab === "outbound" ? selectedFare.outbound : selectedFare.return;

  const activeBaggage = activeTab === "outbound" ? outboundBaggage : returnBaggage;

  const formatTime = (t) =>
    new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const handleSelectFare = (fare) => {
    const updated = { ...selectedFare, [activeTab]: fare };
    setSelectedFare(updated);
    setCache("selectedFare", updated);
  };

  const totalPrice = useMemo(() => {
    if (!selectedFare.outbound || !selectedFare.return) return 0;
    return (selectedFare.outbound.totalPrice + selectedFare.return.totalPrice) * farePassengers;
  }, [selectedFare, farePassengers]);

  const handleContinue = async () => {
    if (!selectedFare.outbound || !selectedFare.return) {
      toast.error("Please select fare for both outbound & return flights");
      return;
    }

    try {
      setLoading(true);
      const payload = {
        tripType: "roundtrip",
        fareIdOutbound: selectedFare.outbound.fareId,
        initialPriceOutbound: selectedFare.outbound.totalPrice,
        fareIdInbound: selectedFare.return.fareId,
        initialPriceInbound: selectedFare.return.totalPrice,
      };

      const quoteResponse = await getFareQuoteAPI(payload);

      // Handle time change
      if (quoteResponse?.isTimeChangedOutbound || quoteResponse?.isTimeChangedInbound) {
        const confirmTime = window.confirm(
          "Flight schedule has changed. Do you want to continue?"
        );
        if (!confirmTime) {
          setLoading(false);
          return;
        }
      }

      const outboundFinalPrice = quoteResponse?.outbound?.newPrice ?? selectedFare.outbound.totalPrice;
      const returnFinalPrice = quoteResponse?.inbound?.newPrice ?? selectedFare.return.totalPrice;

      navigate("/booking", {
        state: {
          outboundFlight,
          returnFlight,
          isInternationalReturn,
          outboundSelectedFare: {
            fareId: selectedFare.outbound.fareId,
            fareType: selectedFare.outbound.fareType,
            segments: selectedFare.outbound.segments,
            totalPrice: outboundFinalPrice,
            baseFare: selectedFare.outbound.baseFare,
            taxes: selectedFare.outbound.taxes,
            fareQuote: quoteResponse?.outbound || null,
          },
          returnSelectedFare: {
            fareId: selectedFare.return.fareId,
            fareType: selectedFare.return.fareType,
            segments: selectedFare.return.segments,
            totalPrice: returnFinalPrice,
            baseFare: selectedFare.return.baseFare,
            taxes: selectedFare.return.taxes,
            fareQuote: quoteResponse?.inbound || null,
          },
          passengers: { adults, children, infants },
          perPassengerFaresOutbound: quoteResponse?.perPassengerFaresOutbound || [],
          perPassengerFaresInbound: quoteResponse?.perPassengerFaresInbound || [],
          fareQuoteFlagsOutbound: quoteResponse?.flagsOutbound || null,
          fareQuoteFlagsInbound: quoteResponse?.flagsInbound || null,
        },
      });
    } catch (err) {
      console.error("Fare Quote Error:", err);
      toast.error("Unable to verify fare. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const summary = outboundFlight?.fares?.length
    ? {
        first: outboundFlight.fares[0].segments?.[0][0],
        last: outboundFlight.fares[0].segments?.[0].slice(-1)[0],
      }
    : null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex justify-center pt-16">
      <FareQuoteOverlay isVisible={loading} />
      <div className="bg-white w-full max-w-6xl rounded-xl p-6 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Fare Options</h2>
          <button onClick={() => navigate(-1)} className="text-xl">✕</button>
        </div>

        {summary && (
          <div className="mb-4 text-sm font-semibold flex gap-2 items-center">
            <span>
              {summary.first.departure.city} → {summary.last.arrival.city}
            </span>
            <span>
              · {formatTime(summary.first.departureTime)} – {formatTime(summary.last.arrivalTime)}
            </span>
          </div>
        )}

        <div className="flex gap-6 mb-6 border-b">
          {["outbound", "return"].map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={`pb-2 font-semibold ${
                activeTab === t
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500"
              }`}
            >
              {t === "outbound" ? "Outbound" : "Return"}
            </button>
          ))}
        </div>

        <div className="flex gap-4 overflow-x-auto">
          {fares.map((fare) => (
            <FareCard
              key={fare.fareId}
              fare={fare}
              baggage={activeBaggage}
              isSelected={selected?.fareId === fare.fareId}
              onSelect={() => handleSelectFare(fare)}
              farePassengers={farePassengers}
            />
          ))}
        </div>

        <div className="mt-6 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {farePassengers} passenger{farePassengers > 1 ? "s" : ""}
            {infants > 0 && ` + ${infants} infant`}
          </div>

          <div className="flex items-center gap-6">
            <div className="text-xl font-bold">
              ₹{totalPrice.toLocaleString("en-IN")}
            </div>

            <button
              onClick={handleContinue}
              disabled={!selectedFare.outbound || !selectedFare.return || loading}
              className={`px-6 py-3 rounded-lg text-white font-bold ${
                selectedFare.outbound && selectedFare.return && !loading
                  ? "bg-blue-600 hover:bg-blue-700"
                  : "bg-gray-400 cursor-not-allowed"
              }`}
            >
              {loading ? "Checking..." : "Continue"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function FareCard({ fare, baggage, isSelected, onSelect, farePassengers }) {
  return (
    <div
      className={`min-w-[320px] border rounded-xl p-4 transition ${
        isSelected ? "border-blue-600 shadow-lg" : "border-gray-300"
      }`}
    >
      <p className="text-2xl font-bold text-center">
        ₹{(fare.totalPrice * farePassengers).toLocaleString("en-IN")}
      </p>

      <p className="text-center text-sm text-gray-500">
        ₹{fare.totalPrice} × {farePassengers} passenger{farePassengers > 1 ? "s" : ""}
      </p>

      <p className="mt-2 text-center font-semibold">{fare.fareType}</p>

      <div className="text-xs text-gray-500 text-center mt-1">
        Baggage: {baggage?.checkin}kg · Cabin: {baggage?.cabin}kg
      </div>

      <button
        onClick={onSelect}
        className={`mt-4 w-full py-2 rounded-lg text-white font-semibold ${
          isSelected ? "bg-pink-800" : "bg-pink-600 hover:bg-pink-700"
        }`}
      >
        {isSelected ? "SELECTED" : "SELECT"}
      </button>
    </div>
  );
}
