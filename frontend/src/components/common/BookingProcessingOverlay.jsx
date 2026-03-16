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
                            className="mb-10"
                        >
                            <Plane className="w-14 h-14 mx-auto" />
                        </motion.div>

                        {/* Progress steps */}
                        <div className="space-y-4 mb-10">
                            {STEPS.map((label, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{
                                        opacity: i <= step ? 1 : 0.3,
                                        x: 0,
                                    }}
                                    transition={{
                                        duration: 0.4,
                                        delay: i * 0.15,
                                    }}
                                    className="flex items-center gap-4"
                                >
                                    <div
                                        className={`w-8 h-8 rounded-full border-2 flex items-center justify-center shrink-0 transition-all duration-300 ${
                                            i < step
                                                ? "bg-white border-white"
                                                : i === step
                                                  ? "border-white"
                                                  : "border-white/40"
                                        }`}
                                    >
                                        {i < step ? (
                                            <svg
                                                className="w-4 h-4 text-[#0047FF]"
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
                                            <div className="w-2.5 h-2.5 bg-white rounded-full animate-pulse" />
                                        ) : null}
                                    </div>
                                    <span className="text-sm font-medium">
                                        {label}
                                    </span>
                                </motion.div>
                            ))}
                        </div>

                        <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="text-white/70 text-sm"
                        >
                            Please don't close this tab
                        </motion.p>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
