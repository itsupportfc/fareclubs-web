import { useCallback, useState } from "react";
import { fetchWithTimeout } from "../../utils/http";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function loadRazorpayScript() {
    return new Promise((resolve) => {
        if (window.Razorpay) return resolve(true);
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
    });
}

/**
 * Hook for the 2-step Razorpay booking flow.
 *
 * Usage:
 *   const { initiateBooking, isProcessing, processingStep } = useRazorpayBooking(token);
 *   initiateBooking(payload, onSuccess, onError);
 */
export function useRazorpayBooking(token) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [processingStep, setProcessingStep] = useState(0);

    const initiateBooking = useCallback(
        async (bookingPayload, onSuccess, onError) => {
            // 1. Load Razorpay checkout script
            const loaded = await loadRazorpayScript();
            if (!loaded) {
                onError("Failed to load payment gateway. Please try again.");
                return;
            }

            // 2. Create Razorpay order — send only what the endpoint needs (no passengers)
            let orderData;
            try {
                const createOrderPayload = {
                    fareIdOutbound: bookingPayload.fareIdOutbound,
                    fareIdInbound: bookingPayload.fareIdInbound ?? null,
                    tripType: bookingPayload.tripType,
                    isInternationalReturn:
                        bookingPayload.isInternationalReturn ?? false,
                    // Explicitly named so backend can re-verify the client quote.
                    clientTotalAmount: bookingPayload.totalAmount,
                };
                setProcessingStep(1); // "Securing your fare..."
                const orderRes = await fetchWithTimeout(
                    `${API_BASE}/flights/booking/create-order`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            ...(token
                                ? { Authorization: `Bearer ${token}` }
                                : {}),
                        },
                        body: JSON.stringify(createOrderPayload),
                    },
                    15_000, // 15s timeout
                );

                if (!orderRes.ok) {
                    const err = await orderRes.json();
                    throw new Error(
                        err?.detail || "Failed to create payment order",
                    );
                }
                orderData = await orderRes.json();
            } catch (err) {
                onError(err.message);
                return;
            }

            // 3. Find lead passenger for prefill
            const leadPax =
                bookingPayload.passengers?.find((p) => p.isLeadPax) ||
                bookingPayload.passengers?.[0];

            // 4. Open Razorpay checkout modal
            const rzp = new window.Razorpay({
                key: orderData.razorpayPublicKey,
                amount: orderData.paymentAmountPaise,
                currency: orderData.paymentCurrency,
                order_id: orderData.paymentOrderId,
                name: "FareClubs",
                description: "Flight Booking",
                theme: { color: "#4F46E5" },
                prefill: {
                    name: `${leadPax?.firstName || ""} ${leadPax?.lastName || ""}`.trim(),
                    email: leadPax?.email || "",
                    contact: leadPax?.contactNo || "",
                },
                handler: async (response) => {
                    // Payment succeeded — show processing overlay
                    setIsProcessing(true);
                    setProcessingStep(0); // "Verifying payment..."

                    // Explicit payload — no spread, every field intentional
                    const confirmPayload = {
                        fareIdOutbound: bookingPayload.fareIdOutbound,
                        fareIdInbound: bookingPayload.fareIdInbound ?? null,
                        tripType: bookingPayload.tripType,
                        isInternationalReturn:
                            bookingPayload.isInternationalReturn ?? false,
                        passengers: bookingPayload.passengers,
                        clientTotalAmount: bookingPayload.totalAmount,
                        acceptPriceChange: false,
                        // Keep payment ids separate from booking ids.
                        paymentOrderId: response.razorpay_order_id,
                        paymentId: response.razorpay_payment_id,
                        paymentSignature: response.razorpay_signature,
                    };

                    const confirmBooking = async (payload) => {
                        const res = await fetchWithTimeout(
                            `${API_BASE}/flights/booking/confirm`,
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    ...(token
                                        ? { Authorization: `Bearer ${token}` }
                                        : {}),
                                },
                                body: JSON.stringify(payload),
                            },
                            120_000, // 2-min timeout — TBO ticketing can be slow
                        );
                        if (!res.ok) {
                            if (res.status === 410) {
                                throw new Error(
                                    "Your session expired after payment. Don't worry — your payment is safe. Please contact support@fareclubs.com for assistance.",
                                );
                            }
                            const err = await res.json();
                            throw new Error(
                                err?.detail || "Booking confirmation failed",
                            );
                        }
                        return res.json();
                    };

                    try {
                        setProcessingStep(1); // "Booking with airline..."
                        let booking = await confirmBooking(confirmPayload);
                        const legs = [booking?.outboundLeg, booking?.inboundLeg].filter(Boolean);
                        const needsReconfirm =
                            booking?.overallStatus === "pending" &&
                            legs.some(
                                (leg) =>
                                    leg?.providerPriceChanged ||
                                    leg?.providerTimeChanged,
                            );

                        if (needsReconfirm) {
                            const accepted = window.confirm(
                                "Airline fare/time changed. Click OK to confirm booking again with updated details.",
                            );
                            if (!accepted) {
                                setIsProcessing(false);
                                onError(
                                    "Booking paused. Please review updated fare/time and confirm again.",
                                );
                                return;
                            }

                            setProcessingStep(1);
                            booking = await confirmBooking({
                                ...confirmPayload,
                                acceptPriceChange: true,
                            });
                        }

                        setProcessingStep(2); // "Generating ticket..."
                        onSuccess(booking);
                    } catch (err) {
                        onError(err.message);
                    } finally {
                        setIsProcessing(false);
                        setProcessingStep(0);
                    }
                },
                modal: {
                    ondismiss: () => {
                        onError("Payment was cancelled. You can try again.");
                    },
                },
            });

            rzp.open();
        },
        [token],
    );

    return { initiateBooking, isProcessing, processingStep };
}
