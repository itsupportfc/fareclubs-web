"""Centralized booking and provider status enums.

Why this file exists:
- the API layer should not hardcode provider magic numbers
- the persistence layer should not import from the API layer
- one place should define how provider states map to product states
"""

from __future__ import annotations

from enum import Enum, IntEnum


class TripType(str, Enum):
    ONEWAY = "oneway"
    ROUNDTRIP = "roundtrip"


class LegDirection(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class BookingOverallStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    PARTIAL = "partial"


class BookingLegStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    FAILED = "failed"


class BookingRecordStatus(str, Enum):
    """Values stored in bookings.status in our DB."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    FAILED = "failed"
    NEEDS_ATTENTION = "needs_attention"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    CREATED = "created"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class TicketStatus(IntEnum):
    """TBO TicketStatus values.

    Keep provider names and integers here only.
    Everywhere else, call helper functions instead of comparing raw numbers.
    """

    FAILED = 0
    CONFIRMED = 1
    IN_PROGRESS = 2
    UNAVAILABLE = 3
    SYSTEM_ERROR = 4
    PENDING = 5
    ISSUED = 6
    UNKNOWN_7 = 7  # undocumented by TBO as of 2026-04
    PRICE_CHANGED = 8
    PROVIDER_ERROR = 9


class BookStatus(IntEnum):
    """TBO Book API status values returned before Ticket API."""

    NOT_SET = 0
    SUCCESSFUL = 1
    FAILED = 2
    OTHER_FARE = 3
    OTHER_CLASS = 4
    BOOKED_OTHER = 5
    NOT_CONFIRMED = 6

    @classmethod
    def to_ticket_status(cls, value: int | None) -> TicketStatus:
        if value is None:
            return TicketStatus.PENDING

        mapping: dict[int, TicketStatus] = {
            cls.NOT_SET: TicketStatus.PENDING,
            cls.SUCCESSFUL: TicketStatus.CONFIRMED,
            cls.FAILED: TicketStatus.FAILED,
            cls.OTHER_FARE: TicketStatus.PRICE_CHANGED,
            cls.OTHER_CLASS: TicketStatus.PRICE_CHANGED,
            cls.BOOKED_OTHER: TicketStatus.ISSUED,
            cls.NOT_CONFIRMED: TicketStatus.PENDING,
        }
        return mapping.get(value, TicketStatus.PENDING)


FAILED_TICKET_STATUSES = frozenset(
    {
        TicketStatus.FAILED,
        TicketStatus.UNAVAILABLE,
        TicketStatus.SYSTEM_ERROR,
        TicketStatus.PROVIDER_ERROR,
    }
)
SOFT_TICKET_STATUSES = frozenset(
    {
        TicketStatus.IN_PROGRESS,
        TicketStatus.PENDING,
        TicketStatus.UNKNOWN_7,
    }
)
SUCCESS_TICKET_STATUSES = frozenset({TicketStatus.CONFIRMED, TicketStatus.ISSUED})


def ticket_status_to_booking_record_status(ticket_status: int | None) -> str:
    """Map provider ticket status to our DB booking.status value."""

    if ticket_status in SUCCESS_TICKET_STATUSES:
        return BookingRecordStatus.CONFIRMED.value
    if ticket_status in FAILED_TICKET_STATUSES:
        return BookingRecordStatus.FAILED.value
    if ticket_status == TicketStatus.PRICE_CHANGED:
        return BookingRecordStatus.NEEDS_ATTENTION.value
    return BookingRecordStatus.PENDING.value


def ticket_status_to_leg_status(ticket_status: int | None) -> BookingLegStatus:
    """Map provider ticket status to a frontend-facing leg state."""

    if ticket_status in SUCCESS_TICKET_STATUSES:
        return BookingLegStatus.CONFIRMED
    if ticket_status in FAILED_TICKET_STATUSES:
        return BookingLegStatus.FAILED
    return BookingLegStatus.PENDING


def booking_record_status_to_leg_status(booking_status: str) -> BookingLegStatus:
    if booking_status == BookingRecordStatus.CONFIRMED.value:
        return BookingLegStatus.CONFIRMED
    if booking_status == BookingRecordStatus.FAILED.value:
        return BookingLegStatus.FAILED
    return BookingLegStatus.PENDING


def derive_overall_booking_status(
    outbound_leg_status: BookingLegStatus,
    inbound_leg_status: BookingLegStatus | None,
) -> BookingOverallStatus:
    """Trip-level truth used by the confirmation page.

    Rules:
    - one-way: mirror outbound status, but non-confirmed collapses to pending
    - roundtrip: both confirmed => confirmed
                 one confirmed + one not confirmed => partial
                 none confirmed => pending
    """

    if inbound_leg_status is None:
        if outbound_leg_status is BookingLegStatus.CONFIRMED:
            return BookingOverallStatus.CONFIRMED
        return BookingOverallStatus.PENDING

    confirmed_count = sum(
        status is BookingLegStatus.CONFIRMED
        for status in (outbound_leg_status, inbound_leg_status)
    )
    if confirmed_count == 2:
        return BookingOverallStatus.CONFIRMED
    if confirmed_count == 1:
        return BookingOverallStatus.PARTIAL
    return BookingOverallStatus.PENDING
