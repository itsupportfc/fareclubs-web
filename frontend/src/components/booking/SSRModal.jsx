import React, { useState } from "react";
import {
  X,
  Armchair,
  UtensilsCrossed,
  Luggage,
} from "lucide-react";
import { motion } from "framer-motion";
import flightNose from "../../assets/flight-nose.png";
import flightTail from "../../assets/Flight-tail.png";
import {
  AIRCRAFT_LAYOUTS,
  uniqueByCode,
  computeSsrTotal,
  currencyFmt,
} from "../../utils/formatters";

/* ---- Segment Tabs (outbound / inbound) ---- */
const TripTabs = ({ active, setActive, hasInbound }) =>
  hasInbound ? (
    <div className="flex gap-3 mb-4">
      {["outbound", "inbound"].map((t) => (
        <button
          key={t}
          onClick={() => setActive(t)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
            active === t
              ? "bg-[#0047FF] text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          {t === "outbound" ? "Outbound" : "Inbound"}
        </button>
      ))}
    </div>
  ) : null;

const LegTabs = ({ segments, index, setIndex }) =>
  segments.length > 1 ? (
    <div className="flex gap-3 mb-4 flex-wrap">
      {segments.map((s, i) => (
        <button
          key={i}
          onClick={() => setIndex(i)}
          className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
            index === i
              ? "bg-[#0047FF] text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          Leg {i + 1}
        </button>
      ))}
    </div>
  ) : null;

const PassengerSelector = ({ travellers, active, setActive }) => (
  <div className="flex gap-2 mb-4 flex-wrap">
    {travellers.map(
      (t, i) =>
        t.type !== "Infant" && (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
              active === i
                ? "bg-[#0047FF] text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {t.firstName
              ? `${t.firstName} ${t.lastName}`
              : `Pax ${i + 1}`}
          </button>
        ),
    )}
  </div>
);

/* ---- Seats Tab ---- */
const SeatsTab = ({
  ssrData,
  travellers,
  selectedSeats,
  setSelectedSeats,
  hasInbound,
}) => {
  const [trip, setTrip] = useState("outbound");
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [activePax, setActivePax] = useState(0);

  const segments =
    trip === "outbound"
      ? ssrData?.outbound?.segments
      : ssrData?.inbound?.segments;

  const segment = segments?.[segmentIndex];

  if (!segment?.seatOptions) {
    return (
      <p className="text-gray-500 text-sm">
        No seats available for this segment.
      </p>
    );
  }

  const seatKey = `${trip}-${segmentIndex}`;
  const selectedForThisSegment = selectedSeats[seatKey] || {};

  const isSeatTakenByAnotherPassenger = (seatCode, passengerIndex) => {
    return Object.entries(selectedForThisSegment).some(
      ([paxIndex, seat]) =>
        Number(paxIndex) !== passengerIndex && seat?.code === seatCode,
    );
  };

  return (
    <>
      <TripTabs active={trip} setActive={setTrip} hasInbound={hasInbound} />
      <LegTabs
        segments={segments}
        index={segmentIndex}
        setIndex={setSegmentIndex}
      />
      <PassengerSelector
        travellers={travellers}
        active={activePax}
        setActive={setActivePax}
      />

      <div className="bg-[#cfe7f6] rounded-xl mb-4">
        <div className="flex justify-center bg-white py-4 rounded-t-xl">
          <img src={flightNose} className="h-20" alt="Flight nose" />
        </div>

        <div className="bg-white p-4">
          {segment.seatOptions.map((row) => (
            <div key={row.rowNumber} className="flex justify-center mb-1">
              <span className="w-6 text-xs text-gray-400 flex items-center">
                {row.rowNumber}
              </span>

              {AIRCRAFT_LAYOUTS["A320"].map((c, i) => {
                if (!c) return <div key={i} className="w-6" />;

                const seat = row.seats.find(
                  (s) => s.code === `${row.rowNumber}${c}`,
                );

                if (!seat) return <div key={i} className="w-9" />;

                const isSelected =
                  selectedSeats[seatKey]?.[activePax]?.code === seat.code;

                const takenByAnotherPassenger = isSeatTakenByAnotherPassenger(
                  seat.code,
                  activePax,
                );

                const isDisabled =
                  seat.status !== "available" || takenByAnotherPassenger;

                return (
                  <button
                    key={seat.code}
                    disabled={isDisabled}
                    title={
                      takenByAnotherPassenger
                        ? "Already selected by another passenger"
                        : seat.status === "available"
                          ? `₹${seat.price}`
                          : seat.status
                    }
                    onClick={() =>
                      setSelectedSeats((prev) => ({
                        ...prev,
                        [seatKey]: {
                          ...(prev[seatKey] || {}),
                          [activePax]: seat,
                        },
                      }))
                    }
                    className={`w-9 h-9 m-0.5 rounded text-xs font-medium transition-all duration-200 ${
                      isSelected
                        ? "bg-[#0047FF] text-white shadow-md"
                        : takenByAnotherPassenger
                          ? "bg-red-200 text-red-700 cursor-not-allowed"
                          : seat.status !== "available"
                            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                            : "bg-pink-50 text-gray-700 hover:bg-pink-100"
                    }`}
                  >
                    {c}
                  </button>
                );
              })}

              <span className="w-6 text-xs text-gray-400 flex items-center justify-end">
                {row.rowNumber}
              </span>
            </div>
          ))}
        </div>

        <div className="flex justify-center bg-white py-4 rounded-b-xl">
          <img src={flightTail} className="h-20" alt="Flight tail" />
        </div>
      </div>
    </>
  );
};

/* ---- Meals Tab ---- */
const MealsTab = ({
  ssrData,
  travellers,
  selectedMeals,
  setSelectedMeals,
  hasInbound,
}) => {
  const [trip, setTrip] = useState("outbound");
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [activePax, setActivePax] = useState(0);

  const segments =
    trip === "outbound"
      ? ssrData?.outbound?.segments
      : ssrData?.inbound?.segments;
  const segment = segments?.[segmentIndex];
  const key = `${trip}-${segmentIndex}`;
  const meals = uniqueByCode(segment?.mealOptions || []);

  if (!meals.length) {
    return (
      <p className="text-gray-500 text-sm">
        No meals available for this segment.
      </p>
    );
  }

  return (
    <>
      <TripTabs active={trip} setActive={setTrip} hasInbound={hasInbound} />
      <LegTabs
        segments={segments}
        index={segmentIndex}
        setIndex={setSegmentIndex}
      />
      <PassengerSelector
        travellers={travellers}
        active={activePax}
        setActive={setActivePax}
      />

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {meals.map((m) => (
          <button
            key={m.code}
            onClick={() =>
              setSelectedMeals((p) => ({
                ...p,
                [key]: {
                  ...(p[key] || {}),
                  [activePax]: m,
                },
              }))
            }
            className={`border rounded-xl p-4 text-left transition-all duration-200 ${
              selectedMeals[key]?.[activePax]?.code === m.code
                ? "bg-green-50 border-green-400 ring-2 ring-green-200"
                : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
            }`}
          >
            <p className="text-sm font-medium text-gray-800">
              {m.description || m.name}
            </p>
            <p className="text-sm font-bold text-green-700 mt-1">
              ₹{currencyFmt(m.price)}
            </p>
          </button>
        ))}
      </div>
    </>
  );
};

/* ---- Baggage Tab ---- */
const BaggageTab = ({
  ssrData,
  travellers,
  selectedBag,
  setSelectedBag,
  hasInbound,
}) => {
  const [trip, setTrip] = useState("outbound");
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [activePax, setActivePax] = useState(0);

  const segments =
    trip === "outbound"
      ? ssrData?.outbound?.segments
      : ssrData?.inbound?.segments;
  const segment = segments?.[segmentIndex];
  const key = `${trip}-${segmentIndex}`;
  const bags = segment?.baggageOptions || [];

  if (!bags.length) {
    return (
      <p className="text-gray-500 text-sm">
        No baggage options available.
      </p>
    );
  }

  return (
    <>
      <TripTabs active={trip} setActive={setTrip} hasInbound={hasInbound} />
      <LegTabs
        segments={segments}
        index={segmentIndex}
        setIndex={setSegmentIndex}
      />
      <PassengerSelector
        travellers={travellers}
        active={activePax}
        setActive={setActivePax}
      />

      <div className="flex gap-4 flex-wrap">
        {bags.map((b) => (
          <button
            key={b.code}
            onClick={() =>
              setSelectedBag((p) => ({
                ...p,
                [key]: {
                  ...(p[key] || {}),
                  [activePax]: b,
                },
              }))
            }
            className={`border rounded-xl px-5 py-4 text-center transition-all duration-200 min-w-[120px] ${
              selectedBag[key]?.[activePax]?.code === b.code
                ? "bg-green-50 border-green-400 ring-2 ring-green-200"
                : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
            }`}
          >
            <Luggage className="w-5 h-5 mx-auto mb-1 text-gray-600" />
            <p className="text-sm font-semibold text-gray-800">
              {b.weight}kg
            </p>
            <p className="text-sm font-bold text-green-700">
              ₹{currencyFmt(b.price)}
            </p>
          </button>
        ))}
      </div>
    </>
  );
};

/* ---- Main SSR Modal ---- */
export default function SSRModal({
  ssrData,
  ssrLoading,
  travellers,
  selectedSeats,
  setSelectedSeats,
  selectedMeals,
  setSelectedMeals,
  selectedBag,
  setSelectedBag,
  onClose,
  hasInbound,
}) {
  const [activeTab, setActiveTab] = useState("seats");

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex justify-center items-start pt-10 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        className="bg-white w-full max-w-5xl rounded-2xl flex flex-col max-h-[90vh] mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b shrink-0">
          <h2 className="font-display text-lg text-gray-900">
            Select Add-ons
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors duration-200"
            aria-label="Close modal"
            type="button"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-6 px-6 pt-4 border-b shrink-0">
          {[
            { key: "seats", icon: Armchair, label: "SEATS" },
            { key: "meals", icon: UtensilsCrossed, label: "MEALS" },
            { key: "baggage", icon: Luggage, label: "BAGGAGE" },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`pb-3 font-semibold text-sm flex items-center gap-1.5 transition-colors duration-200 ${
                activeTab === t.key
                  ? "border-b-2 border-[#0047FF] text-[#0047FF]"
                  : "text-gray-400 hover:text-gray-600"
              }`}
              type="button"
            >
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-6">
          {ssrLoading || !ssrData ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <div className="w-8 h-8 border-4 border-gray-200 border-t-[#0047FF] rounded-full animate-spin mb-3" />
              <p className="text-sm">Loading add-ons...</p>
            </div>
          ) : (
            <>
              {activeTab === "seats" && (
                <SeatsTab
                  ssrData={ssrData}
                  travellers={travellers}
                  selectedSeats={selectedSeats}
                  setSelectedSeats={setSelectedSeats}
                  hasInbound={hasInbound}
                />
              )}
              {activeTab === "meals" && (
                <MealsTab
                  ssrData={ssrData}
                  travellers={travellers}
                  selectedMeals={selectedMeals}
                  setSelectedMeals={setSelectedMeals}
                  hasInbound={hasInbound}
                />
              )}
              {activeTab === "baggage" && (
                <BaggageTab
                  ssrData={ssrData}
                  travellers={travellers}
                  selectedBag={selectedBag}
                  setSelectedBag={setSelectedBag}
                  hasInbound={hasInbound}
                />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t bg-gray-50 rounded-b-2xl shrink-0">
          <button
            onClick={() => {
              setSelectedSeats({});
              setSelectedMeals({});
              setSelectedBag({});
              onClose();
            }}
            className="px-5 py-2 rounded-xl border border-gray-300 text-gray-700 hover:bg-gray-100 text-sm font-medium transition-colors duration-200"
            type="button"
          >
            Cancel
          </button>

          <p className="font-bold text-gray-800">
            SSR Total:{" "}
            <span className="text-[#0047FF]">
              ₹{currencyFmt(
                computeSsrTotal(selectedSeats, selectedMeals, selectedBag),
              )}
            </span>
          </p>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[#0047FF] text-white hover:bg-[#003ACC] text-sm font-semibold transition-colors duration-200"
            type="button"
          >
            Add to Booking
          </button>
        </div>
      </motion.div>
    </div>
  );
}