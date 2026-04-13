import React, { useState } from "react";
import { X, Star, Plane, Luggage, UtensilsCrossed } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getFareQuoteAPI } from "../api/flight";
import { toast } from "sonner";
import FareQuoteOverlay from "../common/FareQuoteOverlay";

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


  const segments =
    flight.segments ||
    fares[0]?.segments ||
    actualFlight.segments ||
    [];

  const firstSegment = segments[0];
  const lastSegment = segments[segments.length - 1];

  const stopsCount =
    flight.stopsCount ??
    actualFlight.noOfStops ??
    Math.max(0, segments.length - 1);

  const formatTime = (d) =>
    new Date(d).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });

  const formatDate = (d) =>
    new Date(d).toLocaleDateString("en-IN", {
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "2-digit",
    });

  const navigateToBooking = (fare, quoteResponse, newPrice) => {
    const fareIdOutbound = fare?.fareId || fare?.FareId;
    navigate("/booking", {
      state: {
        outboundFlight: {
          ...actualFlight,
          segments,
          stopsCount,
        },
        outboundSelectedFare: {
          ...fare,
          fareId: fareIdOutbound,
          totalPrice: newPrice,
        },
        returnSelectedFare: null,
        passengers,
        perPassengerFares: quoteResponse?.perPassengerFaresOutbound || [],
        fareQuoteFlags: quoteResponse?.flagsOutbound || null,
      },
    });
  };

  const handleBookNow = async (fare) => {
    try {
      const fareIdOutbound = fare?.fareId || fare?.FareId;
      if (!fareIdOutbound) throw new Error("fareIdOutbound is required");

      setLoadingFareId(fareIdOutbound);
      setPriceChange(null);
      setTimeChanged(null);

      const payload = {
        tripType: "oneway",
        fareIdOutbound,
        initialPriceOutbound: fare.totalPrice,
        fareIdInbound: "",
        initialPriceInbound: 0,
      };

      const quoteResponse = await getFareQuoteAPI(payload);
      const newPrice = quoteResponse?.outbound?.newPrice ?? fare.totalPrice;

      if (quoteResponse?.isPriceChanged && quoteResponse?.outbound) {
        setPriceChange({
          fareId: fareIdOutbound,
          oldPrice: fare.totalPrice,
          newPrice,
          fare,
          quoteResponse,
        });
        setLoadingFareId(null);
        return;
      }

      if (quoteResponse?.isTimeChangedOutbound) {
        setTimeChanged({ fareId: fareIdOutbound, fare, quoteResponse, newPrice });
        setLoadingFareId(null);
        return;
      }

      navigateToBooking(fare, quoteResponse, newPrice);
    } catch (err) {
      console.error("Fare Quote Error:", err);
      toast.error(err.message || "Unable to verify fare price");
    } finally {
      setLoadingFareId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex justify-center items-center">
      <FareQuoteOverlay isVisible={!!loadingFareId} />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        className="bg-white w-full max-w-6xl rounded-2xl shadow-2xl relative overflow-hidden"
      >
        {/* HEADER */}
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="font-display text-lg">
            Flight Details & Fare Options
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors duration-200"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* FLIGHT SUMMARY */}
        <div className="px-6 py-4 bg-gray-50 border-b flex flex-wrap items-center gap-4 text-sm text-gray-700">
          <div className="flex items-center gap-2 font-display font-semibold text-gray-900">
            {firstSegment?.origin}
            <Plane className="w-4 h-4" />
            {lastSegment?.destination}
          </div>

          <div className="flex items-center gap-2">
            {firstSegment?.carrier?.code && (
              <img
                src={`https://pics.avs.io/60/60/${firstSegment.carrier.code}.png`}
                alt={firstSegment?.carrier?.name}
                className="w-6 h-6 object-contain"
                onError={(e) => (e.target.style.display = "none")}
              />
            )}
            <span>{firstSegment?.carrier?.name}</span>
          </div>

          <div>{formatDate(firstSegment?.departureTime)}</div>

          <div className="font-medium">
            {formatTime(firstSegment?.departureTime)} –{" "}
            {formatTime(lastSegment?.arrivalTime)}
          </div>

          <div className="text-gray-600">
            {Math.floor(actualFlight.totalDurationMinutes / 60)}h{" "}
            {actualFlight.totalDurationMinutes % 60}m ·{" "}
            {stopsCount === 0
              ? "Non Stop"
              : `${stopsCount} Stop${stopsCount > 1 ? "s" : ""}`}
          </div>
        </div>

        {/* PRICE CHANGE BANNER */}
        {priceChange && (
          <div className="mx-6 mt-4 bg-amber-50 border border-amber-300 rounded-xl p-4">
            <p className="text-sm font-semibold text-amber-800 mb-2">
              Fare price has changed
            </p>
            <div className="flex items-center gap-4 text-sm mb-3">
              <span className="text-gray-500 line-through">
                ₹{priceChange.oldPrice.toLocaleString("en-IN")}
              </span>
              <span className="font-display text-lg font-bold text-amber-900">
                ₹{priceChange.newPrice.toLocaleString("en-IN")}
              </span>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  navigateToBooking(
                    priceChange.fare,
                    priceChange.quoteResponse,
                    priceChange.newPrice
                  );
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors duration-200"
              >
                Continue with new price
              </button>
              <button
                onClick={() => {
                  setPriceChange(null);
                  onClose?.();
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors duration-200"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* TIME CHANGE BANNER */}
        {timeChanged && (
          <div className="mx-6 mt-4 bg-amber-50 border border-amber-300 rounded-xl p-4">
            <p className="text-sm font-semibold text-amber-800 mb-2">
              Flight schedule has changed
            </p>
            <p className="text-sm text-amber-700 mb-3">
              The airline has updated the flight timing. Would you like to continue?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  navigateToBooking(
                    timeChanged.fare,
                    timeChanged.quoteResponse,
                    timeChanged.newPrice
                  );
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors duration-200"
              >
                Continue
              </button>
              <button
                onClick={() => {
                  setTimeChanged(null);
                  onClose?.();
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors duration-200"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* FARE OPTIONS */}
        <div className="p-6 overflow-x-auto">
          <div className="flex gap-6 min-w-max">
            {fares.map((fare, idx) => {
              const fareId = fare?.fareId || fare?.FareId;
              const firstLeg = fare?.segments?.[0]?.[0];

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.08 }}
                  className={`relative w-[300px] rounded-2xl border p-5 flex flex-col transition-all duration-200 hover:shadow-lg ${
                    fare.isRecommended
                      ? "border-blue-500 ring-1 ring-blue-500"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  {fare.isRecommended && (
                    <div className="absolute -top-3 left-4 bg-blue-600 text-white text-xs px-3 py-1 rounded-full flex gap-1 items-center">
                      <Star className="w-3 h-3 fill-white" />
                      Recommended
                    </div>
                  )}

                  <p className="font-display text-2xl font-bold">
                    ₹{fare.totalPrice.toLocaleString("en-IN")}
                  </p>

                  <p className="text-sm font-semibold uppercase mt-1">
                    {fare.fareType}
                  </p>

                  {/* FEATURES */}
                  <div className="mt-4 space-y-3 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Luggage className="w-4 h-4 text-gray-500" />
                      <span>
                        Cabin:{" "}
                        <span className="font-medium">
                          {firstLeg?.cabinBaggage || "7 KG"}
                        </span>
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Luggage className="w-4 h-4 text-gray-500" />
                      <span>
                        Check-in:{" "}
                        <span className="font-medium">
                          {firstLeg?.checkedBaggage || "15 KG"}
                        </span>
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <UtensilsCrossed className="w-4 h-4 text-gray-500" />
                      <span>
                        Meals:{" "}
                        <span className="font-medium">
                          {fare?.mealIncluded ? "Included" : "Not Included"}
                        </span>
                      </span>
                    </div>
                  </div>

                  <div className="my-4 border-t" />

                  <button
                    disabled={!!loadingFareId}
                    onClick={() => handleBookNow(fare)}
                    className="mt-2 bg-pink-600 hover:bg-blue-700 text-white py-2.5 rounded-xl font-semibold disabled:opacity-60 transition-colors duration-200"
                  >
                    {loadingFareId === fareId
                      ? "CHECKING PRICE..."
                      : "BOOK NOW"}
                  </button>
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.div>
    </div>
  );
}