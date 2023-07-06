from dataclasses import dataclass
from enum import Enum


@dataclass
class ConfigData:
    token: str


class PriorityLevel(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    NO = 4


class Weekdays(Enum):
    MONDAY = "Mon"
    TUESDAY = "Tue"
    WEDNESDAY = "Wed"
    THURSDAY = "Thu"
    FRIDAY = "Fri"
    SATURDAY = "Sat"
    SUNDAY = "Sun"
