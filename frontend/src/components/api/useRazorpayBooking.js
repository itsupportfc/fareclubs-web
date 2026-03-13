import { useCallback, useState } from "react";

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

            // 2. Create Razorpay order
            let orderData;
            try {
                const res = await fetch(
                    `${API_BASE}/flights/booking/create-order`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                        body: JSON.stringify(bookingPayload),
                    },
                );
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(
                        err?.detail || "Failed to create payment order",
                    );
                }
                orderData = await res.json();
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
                key: orderData.razorpayKeyId,
                amount: orderData.amount,
                currency: orderData.currency,
                order_id: orderData.razorpayOrderId,
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
                    setProcessingStep(0); // Verifying payment...

                    const confirmPayload = {
                        ...bookingPayload,
                        razorpayOrderId: response.razorpay_order_id,
                        razorpayPaymentId: response.razorpay_payment_id,
                        razorpaySignature: response.razorpay_signature,
                    };

                    try {
                        const confirmBooking = async (payload) => {
                            const res = await fetch(
                                `${API_BASE}/flights/booking/confirm`,
                                {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                        Authorization: `Bearer ${token}`,
                                    },
                                    body: JSON.stringify(payload),
                                },
                            );
                            if (!res.ok) {
                                if (res.status === 410) {
                                    throw new Error(
                                        "Your session expired after payment. Don't worry — your payment is safe. Please contact support@fareclubs.com for assistance.",
                                    );
                                }
                                const err = await res.json();
                                throw new Error(
                                    err?.detail ||
                                        "Booking confirmation failed",
                                );
                            }
                            return res.json();
                        };

                        setProcessingStep(1); // Booking with airline...
                        let booking = await confirmBooking(confirmPayload);
                        const needsReconfirm =
                            booking?.status === "pending" &&
                            (booking?.isPriceChanged || booking?.isTimeChanged);

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

                        setProcessingStep(2); // Generating ticket...
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
