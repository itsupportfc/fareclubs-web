/**
 * flightFilters.js
 *
 * Pure filter utility for flight lists.
 * No React, no store — just functions that take data and return filtered data.
 *
 * All field names are camelCase — InternalBaseSchema uses alias_generator=to_camel.
 * The frontend never sees raw TBO schema (no Segments, Airline.AirlineName, etc.).
 *
 * Usage:
 *   import { filterFlights } from "../utils/flightFilters";
 *   const visible = filterFlights(outboundFlights, filters.outbound, filters.maxPrice);
 *
 *   // International return — two passes, same array:
 *   const step1  = filterFlights(outboundFlights, filters.outbound, filters.maxPrice);
 *   const result = filterFlights(step1, filters.inbound, null, "inbound");
 */

/**
 * Count the number of stops in a FlightGroup.
 *
 * FlightGroup.noOfStops (Python: no_of_stops) is a guaranteed integer set by the
 * transformer. No fallback needed — if it's missing the object is malformed.
 */
export function getStopsCount(flightGroup) {
    return flightGroup?.noOfStops ?? 0;
}

/**
 * Get the airline name from the first outbound leg of a FlightGroup.
 *
 * Path: FlightGroup → fares[0] → segments[0] (outbound legs) → [0] (first leg) → carrier.name
 * segments is list[list[FlightSegment]] — outer list = directions, inner list = legs.
 * carrier.name is always present (required field in the Airline schema).
 */
export function getAirlineName(flightGroup) {
    return flightGroup?.fares?.[0]?.segments?.[0]?.[0]?.carrier?.name ?? "";
}

/**
 * Get the departure hour (0–23) from the FlightGroup's top-level departureTime.
 *
 * FlightGroup.departureTime (Python: departure_time) is the outbound departure time,
 * denormalized onto the group for quick access without expanding fares.
 * Returns null if unparseable — filterFlights skips the time filter when null.
 */
export function getDepartureHour(flightGroup) {
    if (!flightGroup?.departureTime) return null;
    const date = new Date(flightGroup.departureTime);
    return Number.isNaN(date.getTime()) ? null : date.getHours();
}

/**
 * Parse a departure time string into an hour (0–23), or null if unparseable.
 * Used internally for inbound legs which store departure time on the segment, not on the group.
 */
function parseHour(depTime) {
    if (!depTime) return null;
    const d = new Date(depTime);
    return Number.isNaN(d.getTime()) ? null : d.getHours();
}

/**
 * Extract the stop count, departure hour, and airline name for a given direction.
 *
 * Outbound: reads top-level FlightGroup fields (noOfStops, departureTime, carrier in segments[0]).
 * Inbound:  reads fares[0].segments[1] directly — the transformer does not denormalize
 *           inbound properties onto FlightGroup top-level fields.
 *
 * This is the only place that knows about the outbound/inbound asymmetry.
 */
function extractDirectionData(flightGroup, direction) {
    if (direction !== "inbound") {
        return {
            stops:   flightGroup?.noOfStops ?? 0,
            depHour: getDepartureHour(flightGroup),
            airline: getAirlineName(flightGroup),
        };
    }
    // Inbound (international return only): segments[1] = inbound legs array
    const legs = flightGroup?.fares?.[0]?.segments?.[1] ?? [];
    return {
        stops:   Math.max(legs.length - 1, 0),
        depHour: parseHour(legs[0]?.departureTime ?? null),
        airline: legs[0]?.carrier?.name ?? "",
    };
}

/**
 * Check if a departure hour falls within any of the selected time slots.
 *
 * Returns true when:
 *   - No slots are selected (hasActive = false) → no time filter active, pass everything
 *   - The hour falls inside at least one selected slot
 *
 * Returns false when:
 *   - Slots are selected but the hour doesn't match any of them
 *   - hour is null (couldn't parse departure time) and a filter is active
 *
 * Why object-based (not array): the store keeps timeSlots as a { key: bool } object.
 * Checking Object.values(...).some(Boolean) is the simplest way to detect if any slot is active.
 *
 * @param {number|null} hour
 * @param {object}      timeSlots  e.g. { earlyMorning: false, morning: true, afternoon: false, evening: false }
 */
export function matchesTimeSlot(hour, timeSlots = {}) {
    const hasActive = Object.values(timeSlots).some(Boolean);
    if (!hasActive) return true; // no active filter, pass all

    if (hour === null) return false; // can't determine hour, but filter is active → fail

    return (
        (timeSlots.earlyMorning && hour >= 0 && hour < 8) ||
        (timeSlots.morning && hour >= 8 && hour < 12) ||
        (timeSlots.afternoon && hour >= 12 && hour < 18) ||
        (timeSlots.evening && hour >= 18 && hour < 24)
    );
}

/**
 * Master filter function. Apply all active filters to a list of FlightGroups.
 *
 * Each filter is independent — a group must pass ALL active filters to be included.
 * Within the stop filter, checked options use OR logic (pass if matching ANY checked option).
 *
 * direction="outbound" (default): reads top-level FlightGroup denorm fields.
 * direction="inbound":            reads fares[0].segments[1] for inbound leg properties.
 *                                 Used as a second-pass filter for international return.
 *                                 Price is NOT re-checked on inbound pass (already filtered).
 *
 * @param {Array}       flightGroups     outboundFlights or inboundFlights from store
 * @param {object}      directionFilters filters.outbound or filters.inbound from store
 * @param {number|null} maxPrice         filters.maxPrice from store; null = no price filter
 * @param {string}      direction        "outbound" (default) or "inbound"
 * @returns {Array}     filtered subset — new array, original is not mutated
 */
export function filterFlights(
    flightGroups,
    directionFilters = {},
    maxPrice = null,
    direction = "outbound",
) {
    return flightGroups.filter((flightGroup) => {
        // ── Price filter ──────────────────────────────────────────────────────────
        // Skipped on the inbound pass — price was already applied during the outbound pass.
        // lowestPrice = fares[0].totalPrice (fares sorted ascending); always present.
        if (direction !== "inbound" && maxPrice != null && flightGroup.lowestPrice > maxPrice)
            return false;

        const { stops, depHour, airline } = extractDirectionData(flightGroup, direction);

        // ── Stop filter (OR logic) ────────────────────────────────────────────────
        // noOfStops for outbound comes from FlightGroup directly.
        // For inbound it is derived from legs.length - 1 in extractDirectionData.
        // nonStop=true, oneStop=true → show 0-stop AND 1-stop (OR, not AND)
        // nonStop=true, oneStop=false → show only 0-stop flights
        const stopFilterActive =
            !!directionFilters.nonStop || !!directionFilters.oneStop;
        if (stopFilterActive) {
            const matchesStop =
                (directionFilters.nonStop && stops === 0) ||
                (directionFilters.oneStop && stops === 1);
            if (!matchesStop) return false;
        }

        // ── Airline filter ────────────────────────────────────────────────────────
        // airlines is an array of selected airline name strings (e.g. ["IndiGo", "Air India"]).
        // Empty array = no filter active.
        if (
            directionFilters.airlines?.length > 0 &&
            !directionFilters.airlines.includes(airline)
        )
            return false;

        // ── Time slot filter ──────────────────────────────────────────────────────
        // Delegates to matchesTimeSlot which handles the "no active slots = pass all" case.
        if (!matchesTimeSlot(depHour, directionFilters.timeSlots)) return false;

        return true;
    });
}
