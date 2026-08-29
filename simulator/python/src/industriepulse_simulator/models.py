from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class MachineType(StrEnum):
    CNC = "CNC"
    COMPRESSOR = "COMPRESSOR"
    ROBOT = "ROBOT"


@dataclass(frozen=True, slots=True)
class Machine:
    site_id: str
    machine_id: str
    machine_type: MachineType


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    event_id: str
    site_id: str
    machine_id: str
    machine_type: MachineType
    timestamp_utc: datetime
    temperature_c: float
    vibration_mm_s: float
    pressure_bar: float
    rpm: int
    sequence: int
    firmware_version: str