import React from "react";
import { Plane, Luggage } from "lucide-react";
import { formatTime, formatDate, getAirlineLogo } from "../../utils/formatters";

export default function FlightItineraryCard({ flight, selectedFare, title }) {
  const segments = selectedFare?.segments;
  if (!segments?.length) return null;

  const allLegs = segments.flatMap((item) =>
    Array.isArray(item) ? item : item?.segments || [item]
  );
  if (!allLegs.length) return null;

  const firstLeg = allLegs[0] || {};
  const carrier = firstLeg?.carrier || {};

  const airlineCode =
    carrier.code ||
    firstLeg?.airlineCode ||
    flight?.segments?.[0]?.airlineCode ||
    "";

  const airlineName =
    carrier.name ||
    firstLeg?.airlineName ||
    flight?.segments?.[0]?.airline ||
    "Airline";

  const flightNumber =
    firstLeg?.flightNumber ||
    flight?.segments?.[0]?.flightNumber ||
    "";

  const cabinClass =
    firstLeg?.cabinClass ||
    flight?.cabinClass ||
    "Economy";

  const getTimeValue = (point = {}) =>
    point.time ||
    point.at ||
    point.dateTime ||
    point.datetime ||
    point.date ||
    point.dateTimeLocal ||
    point.departureTime ||
    point.arrivalTime ||
    "";

  const getCodeValue = (point = {}) =>
    point.code || point.airportCode || point.iataCode || "--";

  const getCityValue = (point = {}) =>
    point.city || point.airportCity || point.name || "--";

  const getTerminalValue = (point = {}) =>
    point.terminal || point.terminalNo || point.term || "";

  const safeFormatTime = (value) => {
    if (!value) return "--:--";
    try {
      return formatTime(value);
    } catch {
      return "--:--";
    }
  };

  const safeFormatDate = (value) => {
    if (!value) return "--";
    try {
      return formatDate(value);
    } catch {
      return "--";
    }
  };

  const getStopsText = () => {
    if (typeof flight?.stops === "number") {
      if (flight.stops === 0) return "Non-stop";
      return `${flight.stops} ${flight.stops === 1 ? "stop" : "stops"}`;
    }

    const stops = Math.max(allLegs.length - 1, 0);
    if (stops === 0) return "Non-stop";
    return `${stops} ${stops === 1 ? "stop" : "stops"}`;
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
        <div className="flex items-center gap-3">
          <img
            src={getAirlineLogo(airlineCode)}
            alt={airlineName}
            className="w-9 h-9 object-contain rounded"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
          <div>
            <p className="font-semibold text-gray-900 text-sm">
              {airlineName}
            </p>
            <p className="text-xs text-gray-500">{flightNumber}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {title && (
            <span className="text-xs font-medium bg-indigo-50 text-indigo-600 px-3 py-1 rounded-full">
              {title}
            </span>
          )}
          <span className="text-xs font-medium bg-blue-50 text-[#0047FF] px-3 py-1 rounded-full capitalize">
            {cabinClass}
          </span>
        </div>
      </div>

      {allLegs.map((leg, idx) => {
        const dep = leg?.departure || leg?.origin || {};
        const arr = leg?.arrival || leg?.destination || {};

        const depTime = leg?.departureTime || getTimeValue(dep);
        const arrTime = leg?.arrivalTime || getTimeValue(arr);

        const depCode = getCodeValue(dep);
        const arrCode = getCodeValue(arr);

        const depCity = getCityValue(dep);
        const arrCity = getCityValue(arr);

        const depTerminal = getTerminalValue(dep);
        const arrTerminal = getTerminalValue(arr);

        const durationText =
          leg?.duration ||
          (typeof leg?.durationMinutes === "number"
            ? `${Math.floor(leg.durationMinutes / 60)}h ${leg.durationMinutes % 60}m`
            : flight?.duration || "--");

        return (
          <div
            key={idx}
            className="px-5 py-4 border-b border-gray-50 last:border-none"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="text-left min-w-0">
                <p className="text-xl font-bold text-gray-900">
                  {safeFormatTime(depTime)}
                </p>
                <p className="text-sm font-semibold text-gray-700">
                  {depCode}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {depCity}
                  {depTerminal ? ` · T${depTerminal}` : ""}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {safeFormatDate(depTime)}
                </p>
              </div>

              <div className="flex-1 flex flex-col items-center gap-1 px-2">
                <p className="text-xs text-gray-500 font-medium">
                  {durationText}
                </p>
                <div className="relative w-full flex items-center">
                  <div className="flex-1 border-t border-dashed border-gray-300" />
                  <Plane className="w-4 h-4 text-[#0047FF] mx-1 shrink-0" />
                  <div className="flex-1 border-t border-dashed border-gray-300" />
                </div>
                <p className="text-[11px] text-gray-400">{getStopsText()}</p>
              </div>

              <div className="text-right min-w-0">
                <p className="text-xl font-bold text-gray-900">
                  {safeFormatTime(arrTime)}
                </p>
                <p className="text-sm font-semibold text-gray-700">
                  {arrCode}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {arrCity}
                  {arrTerminal ? ` · T${arrTerminal}` : ""}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {safeFormatDate(arrTime)}
                </p>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-4 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
              <span className="flex items-center gap-1">
                <Luggage className="w-3.5 h-3.5" />
                Cabin: {leg?.cabinBaggage || "7 KG"}
              </span>
              <span className="w-px h-3 bg-gray-300" />
              <span className="flex items-center gap-1">
                <Luggage className="w-3.5 h-3.5" />
                Check-in: {leg?.checkedBaggage || "15 KG"}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}