from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.db.database import Base
from app.db.models.user import TimestampMixin
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    razorpay_order_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    razorpay_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    bookings: Mapped[list[Booking]] = relationship(back_populates="payment")
    refunds: Mapped[list[Refund]] = relationship(back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order={self.razorpay_order_id} status={self.status}>"


class Refund(TimestampMixin, Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id"), nullable=False, index=True
    )
    razorpay_refund_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    payment: Mapped[Payment] = relationship(back_populates="refunds")

    def __repr__(self) -> str:
        return f"<Refund id={self.id} payment_id={self.payment_id} amount_paise={self.amount_paise}>"


class Booking(TimestampMixin, Base):
    """One row per flown leg.

    Naming rule:
    - id = our internal booking record id
    - provider_booking_id = provider-side booking id (TBO)
    - pnr = provider-side PNR
    """

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_booking_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pnr: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    trip_type: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    linked_booking_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bookings.id"), nullable=True
    )
    origin: Mapped[str] = mapped_column(String(10), nullable=False)
    destination: Mapped[str] = mapped_column(String(10), nullable=False)
    airline_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_lcc: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_domestic: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    ticket_status: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    base_fare: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_fare: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_refundable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provider_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    payment: Mapped[Payment] = relationship(back_populates="bookings")
    passengers: Mapped[list[BookingPassenger]] = relationship(back_populates="booking")
    linked_booking: Mapped[Booking | None] = relationship(
        remote_side=[id], foreign_keys=[linked_booking_id]
    )

    def __repr__(self) -> str:
        return f"<Booking id={self.id} pnr={self.pnr} direction={self.direction} status={self.status}>"


class BookingPassenger(TimestampMixin, Base):
    __tablename__ = "booking_passengers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bookings.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(10), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pax_type: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_lead_pax: Mapped[bool] = mapped_column(Boolean, nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(10), nullable=True)
    passport_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    passport_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    provider_pax_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ticket_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # JSON because one leg can still have multiple segments with separate seats.
    seat_numbers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    base_fare: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="passengers")

    def __repr__(self) -> str:
        return (
            f"<BookingPassenger id={self.id} name={self.title} {self.first_name} {self.last_name}>"
        )
