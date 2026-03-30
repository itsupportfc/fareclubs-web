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
 * Why early-return (return false) instead of building a boolean:
 *   We exit as soon as one filter fails. For long flight lists this is faster
 *   than computing all conditions and ANDing them at the end.
 *
 * @param {Array}       flightGroups     outboundFlights or inboundFlights from store
 * @param {object}      directionFilters filters.outbound or filters.inbound from store
 * @param {number|null} maxPrice         filters.maxPrice from store; null = no price filter
 * @returns {Array}     filtered subset — new array, original is not mutated
 */
export function filterFlights(
    flightGroups,
    directionFilters = {},
    maxPrice = null,
) {
    return flightGroups.filter((flightGroup) => {
        // ── Price filter ──────────────────────────────────────────────────────────
        // lowestPrice = fares[0].totalPrice (fares are sorted ascending by price).
        // It is a required float on FlightGroup — always present.
        // We compare against the cheapest fare: if even the cheapest option is above
        // maxPrice, the entire flight card is hidden.
        // Fares above maxPrice that exist within the same group are still shown
        // inside the fare modal — filtering those is the fare modal's concern.
        if (maxPrice != null && flightGroup.lowestPrice > maxPrice)
            return false;

        const stops = getStopsCount(flightGroup);
        const airline = getAirlineName(flightGroup);
        const depHour = getDepartureHour(flightGroup);

        // ── Stop filter (OR logic) ────────────────────────────────────────────────
        // noOfStops comes from FlightGroup directly — no segment counting needed.
        // Only activate if at least one option is checked.
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
