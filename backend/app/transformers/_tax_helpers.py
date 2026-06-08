"""Helpers to extract specific tax components from TBO's TaxBreakup.

Centralized because different airlines emit GST under different keys
(K3 is most common; some emit CGST/SGST/IGST separately).
"""

from __future__ import annotations

GST_KEYS = frozenset({"K3", "CGST", "SGST", "IGST"})


def extract_gst(tax_breakup) -> float | None:
    """Sum any GST-bearing keys from TBO's TaxBreakup.

    Returns None if no GST line was found at all (don't show a 'GST: ₹0' line
    when the airline simply didn't report it — it might be there, just buried
    inside Tax).
    """
    if not tax_breakup:
        return None
    total = 0.0
    found = False
    for item in tax_breakup:
        if item.key in GST_KEYS:
            total += float(item.value or 0)
            found = True
    return total if found else None
