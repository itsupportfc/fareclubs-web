import { useEffect, useRef, useState } from "react";

/**
 * Returns the number of seconds remaining in the TBO session.
 *
 * @param {number|null} searchTimestamp  Epoch ms when the search API returned.
 *                                       If null, returns the full session duration
 *                                       (safe default — no false expiry).
 * @param {number} sessionDurationMs    Session length in ms. Default: 15 minutes.
 *
 * Usage:
 *   const searchTimestamp = useFlightStore(s => s.searchTimestamp);
 *   const secondsLeft = useSessionCountdown(searchTimestamp);
 *   const isExpired = secondsLeft === 0;
 *   const showWarning = secondsLeft > 0 && secondsLeft <= 300; // last 5 min
 */

export function useSessionCountdown(
    searchTimestamp,
    sessionDurationMs = 15 * 60 * 1000,
) {
    // Calculate remaining seconds from the anchor timestamp.
    // If no timestamp yet (search hasn't happened), return full duration
    // so the timer doesn't falsely show "expired."
    const calcRemaining = () => {
        if (!searchTimestamp) return Math.floor(sessionDurationMs / 1000);
        const elapsed = Date.now() - searchTimestamp;
        const remaining = sessionDurationMs - elapsed;
        return Math.max(0, Math.floor(remaining / 1000));
    };

    const [secondsLeft, setSecondsLeft] = useState(calcRemaining);
    const intervalRef = useRef(null);

    useEffect(() => {
        // Recalculate immediately when searchTimestamp changes
        // (e.g., user does a new search)
        setSecondsLeft(calcRemaining());

        // clear any existing interval before starting a new one
        if (intervalRef.current) clearInterval(intervalRef.current);

        // If already expired o rno timestamp , dont start ticking
        if (!searchTimestamp || calcRemaining() <= 0) return;

        intervalRef.current = setInterval(() => {
            const remaining = calcRemaining();
            setSecondsLeft(remaining);
            if (remaining <= 0) clearInterval(intervalRef.current);
        }, 1000);

        // Cleanup: stops the interval when the component unmounts
        // or when searchTimestamp changes ( new search starts a new interval)
        return () => clearInterval(intervalRef.current);
    }, [searchTimestamp]); // Reset timer on new search

    return secondsLeft;
}
