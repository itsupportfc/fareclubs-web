import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import useFlightStore from "../../store/useFlightStore";
import AirportAutocomplete from "../AirportAutocomplete";

const images = [
  "https://www.fareclubs.com/nav/file/2/Zero",
  "https://www.fareclubs.com/nav/file/2/Ebix",
  "https://www.fareclubs.com/nav/file/2/fataka",
];

function SearchPanel() {
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  const [currentImage, setCurrentImage] = useState(0);
  const [fade, setFade] = useState(true);
  const [showPassengerDropdown, setShowPassengerDropdown] = useState(false);

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
    setTripType,
    searchFlights,
    isLoading,
    error,
  } = useFlightStore();

  const totalPassengers = adults + children + infants;

  /* 🔄 Auto Image Slider */
  useEffect(() => {
    const slider = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setCurrentImage((prev) => (prev + 1) % images.length);
        setFade(true);
      }, 500);
    }, 2500);
    return () => clearInterval(slider);
  }, []);

  /* ❌ Close dropdown on outside click */
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowPassengerDropdown(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  /* 🔍 Search Handler */
  const handleSearch = async (e) => {
    e.preventDefault();

    const today = new Date().toISOString().split("T")[0];
    const originCode = origin?.trim().toUpperCase();
    const destinationCode = destination?.trim().toUpperCase();

    if (!originCode || !destinationCode || !departDate) {
      toast.error("Please fill in origin, destination, and departure date.");
      return;
    }

    if (departDate < today) {
      toast.error("Departure date cannot be in the past.");
      return;
    }

    if (tripType === "roundtrip") {
      if (!returnDate || returnDate < departDate) {
        toast.error("Invalid return date.");
        return;
      }
    }

    navigate(tripType === "oneway" ? "/flights/results" : "/return/results");

    try {
      await searchFlights();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="relative ml-10 mt-22 flex flex-col lg:flex-row items-center justify-center px-[28px] py-10">

      {/* LEFT FORM */}
      <div className="bg-white shadow-2xl w-full lg:w-6/12 p-10">
        <form onSubmit={handleSearch} className="flex flex-col gap-5">

          {/* Trip Type */}
          <div className="flex gap-4">
            {["oneway", "roundtrip"].map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setTripType(type)}
                className={`px-6 py-2 rounded-lg border ${
                  tripType === type
                    ? "bg-[#ff214c] text-white"
                    : "border-[#ff214c] text-[#ff214c]"
                }`}
              >
                {type === "oneway" ? "One Way" : "Round Trip"}
              </button>
            ))}
          </div>

          {/* Airports */}
          <div className="grid md:grid-cols-2 gap-4">
            <AirportAutocomplete label="From" value={origin} onChange={setOrigin} />
            <AirportAutocomplete label="To" value={destination} onChange={setDestination} />
          </div>

          {/* Dates */}
          <div className="grid md:grid-cols-2 gap-4">
            <input type="date" value={departDate} onChange={(e) => setDepartDate(e.target.value)} className="p-3 border rounded-lg" />
            {tripType === "roundtrip" && (
              <input type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} className="p-3 border rounded-lg" />
            )}
          </div>

          {/* Passenger Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setShowPassengerDropdown(!showPassengerDropdown)}
              className="w-full p-3 border rounded-lg flex justify-between"
            >
              {`${totalPassengers} Passengers, ${travelClass}`} ▼
            </button>

            {showPassengerDropdown && (
              <div className="absolute bottom-full mb-3 left-0 z-50 w-96 bg-white border rounded-xl shadow-xl p-6">

                {[
                  { label: "Adults", value: adults, min: 1, key: "adults" },
                  { label: "Children", value: children, min: 0, key: "children" },
                  { label: "Infants", value: infants, min: 0, key: "infants" },
                ].map(({ label, value, min, key }) => (
                  <div key={key} className="flex justify-between items-center mb-4">
                    <span className="font-medium">{label}</span>
                    <div className="flex gap-4 items-center">
                      <button type="button" onClick={() => value > min && useFlightStore.setState({ [key]: value - 1 })} className="px-3 py-1 border rounded">−</button>
                      <span>{value}</span>
                      <button type="button" onClick={() => useFlightStore.setState({ [key]: value + 1 })} className="px-3 py-1 border rounded">+</button>
                    </div>
                  </div>
                ))}

                <select
                  value={travelClass}
                  onChange={(e) => useFlightStore.setState({ travelClass: e.target.value })}
                  className="w-full border p-2 rounded mb-4"
                >
                  <option>Economy</option>
                  <option>Premium Economy</option>
                  <option>Business</option>
                  <option>First</option>
                </select>

                <button
                  type="button"
                  onClick={() => setShowPassengerDropdown(false)}
                  className="w-full bg-[#ff214c] text-white py-2 rounded-lg"
                >
                  Done
                </button>
              </div>
            )}
          </div>

          {error && <div className="text-red-600">{error}</div>}

          <button type="submit" className="bg-[#ff214c] text-white py-3 rounded-lg">
            {isLoading ? "Searching..." : "Search Flights"}
          </button>
        </form>
      </div>

      {/* RIGHT IMAGE */}
      <div className="hidden lg:block lg:w-5/12 ml-10 shadow-2xl">
        <img src={images[currentImage]} className={`transition-opacity duration-500 ${fade ? "opacity-100" : "opacity-0"}`} />
      </div>
    </div>
  );
}

export default SearchPanel;
