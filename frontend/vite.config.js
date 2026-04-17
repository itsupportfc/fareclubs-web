import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
    plugins: [tailwindcss(), react()],
    build: {
        rollupOptions: {
            output: {
                manualChunks: {
                    /// Stable vendor libraries cached separately for better long-term caching
                    vendor: ["react", "react-dom", "react-router-dom"],
                    ui: ["framer-motion", "sonner", "@headlessui/react"],
                },
            },
        },
        minify: "terser",
        terserOptions: {
            compress: {
                drop_console: true, // Remove console logs in production
                drop_debugger: true, // Remove debugger statements
            },
        },
    },
});
