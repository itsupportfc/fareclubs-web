/**
 * FlightResults Component
 *
 * Displays search results. For now, it's a placeholder.
 * Later we'll show real flight cards with prices, airlines, times, etc.
 */

import useFlightStore from "../store/useFlightStore";

function FlightResults() {
    const { searchResults, isLoading } = useFlightStore();

    // Show loading state
    if (isLoading) {
        return (
            <div className="mt-8 text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                <p className="mt-4 text-gray-600">
                    Searching for best flights...
                </p>
            </div>
        );
    }

    // Show results (empty for now)
    if (searchResults.length === 0) {
        return (
            <div className="mt-8 text-center py-12">
                <svg
                    className="mx-auto h-24 w-24 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                    No results yet
                </h3>
                <p className="mt-2 text-gray-500">
                    Search for flights to see available options
                </p>
            </div>
        );
    }

    // Future: Show actual flight cards here
    return (
        <div className="mt-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Available Flights
            </h2>
            {/* Flight cards will go here */}
        </div>
    );
}

export default FlightResults;
