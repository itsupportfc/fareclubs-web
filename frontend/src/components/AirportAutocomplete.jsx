/**
 * AirportAutocomplete Component
 *
 * A reusable autocomplete input for airport selection.
 * Features:
 * - Debounced search (waits 300ms after user stops typing)
 * - Shows dropdown with matching airports
 * - Keyboard navigation (arrow keys, enter, escape)
 * - Click outside to close
 */

import { useEffect, useRef, useState } from "react";

// Use env when provided; default to relative path so nginx proxy works in Docker
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function AirportAutocomplete({
    value,
    onChange,
    placeholder,
    label,
    required = false,
}) {
    const [inputValue, setInputValue] = useState("");
    const [suggestions, setSuggestions] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const wrapperRef = useRef(null);
    const debounceTimer = useRef(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (
                wrapperRef.current &&
                !wrapperRef.current.contains(event.target)
            ) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Search airports with debouncing
    const searchAirports = async (query) => {
        if (query.length < 2) {
            setSuggestions([]);
            setIsOpen(false);
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch(
                `${API_BASE_URL}/airports/search?q=${encodeURIComponent(
                    query
                )}&limit=10`
            );
            console.log("Airport search response:", response);
            if (response.ok) {
                const data = await response.json();
                setSuggestions(data);
                setIsOpen(data.length > 0);
            } else {
                setSuggestions([]);
                setIsOpen(false);
            }
        } catch (error) {
            console.error("Airport search error:", error);
            setSuggestions([]);
            setIsOpen(false);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle input change with debouncing
    const handleInputChange = (e) => {
        const newValue = e.target.value;
        setInputValue(newValue);
        setSelectedIndex(-1);

        // Clear previous timer
        if (debounceTimer.current) {
            clearTimeout(debounceTimer.current);
        }

        // Set new timer for debounced search
        debounceTimer.current = setTimeout(() => {
            searchAirports(newValue);
        }, 300); // Wait 300ms after user stops typing
    };

    // Handle airport selection
    const handleSelect = (airport) => {
        const displayText = `${airport.city_name} (${airport.airport_code})`;
        setInputValue(displayText);
        onChange(airport.airport_code); // Pass airport code to parent
        setIsOpen(false);
        setSuggestions([]);
    };

    // Keyboard navigation
    const handleKeyDown = (e) => {
        if (!isOpen || suggestions.length === 0) return;

        switch (e.key) {
            case "ArrowDown":
                e.preventDefault();
                setSelectedIndex((prev) =>
                    prev < suggestions.length - 1 ? prev + 1 : prev
                );
                break;
            case "ArrowUp":
                e.preventDefault();
                setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
                break;
            case "Enter":
                e.preventDefault();
                if (selectedIndex >= 0) {
                    handleSelect(suggestions[selectedIndex]);
                }
                break;
            case "Escape":
                setIsOpen(false);
                setSelectedIndex(-1);
                break;
        }
    };

    // Initialize input value when value prop changes
    useEffect(() => {
        if (value && !inputValue) {
            // If we have a value but no display text, just set the code for now
            setInputValue(value);
        }
    }, [value, inputValue]);

    return (
        <div ref={wrapperRef} className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">
                {label}
            </label>
            <input
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onFocus={() => {
                    if (suggestions.length > 0) setIsOpen(true);
                }}
                placeholder={placeholder}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={required}
                autoComplete="off"
            />

            {/* Loading indicator */}
            {isLoading && (
                <div className="absolute right-3 top-11 mt-px">
                    <div className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full"></div>
                </div>
            )}

            {/* Dropdown suggestions */}
            {isOpen && suggestions.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {suggestions.map((airport, index) => (
                        <div
                            key={airport.airport_code}
                            onClick={() => handleSelect(airport)}
                            className={`px-4 py-3 cursor-pointer hover:bg-primary/10 ${
                                index === selectedIndex ? "bg-primary/20" : ""
                            } ${index !== 0 ? "border-t border-gray-100" : ""}`}
                        >
                            <div className="font-medium text-gray-900">
                                {airport.city_name} ({airport.airport_code})
                            </div>
                            <div className="text-sm text-gray-600">
                                {airport.airport_name}, {airport.country_name}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* No results message */}
            {isOpen &&
                !isLoading &&
                inputValue.length >= 2 &&
                suggestions.length === 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg px-4 py-3">
                        <div className="text-gray-600 text-sm">
                            No airports found for "{inputValue}"
                        </div>
                    </div>
                )}
        </div>
    );
}

export default AirportAutocomplete;
