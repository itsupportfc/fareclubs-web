/**
 * LoaderOverlay Component
 *
 * Full-screen loader with plane animation crossing from left to right
 * Shown while searching for flights
 */

import { useEffect, useState } from "react";

function LoaderOverlay() {
    const [show, setShow] = useState(true);

    // Minimum display time for better UX (even if API is fast)
    useEffect(() => {
        const timer = setTimeout(() => {
            setShow(true);
        }, 500);
        return () => clearTimeout(timer);
    }, []);

    if (!show) return null;

    return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gradient-to-r from-[#ef6614] to-[#f39c12]">
            {/* Plane Animation Container */}
            <div className="relative w-full h-24 mb-8 overflow-hidden">
                <div className="absolute animate-plane-fly">
                    {/* Simple plane SVG */}
                    <svg
                        width="80"
                        height="80"
                        viewBox="0 0 24 24"
                        fill="white"
                        className="drop-shadow-lg"
                    >
                        <path d="M21,16v-2l-8-5V3.5C13,2.67,12.33,2,11.5,2S10,2.67,10,3.5V9l-8,5v2l8-2.5V19l-2,1.5V22l3.5-1l3.5,1v-1.5L13,19v-5.5L21,16z" />
                    </svg>
                </div>
            </div>

            {/* Loading Text */}
            <div className="text-white text-center px-4">
                <h2 className="text-2xl md:text-3xl font-bold mb-2">
                    Hold on, we're fetching flights for you
                </h2>
                <p className="text-lg opacity-90">
                    Searching the best deals...
                </p>
            </div>

            {/* Progress Bar */}
            <div className="mt-8 w-64 h-1 bg-white/30 rounded-full overflow-hidden">
                <div className="h-full bg-white rounded-full animate-progress"></div>
            </div>
        </div>
    );
}

export default LoaderOverlay;
