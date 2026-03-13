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

  // Close dropdowns on outside click
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

  // ✅ Search handler using only searchFlights
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
      const success = await searchFlights(); // Handles both outbound & inbound
      if (!success) {
        toast.warning("No flights found.");
        return;
      }

      if (tripType === "roundtrip") {
        navigate("/return/results");
      } else {
        navigate("/flights/results");
      }
    } catch (err) {
      console.error(err);
      toast.error("Something went wrong while searching flights.");
    }
  };

  const boxClass =
    "bg-white text-gray-900 text-sm px-3 rounded-md w-full sm:w-[160px] h-[40px] shadow-sm focus:ring-2 focus:ring-pink-400 outline-none transition flex items-center justify-between";
  const labelClass = "text-black text-xs font-medium mb-1";

  return (
    <div className="w-full bg-gradient-to-r p-4 rounded-lg shadow-lg">
      <div className="flex flex-wrap lg:flex-nowrap items-center justify-center gap-3">
        {/* Trip Type */}
        <div className="flex flex-col w-full sm:w-auto relative" id="trip-type-dropdown">
          <label className={labelClass}>TRIP TYPE</label>
          <button
            onClick={() => setIsTripDropdownOpen((prev) => !prev)}
            className={boxClass}
          >
            <span className="capitalize">{tripType === "oneway" ? "One Way" : "Round Trip"}</span>
            <ChevronDown size={16} />
          </button>
          {isTripDropdownOpen && (
            <div className="absolute top-full mt-1 w-full sm:w-[160px] bg-white shadow-lg rounded-md z-50">
              {["oneway", "roundtrip"].map((type) => (
                <button
                  key={type}
                  onClick={() => {
                    setTripType(type);
                    setIsTripDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 transition capitalize ${
                    tripType === type ? "font-semibold text-pink-600" : "text-gray-900"
                  }`}
                >
                  {type === "oneway" ? "One Way" : "Round Trip"}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* From / Swap / To */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full">
          <div className="flex flex-col flex-1 min-w-[160px] w-full sm:w-auto">
            <label className={labelClass}>FROM</label>
            <AirportAutocomplete
              placeholder="DELHI"
              value={origin}
              onChange={setOrigin}
              required
              inputClass={boxClass}
              dropdownClass="w-full sm:w-[160px]"
            />
          </div>

          <div
            onClick={handleSwap}
            className="hidden lg:flex items-center justify-center cursor-pointer hover:scale-110 transition h-[40px]"
          >
            <ArrowLeftRight size={22} className="text-gray-900" />
          </div>

          <div className="flex flex-col flex-1 min-w-[160px] w-full sm:w-auto">
            <label className={labelClass}>TO</label>
            <AirportAutocomplete
              placeholder="MUMBAI"
              value={destination}
              onChange={setDestination}
              required
              inputClass={boxClass}
              dropdownClass="w-full sm:w-[160px]"
            />
          </div>
        </div>

        {/* Dates */}
        <div className="flex flex-col w-full sm:w-auto">
          <label className={labelClass}>DEPARTURE</label>
          <input
            type="date"
            value={departDate}
            onChange={(e) => setDepartDate(e.target.value)}
            className={boxClass + " cursor-pointer"}
          />
        </div>

        <div className="flex flex-col w-full sm:w-auto">
          <label className={labelClass}>RETURN</label>
          <input
            type="date"
            disabled={tripType === "oneway"}
            value={returnDate}
            onChange={(e) => setReturnDate(e.target.value)}
            className={`${boxClass} ${
              tripType === "oneway"
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-white text-gray-900 cursor-pointer focus:ring-pink-400"
            }`}
          />
        </div>

        {/* Passengers & Class */}
        <div className="flex flex-col relative w-full sm:w-auto" ref={passengerDropdownRef}>
          <label className={labelClass}>PASSENGERS & CLASS</label>
          <button onClick={() => setIsPassengerOpen((prev) => !prev)} className={boxClass}>
            <span>
              {totalPassengers} Passenger{totalPassengers > 1 ? "s" : ""}, {travelClass}
            </span>
            <ChevronDown size={16} />
          </button>

          {isPassengerOpen && (
            <div className="absolute top-full mt-2 right-0 bg-white text-gray-900 shadow-lg rounded-xl p-4 w-72 z-50">
              {[
                { label: "Adults", value: adults, set: setAdults, min: 1 },
                { label: "Children", value: children, set: setChildren, min: 0 },
                { label: "Infants", value: infants, set: setInfants, min: 0 },
              ].map((p, i) => (
                <div key={i} className="flex justify-between items-center mb-2">
                  <span>{p.label}</span>
                  <div className="flex items-center gap-2">
                    <button
                      disabled={p.value <= p.min}
                      onClick={() => p.set(p.value - 1)}
                      className="px-2 py-1 bg-gray-200 rounded hover:bg-pink-100 disabled:opacity-40"
                    >
                      -
                    </button>
                    <span>{p.value}</span>
                    <button
                      onClick={() => p.set(p.value + 1)}
                      className="px-2 py-1 bg-gray-200 rounded hover:bg-pink-100"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}

              {/* Travel Class */}
              <div className="mt-3">
                <label className="text-sm font-medium text-gray-900 mb-1 block">Class</label>
                <select
                  value={travelClass}
                  onChange={(e) => setTravelClass(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-pink-400 outline-none"
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

        {/* Search Button */}
        <div className="flex flex-col justify-end w-full sm:w-auto">
          <label className={labelClass}>SEARCH</label>
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className={`${boxClass} ${
              isLoading
                ? "bg-pink-500 text-black cursor-not-allowed"
                : "bg-pink-500 text-black hover:bg-pink-700"
            } justify-center`}
          >
            {isLoading ? "Searching..." : "SEARCH"}
          </button>
        </div>
      </div>

      {error && <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">{error}</div>}
    </div>
  );
};

export default SmallSearch;
