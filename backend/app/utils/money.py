"""Money primitives. INR-only.

Two type families coexist by purpose:
  - int paise: the customer-payable total flows through cache → Razorpay as int.
    Eliminates float drift entirely.
  - Decimal: per-pax fare components (BaseFare, Tax, etc.) need safe division
    by PassengerCount with 2-decimal rounding for display. Decimal handles
    repeating decimals (`1.77 / 3`) cleanly; floats don't.

Floats appear only at two boundaries:
  - inbound: TBO JSON gives us floats. Always go through Decimal(str(value)).
  - outbound: wire responses to the frontend ship rupee floats for backwards
    compatibility. Convert at the FastAPI boundary.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

MONEY_QUANT = Decimal("0.01")


def to_decimal(value: Any) -> Decimal:
    """Convert a TBO/external numeric to Decimal safely.

    Always go through str(value). Decimal(1.77) becomes
    1.7699999999999999...; Decimal(str(1.77)) is exactly 1.77.
    """
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def to_money(value: Any) -> Decimal:
    """Round to 2 decimals using half-up — the standard money rule."""
    return to_decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def divide_money(value: Any, divisor: int | None) -> Decimal:
    """Divide and round to 2 decimals. Used for per-pax allocation."""
    safe_divisor = divisor or 1
    return (to_decimal(value) / Decimal(str(safe_divisor))).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )


def money_to_float(value: Any) -> float:
    """Convert a Decimal money value to float for JSON/wire serialization.

    This is the only place the float boundary is crossed on the way out.
    """
    return float(to_money(value))


def rupees_to_paise(rupees: Any) -> int:
    """Customer-payable rupees → integer paise.

    Used for the `verified_price_paise_*` cache and the Razorpay amount.
    Half-up rounding so 1.775 → 178 paise, never 177.
    """
    if rupees is None:
        return 0
    return int((to_decimal(rupees) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def paise_to_rupees(paise: int) -> float:
    """Integer paise → rupee float, only for wire/log display."""
    return float(Decimal(int(paise)) / 100)
