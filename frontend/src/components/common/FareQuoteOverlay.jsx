import React from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function FareQuoteOverlay({ isVisible }) {
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40"
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        className="bg-white rounded-2xl shadow-xl p-8 flex flex-col items-center gap-4 max-w-xs"
                    >
                        <div className="w-10 h-10 border-4 border-gray-200 border-t-[#0047FF] rounded-full animate-spin" />
                        <p className="text-sm font-semibold text-gray-700">
                            Verifying fare price...
                        </p>
                        <p className="text-xs text-gray-400 text-center">
                            This usually takes a few seconds
                        </p>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
