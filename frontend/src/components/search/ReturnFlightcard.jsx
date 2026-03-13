import React, { useState } from "react";
import { Plane } from "lucide-react";

/**
 * Extract normalized flight data from NEW API JSON
 */
const extractFlight = (flight) => {
  if (!flight) return null;

  const firstFare = flight.fares?.[0];
  const firstSegment = firstFare?.segments?.[0]?.[0];

  if (!firstSegment) return null;

  const dep = new Date(firstSegment.departureTime);
  const arr = new Date(firstSegment.arrivalTime);

  const durationMins = flight.totalDurationMinutes || 0;
  const h = Math.floor(durationMins / 60);
  const m = durationMins % 60;

  return {
    dep,
    arr,
    h,
    m,
    airlineName: firstSegment.carrier?.name || "Unknown Airline",
    airlineCode: firstSegment.carrier?.code || "",
    origin: flight.origin,
    dest: flight.destination,
    stops: flight.noOfStops,
    fare: flight.lowestPrice || 0,
    fares: flight.fares || [],
    groupId: flight.groupId,
  };
};

export default function ReturnFlightCard({
  outboundFlight,
  returnFlight,
  passengerCount = 1,
  onViewFares,
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  if (!outboundFlight || !returnFlight) return null;

  const outbound = extractFlight(outboundFlight);
  const inbound = extractFlight(returnFlight);

  if (!outbound || !inbound) return null;

  const totalFare = outbound.fare + inbound.fare;

  const FlightBlock = ({ data, label, color }) => (
    <div className="w-full bg-white rounded-lg border shadow-sm">
      <div className={`px-4 py-2 ${color} font-semibold rounded-t-lg`}>
        {label}
      </div>

      <div className="flex flex-col md:flex-row justify-between px-4 py-3 gap-4">
        {/* Airline */}
        <div className="flex items-center gap-3 min-w-[160px]">
          {data.airlineCode && (
            <img
              src={`https://pics.avs.io/60/60/${data.airlineCode}.png`}
              className="w-10 h-10"
              alt={data.airlineName}
            />
          )}
          <div>
            <p className="text-sm font-bold">{data.airlineName}</p>
          </div>
        </div>

        {/* Time */}
        <div className="flex-1 flex justify-between px-2">
          <div className="text-center">
            <p className="font-semibold">
              {data.dep.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
            <p className="text-xs text-gray-500">{data.origin}</p>
          </div>

          <div className="flex flex-col items-center">
            <Plane className="w-4 h-4 text-yellow-600 mb-1" />
            <p className="text-xs text-gray-600">
              {data.h}h {data.m}m ·{" "}
              {data.stops === 0 ? "Non Stop" : `${data.stops} Stop`}
            </p>
          </div>

          <div className="text-center">
            <p className="font-semibold">
              {data.arr.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
            <p className="text-xs text-gray-500">{data.dest}</p>
          </div>
        </div>

        {/* Fare */}
        <div className="min-w-[120px] text-right">
          <p className="text-lg font-bold">
            ₹{data.fare.toLocaleString("en-IN")}
          </p>
          <p className="text-xs text-gray-500">per adult</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-white border rounded-xl shadow-md p-4 space-y-4">
      {/* OUTBOUND + RETURN */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FlightBlock
          data={outbound}
          label="Outbound"
          color="bg-blue-50 text-blue-600"
        />
        <FlightBlock
          data={inbound}
          label="Return"
          color="bg-green-50 text-green-600"
        />
      </div>

      {/* TOTAL */}
      <div className="border-t pt-3 text-right">
        <p className="text-xl font-bold">
          ₹{totalFare.toLocaleString("en-IN")}
        </p>
        <p className="text-xs text-gray-500">
          total for {passengerCount} adult
          {passengerCount > 1 ? "s" : ""}
        </p>

        <button
          onClick={() => onViewFares({ outboundFlight, returnFlight })}
          className="mt-2 bg-pink-600 hover:bg-pink-700 transition text-white px-4 py-2 rounded-md w-full"
        >
          VIEW FARES
        </button>
      </div>

      {/* DETAILS TOGGLE */}
      <div className="flex justify-end">
        <button
          onClick={() => setDetailsOpen(!detailsOpen)}
          className="text-blue-600 text-sm font-semibold"
        >
          {detailsOpen ? "HIDE DETAILS" : "VIEW DETAILS"}
        </button>
      </div>

      {/* DETAILS */}
      {detailsOpen && (
        <div className="bg-gray-50 p-3 rounded-lg text-sm space-y-1">
          <div>
            <strong>Outbound:</strong> {outbound.origin} → {outbound.dest}
          </div>
          <div>
            <strong>Return:</strong> {inbound.origin} → {inbound.dest}
          </div>
        </div>
      )}
    </div>
  );
}
