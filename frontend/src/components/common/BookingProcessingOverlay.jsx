import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plane } from "lucide-react";

const STEPS = [
    { label: "Verifying payment", hint: "Confirming with your bank" },
    { label: "Booking with airline", hint: "Locking in your seats" },
    { label: "Generating ticket", hint: "Preparing your e-ticket" },
];

export default function BookingProcessingOverlay({ isVisible, step = 0 }) {
    const activeStep = STEPS[Math.min(step, STEPS.length - 1)];

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/85 backdrop-blur-sm"
                >
                    <motion.div
                        initial={{ scale: 0.96, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.96, opacity: 0 }}
                        transition={{ duration: 0.35, ease: "easeOut" }}
                        className="relative w-[min(92vw,440px)] rounded-3xl border border-white/10 bg-gradient-to-br from-[#0B1220] to-[#1a1147] px-8 py-10 text-white shadow-2xl shadow-black/40 overflow-hidden"
                    >
                        {/* soft brand glow */}
                        <div className="pointer-events-none absolute -top-24 -left-16 h-64 w-64 rounded-full bg-[#0047FF]/30 blur-3xl" />
                        <div className="pointer-events-none absolute -bottom-24 -right-16 h-64 w-64 rounded-full bg-[#FF2E57]/25 blur-3xl" />

                        {/* Plane on dotted path */}
                        <div className="relative h-20 mb-8">
                            <svg
                                className="absolute inset-x-0 top-1/2 -translate-y-1/2 w-full h-px"
                                viewBox="0 0 320 1"
                                preserveAspectRatio="none"
                            >
                                <line
                                    x1="0"
                                    y1="0.5"
                                    x2="320"
                                    y2="0.5"
                                    stroke="rgba(255,255,255,0.25)"
                                    strokeWidth="1"
                                    strokeDasharray="4 5"
                                />
                            </svg>
                            <motion.div
                                animate={{ x: ["0%", "calc(100% - 56px)"] }}
                                transition={{
                                    duration: 3.2,
                                    repeat: Infinity,
                                    ease: "easeInOut",
                                    repeatType: "reverse",
                                }}
                                className="absolute top-1/2 -translate-y-1/2 left-0"
                            >
                                <div className="w-14 h-14 rounded-full bg-white/10 ring-1 ring-white/20 flex items-center justify-center backdrop-blur">
                                    <Plane className="w-7 h-7 text-white" />
                                </div>
                            </motion.div>
                        </div>

                        {/* Header copy reflects active step */}
                        <div className="relative text-center mb-7">
                            <p className="font-display text-xl font-semibold tracking-tight">
                                {activeStep.label}
                            </p>
                            <p className="text-white/60 text-sm mt-1">
                                {activeStep.hint}
                            </p>
                        </div>

                        {/* Progress steps */}
                        <div className="relative space-y-3 mb-7">
                            {STEPS.map(({ label }, i) => (
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
                                    className="flex items-center gap-3"
                                >
                                    <div
                                        className={`w-7 h-7 rounded-full border-2 flex items-center justify-center shrink-0 transition-all duration-300 ${
                                            i < step
                                                ? "bg-emerald-400 border-emerald-400"
                                                : i === step
                                                  ? "border-white"
                                                  : "border-white/30"
                                        }`}
                                    >
                                        {i < step ? (
                                            <svg
                                                className="w-3.5 h-3.5 text-slate-900"
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
                                    <span
                                        className={`text-sm ${
                                            i === step
                                                ? "text-white font-medium"
                                                : "text-white/70"
                                        }`}
                                    >
                                        {label}
                                    </span>
                                </motion.div>
                            ))}
                        </div>

                        <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="relative text-center text-white/55 text-xs leading-relaxed"
                        >
                            This usually takes 30–60 seconds.
                            <br />
                            Please don&apos;t close or refresh this tab.
                        </motion.p>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
