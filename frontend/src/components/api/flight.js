const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// ===============================
// 🔹 Search Flights API
// ===============================
export async function searchFlightsAPI(payload) {
  console.group("✈️ SEARCH FLIGHTS API");

  console.log("➡️ Incoming payload from UI:", payload);

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

  console.log("📤 Request Body → /flights/search:", body);

  const response = await fetch(`${API_BASE_URL}/flights/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  console.log("📥 Response Status:", response.status);
  console.log("📥 Response Body:", data);

  if (!response.ok) {
    console.error("❌ Search Flights Error:", data);
    console.groupEnd();
    throw new Error(data?.detail || "Flight search failed");
  }

  console.groupEnd();
  return data;
}

// ===============================
// 🔹 Fare Quote API
// ===============================
export async function getFareQuoteAPI({
  tripType,
  fareIdOutbound,
  initialPriceOutbound,
  fareIdInbound = null,
  initialPriceInbound = null,
}) {
  console.group("💰 FARE QUOTE API");

  const payload = {
    tripType,
    fareIdOutbound,
    initialPriceOutbound,
    fareIdInbound,
    initialPriceInbound,
  };

  console.log("➡️ Incoming params:", payload);

  if (!fareIdOutbound) {
    console.error("❌ Missing outbound fareId");
    console.groupEnd();
    throw new Error("fareIdOutbound is required");
  }

  if (tripType === "roundtrip" && !fareIdInbound) {
    console.error("❌ Missing inbound fareId for roundtrip");
    console.groupEnd();
    throw new Error("fareIdInbound is required for roundtrip");
  }

  console.log("📤 Request Body → /flights/fare-quote:", payload);

  const response = await fetch(`${API_BASE_URL}/flights/fare-quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  console.log("📥 Response Status:", response.status);
  console.log("📥 Response Body:", data);

  if (!response.ok) {
    console.error("❌ Fare Quote Error:", data);
    if (Array.isArray(data?.detail)) {
      console.groupEnd();
      throw new Error(data.detail.map((e) => e.msg).join(", "));
    }
    console.groupEnd();
    throw new Error(data?.detail || "Failed to fetch fare quote");
  }

  console.groupEnd();
  return data;
}

// ===============================
// 🔹 Fare Rules API
// ===============================
export async function getFareRulesAPI({ fareId }) {
  console.group("📜 FARE RULES API");

  console.log("➡️ Incoming params:", { fareId });

  if (!fareId) {
    console.error("❌ Missing fareId");
    console.groupEnd();
    throw new Error("fareId is required for fare rules");
  }

  const payload = { fareId };

  console.log("📤 Request Body → /flights/fare-rules:", payload);

  const response = await fetch(`${API_BASE_URL}/flights/fare-rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  console.log("📥 Response Status:", response.status);
  console.log("📥 Response Body:", data);

  if (!response.ok) {
    console.error("❌ Fare Rules Error:", data);
    console.groupEnd();
    throw new Error(data?.detail || "Failed to fetch fare rules");
  }

  console.groupEnd();
  return data;
}

// ===============================
// 🔹 SSR API (Seats, Meals)
// ===============================
export async function getSSRAPI(payload) {
  console.group("🎟️ SSR API");

  console.log("➡️ Incoming payload:", payload);

  // Basic validation
  if (!payload.fareIdOutbound) {
    console.error("❌ Missing fareIdOutbound");
    console.groupEnd();
    throw new Error("fareIdOutbound is required for SSR");
  }

  console.log("📤 Request Body → /flights/ssr:", payload);

  try {
    const response = await fetch(`${API_BASE_URL}/flights/ssr`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    console.log("📥 Response Status:", response.status);
    console.log("📥 Response Body:", data);

    if (!response.ok) {
      console.error("❌ SSR API Error:", data);
      throw new Error(data?.detail || "SSR API failed");
    }

    console.groupEnd();
    return data;
  } catch (err) {
    console.error("❌ SSR API Exception:", err?.message || err);
    console.groupEnd();
    throw err;
  }
}

// ===============================
// Download E-Ticket PDF
// ===============================
export async function downloadEticketAPI(bookingId, pnr) {
  const response = await fetch(
    `${API_BASE_URL}/flights/booking/${bookingId}/eticket?pnr=${encodeURIComponent(pnr)}`,
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err?.detail || "Failed to download e-ticket");
  }

  return response.blob();
}
