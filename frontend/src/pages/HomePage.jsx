/**
 * HomePage Component
 *
 * Main landing page with search form
 */

import Header from "../components/Header";
import SearchPanel from "../components/SearchPanel";
import FlightResults from "../components/FlightResults";

function HomePage() {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <Header />

            {/* Hero Section with Background */}
            <div className="bg-gradient-to-r from-primary to-primary-dark pt-16 pb-32">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center">
                        <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white drop-shadow">
                            Book Your Perfect Flight
                        </h1>
                        <p className="text-xl text-white/90 drop-shadow">
                            Search and compare flights from multiple airlines
                        </p>
                    </div>
                </div>
            </div>

            {/* Search Panel Container */}
            <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                <SearchPanel />
            </div>

            {/* Results Section */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
                <FlightResults />
            </div>
        </div>
    );
}

export default HomePage;
