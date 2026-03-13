import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plane } from "lucide-react";

const STEPS = [
    "Verifying payment...",
    "Booking with airline...",
    "Generating ticket...",
];

export default function BookingProcessingOverlay({ isVisible, step = 0 }) {
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-gradient-to-br from-[#0047FF]/95 to-[#FF2E57]/95"
                >
                    <div className="text-center text-white px-6 max-w-md">
                        {/* Animated plane */}
                        <motion.div
                            animate={{ x: ["-30%", "30%", "-30%"] }}
                            transition={{
                                duration: 3,
                                repeat: Infinity,
                                ease: "easeInOut",
                            }}
                            className="mb-8"
                        >
                            <Plane className="w-12 h-12 mx-auto" />
                        </motion.div>

                        {/* Progress steps */}
                        <div className="space-y-3 mb-8">
                            {STEPS.map((label, i) => (
                                <div
                                    key={i}
                                    className={`flex items-center gap-3 transition-opacity duration-300 ${
                                        i <= step ? "opacity-100" : "opacity-30"
                                    }`}
                                >
                                    <div
                                        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 ${
                                            i < step
                                                ? "bg-white border-white"
                                                : i === step
                                                  ? "border-white"
                                                  : "border-white/40"
                                        }`}
                                    >
                                        {i < step ? (
                                            <svg
                                                className="w-3.5 h-3.5 text-[#0047FF]"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                                strokeWidth={3}
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    d="M5 13l4 4L19 7"
                                                />
                                            </svg>
                                        ) : i === step ? (
                                            <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                                        ) : null}
                                    </div>
                                    <span className="text-sm font-medium">
                                        {label}
                                    </span>
                                </div>
                            ))}
                        </div>

                        <p className="text-white/70 text-sm">
                            Please don't close this tab
                        </p>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
