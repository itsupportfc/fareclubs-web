import React, { useMemo, useState, useEffect } from "react";
import { Plane } from "lucide-react";
import { motion } from "framer-motion";
import useFlightStore from "../../store/useFlightStore";

/* ---------- HELPERS ---------- */
const formatTime = (dt) =>
  new Date(dt).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });

const formatDate = (dt) =>
  new Date(dt).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
  });

const formatDuration = (mins = 0) => {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h ${m}m`;
};

const diffMinutes = (a, b) =>
  Math.max(0, Math.round((new Date(b) - new Date(a)) / 60000));

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

  const fareRules = fareData[fareId]?.fareRules;
  const fareQuote = fareData[fareId]?.fareQuote;

  /* ---------- FETCH FARE RULES & QUOTE ---------- */
  useEffect(() => {
    if (activeTab === "CANCELLATION" && fareId && fetchedFareId !== fareId) {
      const quotePayload = {
        fareId,
        initialPrice: lowestFare.totalPrice,
      };

      getFareRules({ fareId }).catch(console.error);
      getFareQuote(quotePayload).catch(console.error);

      setFetchedFareId(fareId);
    }
  }, [
    activeTab,
    fareId,
    fetchedFareId,
    lowestFare.totalPrice,
    getFareRules,
    getFareQuote,
  ]);

  /* ---------- VIEW FARES HANDLER ---------- */
  const handleViewFares = () => {
    const itineraryPayload = {
      flight,
      fareId,
      lowestFare,
      segments,
      airline: {
        name: airlineName,
        code: airlineCode,
      },
      totalDurationMinutes: flight.totalDurationMinutes,
      stopsCount,
    };

    setSelectedFlight(itineraryPayload);
    onViewFares(itineraryPayload);
  };

  /* ===============================
     RENDER
     =============================== */
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white border border-gray-100 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 my-3"
    >
      {/* MAIN ROW */}
      <div className="flex flex-col md:flex-row items-center justify-between px-4 py-4 gap-4">
        {/* AIRLINE */}
        <div className="flex items-center gap-3 min-w-[220px]">
          <img
            src={`https://pics.avs.io/60/60/${airlineCode}.png`}
            alt={airlineName}
            className="w-10 h-10 object-contain"
          />
          <div>
            <p className="text-sm font-semibold">{airlineName}</p>
            <p className="text-xs text-gray-500">{flightNumbers}</p>
          </div>
        </div>

        {/* TIMES */}
        <div className="flex flex-1 items-center justify-between px-2">
          <div className="text-center">
            <p className="font-semibold">
              {formatTime(firstSeg.departureTime)}
            </p>
            <p className="text-xs text-gray-500">{firstSeg.origin}</p>
          </div>

          <div className="flex flex-col items-center flex-1 relative group">
            <div className="w-full border-t relative my-2">
              <Plane className="absolute left-1/2 -translate-x-1/2 -top-3 w-4 h-4 text-pink-600" />
            </div>

            <p className="text-xs text-gray-600 cursor-pointer">
              {formatDuration(flight.totalDurationMinutes)} •{" "}
              <span className="underline decoration-dotted">
                {stopsText}
              </span>
            </p>

            {stopsCount > 0 && (
              <div className="absolute top-full mt-2 hidden group-hover:block bg-white border border-gray-100 shadow-xl rounded-xl p-3 text-xs z-10 w-56">
                {layovers.map((l, i) => (
                  <p key={i}>
                    Layover at <strong>{l.airport}</strong> • {l.duration}
                  </p>
                ))}
              </div>
            )}
          </div>

          <div className="text-center">
            <p className="font-semibold">
              {formatTime(lastSeg.arrivalTime)}
            </p>
            <p className="text-xs text-gray-500">{lastSeg.destination}</p>
          </div>
        </div>

        {/* PRICE */}
        <div className="text-right min-w-[180px]">
          <p className="font-display text-xl font-bold text-pink-600">
            ₹{lowestFare.totalPrice.toLocaleString("en-IN")}
          </p>
          <p className="text-xs uppercase tracking-wide text-gray-400">lowest price</p>

          <button
            onClick={handleViewFares}
            className="mt-2 bg-pink-600 text-white px-4 py-2 rounded-md w-full hover:bg-pink-700 transition-colors duration-200"
          >
            VIEW FARES
          </button>
        </div>
      </div>

      {/* DETAILS TOGGLE */}
      <div className="flex justify-end px-4 pb-4">
        <button
          onClick={() => setDetailsOpen(!detailsOpen)}
          className="text-blue-600 text-sm font-semibold hover:text-blue-700 transition-colors duration-200"
        >
          {detailsOpen ? "HIDE DETAILS" : "VIEW DETAILS"}
        </button>
      </div>

      {/* DETAILS PANEL */}
      {detailsOpen && (
        <div className="bg-gray-50 rounded-b-xl">
          {/* TABS */}
          <div className="flex border-b bg-white">
            {["FLIGHT", "FARE", "CANCELLATION"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-semibold transition-colors duration-200 ${
                  activeTab === tab
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-500"
                }`}
              >
                {tab === "FLIGHT"
                  ? "FLIGHT DETAILS"
                  : tab === "FARE"
                  ? "FARE SUMMARY"
                  : "CANCELLATION"}
              </button>
            ))}
          </div>

          {/* FLIGHT DETAILS */}
          {activeTab === "FLIGHT" && (
            <div className="px-4 py-4 space-y-4">
              {segments.map((seg, idx) => {
                const nextSeg = segments[idx + 1];
                const layoverMins =
                  nextSeg &&
                  diffMinutes(seg.arrivalTime, nextSeg.departureTime);

                return (
                  <div key={idx}>
                    <div className="bg-white border border-gray-100 rounded-xl p-3 flex gap-4">
                      <div className="min-w-[160px]">
                        <p className="font-semibold">
                          {seg.carrier.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {seg.carrier.code}-{seg.flightNumber}
                        </p>
                      </div>

                      <div className="flex-1 flex justify-between">
                        <div>
                          <p className="font-semibold">
                            {formatTime(seg.departureTime)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {seg.origin} •{" "}
                            {formatDate(seg.departureTime)}
                          </p>
                        </div>

                        <div className="text-xs text-gray-500">
                          {formatDuration(seg.durationMinutes)}
                        </div>

                        <div className="text-right">
                          <p className="font-semibold">
                            {formatTime(seg.arrivalTime)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {seg.destination} •{" "}
                            {formatDate(seg.arrivalTime)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {layoverMins > 0 && (
                      <div className="text-center text-xs font-semibold text-orange-600 my-2">
                        Layover at {seg.destination} •{" "}
                        {formatDuration(layoverMins)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* FARE SUMMARY */}
          {activeTab === "FARE" && (
            <div className="px-4 py-4 bg-white text-sm space-y-3">
              <div className="flex justify-between">
                <span>Base Fare</span>
                <span>₹{lowestFare.baseFare || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span>Taxes & Fees</span>
                <span>₹{lowestFare.taxes || "—"}</span>
              </div>
              <div className="border-t pt-2 flex justify-between font-semibold">
                <span>Total</span>
                <span>
                  ₹{lowestFare.totalPrice.toLocaleString("en-IN")}
                </span>
              </div>
            </div>
          )}

          {/* CANCELLATION */}
          {activeTab === "CANCELLATION" && (
            <div className="px-4 py-4 bg-white text-sm space-y-3">
              {isFareLoading && (
                <p className="text-gray-500">
                  Fetching cancellation rules...
                </p>
              )}

              {!isFareLoading && fareRules?.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">
                    Cancellation Rules
                  </h3>
                  {fareRules.map((rule, i) => (
                    <div
                      key={i}
                      className="border border-gray-100 p-3 rounded-xl mb-2"
                    >
                      <p className="font-medium">
                        {rule.Fareruledetail || "Rule"}
                      </p>
                      <p className="text-xs text-gray-500">
                        {rule.Origin} → {rule.Destination}
                      </p>
                      <p className="text-sm text-gray-700">
                        {rule.Farerestriction || "N/A"}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {!isFareLoading && fareQuote && (
                <div className="pt-3 border-t">
                  {fareQuote.Response?.IsPriceChanged ? (
                    <p className="text-red-600 font-semibold">
                      Price Updated: ₹
                      {
                        fareQuote.Response.Results.Fare
                          .PublishedFare
                      }
                    </p>
                  ) : (
                    <p className="text-green-600 font-semibold">
                      Fare is valid
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Seats Available:{" "}
                    {fareQuote?.Response?.Results?.SeatsAvailable ??
                      "N/A"}
                  </p>
                </div>
              )}

              {fareError && (
                <p className="text-red-600 text-sm">
                  {fareError}
                </p>
              )}

              {!isFareLoading &&
                !fareRules?.length &&
                !fareError && (
                  <p className="text-gray-500">
                    No cancellation rules found.
                  </p>
                )}
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
