"""
Razorpay Utilities

Thin wrappers around the Razorpay Python SDK for order creation and
payment signature verification.
"""

import razorpay

from app.config import settings


def _client() -> razorpay.Client:
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_order(amount_paise: int, receipt: str) -> dict:
    """Create a Razorpay order. Returns the full order dict from Razorpay."""
    return _client().order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
        }
    )


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature.

    Returns True if valid, False if the signature is invalid.
    """
    try:
        _client().utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
