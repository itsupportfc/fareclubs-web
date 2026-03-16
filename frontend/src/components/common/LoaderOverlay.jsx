import { useEffect, useState } from "react";
import { Plane } from "lucide-react";
import { motion } from "framer-motion";
import Navbar from "../Home/Navbar";
import "./LoaderOverlay.css";

function LoaderOverlay() {
  const [progress, setProgress] = useState(0);

  // Smooth progress animation
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 99) return prev;
        const next = prev + Math.random() * 4;
        return next > 100 ? 100 : next;
      });
    }, 180);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full flex flex-col bg-gradient-to-r from-orange-50 to-orange-100 min-h-screen loader-page">
      {/* Navbar */}
      <div className="shadow-sm">
        <Navbar />
      </div>

      {/* Loader Section */}
      <div className="flex flex-col items-center justify-center flex-grow py-24">
        <div className="relative w-80">

          {/* Plane icon gliding above progress bar */}
          <div
            className="absolute -top-12 transition-transform duration-300 ease-linear"
            style={{
              left: `calc(${Math.min(progress, 100)}% - 20px)`,
              transition: "left 0.25s ease-out",
            }}
          >
            <div className="relative flex items-center">
              <motion.div
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
              >
                <Plane
                  size={42}
                  strokeWidth={2.4}
                  className="text-orange-500 drop-shadow-md"
                />
              </motion.div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-3 bg-orange-200 rounded-full overflow-hidden shadow-inner mt-10">
            <div
              className="h-full bg-orange-500 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${Math.min(progress, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-12 text-center text-gray-800"
        >
          <h2 className="font-display text-lg md:text-xl mb-1">
            {progress < 90
              ? "Hang tight! We're fetching the best flights..."
              : "Almost there! Getting your perfect matches"}
          </h2>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="text-sm text-gray-600"
          >
            Please wait while we prepare your options
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}

export default LoaderOverlay;
