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

  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowPassengerDropdown(false);
      }
    };

    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

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
    <section className="w-full pt-20 lg:pt-24">
      <div className="w-full px-6 sm:px-8 lg:px-12 xl:px-16 2xl:px-20">
        <div className="w-full gap-8 lg:gap-12 flex flex-col lg:flex-row items-stretch">
          {/* LEFT FORM */}
          <div className="w-full lg:w-1/2 bg-white shadow-xl p-5 sm:p-6 lg:p-8 xl:py-15  2xl:p-12">
            <form onSubmit={handleSearch} className="flex flex-col gap-4 w-full">
              {/* Trip Type */}
              <div className="flex flex-wrap gap-4 justify-center sm:justify-start">
                {["oneway", "roundtrip"].map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setTripType(type)}
                    className={`px-6 py-2 rounded-lg border transition-colors duration-200 ${
                      tripType === type
                        ? "bg-[#ff214c] text-white border-[#ff214c]"
                        : "border-[#ff214c] text-[#ff214c] hover:bg-red-50"
                    }`}
                  >
                    {type === "oneway" ? "One Way" : "Round Trip"}
                  </button>
                ))}
              </div>

              {/* Airports */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <AirportAutocomplete
                  label="From"
                  value={origin}
                  onChange={setOrigin}
                />
                <AirportAutocomplete
                  label="To"
                  value={destination}
                  onChange={setDestination}
                />
              </div>

              {/* Dates */}
             <div className="grid grid-cols-1 mt-2 md:grid-cols-2 gap-4">
  <div className="flex flex-col">
    <label className="text-sm font-medium text-gray-700 mb-1">
      Departure
    </label>
    <input
      type="date"
      value={departDate}
      onChange={(e) => setDepartDate(e.target.value)}
      className="w-full p-3 border rounded-lg transition-all duration-200 focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
    />
  </div>

  {tripType === "roundtrip" && (
    <div className="flex flex-col">
      <label className="text-sm font-medium text-gray-700 mb-1">
        Return
      </label>
      <input
        type="date"
        value={returnDate}
        onChange={(e) => setReturnDate(e.target.value)}
        className="w-full p-3 border rounded-lg transition-all duration-200 focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
      />
    </div>
  )}
</div>

              {/* Passenger Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <label className="text- font-medium text-gray-700 mb-1">
     Passengers & Class
    </label>
                <button
                  type="button"
                  onClick={() => setShowPassengerDropdown(!showPassengerDropdown)}
                  className="w-full p-3 border rounded-lg mt-2 flex justify-between items-center transition-all duration-200 hover:border-gray-400"
                >
                  <span>{`${totalPassengers} Passengers, ${travelClass}`}</span>
                  <span>▼</span>
                </button>

                {showPassengerDropdown && (
                  <div className="absolute top-full mt-3 left-0 z-50 w-full sm:w-96 bg-white border border-gray-100 rounded-xl shadow-xl p-6">
                    {[
                      { label: "Adults", value: adults, min: 1, key: "adults" },
                      {
                        label: "Children",
                        value: children,
                        min: 0,
                        key: "children",
                      },
                      { label: "Infants", value: infants, min: 0, key: "infants" },
                    ].map(({ label, value, min, key }) => (
                      <div
                        key={key}
                        className="flex justify-between items-center mb-4"
                      >
                        <span className="font-medium">{label}</span>
                        <div className="flex gap-4 items-center">
                          <button
                            type="button"
                            onClick={() =>
                              value > min &&
                              useFlightStore.setState({ [key]: value - 1 })
                            }
                            className="px-3 py-1 border rounded hover:bg-gray-100 transition-colors duration-200"
                          >
                            −
                          </button>
                          <span>{value}</span>
                          <button
                                                type="button"
                                                disabled={
                                                    totalPassengers >= 9 ||
                                                    (key === "infants" && value >= adults)
                                                }
                                                onClick={() =>
                                                    useFlightStore.setState({
                                                        [key]: value + 1,
                                                    })
                                                }
                                                className="px-3 py-1 border rounded hover:bg-gray-100 transition-colors duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                                            >
                                                +
                                            </button>
                        </div>
                      </div>
                    ))}

                    <select
                      value={travelClass}
                      onChange={(e) =>
                        useFlightStore.setState({ travelClass: e.target.value })
                      }
                      className="w-full border p-2 rounded mb-4 transition-all duration-200 focus:ring-2 focus:ring-pink-400 outline-none"
                    >
                      <option>Economy</option>
                      <option>Premium Economy</option>
                      <option>Business</option>
                      <option>First</option>
                    </select>

                    <button
                      type="button"
                      onClick={() => setShowPassengerDropdown(false)}
                      className="w-full bg-[#ff214c] text-white py-2 rounded-lg hover:bg-[#e61a42] transition-colors duration-200"
                    >
                      Done
                    </button>
                  </div>
                )}
              </div>

              {error && <div className="text-red-600">{error}</div>}

              <button
                type="submit"
                className="bg-[#ff214c] text-white py-4 mt-4 rounded-lg hover:bg-[#e61a42] transition-colors duration-200 font-semibold"
              >
                {isLoading ? "Searching..." : "Search Flights"}
              </button>
            </form>
          </div>

          {/* RIGHT IMAGE */}
          <div className="hidden lg:block lg:w-1/2 w-full">
            <img
              src={images[currentImage]}
              alt="travel banner"
              className={`w-full h-full min-h-[460px] xl:min-h-[500px] 2xl:min-h-[540px] object-fit transition-opacity duration-500 ${
                fade ? "opacity-100" : "opacity-0"
              }`}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

export default SearchPanel;