const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function searchFlightsAPI(payload, signal) {
    const body = {
        tripType: payload.tripType,
        origin: payload.origin,
        destination: payload.destination,
        departureDate: payload.departureDate,
        adults: payload.adults,
        children: payload.children,
        infants: payload.infants,
        cabinClass: payload.cabinClass,
    };

    if (payload.tripType === "roundtrip" && payload.returnDate) {
        body.returnDate = payload.returnDate;
    }

    const response = await fetch(`${API_BASE_URL}/flights/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal, // undefined if caller doesn't pass it - fetch ignores undefined signal
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Flight search failed");
    }

    return data;
}

export async function getFareQuoteAPI({
    tripType,
    fareIdOutbound,
    initialPriceOutbound,
    fareIdInbound = null,
    initialPriceInbound = null,
    isInternationalReturn = false,
    signal,
}) {
    if (!fareIdOutbound) throw new Error("fareIdOutbound is required");
    if (tripType === "roundtrip" && !fareIdInbound && !isInternationalReturn) {
        throw new Error("fareIdInbound is required for roundtrip ");
    }
    const payload = {
        tripType,
        fareIdOutbound,
        initialPriceOutbound,
        fareIdInbound,
        initialPriceInbound,
        isInternationalReturn,
    };

    const response = await fetch(`${API_BASE_URL}/flights/fare-quote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal,
    });

    const data = await response.json();

    if (!response.ok) {
        if (Array.isArray(data?.detail)) {
            throw new Error(data.detail.map((e) => e.msg).join(", "));
        }
        throw new Error(data?.detail || "Failed to fetch fare quote");
    }
    return data;
}

export async function getFareRulesAPI({ fareId, signal }) {
    if (!fareId) {
        throw new Error("fareId is required for fare rules");
    }

    const response = await fetch(`${API_BASE_URL}/flights/fare-rules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fareId }),
        signal,
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Failed to fetch fare rules");
    }

    return data;
}
  

export async function getSSRAPI(payload, signal) {
    // Basic validation
    if (!payload.fareIdOutbound) {
        throw new Error("fareIdOutbound is required for SSR");
    }

    const response = await fetch(`${API_BASE_URL}/flights/ssr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal,
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "SSR API failed");
    }

    return data;
}

export async function downloadEticketAPI(bookingId, pnr, signal) {
    const response = await fetch(
        `${API_BASE_URL}/flights/booking/${bookingId}/eticket?pnr=${encodeURIComponent(pnr)}`,
        { signal },
    );

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err?.detail || "Failed to download e-ticket");
    }

    return response.blob();
}
