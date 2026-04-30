"""Build FareBreakdownInfo from a TBO Fare object.

Shared between booking_transformer (Non-LCC) and tbo_transformer (LCC ticket
response) so we don't keep two parallel implementations of the same arithmetic.
"""

from __future__ import annotations

from app.schemas.internal.booking import FareBreakdownInfo
from app.transformers._tax_helpers import extract_gst


def build_fare_breakdown(fare) -> FareBreakdownInfo | None:
    if fare is None:
        return None
    base_fare = float(fare.BaseFare or 0)
    seat_charges = float(getattr(fare, "TotalSeatCharges", 0) or 0)
    meal_charges = float(getattr(fare, "TotalMealCharges", 0) or 0)
    baggage_charges = float(getattr(fare, "TotalBaggageCharges", 0) or 0)
    ssc_charges = float(getattr(fare, "TotalSpecialServiceCharges", 0) or 0)
    other_charges = float(getattr(fare, "OtherCharges", 0) or 0)
    total_fare = (
        float(fare.PublishedFare)
        if fare.PublishedFare is not None
        else base_fare + float(fare.Tax or 0)
    )

    # PublishedFare = base + (everything else). Subtract the things we surface
    # individually so `taxes_and_surcharges` doesn't double-count.
    taxes_and_surcharges = round(
        total_fare
        - base_fare
        - seat_charges
        - meal_charges
        - baggage_charges
        - ssc_charges
        - other_charges,
        2,
    )

    return FareBreakdownInfo(
        currency=fare.Currency or "INR",
        base_fare=base_fare,
        taxes_and_surcharges=taxes_and_surcharges,
        gst=extract_gst(getattr(fare, "TaxBreakup", None)),
        seat_charges=seat_charges,
        meal_charges=meal_charges,
        baggage_charges=baggage_charges,
        special_service_charges=ssc_charges,
        other_charges=other_charges,
        total_fare=total_fare,
    )
