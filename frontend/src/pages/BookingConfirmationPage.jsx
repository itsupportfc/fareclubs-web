import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/Home/Navbar";

const formatTime = (t) =>
  t
    ? new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "--";

const formatDate = (t) =>
  t ? new Date(t).toLocaleDateString([], { day: "2-digit", month: "short", year: "numeric" }) : "--";

export default function BookingConfirmationPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { booking, outboundFlight } = state || {};

  if (!booking) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <Navbar />
        <p className="text-gray-500 mt-32">No booking information available.</p>
        <button
          onClick={() => navigate("/")}
          className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-full"
        >
          Go to Home
        </button>
      </div>
    );
  }

  const isPending = booking.status === "pending";

  const legs =
    outboundFlight?.segments?.flatMap((s) => s.segments || [s]) || [];
  const firstLeg = legs[0];
  const lastLeg = legs[legs.length - 1];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-3xl mx-auto mt-24 pb-16 space-y-6 px-4">

        {/* Header — confirmed vs pending */}
        {isPending ? (
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <div className="text-5xl mb-3">&#9203;</div>
            <h1 className="text-2xl font-bold text-amber-600">Booking Pending</h1>
            <p className="text-gray-600 mt-2">
              Your payment was successful. Our team is processing your booking and will confirm shortly.
            </p>
            {booking.razorpayPaymentId && (
              <p className="text-sm text-gray-500 mt-2">
                Payment Ref: <span className="font-mono font-semibold">{booking.razorpayPaymentId}</span>
              </p>
            )}
            {(booking.supportPhone || booking.supportEmail) && (
              <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg inline-block">
                <p className="text-sm font-semibold text-amber-800 mb-1">Need help? Contact us:</p>
                {booking.supportPhone && (
                  <p className="text-sm text-amber-700">
                    Phone: <a href={`tel:${booking.supportPhone}`} className="underline">{booking.supportPhone}</a>
                  </p>
                )}
                {booking.supportEmail && (
                  <p className="text-sm text-amber-700">
                    Email: <a href={`mailto:${booking.supportEmail}`} className="underline">{booking.supportEmail}</a>
                  </p>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <div className="text-5xl mb-3">&#9989;</div>
            <h1 className="text-2xl font-bold text-green-600">Booking Confirmed!</h1>
            <p className="text-gray-500 mt-1">
              Your tickets have been issued. Check your email for details.
            </p>
          </div>
        )}

        {/* Notices */}
        {(booking.isPriceChanged || booking.isTimeChanged) && (
          <div className="bg-yellow-50 border border-yellow-300 rounded-xl p-4 text-yellow-800">
            <p className="font-semibold">Notice</p>
            <p className="text-sm mt-1">
              {booking.isPriceChanged && "The fare was updated by the airline. "}
              {booking.isTimeChanged && "The flight schedule was updated by the airline."}
            </p>
          </div>
        )}

        {booking.ssrDenied && (
          <div className="bg-orange-50 border border-orange-300 rounded-xl p-4 text-orange-800">
            <p className="font-semibold">SSR Notice</p>
            <p className="text-sm mt-1">
              {booking.ssrMessage || "Some ancillary requests (seat/meal/baggage) could not be confirmed."}
            </p>
          </div>
        )}

        {/* PNR / Booking Details */}
        <div className="bg-white rounded-xl shadow p-6 space-y-4">
          <h2 className="font-semibold text-lg border-b pb-2">Booking Details</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Outbound PNR</p>
              <p className="text-2xl font-bold text-indigo-600 tracking-widest">
                {booking.pnr}
              </p>
            </div>

            {booking.pnrInbound && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Inbound PNR</p>
                <p className="text-2xl font-bold text-indigo-600 tracking-widest">
                  {booking.pnrInbound}
                </p>
              </div>
            )}

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Booking ID</p>
              <p className="font-semibold">{booking.bookingId}</p>
            </div>

            {booking.bookingIdInbound && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">
                  Inbound Booking ID
                </p>
                <p className="font-semibold">{booking.bookingIdInbound}</p>
              </div>
            )}

            {booking.invoiceNo && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Invoice No</p>
                <p className="font-semibold">{booking.invoiceNo}</p>
              </div>
            )}

            {booking.invoiceAmount != null && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Invoice Amount</p>
                <p className="font-semibold">₹{booking.invoiceAmount}</p>
              </div>
            )}

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Ticket Status</p>
              <p className="font-semibold">
                {booking.ticketStatus === 1 ? "✅ Issued" : `Status ${booking.ticketStatus}`}
              </p>
            </div>
          </div>
        </div>

        {/* Flight Summary */}
        {legs.length > 0 && (
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="font-semibold text-lg border-b pb-2 mb-4">Flight Summary</h2>
            {legs.map((leg, i) => {
              const dep = leg.departure || {};
              const arr = leg.arrival || {};
              const carrier = leg.carrier || {};
              return (
                <div key={i} className="flex justify-between items-center py-3 border-b last:border-none">
                  <div>
                    <p className="font-bold">{formatTime(dep.time || leg.departureTime)}</p>
                    <p className="text-sm">{dep.code || dep.city || "--"}</p>
                    <p className="text-xs text-gray-500">
                      {formatDate(dep.time || leg.departureTime)}
                    </p>
                  </div>
                  <div className="text-center text-xs text-gray-500">
                    <p>{carrier.name || "--"}</p>
                    <div className="w-20 border-t border-gray-300 my-1 mx-auto" />
                    <p>{leg.flightNumber || "--"}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{formatTime(arr.time || leg.arrivalTime)}</p>
                    <p className="text-sm">{arr.code || arr.city || "--"}</p>
                    <p className="text-xs text-gray-500">
                      {formatDate(arr.time || leg.arrivalTime)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="text-center">
          <button
            onClick={() => navigate("/")}
            className="px-8 py-3 bg-indigo-600 text-white rounded-full font-semibold hover:bg-indigo-700"
          >
            Go to Home
          </button>
        </div>
      </div>
    </div>
  );
}
