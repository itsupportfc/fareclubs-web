import React, { useEffect, useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/Home/Navbar";
import { getSSRAPI } from "../components/api/flight";
import { useRazorpayBooking } from "../components/api/useRazorpayBooking";
import {
    Plane,
    Users,
    Phone,
    ShoppingBag,
    CreditCard,
    Info,
    Shield,
    Armchair,
    UtensilsCrossed,
    Luggage,
} from "lucide-react";

import visaLogo from "../assets/payments/Visa1.png";
import mastercardLogo from "../assets/payments/MasterCard.png";
import rupayLogo from "../assets/payments/Rupay.png";
import upiLogo from "../assets/payments/Bhim.jpg";

import { currencyFmt, computeSsrTotal, buildSsr } from "../utils/formatters";
import SectionHeader from "../components/booking/SectionHeader";
import FlightItineraryCard from "../components/booking/FlightItineraryCard";
import TravellerForm from "../components/booking/TravellerForm";
import ContactDetailsSection from "../components/booking/ContactDetailsSection";
import FareSummary from "../components/booking/FareSummary";
import SSRModal from "../components/booking/SSRModal";
import BookingProcessingOverlay from "../components/common/BookingProcessingOverlay";

export default function BookingPage() {
    const { state } = useLocation();
    const navigate = useNavigate();

    // Normalize state from both FareModal (oneway) and ReturnFareModal (roundtrip)
    const {
        outboundFlight,
        returnFlight,
        outboundSelectedFare,
        returnSelectedFare,
        passengers = { adults: 1, children: 0, infants: 0 },
        isInternationalReturn = false,
        // OneWay sends perPassengerFares/fareQuoteFlags
        // Roundtrip sends perPassengerFaresOutbound/Inbound, fareQuoteFlagsOutbound/Inbound
        perPassengerFares,
        fareQuoteFlags: fareQuoteFlagsOneway,
        perPassengerFaresOutbound,
        perPassengerFaresInbound,
        fareQuoteFlagsOutbound,
        fareQuoteFlagsInbound,
    } = state || {};

    const isRoundtrip = !!returnSelectedFare;

    // Normalize per-passenger fares
    const perPaxOutbound = perPassengerFaresOutbound || perPassengerFares || [];
    const perPaxInbound = perPassengerFaresInbound || [];

    // Merge fare quote flags
    const fareQuoteFlags =
        fareQuoteFlagsOneway ||
        fareQuoteFlagsOutbound ||
        fareQuoteFlagsInbound ||
        null;

    const [travellers, setTravellers] = useState([]);
    const [ssrData, setSSRData] = useState(null);
    const [showSSR, setShowSSR] = useState(false);
    const [selectedSeats, setSelectedSeats] = useState({});
    const [selectedMeals, setSelectedMeals] = useState({});
    const [selectedBag, setSelectedBag] = useState({});
    const [bookingError, setBookingError] = useState(null);
    const [ssrLoading, setSsrLoading] = useState(false);

    const token = localStorage.getItem("access_token");
    const { initiateBooking, isProcessing, processingStep } =
        useRazorpayBooking(token);

    /* --- SSR subtotals --- */
    const seatTotal = useMemo(
        () =>
            Object.values(selectedSeats)
                .flatMap((s) => Object.values(s || {}))
                .reduce((sum, s) => sum + (s?.price || 0), 0),
        [selectedSeats],
    );
    const mealTotal = useMemo(
        () =>
            Object.values(selectedMeals)
                .flatMap((s) => Object.values(s || {}))
                .reduce((sum, m) => sum + (m?.price || 0), 0),
        [selectedMeals],
    );
    const bagTotal = useMemo(
        () =>
            Object.values(selectedBag)
                .flatMap((s) => Object.values(s || {}))
                .reduce((sum, b) => sum + (b?.price || 0), 0),
        [selectedBag],
    );
    const ssrTotal = seatTotal + mealTotal + bagTotal;
    const grandTotal =
        (outboundSelectedFare?.totalPrice || 0) +
        (returnSelectedFare?.totalPrice || 0) +
        ssrTotal;

    /* --- Per-head fare helper --- */
    const getPerHeadFare = (paxType, direction = "outbound") => {
        const fares = direction === "outbound" ? perPaxOutbound : perPaxInbound;
        const match = fares.find((f) => f.paxType === paxType);
        const fallbackFare =
            direction === "outbound"
                ? outboundSelectedFare
                : returnSelectedFare;
        if (match) return match;
        return {
            baseFare: fallbackFare?.baseFare || 0,
            tax: fallbackFare?.taxes || 0,
        };
    };

    /* --- Validation --- */
    const travellersComplete = useMemo(() => {
        if (!travellers.length) return false;
        const basicOk = travellers.every(
            (t) =>
                t.title &&
                t.firstName &&
                t.lastName &&
                t.dateOfBirth &&
                t.gender,
        );
        const leadOk = !!(travellers[0]?.email && travellers[0]?.contactNo);
        const panOk =
            !fareQuoteFlags?.isPanRequired || travellers.every((t) => t.pan);
        const passportOk =
            !fareQuoteFlags?.isPassportRequired ||
            travellers.every(
                (t) =>
                    t.passportNo &&
                    t.passportExpiry &&
                    t.passportIssueDate &&
                    t.passportIssueCountryCode,
            );
        return basicOk && leadOk && panOk && passportOk;
    }, [travellers, fareQuoteFlags]);

    /* --- Init travellers --- */
    useEffect(() => {
        if (!passengers) return;
        const list = [];
        const extraFields = {
            pan: "",
            passportNo: "",
            passportExpiry: "",
            passportIssueDate: "",
            passportIssueCountryCode: "",
        };
        for (let i = 0; i < passengers.adults; i++)
            list.push({
                title: "",
                firstName: "",
                lastName: "",
                dateOfBirth: "",
                gender: "",
                type: "Adult",
                email: "",
                contactNo: "",
                addressLine1: "",
                city: "",
                nationality: "IN",
                ...extraFields,
                ...(i === 0
                    ? {
                          gstCompanyName: "",
                          gstNumber: "",
                          gstCompanyAddress: "",
                          gstCompanyEmail: "",
                          gstCompanyPhone: "",
                      }
                    : {}),
            });
        for (let i = 0; i < passengers.children; i++)
            list.push({
                title: "",
                firstName: "",
                lastName: "",
                dateOfBirth: "",
                gender: "",
                type: "Child",
                nationality: "IN",
                ...extraFields,
            });
        for (let i = 0; i < passengers.infants; i++)
            list.push({
                title: "",
                firstName: "",
                lastName: "",
                dateOfBirth: "",
                gender: "",
                type: "Infant",
                nationality: "IN",
                ...extraFields,
            });
        setTravellers(list);
    }, [passengers]);

    /* --- SSR prefetch on mount --- */
    useEffect(() => {
        if (!outboundSelectedFare?.fareId) return;
        let cancelled = false;
        setSsrLoading(true);
        getSSRAPI({
            tripType: isRoundtrip ? "roundtrip" : "oneway",
            fareIdOutbound: outboundSelectedFare.fareId,
            fareIdInbound: returnSelectedFare?.fareId || null,
            isInternationalReturn,
        })
            .then((res) => {
                if (!cancelled) setSSRData(res);
            })
            .catch((err) => console.error("SSR prefetch failed:", err))
            .finally(() => {
                if (!cancelled) setSsrLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [outboundSelectedFare?.fareId, returnSelectedFare?.fareId]);

    /* --- Build booking payload --- */
    const buildPayload = () => {
        const total = computeSsrTotal(
            selectedSeats,
            selectedMeals,
            selectedBag,
        );
        return {
            fareIdOutbound: outboundSelectedFare.fareId,
            fareIdInbound: returnSelectedFare?.fareId || null,
            tripType: isRoundtrip ? "roundtrip" : "oneway",
            isInternationalReturn,
            totalAmount:
                (outboundSelectedFare?.totalPrice || 0) +
                (returnSelectedFare?.totalPrice || 0) +
                total,
            passengers: (() => {
                const list = travellers.map((t, i) => {
                    const paxType =
                        t.type === "Adult" ? 1 : t.type === "Child" ? 2 : 3;
                    const perHeadOut = getPerHeadFare(paxType, "outbound");
                    const perHeadIn = isRoundtrip
                        ? getPerHeadFare(paxType, "inbound")
                        : null;
                    const pax = {
                        title: t.title,
                        firstName: t.firstName,
                        lastName: t.lastName,
                        paxType,
                        dateOfBirth: t.dateOfBirth,
                        gender: t.gender === "Male" ? 1 : 2,
                        addressLine1: t.addressLine1 || "",
                        city: t.city || "",
                        countryCode: "IN",
                        countryName: "India",
                        nationality: t.nationality || "IN",
                        contactNo: t.contactNo || "",
                        email: t.email || "",
                        isLeadPax: i === 0,
                        fare: {
                            baseFare: perHeadOut.baseFare,
                            tax: perHeadOut.tax,
                            yqTax: perHeadOut.yqTax || 0,
                            additionalTxnFeeOfrd:
                                perHeadOut.additionalTxnFeeOfrd || 0,
                            additionalTxnFeePub:
                                perHeadOut.additionalTxnFeePub || 0,
                            pgCharge: perHeadOut.pgCharge || 0,
                        },
                        ssr:
                            buildSsr(
                                i,
                                "outbound",
                                0,
                                selectedSeats,
                                selectedMeals,
                                selectedBag,
                            ) || null,
                    };
                    if (t.pan) pax.pan = t.pan;
                    if (t.passportNo) {
                        pax.passportNo = t.passportNo;
                        pax.passportExpiry = t.passportExpiry || "";
                        pax.passportIssueDate = t.passportIssueDate || "";
                        pax.passportIssueCountryCode =
                            t.passportIssueCountryCode || "";
                    }
                    if (i === 0 && t.gstNumber) {
                        pax.gst = {
                            gstCompanyName: t.gstCompanyName || "",
                            gstNumber: t.gstNumber,
                            gstCompanyAddress: t.gstCompanyAddress || "",
                            gstCompanyEmail: t.gstCompanyEmail || "",
                            gstCompanyContactNumber: t.gstCompanyPhone || "",
                        };
                    }
                    return pax;
                });
                const lead = list[0];
                if (lead) {
                    for (let i = 1; i < list.length; i++) {
                        list[i].addressLine1 = lead.addressLine1;
                        list[i].city = lead.city;
                        list[i].contactNo = lead.contactNo;
                        list[i].email = lead.email;
                    }
                }
                return list;
            })(),
        };
    };

    const handlePay = () => {
        setBookingError(null);
        let payload;
        try {
            payload = buildPayload();
        } catch (err) {
            setBookingError(
                err?.message ||
                    "Fare details are missing for one or more passengers. Please refresh and try again.",
            );
            return;
        }
        initiateBooking(
            payload,
            (booking) =>
                navigate("/booking/confirmation", {
                    state: { booking, outboundFlight },
                }),
            (err) => setBookingError(err),
        );
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <BookingProcessingOverlay
                isVisible={isProcessing}
                step={processingStep}
            />

            {/* Gradient banner */}
            <div className="h-60 bg-gradient-to-r from-[#FF2E57] to-[#0047FF]" />
            <Navbar />

            {/* 2-column grid */}
            <div className="max-w-6xl mx-auto px-4 -mt-32 grid grid-cols-1 lg:grid-cols-3 gap-6 pb-12">
                {/* LEFT COLUMN (2/3) */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Section 1: Flight Details */}
                    <div>
                        <SectionHeader
                            number={1}
                            icon={Plane}
                            title="Flight Details"
                            subtitle="Review your flight itinerary"
                        />
                        <div className="space-y-4">
                            <FlightItineraryCard
                                flight={outboundFlight}
                                selectedFare={outboundSelectedFare}
                                title={isRoundtrip ? "Outbound" : undefined}
                            />
                            {isRoundtrip && (
                                <FlightItineraryCard
                                    flight={returnFlight}
                                    selectedFare={returnSelectedFare}
                                    title="Return"
                                />
                            )}
                        </div>
                    </div>

                    {/* Section 2: Traveller Details */}
                    <div>
                        <SectionHeader
                            number={2}
                            icon={Users}
                            title="Traveller Details"
                            subtitle="Enter names as on government-issued ID"
                        />
                        <TravellerForm
                            travellers={travellers}
                            setTravellers={setTravellers}
                            fareQuoteFlags={fareQuoteFlags}
                        />
                    </div>

                    {/* Section 3: Contact Details */}
                    <div>
                        <SectionHeader
                            number={3}
                            icon={Phone}
                            title="Contact Details"
                            subtitle="Booking confirmation will be sent here"
                        />
                        <ContactDetailsSection
                            travellers={travellers}
                            setTravellers={setTravellers}
                        />
                    </div>

                    {/* Section 4: Add-ons (SSR) */}
                    <div>
                        <SectionHeader
                            number={4}
                            icon={ShoppingBag}
                            title="Add-ons"
                            subtitle="Select seats, meals & extra baggage"
                        />
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                            {ssrTotal > 0 && (
                                <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4">
                                    <p className="text-xs font-semibold uppercase tracking-wide text-green-700 mb-2">
                                        Selected Add-ons
                                    </p>
                                    <div className="flex flex-wrap gap-4 text-sm text-green-800">
                                        {seatTotal > 0 && (
                                            <span className="flex items-center gap-1">
                                                <Armchair className="w-4 h-4" />{" "}
                                                Seats: ₹{currencyFmt(seatTotal)}
                                            </span>
                                        )}
                                        {mealTotal > 0 && (
                                            <span className="flex items-center gap-1">
                                                <UtensilsCrossed className="w-4 h-4" />{" "}
                                                Meals: ₹{currencyFmt(mealTotal)}
                                            </span>
                                        )}
                                        {bagTotal > 0 && (
                                            <span className="flex items-center gap-1">
                                                <Luggage className="w-4 h-4" />{" "}
                                                Baggage: ₹
                                                {currencyFmt(bagTotal)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            <button
                                disabled={!travellersComplete || ssrLoading}
                                onClick={() => setShowSSR(true)}
                                className={`w-full py-3 rounded-xl font-semibold text-sm transition flex items-center justify-center gap-2 ${
                                    travellersComplete
                                        ? "bg-gradient-to-r from-[#0047FF] to-[#0066FF] text-white hover:shadow-md"
                                        : "bg-gray-100 text-gray-400 cursor-not-allowed"
                                }`}
                            >
                                {ssrLoading ? (
                                    <span className="flex items-center gap-2">
                                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        Loading...
                                    </span>
                                ) : (
                                    <>
                                        <ShoppingBag className="w-4 h-4" />
                                        {ssrTotal > 0
                                            ? "Modify Seats / Meals / Baggage"
                                            : "Select Seats / Meals / Baggage"}
                                    </>
                                )}
                            </button>
                            {!travellersComplete && (
                                <p className="text-xs text-gray-400 mt-2 text-center">
                                    Complete traveller &amp; contact details to
                                    unlock add-ons
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Section 5: Important Info */}
                    <div>
                        <SectionHeader
                            number={5}
                            icon={Info}
                            title="Important Information"
                        />
                        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5">
                            <ul className="space-y-2 text-sm text-amber-900">
                                {[
                                    "Carry a valid photo ID (Aadhaar / Passport / Driving Licence).",
                                    "Web check-in opens 48 hours before departure.",
                                    "Arrive at the airport at least 2 hours before domestic departure.",
                                    "Passenger name must exactly match your government-issued ID.",
                                ].map((tip, i) => (
                                    <li
                                        key={i}
                                        className="flex items-start gap-2"
                                    >
                                        <Info className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                                        <span>{tip}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Section 6: Payment */}
                    <div>
                        <SectionHeader
                            number={6}
                            icon={CreditCard}
                            title="Payment"
                            subtitle="Secure checkout powered by Razorpay"
                        />
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                            <div className="flex items-center gap-3 mb-4 flex-wrap">
                                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                                    <Shield className="w-4 h-4 text-green-600" />
                                    <span>100% Secure Payment</span>
                                </div>
                                <div className="flex items-center gap-2 ml-auto">
                                    {[
                                        visaLogo,
                                        mastercardLogo,
                                        rupayLogo,
                                        upiLogo,
                                    ].map((logo, i) => (
                                        <img
                                            key={i}
                                            src={logo}
                                            alt="payment method"
                                            className="h-6 object-contain opacity-70"
                                        />
                                    ))}
                                </div>
                            </div>

                            <button
                                disabled={!travellersComplete}
                                onClick={handlePay}
                                className={`w-full py-3.5 rounded-xl font-bold text-base transition flex items-center justify-center gap-2 ${
                                    travellersComplete
                                        ? "bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] text-white hover:shadow-lg hover:shadow-[#FF2E57]/25 active:scale-[0.98]"
                                        : "bg-gray-200 text-gray-400 cursor-not-allowed"
                                }`}
                            >
                                <CreditCard className="w-5 h-5" />
                                Pay ₹{currencyFmt(grandTotal)} &amp; Book
                            </button>

                            {bookingError && (
                                <div className="mt-3 flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
                                    <Info className="w-4 h-4 mt-0.5 shrink-0" />
                                    <div className="flex flex-col gap-2">
                                        <span>{bookingError}</span>
                                        {bookingError.includes(
                                            "session has expired",
                                        ) && (
                                            <button
                                                onClick={() => navigate("/")}
                                                className="self-start px-4 py-1.5 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 transition"
                                            >
                                                Search Again
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN (1/3) — Fare Summary */}
                <div className="hidden lg:block">
                    <FareSummary
                        outboundFare={outboundSelectedFare}
                        returnFare={returnSelectedFare}
                        passengers={passengers}
                        seatTotal={seatTotal}
                        mealTotal={mealTotal}
                        bagTotal={bagTotal}
                        ssrTotal={ssrTotal}
                    />
                </div>

                {/* Mobile fare summary (fixed bottom bar) */}
                <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-between shadow-[0_-4px_12px_rgba(0,0,0,0.08)]">
                    <div>
                        <p className="text-xs text-gray-500">Total Fare</p>
                        <p className="text-lg font-extrabold bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] bg-clip-text text-transparent">
                            ₹{currencyFmt(grandTotal)}
                        </p>
                    </div>
                    <button
                        disabled={!travellersComplete}
                        onClick={handlePay}
                        className={`px-6 py-2.5 rounded-xl font-bold text-sm ${
                            travellersComplete
                                ? "bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] text-white"
                                : "bg-gray-200 text-gray-400"
                        }`}
                    >
                        Pay &amp; Book
                    </button>
                </div>
            </div>

            {/* SSR Modal */}
            {showSSR && (
                <SSRModal
                    ssrData={ssrData}
                    ssrLoading={ssrLoading}
                    travellers={travellers}
                    selectedSeats={selectedSeats}
                    setSelectedSeats={setSelectedSeats}
                    selectedMeals={selectedMeals}
                    setSelectedMeals={setSelectedMeals}
                    selectedBag={selectedBag}
                    setSelectedBag={setSelectedBag}
                    onClose={() => setShowSSR(false)}
                    hasInbound={isRoundtrip && !!ssrData?.inbound}
                />
            )}
        </div>
    );
}
