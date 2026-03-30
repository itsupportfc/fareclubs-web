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
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const wrapperRef = useRef(null);
  const debounceTimer = useRef(null);

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
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const searchAirports = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/airports/search?q=${encodeURIComponent(query)}&limit=10`
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

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      searchAirports(newValue);
    }, 300);
  };

  const handleSelect = (airport) => {
    const displayText = `${airport.city_name} (${airport.airport_code})`;
    setInputValue(displayText);
    onChange(airport.airport_code);
    setIsOpen(false);
    setSuggestions([]);
  };

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

      default:
        break;
    }
  };

  useEffect(() => {
    if (value && !inputValue) {
      setInputValue(value);
    }
  }, [value, inputValue]);

  return (
    <div ref={wrapperRef} className="relative w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
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
          "w-full h-12 rounded-xl border border-gray-300 bg-white text-black px-4 text-sm outline-none transition-all duration-200 focus:border-black focus:ring-0"
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
              className={`px-4 py-3 cursor-pointer hover:bg-gray-50 ${
                index === selectedIndex ? "bg-gray-100" : ""
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

      {isOpen && !isLoading && inputValue.length >= 2 && suggestions.length === 0 && (
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