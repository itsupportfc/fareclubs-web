import { useEffect, useRef, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function AirportAutocomplete({
    value,
    onChange,
    placeholder,
    label,
    required = false,
    inputClass = "",
    dropdownClass = "",
}) {
    const [inputValue, setInputValue] = useState("");
    const [suggestions, setSuggestions] = useState([]);
    const [isOpen, setIsOpen] = useState(false); // dropdown
    const [isLoading, setIsLoading] = useState(false); // calling API
    const [selectedIndex, setSelectedIndex] = useState(-1);

    const wrapperRef = useRef(null);
    const debounceTimer = useRef(null);
    const abortControllerRef = useRef(null); // NEW: tracks the in-flight request

    // when user clicks outside the component, close the dropdown
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
    }, []); //runs once on mount and cleanup on unmount

    const searchAirports = async (query) => {
        if (query.length < 2) {
            setSuggestions([]);
            setIsOpen(false);
            return;
        }

        // cancel the previous request before starting a new one
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        abortControllerRef.current = new AbortController();
        setIsLoading(true);

        try {
            const response = await fetch(
                `${API_BASE_URL}/airports/search?q=${encodeURIComponent(query)}&limit=10`,
                { signal: abortControllerRef.current.signal },
            );
            if (response.ok) {
                const data = await response.json();
                setSuggestions(data);
                setIsOpen(data.length > 0);
            } else {
                setSuggestions([]);
                setIsOpen(false);
            }
        } catch (error) {
            // AbortError is expected when we cancel — not a real error
            if (error.name === "AbortError") return;
            console.error("Airport search error:", error);
            setSuggestions([]);
            setIsOpen(false);
        } finally {
            setIsLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const newValue = e.target.value;
        setInputValue(newValue);
        setSelectedIndex(-1);
        // cancel previous timer and pending API call
        if (debounceTimer.current) clearTimeout(debounceTimer.current);
        // Set new timer and Wait 300ms before calling API
        debounceTimer.current = setTimeout(() => searchAirports(newValue), 300);
    };

    const handleSelect = (airport) => {
        setInputValue(`${airport.city_name} (${airport.airport_code})`);
        onChange(airport.airport_code); // this prop of AirportAutoComplete
        setIsOpen(false);
        setSuggestions([]);
    };

    const handleKeyDown = (e) => {
        if (!isOpen || suggestions.length === 0) return;
        switch (e.key) {
            case "ArrowDown":
                e.preventDefault();
                setSelectedIndex((prev) =>
                    Math.min(prev + 1, suggestions.length - 1),
                );
                break;
            case "ArrowUp":
                e.preventDefault();
                setSelectedIndex((prev) => Math.max(prev - 1, -1));
                break;
            case "Enter":
                e.preventDefault();
                if (selectedIndex >= 0)
                    handleSelect(suggestions[selectedIndex]);
                break;
            case "Escape":
                setIsOpen(false);
                setSelectedIndex(-1);
                break;
            default:
                break;
        }
    };

    useEffect(() => {
        if (value && !inputValue) setInputValue(value);
    }, [value, inputValue]);

    return (
        <div ref={wrapperRef} className="relative w-full">
            {label && (
                <label className="block text-sm font-medium text-gray-700 mb-2 ">
                    {label}
                </label>
            )}
            <input
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onFocus={() => {
                    if (suggestions.length > 0) setIsOpen(true);
                }}
                placeholder={placeholder}
                className={
                    inputClass ||
                    "w-full h-12 rounded-xl border border-gray-200 bg-white text-black px-4 text-sm outline-none transition-all duration-200 focus:border-black focus:ring-0"
                }
                required={required}
                autoComplete="off"
            />
            {isLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
                </div>
            )}
            {isOpen && suggestions.length > 0 && (
                <div
                    className={
                        dropdownClass
                            ? `absolute z-50 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto ${dropdownClass}`
                            : "absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
                    }
                >
                    {suggestions.map((airport, index) => (
                        <div
                            key={airport.airport_code}
                            onClick={() => handleSelect(airport)}
                            className={`px-4 py-3 cursor-pointer hover:bg-gray-50 ${index === selectedIndex ? "bg-gray-100" : ""} ${index !== 0 ? "border-t border-gray-100" : ""}`}
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
