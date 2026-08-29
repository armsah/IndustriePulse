from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FaultType(StrEnum):
    OVERHEAT = "overheat"
    VIBRATION_DRIFT = "vibration_drift"


@dataclass(frozen=True, slots=True)
class Fault:
    machine_id: str
    fault_type: FaultType
    start_sequence: int
    duration_events: int

    def __post_init__(self) -> None:
        if self.start_sequence < 1:
            raise ValueError("start_sequence must be greater than zero")

        if self.duration_events <= 0:
            raise ValueError("duration_events must be greater than zero")

    def is_active(self, sequence: int) -> bool:
        return (
            self.start_sequence
            <= sequence
            < self.start_sequence + self.duration_events
        )