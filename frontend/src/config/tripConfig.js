/**
 * Trip Configuration — Strategy pattern for trip type variants.
 *
 * WHY THIS FILE EXISTS:
 * Instead of scattering `if (isInternationalReturn)` checks across 7+ files,
 * we define all behavioral differences here. Each component reads from config.
 *
 * HOW IT WORKS:
 * 1. resolveTripConfig() picks the right config based on tripType + flags
 * 2. Components call useTripConfig() hook to get the config
 * 3. Config properties drive rendering and business logic
 *
 * TO ADD A NEW VARIANT (e.g., multi-city):
 * 1. Add a MULTI_CITY config object here
 * 2. Update resolveTripConfig() to return it
 * 3. Add any new layout component if needed
 * That's it — no other files need to know about the new variant's internals.
 */

const DOMESTIC_RETURN = {
    type: "domestic-return",

    // LAYOUT: Show two separate columns (Departure + Return) on the results page.
    // Domestic return has independent outbound and inbound flight lists.
    hasSeparateLists: true,
    cardType: "single", // Each crad shows one flight (either outbound or return)

    // FARE MODAL: Show Outbound/Return tabs so user picks one fare per direction.
    showFareTabs: true,
    selectionMode: "two_fares", //User must select 2 independent fares

    // PRICING: Sum both fares. Each fare's totalPrice is already total for all pax.
    // DO NOT multiply by passenger count — PublishedFare already includes all pax.
    getDisplayPrice: (outFare, inFare) =>
        (outFare?.totalPrice || 0) + (inFare?.totalPrice || 0),

    isRoundTrip: true,

    // BOOKING: Return the inbound fare's ID (domestic has separate fareIds).
    getFareIdInbound: (_outFare, retFare) => retFare?.fareId || null,

    //  FARE QUOTE: Two separate fareIds → backend makes TWO TBO calls.
    buildFareQuotePayload: (outFare, retFare) => ({
        tripType: "roundtrip",
        fareIdOutbound: outFare.fareId,
        initialPriceOutbound: outFare.totalPrice,
        fareIdInbound: retFare.fareId,
        initialPriceInbound: retFare.totalPrice,
        isInternationalReturn: false,
    }),

    // ITINERARY: Each fare has its own segments.
    getOutboundSegments: (fare) => fare?.segments,
    getReturnSegments: (_outFare, retFare) => retFare?.segments,

    showReturnItinerary: true,
    showFareBreakdown: true,
};

const INTERNATIONAL_RETURN = {
    type: "international_return",

    // LAYOUT: Single column — inboundFlights is empty.
    // Each card shows BOTH directions side-by-side (segments[0] + segments[1]).
    hasSeparateLists: false,
    cardType: "clubbed",

    // FARE MODAL: No tabs — one fare list covers both directions.
    showFareTabs: false,
    selectionMode: "single_fare",

    // PRICING: Only outbound fare — it IS the roundtrip price (already all-pax total).
    getDisplayPrice: (outFare, _inFare) => outFare?.totalPrice || 0,

    isRoundTrip: true,

    // BOOKING: null — one fareId covers both directions.
    getFareIdInbound: () => null,

    // FARE QUOTE: Only outbound fareId. Backend makes ONE TBO call.
    buildFareQuotePayload: (outFare) => ({
        tripType: "roundtrip",
        fareIdOutbound: outFare.fareId,
        initialPriceOutbound: outFare.totalPrice,
        isInternationalReturn: true,
        fareIdInbound: null,
        initialPriceInbound: null,
    }),

    // ITINERARY: Both directions in ONE fare's segments array.
    // segments[0] = outbound legs, segments[1] = inbound legs.
    // These are READ-ONLY VIEWS — they don't split the original data.
    getOutboundSegments: (fare) =>
        fare?.segments?.[0] ? [fare.segments[0]] : [],
    getReturnSegments: (outFare) =>
        outFare?.segments?.[1] ? [outFare.segments[1]] : [],

    showReturnItinerary: true,
    showFareBreakdown: false, // Hides misleading "Return: ₹0" in FareSummary
};

const ONE_WAY = {
    type: "oneway",
    hasSeparateLists: false,
    cardType: "single",
    showFareTabs: false,
    selectionMode: "single_fare",
    getDisplayPrice: (outFare) => outFare?.totalPrice || 0,
    isRoundtrip: false,
    getFareIdInbound: () => null,
    buildFareQuotePayload: (outFare) => ({
        tripType: "oneway",
        fareIdOutbound: outFare.fareId,
        initialPriceOutbound: outFare.totalPrice,
        fareIdInbound: null,
        initialPriceInbound: null,
        isInternationalReturn: false,
    }),
    getOutboundSegments: (fare) => fare?.segments,
    getReturnSegments: () => [],
    showReturnItinerary: false,
    showFareBreakdown: false,
};
/**
 * Resolves config: oneway → ONE_WAY, international return → INTERNATIONAL_RETURN, else DOMESTIC_RETURN.
 */
export function resolveTripConfig({ tripType, isInternationalReturn }) {
    if (tripType === "oneway") return ONE_WAY;
    if (isInternationalReturn) return INTERNATIONAL_RETURN;
    return DOMESTIC_RETURN;
}

export { DOMESTIC_RETURN, INTERNATIONAL_RETURN, ONE_WAY };
