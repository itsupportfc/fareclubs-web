/**
 * Flight Search Store using Zustand
 *
 * This is a centralized state management store for flight search.
 * It holds all form inputs and provides functions to update them.
 *
 * Why Zustand?
 * - Simple API (just hooks, no providers needed)
 * - Less boilerplate than Redux
 * - Good performance (only re-renders components that use changed state)
 */

import { create } from "zustand";

// Get API base URL from environment variable
// Fallback to relative path for Docker/nginx proxy
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// Helper function to map travel class to API enum
const getTravelClassEnum = (className) => {
    const classMap = {
        Economy: 2,
        "Premium Economy": 3,
        Business: 4,
        First: 6,
    };
    return classMap[className] || 2; // Default to Economy
};

const useFlightStore = create((set, get) => ({
    // Search form fields
    origin: "",
    destination: "",
    departDate: "",
    returnDate: "",
    adults: 1,
    children: 0,
    infants: 0,
    travelClass: "Economy", // Economy, Premium Economy, Business, First
    tripType: "oneway", // oneway, roundtrip, multicity

    // Search results (we'll populate this later when we connect backend)
    searchResults: [],
    isLoading: false,
    error: null,

    // Actions to update state
    // Each action uses 'set' to update the store
    setOrigin: (origin) => set({ origin }),
    setDestination: (destination) => set({ destination }),
    setDepartDate: (departDate) => set({ departDate }),
    setReturnDate: (returnDate) => set({ returnDate }),
    setAdults: (adults) => set({ adults }),
    setChildren: (children) => set({ children }),
    setInfants: (infants) => set({ infants }),
    setTravelClass: (travelClass) => set({ travelClass }),
    setTripType: (tripType) => set({ tripType }),

    // Action to perform search
    searchFlights: async () => {
        const state = get();
        set({ isLoading: true, error: null });

        try {
            // TODO: Implement getUserIP later - using placeholder for now
            const userIP = "0.0.0.0";

            // Build segments array based on trip type
            const segments = [];

            // Outbound segment
            // TBO requires specific time formats: '00:00:00' for AnyTime
            segments.push({
                Origin: state.origin,
                Destination: state.destination,
                FlightCabinClass: getTravelClassEnum(state.travelClass),
                PreferredDepartureTime: state.departDate + "T00:00:00",
                PreferredArrivalTime: state.departDate + "T00:00:00",
            });

            // Return segment (if round trip)
            if (state.tripType === "roundtrip" && state.returnDate) {
                segments.push({
                    Origin: state.destination,
                    Destination: state.origin,
                    FlightCabinClass: getTravelClassEnum(state.travelClass),
                    PreferredDepartureTime: state.returnDate + "T00:00:00",
                    PreferredArrivalTime: state.returnDate + "T00:00:00",
                });
            }

            // Build the API request payload
            const payload = {
                EndUserIp: userIP,
                AdultCount: state.adults,
                ChildCount: state.children,
                InfantCount: state.infants,
                DirectFlight: false,
                OneStopFlight: false,
                JourneyType: state.tripType === "roundtrip" ? 2 : 1, // 1 = Oneway, 2 = Return
                PreferredAirlines: null,
                Segments: segments,
                Sources: null,
            };

            console.log("Sending search request:", payload);

            // Make API call to backend using environment variable
            const response = await fetch(`${API_BASE_URL}/flights/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to search flights");
            }

            const data = await response.json();
            console.log("Search response:", data);

            set({
                isLoading: false,
                searchResults: data,
                error: null,
            });
        } catch (error) {
            console.error("Search error:", error);
            set({
                isLoading: false,
                error: error.message,
                searchResults: [],
            });
        }
    },

    // Reset the form
    resetSearch: () =>
        set({
            origin: "",
            destination: "",
            departDate: "",
            returnDate: "",
            adults: 1,
            children: 0,
            infants: 0,
            travelClass: "Economy",
            tripType: "oneway",
        }),
}));

export default useFlightStore;
