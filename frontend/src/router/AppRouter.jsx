import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "../components/common/DashBoard";
import FlightResultsPage from "../pages/FlightResultsPage";
import ReturnResultsPage from "../pages/ReturnResultsPage";
import BookingPage from "../pages/BookingPage";
import BookingConfirmationPage from "../pages/BookingConfirmationPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/flights/results" element={<FlightResultsPage />} />
        <Route path="/return/results" element={<ReturnResultsPage />} />
        <Route path="/booking" element={<BookingPage />} />
        <Route path="/booking/confirmation" element={<BookingConfirmationPage />} />
      </Routes>
    </BrowserRouter>
  );
}
