"""Razorpay webhook handler.

Razorpay calls this endpoint server-to-server when a payment is captured or
fails. This is the safety net for the synchronous browser flow: if the user's
tab dies after Razorpay capture but before /flights/booking/confirm, the
backend would otherwise have no record of the charge. The webhook fills that
gap by persisting a Payment row and alerting staff for manual follow-up.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.db.database import get_db
from app.db.models.booking import Payment
from app.domain.booking_enums import PaymentStatus
from app.utils.email import build_orphan_payment_email, send_staff_alert_email
from app.utils.razorpay_utils import verify_webhook_signature
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    if not verify_webhook_signature(body, signature, settings.RAZORPAY_WEBHOOK_SECRET):
        logger.warning("Razorpay webhook: invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    event = await request.json()
    event_type = event.get("event", "")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")
    amount_paise = payment_entity.get("amount", 0)

    if not order_id or not payment_id:
        logger.warning(
            "Razorpay webhook: missing order_id/payment_id in event=%s", event_type
        )
        return {"status": "ignored"}

    if event_type not in ("payment.captured", "payment.failed"):
        return {"status": "ignored", "event": event_type}

    existing = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == order_id)
    )
    payment = existing.scalar_one_or_none()

    if payment is not None:
        logger.info(
            "Razorpay webhook: payment row exists for order=%s status=%s — no-op",
            order_id,
            payment.status,
        )
        return {"status": "ok", "action": "noop"}

    new_status = (
        PaymentStatus.CAPTURED.value
        if event_type == "payment.captured"
        else PaymentStatus.FAILED.value
    )
    db.add(
        Payment(
            user_id=None,
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=None,
            amount_paise=amount_paise,
            status=new_status,
        )
    )
    await db.commit()

    if event_type == "payment.captured":
        subject, html = build_orphan_payment_email(
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            amount_paise=amount_paise,
            event_type=event_type,
        )
        background_tasks.add_task(send_staff_alert_email, subject, html)

    logger.warning(
        "Razorpay webhook: ORPHAN payment recorded order=%s payment=%s event=%s",
        order_id,
        payment_id,
        event_type,
    )
    return {"status": "ok", "action": "orphan_recorded"}
