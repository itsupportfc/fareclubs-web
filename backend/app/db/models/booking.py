from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app.db.database import Base
from app.db.models.user import TimestampMixin
from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    razorpay_order_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    razorpay_signature: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(5), server_default="INR", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # created | captured | failed | refunded
    refund_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    refund_amount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)

    bookings: Mapped[list[Booking]] = relationship(back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order={self.razorpay_order_id} status={self.status}>"


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "tbo" | future providers
    provider_booking_id: Mapped[int] = mapped_column(Integer, nullable=False)
    pnr: Mapped[str] = mapped_column(String(20), nullable=False)
    trip_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # oneway | roundtrip
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # outbound | inbound
    linked_booking_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bookings.id"), nullable=True
    )
    origin: Mapped[str] = mapped_column(String(10), nullable=False)
    destination: Mapped[str] = mapped_column(String(10), nullable=False)
    airline_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_lcc: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_domestic: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # confirmed | pending | cancelled | failed
    ticket_status: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(5), server_default="INR", nullable=False
    )
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
        return f"<Booking id={self.id} pnr={self.pnr} status={self.status}>"


class BookingPassenger(TimestampMixin, Base):
    __tablename__ = "booking_passengers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bookings.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(10), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pax_type: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 1=Adult, 2=Child, 3=Infant
    gender: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    contact_no: Mapped[str] = mapped_column(String(20), nullable=False)
    is_lead_pax: Mapped[bool] = mapped_column(Boolean, nullable=False)
    nationality: Mapped[str] = mapped_column(String(10), nullable=False)
    passport_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_pax_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ticket_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_fare: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="passengers")

    def __repr__(self) -> str:
        return f"<BookingPassenger id={self.id} name={self.first_name} {self.last_name}>"
