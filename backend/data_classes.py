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


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
