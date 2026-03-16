import React from "react";
import { Plane, Luggage } from "lucide-react";
import { formatTime, formatDate, getAirlineLogo } from "../../utils/formatters";

export default function FlightItineraryCard({ flight, selectedFare, title }) {
    const segments = selectedFare?.segments;
    if (!segments?.length) return null;

    const allLegs = segments.flatMap((f) =>
        Array.isArray(f) ? f : f?.segments || [f],
    );
    if (!allLegs.length) return null;

    const firstLeg = allLegs[0];
    const carrier = firstLeg?.carrier || {};
    const airlineCode = carrier.code || "";
    const airlineName =
        carrier.name || flight?.segments?.[0]?.airline || "Airline";
    const flightNumber =
        firstLeg?.flightNumber ||
        flight?.segments?.[0]?.flightNumber ||
        "";
    const cabinClass = flight?.cabinClass || "Economy";

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Airline header bar */}
            <div className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
                <div className="flex items-center gap-3">
                    <img
                        src={getAirlineLogo(airlineCode)}
                        alt={airlineName}
                        className="w-9 h-9 object-contain rounded"
                        onError={(e) => {
                            e.target.style.display = "none";
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
                    <span className="text-xs font-medium bg-blue-50 text-[#0047FF] px-3 py-1 rounded-full">
                        {cabinClass}
                    </span>
                </div>
            </div>

            {/* Per-leg details */}
            {allLegs.map((leg, idx) => {
                const dep = leg.departure || {};
                const arr = leg.arrival || {};
                return (
                    <div
                        key={idx}
                        className="px-5 py-4 border-b border-gray-50 last:border-none"
                    >
                        <div className="flex items-center justify-between gap-4">
                            {/* Departure */}
                            <div className="text-left min-w-0">
                                <p className="text-xl font-bold text-gray-900">
                                    {formatTime(dep.time)}
                                </p>
                                <p className="text-sm font-semibold text-gray-700">
                                    {dep.code || "--"}
                                </p>
                                <p className="text-xs text-gray-500 truncate">
                                    {dep.city || "--"}
                                    {dep.terminal ? ` · T${dep.terminal}` : ""}
                                </p>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {formatDate(dep.time)}
                                </p>
                            </div>

                            {/* Middle connector */}
                            <div className="flex-1 flex flex-col items-center gap-1 px-2">
                                <p className="text-xs text-gray-500 font-medium">
                                    {leg.duration || flight?.duration || "--"}
                                </p>
                                <div className="relative w-full flex items-center">
                                    <div className="flex-1 border-t border-dashed border-gray-300" />
                                    <Plane className="w-4 h-4 text-[#0047FF] mx-1 shrink-0" />
                                    <div className="flex-1 border-t border-dashed border-gray-300" />
                                </div>
                                <p className="text-[11px] text-gray-400">
                                    {flight?.stops === 0
                                        ? "Non-stop"
                                        : `${flight?.stops || 0} stop`}
                                </p>
                            </div>

                            {/* Arrival */}
                            <div className="text-right min-w-0">
                                <p className="text-xl font-bold text-gray-900">
                                    {formatTime(arr.time)}
                                </p>
                                <p className="text-sm font-semibold text-gray-700">
                                    {arr.code || "--"}
                                </p>
                                <p className="text-xs text-gray-500 truncate">
                                    {arr.city || "--"}
                                    {arr.terminal ? ` · T${arr.terminal}` : ""}
                                </p>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {formatDate(arr.time)}
                                </p>
                            </div>
                        </div>

                        {/* Baggage info */}
                        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
                            <span className="flex items-center gap-1">
                                <Luggage className="w-3.5 h-3.5" />
                                Cabin: {leg.cabinBaggage || 7}kg
                            </span>
                            <span className="w-px h-3 bg-gray-300" />
                            <span className="flex items-center gap-1">
                                <Luggage className="w-3.5 h-3.5" />
                                Check-in: {leg.checkedBaggage || 15}kg
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
