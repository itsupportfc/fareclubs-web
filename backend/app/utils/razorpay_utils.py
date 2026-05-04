"""
Razorpay Utilities

Thin wrappers around the Razorpay Python SDK for order creation and
payment signature verification.
"""

import hashlib
import hmac
import logging

import razorpay
from app.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton. The SDK holds a requests.Session internally; reusing
# this object across calls means TCP/TLS handshakes to api.razorpay.com are
# amortized. No explicit close() is needed — requests releases its pool on GC.
_razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def create_order(amount_paise: int, receipt: str) -> dict:
    """Create a Razorpay order. Returns the full order dict from Razorpay."""
    return _razorpay_client.order.create(
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
        _razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except razorpay.errors.SignatureVerificationError:
        logger.warning(
            "Payment signature verification FAILED: order_id=%s, payment_id=%s",
            order_id,
            payment_id,
        )
        return False


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify a Razorpay webhook signature.

    Different scheme from the order/payment signature: HMAC-SHA256 of the
    raw request body using the webhook secret.
    """
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
