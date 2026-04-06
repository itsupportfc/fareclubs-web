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
    ? new Date(t).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    ? new Date(t).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
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
      type="button"
      type="button"
    >
      {copied ? (
        <Check className="w-4 h-4 text-emerald-300" />
      ) : (
        <Copy className="w-4 h-4 opacity-70 hover:opacity-100" />
      )}
    </button>
  );
}

function Card({ className = "", children }) {
  return (
    <div
      className={`bg-white rounded-2xl border border-gray-100 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

function SectionTitle({ icon: Icon, title }) {
  return (
    <h2 className="font-display text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-[#0047FF]" />
      {title}
    </h2>
  );
}

function DetailCell({ label, value }) {
  return (
    <div className="rounded-xl bg-gray-50 border border-gray-100 px-4 py-3">
      <p className="text-[10px] text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="font-semibold text-gray-800 text-sm mt-1 break-words">
        {value || "--"}
      </p>
    </div>
  );
}

function Card({ className = "", children }) {
  return (
    <div
      className={`bg-white rounded-2xl border border-gray-100 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

function SectionTitle({ icon: Icon, title }) {
  return (
    <h2 className="font-display text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-[#0047FF]" />
      {title}
    </h2>
  );
}

function DetailCell({ label, value }) {
  return (
    <div className="rounded-xl bg-gray-50 border border-gray-100 px-4 py-3">
      <p className="text-[10px] text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="font-semibold text-gray-800 text-sm mt-1 break-words">
        {value || "--"}
      </p>
    </div>
  );
}

export default function BookingConfirmationPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [taxExpanded, setTaxExpanded] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const pageData = useMemo(() => {
    if (state?.booking) return state;
    try {
      const stored = sessionStorage.getItem("fc_booking_confirmation");
      if (stored) return JSON.parse(stored);
    } catch {}
    return {};
  }, [state]);

  const { booking, outboundFlight, inboundFlight } = pageData;

  if (!booking) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <Navbar />
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center mt-32 space-y-4 px-4"
          className="text-center mt-32 space-y-4 px-4"
        >
          <Info className="w-12 h-12 text-gray-300 mx-auto" />
          <p className="text-gray-500">No booking information available.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2.5 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-full font-semibold hover:shadow-lg transition-all"
            type="button"
            type="button"
          >
            Go to Home
          </button>
        </motion.div>
      </div>
    );
  }

  const bookingStatus = booking.overallStatus ?? booking.status;
  const bookingPaymentId = booking.paymentId ?? booking.razorpayPaymentId;

  const isPending = bookingStatus === "pending";
  const isPartial = bookingStatus === "partial";
  const isConfirmed = bookingStatus === "confirmed";

  const outboundLeg =
    booking.outboundLeg ?? {
      legDirection: "outbound",
      legStatus: booking.status === "pending" ? "pending" : "confirmed",
      bookingRecordId: booking.bookingId,
      providerBookingId: booking.providerBookingId,
      providerPnr: booking.pnr,
      providerTicketStatus: booking.ticketStatus,
      providerSsrDenied: booking.ssrDenied,
      providerSsrMessage: booking.ssrMessage,
      providerPriceChanged: booking.isPriceChanged,
      providerTimeChanged: booking.isTimeChanged,
      invoiceNo: booking.invoiceNo,
      invoiceAmount: booking.invoiceAmount,
      customerMessage: booking.errorMessage,
      segmentBaggage: booking.segmentBaggage,
      fareBreakdown: booking.fareBreakdown,
      miniFareRules: booking.miniFareRules,
    };

  const inboundLeg =
    booking.inboundLeg ??
    (booking.pnrInbound || booking.bookingIdInbound || booking.inboundStatus
      ? {
          legDirection: "inbound",
          legStatus: booking.inboundStatus,
          bookingRecordId: booking.bookingIdInbound,
          providerBookingId: booking.providerBookingIdInbound,
          providerPnr: booking.pnrInbound,
          providerTicketStatus: booking.ticketStatusInbound,
          invoiceNo: booking.invoiceNoInbound,
          invoiceAmount: booking.invoiceAmountInbound,
          customerMessage: booking.inboundErrorMessage,
          fareBreakdown: booking.inboundFareBreakdown,
          miniFareRules: booking.inboundMiniFareRules,
          segmentBaggage: booking.inboundSegmentBaggage,
        }
      : null);

  const primaryLeg = outboundLeg || inboundLeg;

  const displayPnr = outboundLeg?.providerPnr ?? booking.pnr ?? "PENDING";
  const displayInboundPnr =
    inboundLeg?.providerPnr ?? booking.pnrInbound ?? null;

  const displayBookingId =
    outboundLeg?.bookingRecordId ?? booking.bookingId ?? "--";
  const displayInboundBookingId =
    inboundLeg?.bookingRecordId ?? booking.bookingIdInbound ?? null;

  const displayInvoiceNo =
    outboundLeg?.invoiceNo ?? booking.invoiceNo ?? null;
  const displayInvoiceAmount =
    outboundLeg?.invoiceAmount ?? booking.invoiceAmount ?? null;

  const displayTicketStatus =
    outboundLeg?.providerTicketStatus ??
    inboundLeg?.providerTicketStatus ??
    booking.ticketStatus;

  const ticketStatusLabel =
    TICKET_STATUS_LABELS[displayTicketStatus] ||
    `Status ${displayTicketStatus ?? "--"}`;

  const passengers = booking.passengers || [];
  const fareBreakdown =
    outboundLeg?.fareBreakdown ?? inboundLeg?.fareBreakdown ?? null;
  const segmentBaggage =
    outboundLeg?.segmentBaggage ?? inboundLeg?.segmentBaggage ?? [];
  const miniFareRules =
    outboundLeg?.miniFareRules ?? inboundLeg?.miniFareRules ?? [];

  const legs =
    outboundFlight?.segments?.flatMap((s) => s.segments || [s]) || [];

  const hasPriceOrTimeNotice = [outboundLeg, inboundLeg].some(
    (leg) => leg?.providerPriceChanged || leg?.providerTimeChanged,
  );

  const ssrNoticeLeg = [outboundLeg, inboundLeg].find(
    (leg) => leg?.providerSsrDenied,
  );

  const ticketStatusLabel =
    TICKET_STATUS_LABELS[booking.ticketStatus] ||
    `Status ${booking.ticketStatus}`;

  const handleDownloadEticket = async ({
  bookingId,
  pnr,
  fileLabel = "ETicket",
}) => {
  if (!bookingId || !pnr || pnr === "PENDING") return;

  setDownloading(true);
  try {
    const blob = await downloadEticketAPI(bookingId, pnr);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `FareClubs_${fileLabel}_${pnr}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("[ETicket] Download failed:", err.message);
  } finally {
    setDownloading(false);
  }
};

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="h-52 bg-gradient-to-r from-[#FF2E57] via-[#8B5CF6] to-[#0047FF]" />
      <div className="h-52 bg-gradient-to-r from-[#FF2E57] via-[#8B5CF6] to-[#0047FF]" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-32 pb-16">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          {/* LEFT COLUMN */}
          <div className="xl:col-span-8 space-y-6">
            {/* Status Banner */}
            <motion.div
              custom={0}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              {isPending ? (
                <Card className="p-7 text-center shadow-lg border-amber-100">
                  <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-4">
                    <Clock className="w-7 h-7 text-amber-500" />
                  </div>
                  <h1 className="font-display text-2xl text-amber-600 font-bold">
                    Booking Pending
                  </h1>
                  <p className="text-gray-500 mt-2 text-sm max-w-md mx-auto">
                    Your payment was successful. Our team is verifying your
                    booking with the airline and will confirm shortly.
                  </p>

                  {booking.razorpayPaymentId && (
                    <p className="text-xs text-gray-400 mt-3 font-mono break-all">
                      Payment Ref: {booking.razorpayPaymentId}
                    </p>
                  )}

                  {(booking.supportPhone || booking.supportEmail) && (
                    <div className="mt-5 inline-flex flex-col gap-2 bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 text-sm text-left">
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
                          className="flex items-center gap-2 text-amber-700 hover:underline break-all"
                        >
                          <Mail className="w-3.5 h-3.5" />
                          {booking.supportEmail}
                        </a>
                      )}
                    </div>
                  )}
                </Card>
              ) : isPartial ? (
                <Card className="overflow-hidden shadow-lg">
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-7 py-6 text-white text-center">
                    <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-3">
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

                  <div className="bg-amber-50 border-t border-amber-200 px-7 py-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-3">
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
                      <div className="mt-4 inline-flex flex-col gap-2 bg-amber-100 border border-amber-200 rounded-xl px-5 py-3 text-sm text-left">
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
                            className="flex items-center gap-2 text-amber-700 hover:underline break-all"
                          >
                            <Mail className="w-3.5 h-3.5" />
                            {booking.supportEmail}
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              ) : (
                <Card className="overflow-hidden shadow-lg">
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-7 py-7 text-white text-center">
                    <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-3">
                      <CheckCircle2 className="w-8 h-8" />
                    </div>
                    <h1 className="font-display text-2xl font-bold">
                      Booking Confirmed!
                    </h1>
                    <p className="text-emerald-100 mt-1 text-sm">
                      Your tickets have been issued. An e-ticket has been sent
                      to your email.
                    </p>
                  </div>
                </Card>
              )}
            </motion.div>

            {/* Flight Details */}
            {legs.length > 0 && (
              <motion.div
                custom={1}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
              >
                <Card className="p-6">
                  <SectionTitle icon={Plane} title="Flight Details" />

                  <div className="space-y-4">
                    {legs.map((leg, i) => {
                      const dep = leg.departure || {};
                      const arr = leg.arrival || {};
                      const carrier = leg.carrier || {};
                      const baggageInfo = segmentBaggage[i];

                      return (
                        <div
                          key={i}
                          className={`rounded-2xl border border-gray-100 p-4 sm:p-5 ${
                            i < legs.length - 1 ? "bg-white" : "bg-white"
                          }`}
                        >
                          <div className="flex flex-wrap items-center gap-2 mb-4">
                            <span className="text-xs font-bold text-gray-900 bg-gray-100 px-2.5 py-1 rounded-md">
                              {carrier.code || "--"} {leg.flightNumber || "--"}
                            </span>
                            <span className="text-xs text-gray-500">
                              {carrier.name || ""}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-5 items-center">
                            <div>
                              <p className="font-display text-2xl font-bold text-gray-900">
                                {formatTime(dep.time || leg.departureTime)}
                              </p>
                              <p className="text-sm font-semibold text-gray-700 mt-1">
                                {dep.code || dep.city || "--"}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                {dep.name || ""}{" "}
                                {dep.terminal ? `T${dep.terminal}` : ""}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                {formatDate(dep.time || leg.departureTime)}
                              </p>
                            </div>

                            <div className="flex flex-col items-center gap-2 min-w-[110px]">
                              {leg.durationMinutes && (
                                <span className="text-[11px] text-gray-400 font-medium">
                                  {Math.floor(leg.durationMinutes / 60)}h{" "}
                                  {leg.durationMinutes % 60}m
                                </span>
                              )}
                              <div className="flex items-center gap-2 w-full">
                                <div className="h-px flex-1 bg-gray-300" />
                                <Plane className="w-3.5 h-3.5 text-gray-400 rotate-90" />
                                <div className="h-px flex-1 bg-gray-300" />
                              </div>
                            </div>
                            <div className="flex flex-col items-center gap-2 min-w-[110px]">
                              {leg.durationMinutes && (
                                <span className="text-[11px] text-gray-400 font-medium">
                                  {Math.floor(leg.durationMinutes / 60)}h{" "}
                                  {leg.durationMinutes % 60}m
                                </span>
                              )}
                              <div className="flex items-center gap-2 w-full">
                                <div className="h-px flex-1 bg-gray-300" />
                                <Plane className="w-3.5 h-3.5 text-gray-400 rotate-90" />
                                <div className="h-px flex-1 bg-gray-300" />
                              </div>
                            </div>

                            <div className="md:text-right">
                              <p className="font-display text-2xl font-bold text-gray-900">
                                {formatTime(arr.time || leg.arrivalTime)}
                              </p>
                              <p className="text-sm font-semibold text-gray-700 mt-1">
                                {arr.code || arr.city || "--"}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                {arr.name || ""}{" "}
                                {arr.terminal ? `T${arr.terminal}` : ""}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                {formatDate(arr.time || leg.arrivalTime)}
                              </p>
                            </div>
                          </div>

                          {(baggageInfo ||
                            leg.checkedBaggage ||
                            leg.cabinBaggage) && (
                            <div className="mt-4 flex flex-wrap gap-2.5">
                              {(baggageInfo?.baggage || leg.checkedBaggage) && (
                                <span className="inline-flex items-center gap-1.5 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                  <Luggage className="w-3 h-3" />
                                  Check-in:{" "}
                                  {baggageInfo?.baggage || leg.checkedBaggage}
                                </span>
                              )}

                              {(baggageInfo?.cabinBaggage ||
                                leg.cabinBaggage) && (
                                <span className="inline-flex items-center gap-1.5 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                  <Luggage className="w-3 h-3" />
                                  Cabin:{" "}
                                  {baggageInfo?.cabinBaggage ||
                                    leg.cabinBaggage}
                                </span>
                              )}

                              {baggageInfo?.meal && (
                                <span className="inline-flex items-center gap-1.5 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                  🍽 Meal: {baggageInfo.meal}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Passenger Details */}
            {passengers.length > 0 && (
              <motion.div
                custom={2}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
              >
                <Card className="p-6">
                  <SectionTitle icon={Users} title="Passenger Details" />

                  {/* Mobile cards */}
                  <div className="grid gap-3 sm:hidden">
                    {passengers.map((pax, i) => {
                      const seatDisplay =
                        pax.seatNumbers?.filter(Boolean).join(" · ") || "--";

                      return (
                        <div
                          key={i}
                          className="rounded-xl border border-gray-100 bg-gray-50 p-4"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-semibold text-gray-900">
                                {pax.title} {pax.firstName} {pax.lastName}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                {PAX_LABELS[pax.paxType] || "Adult"}
                              </p>
                            </div>
                            <span className="text-xs text-gray-400">
                              #{i + 1}
                            </span>
                          </div>

                          <div className="mt-3 space-y-1.5 text-xs text-gray-600">
                            <p>Ticket: {pax.ticketNumber || "--"}</p>
                            <p>Seat: {seatDisplay}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Desktop table */}
                  <div className="hidden sm:block overflow-x-auto -mx-2">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs text-gray-400 uppercase tracking-wide">
                          <th className="px-2 pb-3 font-medium">#</th>
                          <th className="px-2 pb-3 font-medium">Passenger</th>
                          <th className="px-2 pb-3 font-medium">Type</th>
                          <th className="px-2 pb-3 font-medium">
                            Ticket Number
                          </th>
                          <th className="px-2 pb-3 font-medium">Seat(s)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {passengers.map((pax, i) => {
                          const seatDisplay =
                            pax.seatNumbers?.filter(Boolean).join(" · ") ||
                            "--";

                          return (
                            <tr key={i} className="text-gray-700">
                              <td className="px-2 py-3 text-gray-400">
                                {i + 1}
                              </td>
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
                              <td className="px-2 py-3 font-mono text-xs text-gray-500">
                                {seatDisplay}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Notices */}
            {(booking.isPriceChanged ||
              booking.isTimeChanged ||
              booking.ssrDenied) && (
              <motion.div
                custom={3}
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
          </div>

          {/* RIGHT COLUMN */}
          <div className="xl:col-span-4 space-y-6 xl:sticky xl:top-24 self-start">
            {/* PNR & Booking Details */}
            <motion.div
              custom={4}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <Card className="overflow-hidden">
                <div className="bg-gradient-to-r from-[#0047FF] to-[#0066FF] px-6 py-5">
                  <div className="grid grid-cols-1 gap-4">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="text-white">
                        <p className="text-[10px] uppercase tracking-widest text-blue-200">
                          PNR
                        </p>
                        <div className="flex items-center flex-wrap">
                          <span className="font-display text-2xl font-bold tracking-[0.16em] break-all">
                            {booking.pnr}
                          </span>
                          {booking.pnr !== "PENDING" ? (
                            <CopyButton text={booking.pnr} />
                          ) : (
                            <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-400/20 text-amber-200">
                              Processing
                            </span>
                          )}
                        </div>
                      </div>

                      <div>
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                            isConfirmed
                              ? "bg-emerald-400/20 text-emerald-100"
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

                    {booking.pnrInbound && (
                      <div className="text-white">
                        <p className="text-[10px] uppercase tracking-widest text-blue-200">
                          Return PNR
                        </p>
                        <div className="flex items-center flex-wrap">
                          <span className="font-display text-2xl font-bold tracking-[0.16em] break-all">
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
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 gap-3">
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

                  {(isConfirmed || isPartial) && (
  <div className="flex flex-col sm:flex-row xl:flex-col gap-3">
    {booking.bookingId && booking.pnr && booking.pnr !== "PENDING" && (
      <button
        onClick={() =>
          handleDownloadEticket({
            bookingId: booking.bookingId,
            pnr: booking.pnr,
            fileLabel: booking.pnrInbound ? "Outbound_ETicket" : "ETicket",
          })
        }
        disabled={downloading}
        type="button"
        className="inline-flex items-center justify-center gap-2 px-5 py-3 bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:shadow-[#FF2E57]/20 transition-all active:scale-[0.97] disabled:opacity-60"
      >
        <Download className="w-4 h-4" />
        {downloading ? "Downloading..." : booking.pnrInbound ? "Download Outbound E-Ticket" : "Download E-Ticket"}
      </button>
    )}

    {booking.bookingIdInbound &&
      booking.pnrInbound &&
      booking.pnrInbound !== "PENDING" && (
        <button
          onClick={() =>
            handleDownloadEticket({
              bookingId: booking.bookingIdInbound,
              pnr: booking.pnrInbound,
              fileLabel: "Return_ETicket",
            })
          }
          disabled={downloading}
          type="button"
          className="inline-flex items-center justify-center gap-2 px-5 py-3 bg-gradient-to-r from-[#0047FF] to-[#0066FF] text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:shadow-[#0047FF]/20 transition-all active:scale-[0.97] disabled:opacity-60"
        >
          <Download className="w-4 h-4" />
          {downloading ? "Downloading..." : "Download Return E-Ticket"}
        </button>
      )}

    <button
      onClick={() => window.print()}
      type="button"
      className="inline-flex items-center justify-center gap-2 px-5 py-3 border border-gray-200 text-gray-700 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-all active:scale-[0.97]"
    >
      <Printer className="w-4 h-4" />
      Print
    </button>
  </div>
)}
                </div>
              </Card>
            </motion.div>

            {/* Fare Breakdown */}
            {fareBreakdown && (
              <motion.div
                custom={5}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
              >
                <Card className="p-6">
                  <SectionTitle icon={Receipt} title="Fare Breakdown" />

                  <div className="space-y-3">
                    <div className="flex justify-between text-sm text-gray-700">
                      <span>Base Fare</span>
                      <span>₹{currencyFmt(fareBreakdown.baseFare)}</span>
                    </div>

                    <div className="flex justify-between text-sm text-gray-700 gap-4">
                      <button
                        onClick={() => setTaxExpanded(!taxExpanded)}
                        type="button"
                        className="flex items-center gap-1 text-gray-700 hover:text-[#0047FF] transition-colors text-left"
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
                    <div className="flex justify-between text-sm text-gray-700 gap-4">
                      <button
                        onClick={() => setTaxExpanded(!taxExpanded)}
                        type="button"
                        className="flex items-center gap-1 text-gray-700 hover:text-[#0047FF] transition-colors text-left"
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

                    {taxExpanded && fareBreakdown.taxBreakup?.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        className="space-y-1 bg-gray-50 rounded-xl p-3 border border-gray-100"
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
                    {taxExpanded && fareBreakdown.taxBreakup?.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        className="space-y-1 bg-gray-50 rounded-xl p-3 border border-gray-100"
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

                    <div className="border-t border-dashed border-gray-200 pt-4 flex justify-between items-center">
                      <span className="font-bold text-gray-900">
                        Total Paid
                      </span>
                      <span className="font-display text-2xl font-extrabold bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] bg-clip-text text-transparent">
                        ₹{currencyFmt(fareBreakdown.totalFare)}
                      </span>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Policy */}
            {miniFareRules.length > 0 && (
              <motion.div
                custom={6}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
              >
                <Card className="p-6">
                  <SectionTitle
                    icon={ShieldAlert}
                    title="Cancellation & Change Policy"
                  />

                  <div className="space-y-3">
                    {miniFareRules.map((rule, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-gray-100 bg-gray-50 p-4"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="text-xs font-medium text-gray-700">
                            {rule.journeyPoints}
                          </p>
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                              rule.type === "Cancellation"
                                ? "bg-red-50 text-red-600"
                                : "bg-blue-50 text-blue-600"
                            }`}
                          >
                            {rule.type}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                          {rule.details || "N/A"}
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Go Home */}
            <motion.div
              custom={7}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <button
                onClick={() => {
                  try {
                    sessionStorage.removeItem("fc_booking_confirmation");
                  } catch {}
                  navigate("/");
                }}
                type="button"
                className="w-full inline-flex items-center justify-center gap-2 px-8 py-3 bg-gradient-to-r from-[#FF2E57] to-[#0047FF] text-white rounded-2xl font-semibold hover:shadow-lg hover:shadow-[#FF2E57]/20 transition-all active:scale-[0.97]"
              >
                <Home className="w-4 h-4" />
                Go to Home
              </button>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}