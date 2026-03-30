import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, ArrowLeftRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import useFlightStore from "../../store/useFlightStore";
import AirportAutocomplete from "../AirportAutocomplete";

const SmallSearch = () => {
  const navigate = useNavigate();
  const passengerDropdownRef = useRef();

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

  const [isPassengerOpen, setIsPassengerOpen] = useState(false);
  const [isTripDropdownOpen, setIsTripDropdownOpen] = useState(false);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        passengerDropdownRef.current &&
        !passengerDropdownRef.current.contains(e.target)
      ) {
        setIsPassengerOpen(false);
      }
      if (!e.target.closest("#trip-type-dropdown")) {
        setIsTripDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const totalPassengers = adults + children + infants;

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  const handleSearch = async () => {
    if (!origin || !destination || !departDate) {
      toast.error("Please fill all required fields before searching.");
      return;
    }

    if (tripType === "roundtrip" && !returnDate) {
      toast.error("Please select return date for round-trip.");
      return;
    }

    try {
      const success = await searchFlights();
      if (!success) {
        toast.warning("No flights found.");
        return;
      }

      navigate(tripType === "roundtrip" ? "/return/results" : "/flights/results");
    } catch (err) {
      console.error(err);
      toast.error("Something went wrong while searching flights.");
    }
  };

  const labelClass = "text-xs font-semibold text-black mb-1";
  const commonFieldClass =
    "w-full h-12 rounded-xl border border-gray-300 bg-white text-black px-4 text-sm outline-none transition-all duration-200 focus:border-black focus:ring-0";
  const buttonFieldClass =
    "w-full h-12 rounded-xl border border-gray-300 bg-white text-black px-4 text-sm outline-none transition-all duration-200 flex items-center justify-between";
  const fieldWrapperClass = "flex flex-col w-full sm:w-[170px]";

  return (
    <div className="w-full p-4 rounded-lg">
      <div className="flex flex-wrap lg:flex-nowrap items-end justify-center gap-4">
        {/* Trip Type */}
        <div className={fieldWrapperClass} id="trip-type-dropdown">
          <label className={labelClass}>TRIP TYPE</label>
          <button
            type="button"
            onClick={() => setIsTripDropdownOpen((prev) => !prev)}
            className={buttonFieldClass}
          >
            <span className="capitalize">
              {tripType === "oneway" ? "One Way" : "Round Trip"}
            </span>
            <ChevronDown size={16} className="text-black" />
          </button>

          {isTripDropdownOpen && (
            <div className="absolute mt-[76px] w-[170px] bg-white shadow-lg rounded-xl z-50 border border-gray-200 overflow-hidden">
              {["oneway", "roundtrip"].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => {
                    setTripType(type);
                    setIsTripDropdownOpen(false);
                  }}
                  className={`w-full text-left px-4 py-3 text-sm hover:bg-gray-50 transition-colors ${
                    tripType === type
                      ? "font-semibold text-black bg-gray-50"
                      : "text-black"
                  }`}
                >
                  {type === "oneway" ? "One Way" : "Round Trip"}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* From */}
        <div className={fieldWrapperClass}>
          <label className={labelClass}>FROM</label>
          <AirportAutocomplete
            placeholder="DELHI"
            value={origin}
            onChange={setOrigin}
            required
            inputClass={commonFieldClass}
            dropdownClass="w-full  sm:w-[170px]"
          />
        </div>

        {/* Swap */}
        <div
          onClick={handleSwap}
          className="hidden lg:flex items-center justify-center cursor-pointer hover:scale-110 transition-transform duration-200 h-12 px-1"
        >
          <ArrowLeftRight size={20} className="text-black" />
        </div>

        {/* To */}
        <div className={fieldWrapperClass}>
          <label className={labelClass}>TO</label>
          <AirportAutocomplete
            placeholder="MUMBAI"
            value={destination}
            onChange={setDestination}
            required
            inputClass={commonFieldClass}
            dropdownClass="w-full sm:w-[170px]"
          />
        </div>

        {/* Departure */}
        <div className={fieldWrapperClass}>
          <label className={labelClass}>DEPARTURE</label>
          <input
            type="date"
            value={departDate}
            onChange={(e) => setDepartDate(e.target.value)}
            className={commonFieldClass}
          />
        </div>

        {/* Return */}
        <div className={fieldWrapperClass}>
          <label className={labelClass}>RETURN</label>
          <input
            type="date"
            disabled={tripType === "oneway"}
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            className={`${commonFieldClass} ${
              tripType === "oneway" ? "bg-gray-100 text-gray-400 cursor-not-allowed" : ""
            }`}
          />
        </div>

        {/* Passengers & Class */}
        <div className={`${fieldWrapperClass} relative`} ref={passengerDropdownRef}>
          <label className={labelClass}>PASSENGERS & CLASS</label>
          <button
            type="button"
            onClick={() => setIsPassengerOpen((prev) => !prev)}
            className={buttonFieldClass}
          >
            <span className="truncate">
              {totalPassengers} Passenger{totalPassengers > 1 ? "s" : ""}, {travelClass}
            </span>
            <ChevronDown size={16} className="text-black" />
          </button>

          {isPassengerOpen && (
            <div className="absolute top-full mt-2 right-0 bg-white text-black shadow-lg rounded-xl p-4 w-72 z-50 border border-gray-200">
              {[
                { label: "Adults", value: adults, set: setAdults, min: 1 },
                { label: "Children", value: children, set: setChildren, min: 0 },
                { label: "Infants", value: infants, set: setInfants, min: 0 },
              ].map((p, i) => (
                <div key={i} className="flex justify-between items-center mb-3">
                  <span className="text-sm text-black">{p.label}</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={p.value <= p.min}
                      onClick={() => p.set(p.value - 1)}
                      className="w-8 h-8 rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-40 text-black"
                    >
                      -
                    </button>
                    <span className="min-w-[20px] text-center text-black">{p.value}</span>
                    <button
                      type="button"
                      onClick={() => p.set(p.value + 1)}
                      className="w-8 h-8 rounded-md bg-gray-100 hover:bg-gray-200 text-black"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}

              <div className="mt-3">
                <label className="text-sm font-medium text-black mb-1 block">Class</label>
                <select
                  value={travelClass}
                  onChange={(e) => setTravelClass(e.target.value)}
                  className={commonFieldClass}
                >
                  <option value="Economy">Economy</option>
                  <option value="Premium Economy">Premium Economy</option>
                  <option value="Business">Business</option>
                  <option value="First">First Class</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Search */}
        <div className={fieldWrapperClass}>
          <label className={labelClass}>SEARCH</label>
          <button
            type="button"
            onClick={handleSearch}
            disabled={isLoading}
            className={`w-full h-12 rounded-xl border border-black bg-white text-black px-4 text-sm font-semibold transition-all duration-200 ${
              isLoading ? "cursor-not-allowed opacity-70" : "hover:bg-gray-50"
            }`}
          >
            {isLoading ? "Searching..." : "SEARCH"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};

export default SmallSearch;