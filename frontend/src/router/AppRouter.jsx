import React, { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Each page becomes its own chunk, loaded only when the route is first visited
// vite generates files like BookingPage.[hash].js that the browser downloads on demand

const Dashboard = lazy(() => import("../components/common/DashBoard"));
const FlightResultsPage = lazy(() => import("../pages/FlightResultsPage"));
const ReturnResultsPage = lazy(() => import("../pages/ReturnResultsPage"));
const BookingPage = lazy(() => import("../pages/BookingPage"));
const BookingConfirmationPage = lazy(
    () => import("../pages/BookingConfirmationPage"),
);

// Lightweight fallback rendered before the page chunk is available
function PageLoader() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-[#FF2E57] border-t-transparent" />
        </div>
    );
}

function NotFound() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4 text-center">
            <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
            <p className="text-xl text-gray-600 mb-2">Page not found</p>
            <p className="text-gray-400 mb-8">
                The page you're looking for doesn't exist.
            </p>
            <a
                href="/"
                className="px-6 py-3 bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] text-white font-semibold rounded-xl hover:shadow-lg transition"
            >
                Back to Home
            </a>
        </div>
    );
}

export default function AppRouter() {
    return (
        <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route
                        path="/flights/results"
                        element={<FlightResultsPage />}
                    />
                    <Route
                        path="/return/results"
                        element={<ReturnResultsPage />}
                    />
                    <Route path="/booking" element={<BookingPage />} />
                    <Route
                        path="/booking/confirmation"
                        element={<BookingConfirmationPage />}
                    />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </Suspense>
        </BrowserRouter>
    );
}
