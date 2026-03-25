export const formatTime = (t) =>
    t
        ? new Date(t).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
          })
        : "--";

export const formatDate = (t) =>
    t
        ? new Date(t).toLocaleDateString([], {
              day: "2-digit",
              month: "short",
              year: "numeric",
          })
        : "--";

export const currencyFmt = (n) =>
    Number(n || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 0,
    });

export const getAirlineLogo = (code) =>
    code ? `https://pics.avs.io/60/60/${code}.png` : "";

export const AIRCRAFT_LAYOUTS = {
    A320: ["A", "B", "C", "", "D", "E", "F"],
};

export const uniqueByCode = (arr = []) => {
    const map = new Map();
    arr.forEach((i) => i?.code && !map.has(i.code) && map.set(i.code, i));
    return [...map.values()];
};

export function computeSsrTotal(seats, meals, bags) {
    const seatTotal = Object.values(seats)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, s) => sum + (s?.price || 0), 0);
    const mealTotal = Object.values(meals)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, m) => sum + (m?.price || 0), 0);
    const bagTotal = Object.values(bags)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, b) => sum + (b?.price || 0), 0);
    return seatTotal + mealTotal + bagTotal;
}

export function buildSsr(passengerIndex, trip, segmentIndex, seats, meals, bags) {
    const key = `${trip}-${segmentIndex}`;
    const seatObj = seats[key]?.[passengerIndex];
    const mealObj = meals[key]?.[passengerIndex];
    const bagObj = bags[key]?.[passengerIndex];
    const seatCode = (seatObj?.status === "available" ? seatObj?.code : null) || null;
    const seatDescription = seatObj?.description || null;
    const mealCode = mealObj?.code || null;
    const mealDescription = mealObj?.name || mealObj?.description || null;
    const baggageCode = bagObj?.code || null;
    if (!seatCode && !mealCode && !baggageCode) return null;
    return { seatCode, seatDescription, mealCode, mealDescription, baggageCode };
}
