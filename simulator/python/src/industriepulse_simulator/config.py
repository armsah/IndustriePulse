from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulatorConfig:
    seed: int = 42
    interval_seconds: float = 5.0

    late_event_rate: float = 0.02
    duplicate_rate: float = 0.01
    malformed_rate: float = 0.001

    late_event_delay_seconds: int = 30

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        for name, value in (
            ("late_event_rate", self.late_event_rate),
            ("duplicate_rate", self.duplicate_rate),
            ("malformed_rate", self.malformed_rate),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        if self.late_event_delay_seconds <= 0:
            raise ValueError(
                "late_event_delay_seconds must be greater than zero"
            )