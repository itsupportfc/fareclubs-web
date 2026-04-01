"""
TBO Enums

Integer enums matching TBO API values.
"""

from enum import IntEnum


class JourneyType(IntEnum):
    ONEWAY = 1
    RETURN = 2
    MULTISTOP = 3
    ADVANCE_SEARCH = 4
    SPECIAL_RETURN = 5


class PassengerType(IntEnum):
    ADULT = 1
    CHILD = 2
    INFANT = 3


class FlightCabinClass(IntEnum):
    UNKNOWN = 0
    ALL = 1
    ECONOMY = 2
    PREMIUM_ECONOMY = 3
    BUSINESS = 4
    PREMIUM_BUSINESS = 5
    FIRST = 6


class TripIndicator(IntEnum):
    OUTBOUND = 1
    INBOUND = 2


class BaggageDescriptionEnum(IntEnum):
    NOT_SET = 0
    INCLUDED = 1
    DIRECT = 2
    IMPORTED = 3
    UPGRADE = 4
    IMPORTED_UPGRADE = 5


class MealDescriptionEnum(IntEnum):
    INCLUDED = 1
    DIRECT = 2
    IMPORTED = 3  # meal charges are added while importing the tickey


class SeatAvailabilityTypeEnum(IntEnum):
    NOT_SET = 0
    AVAILABLE = 1
    RESERVED = 3
    BLOCKED = 4
    NO_SEAT_HERE = 5


class SeatDescriptionEnum(IntEnum):
    NOT_SET = 0
    INCLUDED = 1
    PURCHASE = 2  # seat charges are added while making ticket

class SeatTypeEnum(IntEnum):
    NotSet = 0
    Window = 1
    Aisle = 2
    Middle = 3
    WindowRecline = 4
    WindowWing = 5
    WindowExitRow = 6
    WindowReclineWing = 7
    WindowReclineExitRow = 8
    WindowWingExitRow = 9
    AisleRecline = 10
    AisleWing = 11
    AisleExitRow = 12
    AisleReclineWing = 13
    AisleReclineExitRow = 14
    AisleWingExitRow = 15
    MiddleRecline = 16
    MiddleWing = 17
    MiddleExitRow = 18
    MiddleReclineWing = 19
    MiddleReclineExitRow = 20
    MiddleWingExitRow = 21
    WindowReclineWingExitRow = 22
    AisleReclineWingExitRow = 23
    MiddleReclineWingExitRow = 24
    WindowBulkhead = 25
    WindowQuiet = 26
    WindowBulkheadQuiet = 27
    MiddleBulkhead = 28
    MiddleQuiet = 29
    MiddleBulkheadQuiet = 30
    AisleBulkhead = 31
    AisleQuiet = 32
    AisleBulkheadQuiet = 33
    CentreAisle = 34
    CentreMiddle = 35
    CentreAisleBulkhead = 36
    CentreAisleQuiet = 37
    CentreAisleBulkheadQuiet = 38
    CentreMiddleBulkhead = 39
    CentreMiddleQuiet = 40
    CentreMiddleBulkheadQuiet = 41
    WindowBulkheadWing = 42
    WindowBulkheadExitRow = 43
    MiddleBulkheadWing = 44
    MiddleBulkheadExitRow = 45
    AisleBulkheadWing = 46
    AisleBulkheadExitRow = 47

class SeatWayTypeEnum(IntEnum):
    SEGMENT = 1
    FULL_JOURNEY = 2