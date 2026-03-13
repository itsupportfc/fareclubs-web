"""Async email utilities for staff alert notifications."""

import logging
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from app.config import settings

logger = logging.getLogger(__name__)


async def send_staff_alert_email(subject: str, html_body: str) -> None:
    """Send an alert email to staff. Silently skips if SMTP is not configured."""
    if not settings.SMTP_HOST or not settings.STAFF_ALERT_EMAILS:
        logger.debug("SMTP not configured — skipping staff alert email")
        return

    recipients = [
        e.strip() for e in settings.STAFF_ALERT_EMAILS.split(",") if e.strip()
    ]
    if not recipients:
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True,
        )
        logger.info("Staff alert email sent: %s", subject)
    except Exception:
        logger.exception("Failed to send staff alert email: %s", subject)


def build_booking_failure_email(
    payload,
    error_message: str,
    razorpay_payment_id: str,
    razorpay_order_id: str,
) -> tuple[str, str]:
    """Build subject and HTML body for a booking failure alert.

    Returns (subject, html_body).
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lead_pax = next(
        (p for p in payload.passengers if p.is_lead_pax), payload.passengers[0]
    )

    subject = f"[BOOKING FAILED] {lead_pax.first_name} {lead_pax.last_name} — {payload.fare_id_outbound[:12]}"

    pax_rows = "".join(
        f"<tr><td>{p.title} {p.first_name} {p.last_name}</td>"
        f"<td>{p.email}</td><td>{p.contact_no}</td></tr>"
        for p in payload.passengers
    )

    html_body = f"""
    <html><body style="font-family:sans-serif;font-size:14px;color:#333;">
    <h2 style="color:#c0392b;">Booking Failure Alert</h2>
    <table style="border-collapse:collapse;width:100%;" cellpadding="8">
      <tr><td><strong>Timestamp</strong></td><td>{timestamp}</td></tr>
      <tr><td><strong>Razorpay Payment ID</strong></td><td>{razorpay_payment_id}</td></tr>
      <tr><td><strong>Razorpay Order ID</strong></td><td>{razorpay_order_id}</td></tr>
      <tr><td><strong>Fare ID (outbound)</strong></td><td>{payload.fare_id_outbound}</td></tr>
      <tr><td><strong>Fare ID (inbound)</strong></td><td>{payload.fare_id_inbound or "N/A"}</td></tr>
      <tr><td><strong>Trip Type</strong></td><td>{payload.trip_type}</td></tr>
      <tr><td><strong>Error</strong></td><td style="color:#c0392b;">{error_message}</td></tr>
    </table>
    <h3>Passengers</h3>
    <table style="border-collapse:collapse;width:100%;" border="1" cellpadding="6">
      <tr style="background:#f5f5f5;"><th>Name</th><th>Email</th><th>Phone</th></tr>
      {pax_rows}
    </table>
    <p style="margin-top:16px;color:#999;font-size:12px;">
      Action required: verify payment status in Razorpay dashboard and manually issue ticket or initiate refund.
    </p>
    </body></html>
    """

    return subject, html_body


def build_booking_attention_email(
    payload,
    message: str,
    razorpay_payment_id: str,
    razorpay_order_id: str,
) -> tuple[str, str]:
    """Build subject and HTML body for a non-failure booking attention alert.

    Used for in-progress / verification states that require manual monitoring.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lead_pax = next(
        (p for p in payload.passengers if p.is_lead_pax), payload.passengers[0]
    )

    subject = f"[BOOKING ATTENTION] {lead_pax.first_name} {lead_pax.last_name} — {payload.fare_id_outbound[:12]}"

    pax_rows = "".join(
        f"<tr><td>{p.title} {p.first_name} {p.last_name}</td>"
        f"<td>{p.email}</td><td>{p.contact_no}</td></tr>"
        for p in payload.passengers
    )

    html_body = f"""
        <html><body style="font-family:sans-serif;font-size:14px;color:#333;">
        <h2 style="color:#d68910;">Booking Requires Attention</h2>
        <table style="border-collapse:collapse;width:100%;" cellpadding="8">
            <tr><td><strong>Timestamp</strong></td><td>{timestamp}</td></tr>
            <tr><td><strong>Razorpay Payment ID</strong></td><td>{razorpay_payment_id}</td></tr>
            <tr><td><strong>Razorpay Order ID</strong></td><td>{razorpay_order_id}</td></tr>
            <tr><td><strong>Fare ID (outbound)</strong></td><td>{payload.fare_id_outbound}</td></tr>
            <tr><td><strong>Fare ID (inbound)</strong></td><td>{payload.fare_id_inbound or "N/A"}</td></tr>
            <tr><td><strong>Trip Type</strong></td><td>{payload.trip_type}</td></tr>
            <tr><td><strong>Status</strong></td><td style="color:#d68910;">{message}</td></tr>
        </table>
        <h3>Passengers</h3>
        <table style="border-collapse:collapse;width:100%;" border="1" cellpadding="6">
            <tr style="background:#f5f5f5;"><th>Name</th><th>Email</th><th>Phone</th></tr>
            {pax_rows}
        </table>
        <p style="margin-top:16px;color:#999;font-size:12px;">
            Action required: monitor booking status and verify final ticket issuance with provider.
        </p>
        </body></html>
        """

    return subject, html_body
