import React from "react";
import {
    CreditCard,
    Armchair,
    UtensilsCrossed,
    Luggage,
    Tag,
} from "lucide-react";
import { currencyFmt } from "../../utils/formatters";

export default function FareSummary({
    outboundFare,
    returnFare,
    passengers,
    seatTotal,
    mealTotal,
    bagTotal,
    ssrTotal,
}) {
    const outBaseFare = outboundFare?.baseFare || 0;
    const outTaxes = outboundFare?.taxes || 0;
    const retBaseFare = returnFare?.baseFare || 0;
    const retTaxes = returnFare?.taxes || 0;

    const totalBaseFare = outBaseFare + retBaseFare;
    const totalTaxes = outTaxes + retTaxes;
    const totalPrice =
        (outboundFare?.totalPrice || 0) + (returnFare?.totalPrice || 0);
    const grandTotal = totalPrice + ssrTotal;

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden sticky top-20">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#FF2E57] to-[#0047FF] px-5 py-4">
                <h3 className="text-white font-display text-base flex items-center gap-2">
                    <CreditCard className="w-4 h-4" />
                    Fare Summary
                </h3>
            </div>

            <div className="p-5 space-y-4">
                {/* Base Fare */}
                <div>
                    <div className="flex justify-between text-sm font-medium text-gray-700">
                        <span>Base Fare</span>
                        <span>₹{currencyFmt(totalBaseFare)}</span>
                    </div>
                    <div className="mt-1 space-y-0.5">
                        {passengers?.adults > 0 && (
                            <p className="text-xs text-gray-400 pl-3">
                                {passengers.adults} Adult
                                {passengers.adults > 1 ? "s" : ""}
                            </p>
                        )}
                        {passengers?.children > 0 && (
                            <p className="text-xs text-gray-400 pl-3">
                                {passengers.children} Child
                                {passengers.children > 1 ? "ren" : ""}
                            </p>
                        )}
                        {passengers?.infants > 0 && (
                            <p className="text-xs text-gray-400 pl-3">
                                {passengers.infants} Infant
                                {passengers.infants > 1 ? "s" : ""}
                            </p>
                        )}
                    </div>
                </div>

                {/* Taxes & Fees */}
                <div className="flex justify-between text-sm text-gray-700">
                    <span>Taxes &amp; Fees</span>
                    <span>₹{currencyFmt(totalTaxes)}</span>
                </div>

                {/* Per-flight breakdown for roundtrip */}
                {returnFare && (
                    <div className="bg-gray-50 rounded-lg p-3 space-y-1.5 text-xs text-gray-600">
                        <div className="flex justify-between">
                            <span>Outbound</span>
                            <span>₹{currencyFmt(outboundFare?.totalPrice || 0)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Return</span>
                            <span>₹{currencyFmt(returnFare?.totalPrice || 0)}</span>
                        </div>
                    </div>
                )}

                {/* Add-ons (only if SSR > 0) */}
                {ssrTotal > 0 && (
                    <div className="bg-green-50 rounded-lg p-3 space-y-1.5">
                        <p className="text-xs font-semibold text-green-700 uppercase tracking-wide">
                            Add-ons
                        </p>
                        {seatTotal > 0 && (
                            <div className="flex justify-between text-xs text-green-800">
                                <span className="flex items-center gap-1">
                                    <Armchair className="w-3.5 h-3.5" /> Seats
                                </span>
                                <span>₹{currencyFmt(seatTotal)}</span>
                            </div>
                        )}
                        {mealTotal > 0 && (
                            <div className="flex justify-between text-xs text-green-800">
                                <span className="flex items-center gap-1">
                                    <UtensilsCrossed className="w-3.5 h-3.5" /> Meals
                                </span>
                                <span>₹{currencyFmt(mealTotal)}</span>
                            </div>
                        )}
                        {bagTotal > 0 && (
                            <div className="flex justify-between text-xs text-green-800">
                                <span className="flex items-center gap-1">
                                    <Luggage className="w-3.5 h-3.5" /> Baggage
                                </span>
                                <span>₹{currencyFmt(bagTotal)}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Coupon placeholder */}
                <button className="flex items-center gap-2 text-sm text-[#0047FF] font-medium hover:underline w-full transition-colors duration-200">
                    <Tag className="w-4 h-4" />
                    Apply Coupon Code
                </button>

                {/* Grand Total */}
                <div className="border-t border-dashed border-gray-200 pt-3">
                    <div className="flex justify-between items-center">
                        <span className="font-bold text-gray-900">Grand Total</span>
                        <span className="font-display text-xl font-extrabold bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] bg-clip-text text-transparent">
                            ₹{currencyFmt(grandTotal)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
