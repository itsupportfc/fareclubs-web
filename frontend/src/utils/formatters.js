/* 

- `VITE_*` values are baked into the built JS by Vite.
- Keeping URL creation in one helper avoids repeating `import.meta.env.VITE_BACKEND_BASE_URL` across components.
- If `VITE_BACKEND_BASE_URL` is empty, URLs become same-origin paths like `/static/logos/AI.gif`.
- Same-origin paths are more portable across local, staging, and production.

Recommended VPS `.env`:

```env
VITE_API_BASE_URL=/api/v1
VITE_BACKEND_BASE_URL=
```

Your current value also works:

```env
VITE_BACKEND_BASE_URL=https://fareclubs.com
```

But an empty value is cleaner when frontend, API, and static files are served from the same Nginx domain.
 */
const backendOrigin = (import.meta.env.VITE_BACKEND_BASE_URL || "").replace(
    /\/$/,
    "",
);

export const getStaticUrl = (path = "") => {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;

    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${backendOrigin}${normalizedPath}`;
};

export const getFallbackAirlineLogo = () =>
    getStaticUrl("/static/logos/nologo.gif");

export const getAirlineLogo = (code) =>
    code ? getStaticUrl(`/static/logos/${code.toUpperCase()}.gif`) : "";

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

export const AIRCRAFT_LAYOUTS = {
    A320: ["A", "B", "C", "", "D", "E", "F"],
};

export const uniqueByCode = (arr = []) => {
    const map = new Map();
    arr.forEach((i) => i?.code && !map.has(i.code) && map.set(i.code, i));
    return [...map.values()];
};

export function computeSsrTotal(
    seats,
    meals,
    bags,
    journeyMeals = {},
    journeyBags = {},
) {
    const seatTotal = Object.values(seats)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, s) => sum + (s?.price || 0), 0);
    const mealTotal = Object.values(meals)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, m) => sum + (m?.price || 0), 0);
    const bagTotal = Object.values(bags)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, b) => sum + (b?.price || 0), 0);
    // Journey-level: one selection per (trip, passenger). Price applies once,
    // not per-segment.
    const journeyMealTotal = Object.values(journeyMeals)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, m) => sum + (m?.price || 0), 0);
    const journeyBagTotal = Object.values(journeyBags)
        .flatMap((s) => Object.values(s || {}))
        .reduce((sum, b) => sum + (b?.price || 0), 0);
    return (
        seatTotal + mealTotal + bagTotal + journeyMealTotal + journeyBagTotal
    );
}

export function buildSsr(
    passengerIndex,
    trip,
    segmentIndex,
    seats,
    meals,
    bags,
) {
    const key = `${trip}-${segmentIndex}`;
    const seatObj = seats[key]?.[passengerIndex];
    const mealObj = meals[key]?.[passengerIndex];
    const bagObj = bags[key]?.[passengerIndex];
    const seatCode =
        (seatObj?.status === "available" ? seatObj?.code : null) || null;
    const seatDescription = seatObj?.description || null;
    const mealCode = mealObj?.code || null;
    const mealDescription = mealObj?.name || mealObj?.description || null;
    const baggageCode = bagObj?.code || null;
    if (!seatCode && !mealCode && !baggageCode) return null;
    return {
        seatCode,
        seatDescription,
        mealCode,
        mealDescription,
        baggageCode,
    };
}

/**
 * Build the journey-level SSR object for one passenger / one trip direction.
 * Returns null if the user picked nothing trip-wide.
 */
export function buildJourneySsr(
    passengerIndex,
    trip,
    journeyMeals,
    journeyBags,
) {
    const meal = journeyMeals[trip]?.[passengerIndex];
    const bag = journeyBags[trip]?.[passengerIndex];
    if (!meal && !bag) return null;
    return {
        mealCode: meal?.code || null,
        baggageCode: bag?.code || null,
    };
}
