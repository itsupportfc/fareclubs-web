import React from "react";
import { getAirlineLogo, getFallbackAirlineLogo } from "../../utils/formatters";

/* 

- `loading="lazy"` delays offscreen logo requests.
- `decoding="async"` lets the browser decode images without blocking rendering.
- `width` and `height` reserve space before the image loads, reducing layout shift.
*/
export default function AirlineLogo({
    code,
    alt,
    className = "w-10 h-10 object-contain",
    width = 40,
    height = 40,
    loading = "lazy",
    fetchpriority,
}) {
    const src = getAirlineLogo(code);
    if (!src) return null;

    return (
        <img
            src={src}
            alt={alt}
            className={className}
            width={width}
            height={height}
            loading={loading}
            fetchpriority={fetchpriority}
            onError={(event) => {
                if (!event.currentTarget.dataset.fallbackApplied) {
                    event.currentTarget.dataset.fallbackApplied = true;
                    event.currentTarget.src = getFallbackAirlineLogo();
                    return;
                }

                event.currentTarget.style.display = "none"; // hide if fallback also fails
            }}
        />
    );
}
