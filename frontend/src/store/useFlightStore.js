import { create } from "zustand";
import {
  searchFlightsAPI,
  getFareQuoteAPI,
  getFareRulesAPI,
} from "../components/api/flight";

/* ---------------- PERSIST CACHE ---------------- */
const CACHE_KEY = "flightCache";

const loadCache = () => {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

const saveCache = (cache) => {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch {}
};

const useFlightStore = create((set, get) => ({
  // ✈️ Search Inputs
  origin: "",
  destination: "",
  departDate: "",
  returnDate: "",
  adults: 1,
  children: 0,
  infants: 0,
  travelClass: "Economy",
  tripType: "oneway",

  // 📦 Results
  outboundFlights: [],
  inboundFlights: [],
  isInternationalReturn: false,

  // ⏳ Loading
  isLoading: false,
  isReturnLoading: false,
  isFareLoading: false,

  // ❌ Errors
  error: null,
  returnError: null,
  fareError: null,

  // 💳 Fare Info per fareId
  fareData: {},

  // 🗄️ Cache (persisted)
  flightCache: loadCache(),

  // ===============================
  // 🔸 Setters
  // ===============================
  setOrigin: (origin) => set({ origin }),
  setDestination: (destination) => set({ destination }),
  setDepartDate: (departDate) => set({ departDate }),
  setReturnDate: (returnDate) => set({ returnDate }),
  setAdults: (adults) => set({ adults }),
  setChildren: (children) => set({ children }),
  setInfants: (infants) => set({ infants }),
  setTravelClass: (travelClass) => set({ travelClass }),
  setTripType: (tripType) => set({ tripType }),

  // ===============================
  // 🔄 Flight Cache Methods
  // ===============================
  setCache: (key, value) =>
    set((state) => {
      const updated = { ...state.flightCache, [key]: value };
      saveCache(updated);
      return { flightCache: updated };
    }),

  getCache: (key) => get().flightCache?.[key],

  clearCache: () => {
    sessionStorage.removeItem(CACHE_KEY);
    set({ flightCache: {} });
  },

  // ===============================
  // 🧠 Common Cache Helpers (NEW)
  // ===============================
  setSelectedFlight: (flight) =>
    get().setCache("selectedFlight", flight),

  getSelectedFlight: () =>
    get().getCache("selectedFlight"),

  setSelectedFare: (fare) =>
    get().setCache("selectedFare", fare),

  getSelectedFare: () =>
    get().getCache("selectedFare"),

  setSearchResults: (data) =>
    get().setCache("searchResults", data),

  getSearchResults: () =>
    get().getCache("searchResults"),

  // ===============================
  // 🧳 Booking Layer (NEW)
  // ===============================
  selectedOutbound: null,
  selectedInbound: null,
  fareSnapshot: null,
  bookingStep: "results", // results | booking | payment

  setSelectedFlights: (outbound, inbound) => {
    get().setCache("selectedOutbound", outbound);
    get().setCache("selectedInbound", inbound);
    set({ selectedOutbound: outbound, selectedInbound: inbound });
  },

  loadSelectedFlightsFromCache: () => {
    const outbound = get().getCache("selectedOutbound");
    const inbound = get().getCache("selectedInbound");
    if (outbound || inbound) {
      set({ selectedOutbound: outbound, selectedInbound: inbound });
    }
  },

  setFareSnapshot: (snapshot) => {
    get().setCache("fareSnapshot", snapshot);
    set({ fareSnapshot: snapshot });
  },

  loadFareSnapshotFromCache: () => {
    const snapshot = get().getCache("fareSnapshot");
    if (snapshot) set({ fareSnapshot: snapshot });
  },

  setBookingStep: (step) => set({ bookingStep: step }),

  // ===============================
  // 🔍 Search Flights
  // ===============================
  searchFlights: async () => {
    const state = get();
    set({
      isLoading: true,
      error: null,
      outboundFlights: [],
      inboundFlights: [],
    });

    try {
      const payload = {
        tripType: state.tripType,
        origin: state.origin?.trim().toUpperCase(),
        destination: state.destination?.trim().toUpperCase(),
        departureDate: state.departDate,
        returnDate:
          state.tripType === "roundtrip" ? state.returnDate : undefined,
        adults: state.adults,
        children: state.children,
        infants: state.infants,
        cabinClass: state.travelClass?.toLowerCase(),
        directOnly: false,
        preferredAirlines: [],
      };

      const data = await searchFlightsAPI(payload);

      const outboundFlights = Array.isArray(data?.outboundFlights)
        ? data.outboundFlights
        : [];
      const inboundFlights = Array.isArray(data?.inboundFlights)
        ? data.inboundFlights
        : [];

      set({
        outboundFlights,
        inboundFlights,
        isInternationalReturn: data?.isInternationalReturn || false,
        isLoading: false,
        error:
          outboundFlights.length === 0 && inboundFlights.length === 0
            ? "No flights found"
            : null,
      });

      // ✅ cache search response
      get().setSearchResults({
        outboundFlights,
        inboundFlights,
        origin: state.origin,
        destination: state.destination,
        passengers: {
          adults: state.adults,
          children: state.children,
          infants: state.infants,
        },
        tripType: state.tripType,
      });

      return outboundFlights.length > 0 || inboundFlights.length > 0;
    } catch (err) {
      set({
        outboundFlights: [],
        inboundFlights: [],
        isLoading: false,
        error: err.message || "Failed to search flights",
      });
      console.error("❌ Search Flights Error:", err);
      return false;
    }
  },

  // ===============================
  // 💰 Fare Quote
  // ===============================
  getFareQuote: async ({ fareId, initialPrice }) => {
    if (!fareId) throw new Error("fareId is required");

    set({ isFareLoading: true, fareError: null });

    try {
      const payload = { fareId, initialPrice };
      const response = await getFareQuoteAPI(payload);

      set((state) => ({
        fareData: {
          ...state.fareData,
          [fareId]: {
            ...(state.fareData[fareId] || {}),
            fareQuote: response,
          },
        },
        isFareLoading: false,
      }));

      return response;
    } catch (err) {
      set({ isFareLoading: false, fareError: err.message });
      throw err;
    }
  },

  // ===============================
  // 📜 Fare Rules
  // ===============================
  getFareRules: async ({ fareId }) => {
    if (!fareId) throw new Error("fareId is required");

    set({ isFareLoading: true, fareError: null });

    try {
      const payload = { fareId };
      const response = await getFareRulesAPI(payload);

      set((state) => ({
        fareData: {
          ...state.fareData,
          [fareId]: {
            ...(state.fareData[fareId] || {}),
            fareRules: response?.Response?.FareRules || [],
          },
        },
        isFareLoading: false,
      }));

      return response;
    } catch (err) {
      set({ isFareLoading: false, fareError: err.message });
      throw err;
    }
  },

  // ===============================
  // 🔄 Reset
  // ===============================
  resetSearch: () => {
    sessionStorage.removeItem(CACHE_KEY);
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
      outboundFlights: [],
      inboundFlights: [],
      isInternationalReturn: false,
      error: null,
      returnError: null,
      fareData: {},
      fareError: null,
      flightCache: {},
      // reset booking state
      selectedOutbound: null,
      selectedInbound: null,
      fareSnapshot: null,
      bookingStep: "results",
    });
  },
}));

export default useFlightStore;
