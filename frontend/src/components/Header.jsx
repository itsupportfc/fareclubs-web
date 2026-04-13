/**
 * Header Component
 *
 * Displays the site logo and main navigation.
 * This is a presentational component (no state logic).
 */

function Header() {
    return (
        <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    {/* Logo */}
                    <div className="flex items-center">
                        <h1 className="text-2xl font-bold text-primary">
                            Fareclubs
                        </h1>
                    </div>

                    {/* Navigation */}
                    <nav className="hidden md:flex space-x-8">
                        <a
                            href="#"
                            className="text-gray-700 hover:text-primary font-medium"
                        >
                            Flights
                        </a>
                        <a
                            href="#"
                            className="text-gray-700 hover:text-primary font-medium"
                        >
                            Hotels
                        </a>
                        <a
                            href="#"
                            className="text-gray-700 hover:text-primary font-medium"
                        >
                            My Trips
                        </a>
                    </nav>

                    {/* Login/Signup (placeholder) */}
                    <div className="flex items-center space-x-4">
                        <button className="text-gray-700 hover:text-primary font-medium">
                            Login
                        </button>
                        <button className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark">
                            Sign Up
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
