from __future__ import annotations

from dataclasses import dataclass

from industriepulse_simulator.models import MachineType


@dataclass(frozen=True, slots=True)
class TelemetryProfile:
    temperature_c: float
    temperature_jitter: float

    vibration_mm_s: float
    vibration_jitter: float

    pressure_bar: float
    pressure_jitter: float

    rpm: int
    rpm_jitter: int


PROFILES: dict[MachineType, TelemetryProfile] = {
    MachineType.CNC: TelemetryProfile(
        temperature_c=62.0,
        temperature_jitter=3.0,
        vibration_mm_s=2.2,
        vibration_jitter=0.4,
        pressure_bar=6.5,
        pressure_jitter=0.3,
        rpm=3200,
        rpm_jitter=250,
    ),
    MachineType.COMPRESSOR: TelemetryProfile(
        temperature_c=78.0,
        temperature_jitter=4.0,
        vibration_mm_s=3.5,
        vibration_jitter=0.6,
        pressure_bar=9.5,
        pressure_jitter=0.5,
        rpm=1800,
        rpm_jitter=120,
    ),
    MachineType.ROBOT: TelemetryProfile(
        temperature_c=48.0,
        temperature_jitter=2.5,
        vibration_mm_s=1.4,
        vibration_jitter=0.3,
        pressure_bar=5.8,
        pressure_jitter=0.4,
        rpm=1400,
        rpm_jitter=180,
    ),
}