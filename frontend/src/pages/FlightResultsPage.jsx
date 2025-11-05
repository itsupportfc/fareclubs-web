/**
 * FlightResultsPage Component
 *
 * Displays search results after flight search completes
 */

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useFlightStore from "../store/useFlightStore";
import LoaderOverlay from "../components/LoaderOverlay";

function FlightResultsPage() {
    const navigate = useNavigate();
    const { searchResults, isLoading } = useFlightStore();

    // Redirect to home if no search results
    useEffect(() => {
        if (!isLoading && (!searchResults || !searchResults.Response)) {
            navigate("/");
        }
    }, [searchResults, isLoading, navigate]);

    // Show loader while searching
    if (isLoading) {
        return <LoaderOverlay />;
    }

    // If no results yet, show nothing (will redirect)
    if (!searchResults || !searchResults.Response) {
        return null;
    }

    const { Response } = searchResults;
    const flights = Response.Results?.[0] || [];

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header with search summary */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">
                                {Response.Origin} → {Response.Destination}
                            </h1>
                            <p className="text-gray-600">
                                {flights.length} flights found
                            </p>
                        </div>
                        <button
                            onClick={() => navigate("/")}
                            className="px-4 py-2 text-primary border border-primary rounded-lg hover:bg-primary hover:text-white transition-colors"
                        >
                            Modify Search
                        </button>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="max-w-7xl mx-auto px-4 py-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold mb-4">
                        Available Flights ({flights.length})
                    </h2>

                    {/* Temporary: Show raw JSON for verification */}
                    <div className="space-y-4">
                        {flights.slice(0, 5).map((flight, index) => (
                            <div
                                key={flight.ResultIndex || index}
                                className="border border-gray-200 rounded-lg p-4"
                            >
                                {/* Quick preview of flight data */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-semibold">
                                            {flight.AirlineCode} -{" "}
                                            {
                                                flight.Segments?.[0]?.[0]
                                                    ?.Airline?.FlightNumber
                                            }
                                        </p>
                                        <p className="text-sm text-gray-600">
                                            {
                                                flight.Segments?.[0]?.[0]
                                                    ?.Origin?.Airport?.CityName
                                            }{" "}
                                            →{" "}
                                            {
                                                flight.Segments?.[0]?.[0]
                                                    ?.Destination?.Airport
                                                    ?.CityName
                                            }
                                        </p>
                                        <p className="text-sm text-gray-500">
                                            {new Date(
                                                flight.Segments?.[0]?.[0]?.Origin?.DepTime
                                            ).toLocaleTimeString()}{" "}
                                            -{" "}
                                            {new Date(
                                                flight.Segments?.[0]?.[0]?.Destination?.ArrTime
                                            ).toLocaleTimeString()}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-2xl font-bold text-primary">
                                            ₹
                                            {flight.Fare?.OfferedFare?.toLocaleString(
                                                "en-IN"
                                            )}
                                        </p>
                                        <p className="text-sm text-gray-600">
                                            per adult
                                        </p>
                                    </div>
                                </div>

                                {/* Raw JSON for debugging (temporary) */}
                                <details className="mt-4">
                                    <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                                        View raw JSON
                                    </summary>
                                    <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-auto max-h-60">
                                        {JSON.stringify(flight, null, 2)}
                                    </pre>
                                </details>
                            </div>
                        ))}

                        {flights.length > 5 && (
                            <p className="text-center text-gray-500">
                                ... and {flights.length - 5} more flights
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default FlightResultsPage;
