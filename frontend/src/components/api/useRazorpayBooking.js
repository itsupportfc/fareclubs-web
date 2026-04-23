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
            const loaded = await loadRazorpayScript();
            if (!loaded) {
                onError("Failed to load payment gateway. Please try again.");
                return;
            }

            let orderData;
            try {
                const ssrSelectionsOutbound =
                    bookingPayload.passengers?.flatMap(
                        (p) => p.ssrSegmentsOutbound ?? [],
                    ) ?? null;

                const ssrSelectionsInbound = bookingPayload.fareIdInbound
                    ? (bookingPayload.passengers?.flatMap(
                          (p) => p.ssrSegmentsInbound ?? [],
                      ) ?? null)
                    : null;

                const createOrderPayload = {
                    fareIdOutbound: bookingPayload.fareIdOutbound,
                    fareIdInbound: bookingPayload.fareIdInbound ?? null,
                    tripType: bookingPayload.tripType,
                    isInternationalReturn:
                        bookingPayload.isInternationalReturn ?? false,
                    clientTotalAmount: bookingPayload.totalAmount,
                    ssrSelectionsOutbound,
                    ssrSelectionsInbound,
                };

                setProcessingStep(1);

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
                    15_000,
                );

                if (!orderRes.ok) {
                    const err = await orderRes.json();
                    throw new Error(
                        err?.detail || "Failed to create payment order",
                    );
                }

                orderData = await orderRes.json();
                // console.log("[CREATE ORDER SUCCESS BODY]", orderData);
            } catch (err) {
                // console.error("[CREATE ORDER ERROR]", err);
                onError(err.message);
                return;
            }

            const leadPax =
                bookingPayload.passengers?.find((p) => p.isLeadPax) ||
                bookingPayload.passengers?.[0];

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
                    setIsProcessing(true);
                    setProcessingStep(0);

                    const confirmPayload = {
                        fareIdOutbound: bookingPayload.fareIdOutbound,
                        fareIdInbound: bookingPayload.fareIdInbound ?? null,
                        tripType: bookingPayload.tripType,
                        isInternationalReturn:
                            bookingPayload.isInternationalReturn ?? false,
                        passengers: bookingPayload.passengers,
                        clientTotalAmount: bookingPayload.totalAmount,
                        paymentOrderId: response.razorpay_order_id,
                        paymentId: response.razorpay_payment_id,
                        paymentSignature: response.razorpay_signature,
                    };

                    const confirmBooking = async (payload) => {
                        // console.log("[CONFIRM PAYLOAD SENT]", payload);

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
                            240_000,
                        );

                        // console.log(
                        //     "[CONFIRM RESPONSE STATUS]",
                        //     res.status,
                        //     res.ok,
                        // );

                        if (!res.ok) {
                            if (res.status === 410) {
                                throw new Error(
                                    "Your session expired after payment. Don't worry — your payment is safe. Please contact support@fareclubs.com for assistance.",
                                );
                            }

                            const err = await res.json();
                            // console.error("[CONFIRM API ERROR BODY]", err);
                            throw new Error(
                                err?.detail || "Booking confirmation failed",
                            );
                        }

                        const data = await res.json();
                        // console.log("[CONFIRM API SUCCESS BODY]", data);
                        return data;
                    };

                    try {
                        setProcessingStep(1);
                        const booking = await confirmBooking(confirmPayload);
                        setProcessingStep(2);
                        onSuccess(booking);
                    } catch (err) {
                        // map the timeout to a user friendly message
                        const isTimeout =
                            err?.name === "TimeoutError" ||
                            err?.name === "AbortError";
                        onError(
                            isTimeout
                                ? "Your payment was received and your booking is still being finalized. Please check your email in a few minutes for your e-ticket. Do NOT pay again - contact support@fareclubs.com if you dont receive an email within 15 minutes."
                                : err.message,
                        );
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
