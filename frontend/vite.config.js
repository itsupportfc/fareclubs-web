import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
    plugins: [tailwindcss(), react()],
    esbuild: { drop: ["console", "debugger"] }, // Remove console and debugger in production
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
        minify: "esbuild", // Use esbuild for faster minification
    },
});
