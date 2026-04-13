/**
 * SearchPanel Component
 *
 * Main flight search form that connects to Zustand store.
 * Users can input origin, destination, dates, passengers, and class.
 *
 * Key concepts:
 * - Uses useFlightStore hook to read/write state
 * - Controlled inputs (value comes from store, onChange updates store)
 * - Simple validation (e.g., require origin/destination)
 */

import useFlightStore from "../store/useFlightStore";
import AirportAutocomplete from "./AirportAutocomplete";
import { useNavigate } from "react-router-dom";

function SearchPanel() {
    const navigate = useNavigate();

    // Get state and actions from Zustand store
    // This component will re-render only when these specific values change
    const {
        origin,
        destination,
        departDate,
        returnDate,
        adults,
        children,
        infants,
        travelClass,
        tripType,
        setOrigin,
        setDestination,
        setDepartDate,
        setReturnDate,
        setAdults,
        setChildren,
        setInfants,
        setTravelClass,
        setTripType,
        searchFlights,
        isLoading,
        error,
    } = useFlightStore();

    // Handle form submission
    const handleSearch = async (e) => {
        e.preventDefault(); // Prevent page reload

        // Basic validation
        if (!origin || !destination || !departDate) {
            alert("Please fill in origin, destination, and departure date");
            return;
        }

        // Trigger search and navigate to results page
        await searchFlights();
        navigate("/flights/results");
    };

    return (
        // -mt-8 means -ve top margin to overlap above section
        // z-10 ensures it appears above other content
        <div className="bg-white rounded-xl shadow-lg p-6 -mt-8 relative z-10">
            {/* Trip type selector */}
            <div className="flex space-x-4 mb-6">
                <button
                    onClick={() => setTripType("oneway")}
                    className={`px-4 py-2 rounded-lg font-medium ${
                        tripType === "oneway"
                            ? "bg-primary text-white"
                            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                >
                    One Way
                </button>
                <button
                    onClick={() => setTripType("roundtrip")}
                    className={`px-4 py-2 rounded-lg font-medium ${
                        tripType === "roundtrip"
                            ? "bg-primary text-white"
                            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                >
                    Round Trip
                </button>
            </div>

            <form onSubmit={handleSearch}>
                {/* Origin and Destination - First Row */}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {/* Origin */}
                    <AirportAutocomplete
                        label="From"
                        value={origin}
                        onChange={setOrigin}
                        placeholder="Delhi (DEL)"
                        required
                    />
                    {/* Destination */}
                    <AirportAutocomplete
                        label="To"
                        value={destination}
                        onChange={setDestination}
                        placeholder="Mumbai (BOM)"
                        required
                    />
                </div>

                
                {/* Dates - Second Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {/* Departure Date */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Departure
                        </label>
                        <input
                            type="date"
                            value={departDate}
                            onChange={(e) => setDepartDate(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                        />
                    </div>

                    {/* Return Date (only for round trip) */}
                    {tripType === "roundtrip" && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Return
                            </label>
                            <input
                                type="date"
                                value={returnDate}
                                onChange={(e) => setReturnDate(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    )}
                </div>

                {/* Passengers and Class - Third Row */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    {/* Adults */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Adults
                        </label>
                        <input
                            type="number"
                            value={adults}
                            onChange={(e) => setAdults(Number(e.target.value))}
                            min="1"
                            max="9"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Children */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Children
                        </label>
                        <input
                            type="number"
                            value={children}
                            onChange={(e) =>
                                setChildren(Number(e.target.value))
                            }
                            min="0"
                            max="9"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Infants */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Infants
                        </label>
                        <input
                            type="number"
                            value={infants}
                            onChange={(e) => setInfants(Number(e.target.value))}
                            min="0"
                            max="9"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Travel Class */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Class
                        </label>
                        <select
                            value={travelClass}
                            onChange={(e) => setTravelClass(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="Economy">Economy</option>
                            <option value="Premium Economy">
                                Premium Economy
                            </option>
                            <option value="Business">Business</option>
                            <option value="First">First Class</option>
                        </select>
                    </div>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                        <p className="font-medium">Error:</p>
                        <p>{error}</p>
                    </div>
                )}

                {/* Search Button */}
                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-primary text-white py-4 rounded-lg font-semibold text-lg hover:bg-primary-dark disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                    {isLoading ? "Searching..." : "Search Flights"}
                </button>
            </form>
        </div>
    );
}

export default SearchPanel;
