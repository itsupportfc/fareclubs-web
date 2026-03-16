import React, { useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  Clock,
  Copy,
  Check,
  Download,
  Printer,
  Plane,
  Luggage,
  Users,
  Receipt,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Info,
  Home,
  Phone,
  Mail,
} from "lucide-react";
import Navbar from "../components/Home/Navbar";
import { downloadEticketAPI } from "../components/api/flight";
import { currencyFmt } from "../utils/formatters";

const PAX_LABELS = { 1: "Adult", 2: "Child", 3: "Infant" };
const TICKET_STATUS_LABELS = {
  1: "Confirmed",
  2: "In Progress",
  5: "Pending",
  6: "Issued",
};

const formatTime = (t) =>
  t
    ? new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "--";

const formatDate = (t) =>
  t
    ? new Date(t).toLocaleDateString([], {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "--";

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, delay: i * 0.08, ease: "easeOut" },
  }),
};

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      onClick={handleCopy}
      className="ml-2 p-1.5 rounded-lg hover:bg-white/20 transition-colors"
      title="Copy PNR"
    >
      {copied ? (
        <Check className="w-4 h-4 text-emerald-300" />
      ) : (
        <Copy className="w-4 h-4 opacity-70 hover:opacity-100" />
      )}
    </button>
  );
}

export default function BookingConfirmationPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [taxExpanded, setTaxExpanded] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // Restore from sessionStorage if navigated here via refresh
  const pageData = useMemo(() => {
    if (state?.booking) return state;
    try {
      const stored = sessionStorage.getItem("fc_booking_confirmation");
      if (stored) return JSON.parse(stored);
    } catch {}
    return {};
  }, [state]);

  const { booking, outboundFlight } = pageData;

  if (!booking) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <Navbar />
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center mt-32 space-y-4"
        >
          <Info className="w-12 h-12 text-gray-300 mx-auto" />
          <p className="text-gray-500">No booking information available.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2.5 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-full font-semibold hover:shadow-lg transition-all"
          >
            Go to Home
          </button>
        </motion.div>
      </div>
    );
  }

  const isPending = booking.status === "pending";
  const isPartial = booking.status === "partial";
  const isConfirmed = booking.status === "confirmed";

  const legs =
    outboundFlight?.segments?.flatMap((s) => s.segments || [s]) || [];

  const passengers = booking.passengers || [];
  const fareBreakdown = booking.fareBreakdown;
  const segmentBaggage = booking.segmentBaggage || [];
  const miniFareRules = booking.miniFareRules || [];

  const handleDownloadEticket = async () => {
    if (!booking.bookingId || !booking.pnr) {
      return;
    }
    setDownloading(true);
    try {
      const blob = await downloadEticketAPI(booking.bookingId, booking.pnr);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `FareClubs_ETicket_${booking.pnr}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[ETicket] Download failed:", err.message);
    } finally {
      setDownloading(false);
    }
  };

  const ticketStatusLabel =
    TICKET_STATUS_LABELS[booking.ticketStatus] ||
    `Status ${booking.ticketStatus}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* Top gradient banner */}
      <div className="h-52 bg-gradient-to-r from-[#FF2E57] to-[#0047FF]" />

      <div className="max-w-3xl mx-auto px-4 -mt-36 pb-16 space-y-5">
        {/* ── Status Banner ── */}
        <motion.div
          custom={0}
          initial="hidden"
          animate="visible"
          variants={fadeUp}
        >
          {isPending ? (
            <div className="bg-white rounded-2xl shadow-lg border border-amber-100 p-7 text-center">
              <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-4">
                <Clock className="w-7 h-7 text-amber-500" />
              </div>
              <h1 className="font-display text-2xl text-amber-600 font-bold">
                Booking Pending
              </h1>
              <p className="text-gray-500 mt-2 text-sm max-w-md mx-auto">
                Your payment was successful. Our team is verifying your booking
                with the airline and will confirm shortly.
              </p>
              {booking.razorpayPaymentId && (
                <p className="text-xs text-gray-400 mt-3 font-mono">
                  Payment Ref: {booking.razorpayPaymentId}
                </p>
              )}
              {(booking.supportPhone || booking.supportEmail) && (
                <div className="mt-5 inline-flex flex-col gap-1.5 bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 text-sm">
                  <p className="font-semibold text-amber-800 text-xs uppercase tracking-wide">
                    Need help?
                  </p>
                  {booking.supportPhone && (
                    <a
                      href={`tel:${booking.supportPhone}`}
                      className="flex items-center gap-2 text-amber-700 hover:underline"
                    >
                      <Phone className="w-3.5 h-3.5" />
                      {booking.supportPhone}
                    </a>
                  )}
                  {booking.supportEmail && (
                    <a
                      href={`mailto:${booking.supportEmail}`}
                      className="flex items-center gap-2 text-amber-700 hover:underline"
                    >
                      <Mail className="w-3.5 h-3.5" />
                      {booking.supportEmail}
                    </a>
                  )}
                </div>
              )}
            </div>
          ) : isPartial ? (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              {/* Confirmed leg */}
              <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-7 py-5 text-white text-center">
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-2">
                  <CheckCircle2 className="w-7 h-7" />
                </div>
                <h1 className="font-display text-xl font-bold">
                  {booking.inboundStatus === "failed"
                    ? "Outbound Flight Confirmed"
                    : "Return Flight Confirmed"}
                </h1>
                <p className="text-emerald-100 mt-1 text-sm">
                  {booking.inboundStatus === "failed"
                    ? "Your outbound ticket has been issued."
                    : "Your return ticket has been issued."}
                </p>
              </div>
              {/* Failed leg */}
              <div className="bg-amber-50 border-t border-amber-200 px-7 py-5 text-center">
                <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-2">
                  <AlertTriangle className="w-6 h-6 text-amber-500" />
                </div>
                <h2 className="font-display text-lg font-bold text-amber-700">
                  {booking.inboundStatus === "failed"
                    ? "Return Flight Needs Attention"
                    : "Outbound Flight Needs Attention"}
                </h2>
                <p className="text-amber-600 mt-1 text-sm max-w-md mx-auto">
                  {booking.inboundErrorMessage ||
                    booking.errorMessage ||
                    "One of your flights encountered an issue. Our team has been notified and will resolve this shortly."}
                </p>
                {(booking.supportPhone || booking.supportEmail) && (
                  <div className="mt-4 inline-flex flex-col gap-1.5 bg-amber-100 border border-amber-200 rounded-xl px-5 py-3 text-sm">
                    <p className="font-semibold text-amber-800 text-xs uppercase tracking-wide">
                      Need help?
                    </p>
                    {booking.supportPhone && (
                      <a
                        href={`tel:${booking.supportPhone}`}
                        className="flex items-center gap-2 text-amber-700 hover:underline"
                      >
                        <Phone className="w-3.5 h-3.5" />
                        {booking.supportPhone}
                      </a>
                    )}
                    {booking.supportEmail && (
                      <a
                        href={`mailto:${booking.supportEmail}`}
                        className="flex items-center gap-2 text-amber-700 hover:underline"
                      >
                        <Mail className="w-3.5 h-3.5" />
                        {booking.supportEmail}
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-7 py-6 text-white text-center">
                <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-3">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h1 className="font-display text-2xl font-bold">
                  Booking Confirmed!
                </h1>
                <p className="text-emerald-100 mt-1 text-sm">
                  Your tickets have been issued. An e-ticket has been sent to
                  your email.
                </p>
              </div>
            </div>
          )}
        </motion.div>

        {/* ── PNR & Booking Details Card ── */}
        <motion.div
          custom={1}
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
        >
          {/* PNR strip */}
          <div className="bg-gradient-to-r from-[#0047FF] to-[#0066FF] px-6 py-4 flex flex-wrap items-center gap-x-8 gap-y-3">
            <div className="text-white">
              <p className="text-[10px] uppercase tracking-widest text-blue-200">
                PNR
              </p>
              <div className="flex items-center">
                <span className="font-display text-2xl font-bold tracking-[0.2em]">
                  {booking.pnr}
                </span>
                {booking.pnr !== "PENDING" && (
                  <CopyButton text={booking.pnr} />
                )}
                {booking.pnr === "PENDING" && (
                  <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-400/20 text-amber-200">
                    Processing
                  </span>
                )}
              </div>
            </div>
            {booking.pnrInbound && (
              <div className="text-white">
                <p className="text-[10px] uppercase tracking-widest text-blue-200">
                  Return PNR
                </p>
                <div className="flex items-center">
                  <span className="font-display text-2xl font-bold tracking-[0.2em]">
                    {booking.pnrInbound}
                  </span>
                  {booking.pnrInbound !== "PENDING" ? (
                    <CopyButton text={booking.pnrInbound} />
                  ) : (
                    <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-400/20 text-amber-200">
                      Processing
                    </span>
                  )}
                </div>
              </div>
            )}
            <div className="ml-auto">
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                  isConfirmed
                    ? "bg-emerald-400/20 text-emerald-100"
                    : isPartial
                      ? "bg-amber-400/20 text-amber-100"
                      : "bg-amber-400/20 text-amber-100"
                }`}
              >
                {isConfirmed ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : (
                  <Clock className="w-3.5 h-3.5" />
                )}
                {isPartial ? "Partial" : ticketStatusLabel}
              </span>
            </div>
          </div>

          {/* Details grid */}
          <div className="px-6 py-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <DetailCell label="Booking ID" value={booking.bookingId} />
            {booking.bookingIdInbound && (
              <DetailCell
                label="Return Booking ID"
                value={booking.bookingIdInbound}
              />
            )}
            {booking.invoiceNo && (
              <DetailCell label="Invoice No" value={booking.invoiceNo} />
            )}
            {booking.invoiceAmount != null && (
              <DetailCell
                label="Invoice Amount"
                value={`₹${currencyFmt(booking.invoiceAmount)}`}
              />
            )}
          </div>

          {/* Action buttons — e-ticket download only for fully confirmed */}
          {(isConfirmed || isPartial) && (
            <div className="px-6 pb-5 flex flex-wrap gap-3">
              {isConfirmed && (
                <button
                  onClick={handleDownloadEticket}
                  disabled={downloading}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:shadow-[#FF2E57]/20 transition-all active:scale-[0.97] disabled:opacity-60"
                >
                  <Download className="w-4 h-4" />
                  {downloading ? "Downloading..." : "Download E-Ticket"}
                </button>
              )}
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-2 px-5 py-2.5 border border-gray-200 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-all active:scale-[0.97]"
              >
                <Printer className="w-4 h-4" />
                Print
              </button>
            </div>
          )}
        </motion.div>

        {/* ── Flight Timeline ── */}
        {legs.length > 0 && (
          <motion.div
            custom={2}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
          >
            <h2 className="font-display text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Plane className="w-4 h-4 text-[#0047FF]" />
              Flight Details
            </h2>
            <div className="space-y-0">
              {legs.map((leg, i) => {
                const dep = leg.departure || {};
                const arr = leg.arrival || {};
                const carrier = leg.carrier || {};
                const baggageInfo = segmentBaggage[i];

                return (
                  <div
                    key={i}
                    className={`py-4 ${
                      i < legs.length - 1
                        ? "border-b border-dashed border-gray-200"
                        : ""
                    }`}
                  >
                    {/* Airline + Flight number */}
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-bold text-gray-900 bg-gray-100 px-2.5 py-1 rounded-md">
                        {carrier.code || "--"}{" "}
                        {leg.flightNumber || "--"}
                      </span>
                      <span className="text-xs text-gray-500">
                        {carrier.name || ""}
                      </span>
                    </div>

                    {/* Timeline row */}
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <p className="font-display text-xl font-bold text-gray-900">
                          {formatTime(dep.time || leg.departureTime)}
                        </p>
                        <p className="text-sm font-medium text-gray-700">
                          {dep.code || dep.city || "--"}
                        </p>
                        <p className="text-xs text-gray-400">
                          {dep.name || ""}{" "}
                          {dep.terminal ? `T${dep.terminal}` : ""}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(dep.time || leg.departureTime)}
                        </p>
                      </div>

                      <div className="flex flex-col items-center gap-1 min-w-[80px]">
                        {leg.durationMinutes && (
                          <span className="text-[10px] text-gray-400">
                            {Math.floor(leg.durationMinutes / 60)}h{" "}
                            {leg.durationMinutes % 60}m
                          </span>
                        )}
                        <div className="flex items-center gap-1 w-full">
                          <div className="h-px flex-1 bg-gray-300" />
                          <Plane className="w-3 h-3 text-gray-400 rotate-90" />
                          <div className="h-px flex-1 bg-gray-300" />
                        </div>
                      </div>

                      <div className="flex-1 text-right">
                        <p className="font-display text-xl font-bold text-gray-900">
                          {formatTime(arr.time || leg.arrivalTime)}
                        </p>
                        <p className="text-sm font-medium text-gray-700">
                          {arr.code || arr.city || "--"}
                        </p>
                        <p className="text-xs text-gray-400">
                          {arr.name || ""}{" "}
                          {arr.terminal ? `T${arr.terminal}` : ""}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(arr.time || leg.arrivalTime)}
                        </p>
                      </div>
                    </div>

                    {/* Baggage info */}
                    {(baggageInfo || leg.checkedBaggage || leg.cabinBaggage) && (
                      <div className="mt-3 flex flex-wrap gap-3">
                        {(baggageInfo?.baggage || leg.checkedBaggage) && (
                          <span className="inline-flex items-center gap-1.5 text-xs text-gray-500 bg-gray-50 px-2.5 py-1 rounded-md">
                            <Luggage className="w-3 h-3" />
                            Check-in:{" "}
                            {baggageInfo?.baggage || leg.checkedBaggage}
                          </span>
                        )}
                        {(baggageInfo?.cabinBaggage || leg.cabinBaggage) && (
                          <span className="inline-flex items-center gap-1.5 text-xs text-gray-500 bg-gray-50 px-2.5 py-1 rounded-md">
                            <Luggage className="w-3 h-3" />
                            Cabin:{" "}
                            {baggageInfo?.cabinBaggage || leg.cabinBaggage}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ── Passenger Details ── */}
        {passengers.length > 0 && (
          <motion.div
            custom={3}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
          >
            <h2 className="font-display text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Users className="w-4 h-4 text-[#0047FF]" />
              Passenger Details
            </h2>

            <div className="overflow-x-auto -mx-2">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 uppercase tracking-wide">
                    <th className="px-2 pb-3 font-medium">#</th>
                    <th className="px-2 pb-3 font-medium">Passenger</th>
                    <th className="px-2 pb-3 font-medium">Type</th>
                    <th className="px-2 pb-3 font-medium">Ticket Number</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {passengers.map((pax, i) => (
                    <tr key={i} className="text-gray-700">
                      <td className="px-2 py-3 text-gray-400">{i + 1}</td>
                      <td className="px-2 py-3 font-medium">
                        {pax.title} {pax.firstName} {pax.lastName}
                      </td>
                      <td className="px-2 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                          {PAX_LABELS[pax.paxType] || "Adult"}
                        </span>
                      </td>
                      <td className="px-2 py-3 font-mono text-xs text-gray-500">
                        {pax.ticketNumber || "--"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {/* ── Fare Breakdown ── */}
        {fareBreakdown && (
          <motion.div
            custom={4}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
          >
            <h2 className="font-display text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Receipt className="w-4 h-4 text-[#0047FF]" />
              Fare Breakdown
            </h2>

            <div className="space-y-2.5">
              <div className="flex justify-between text-sm text-gray-700">
                <span>Base Fare</span>
                <span>₹{currencyFmt(fareBreakdown.baseFare)}</span>
              </div>

              <div className="flex justify-between text-sm text-gray-700">
                <button
                  onClick={() => setTaxExpanded(!taxExpanded)}
                  className="flex items-center gap-1 text-gray-700 hover:text-[#0047FF] transition-colors"
                >
                  Taxes & Fees
                  {fareBreakdown.taxBreakup?.length > 0 &&
                    (taxExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    ))}
                </button>
                <span>₹{currencyFmt(fareBreakdown.tax)}</span>
              </div>

              {/* Expandable tax breakup */}
              {taxExpanded && fareBreakdown.taxBreakup?.length > 0 && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="ml-4 space-y-1 bg-gray-50 rounded-lg p-3"
                >
                  {fareBreakdown.taxBreakup.map((tb, i) => (
                    <div
                      key={i}
                      className="flex justify-between text-xs text-gray-500"
                    >
                      <span>{tb.key}</span>
                      <span>₹{currencyFmt(tb.value)}</span>
                    </div>
                  ))}
                </motion.div>
              )}

              <div className="border-t border-dashed border-gray-200 pt-3 flex justify-between items-center">
                <span className="font-bold text-gray-900">Total Paid</span>
                <span className="font-display text-xl font-extrabold bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] bg-clip-text text-transparent">
                  ₹{currencyFmt(fareBreakdown.totalFare)}
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Cancellation / Change Policy ── */}
        {miniFareRules.length > 0 && (
          <motion.div
            custom={5}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
          >
            <h2 className="font-display text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-[#0047FF]" />
              Cancellation & Change Policy
            </h2>

            <div className="overflow-x-auto -mx-2">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 uppercase tracking-wide">
                    <th className="px-2 pb-3 font-medium">Route</th>
                    <th className="px-2 pb-3 font-medium">Type</th>
                    <th className="px-2 pb-3 font-medium">
                      Charges / Details
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {miniFareRules.map((rule, i) => (
                    <tr key={i} className="text-gray-700">
                      <td className="px-2 py-2.5 text-xs">
                        {rule.journeyPoints}
                      </td>
                      <td className="px-2 py-2.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            rule.type === "Cancellation"
                              ? "bg-red-50 text-red-600"
                              : "bg-blue-50 text-blue-600"
                          }`}
                        >
                          {rule.type}
                        </span>
                      </td>
                      <td className="px-2 py-2.5 text-xs text-gray-500">
                        {rule.details || "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {/* ── Notices ── */}
        {(booking.isPriceChanged ||
          booking.isTimeChanged ||
          booking.ssrDenied) && (
          <motion.div
            custom={6}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="space-y-3"
          >
            {(booking.isPriceChanged || booking.isTimeChanged) && (
              <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-2xl p-4">
                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm text-amber-800">
                    Notice
                  </p>
                  <p className="text-sm text-amber-700 mt-0.5">
                    {booking.isPriceChanged &&
                      "The fare was updated by the airline during booking. "}
                    {booking.isTimeChanged &&
                      "The flight schedule was updated by the airline."}
                  </p>
                </div>
              </div>
            )}

            {booking.ssrDenied && (
              <div className="flex items-start gap-3 bg-orange-50 border border-orange-200 rounded-2xl p-4">
                <Info className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm text-orange-800">
                    SSR Notice
                  </p>
                  <p className="text-sm text-orange-700 mt-0.5">
                    {booking.ssrMessage ||
                      "Some ancillary requests (seat/meal/baggage) could not be confirmed by the airline."}
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* ── Go Home ── */}
        <motion.div
          custom={7}
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          className="text-center pt-2"
        >
          <button
            onClick={() => {
              try {
                sessionStorage.removeItem("fc_booking_confirmation");
              } catch {}
              navigate("/");
            }}
            className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-full font-semibold hover:shadow-lg hover:shadow-[#FF2E57]/20 transition-all active:scale-[0.97]"
          >
            <Home className="w-4 h-4" />
            Go to Home
          </button>
        </motion.div>
      </div>
    </div>
  );
}

function DetailCell({ label, value }) {
  return (
    <div>
      <p className="text-[10px] text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="font-semibold text-gray-800 text-sm mt-0.5">{value}</p>
    </div>
  );
}
