/**
 * Main App Component
 * Root component with routing
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import FlightResultsPage from "./pages/FlightResultsPage";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route
                    path="/flights/results"
                    element={<FlightResultsPage />}
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
