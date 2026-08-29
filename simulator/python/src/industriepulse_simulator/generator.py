from __future__ import annotations

import hashlib
import random
from datetime import UTC, datetime, timedelta

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.faults import Fault, FaultType
from industriepulse_simulator.models import Machine, TelemetryEvent
from industriepulse_simulator.profiles import PROFILES


class TelemetryGenerator:
    def __init__(
        self,
        config: SimulatorConfig,
        faults: tuple[Fault, ...] = (),
    ) -> None:
        self._config = config
        self._faults = faults

    def generate(
        self,
        machine: Machine,
        sequence: int,
        timestamp_utc: datetime,
    ) -> TelemetryEvent:
        if sequence < 1:
            raise ValueError("sequence must be greater than zero")

        if timestamp_utc.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")

        timestamp_utc = timestamp_utc.astimezone(UTC)

        rng = self._event_rng(machine.machine_id, sequence)
        profile = PROFILES[machine.machine_type]

        temperature_c = rng.uniform(
            profile.temperature_c - profile.temperature_jitter,
            profile.temperature_c + profile.temperature_jitter,
        )

        vibration_mm_s = rng.uniform(
            profile.vibration_mm_s - profile.vibration_jitter,
            profile.vibration_mm_s + profile.vibration_jitter,
        )

        pressure_bar = rng.uniform(
            profile.pressure_bar - profile.pressure_jitter,
            profile.pressure_bar + profile.pressure_jitter,
        )

        rpm = rng.randint(
            profile.rpm - profile.rpm_jitter,
            profile.rpm + profile.rpm_jitter,
        )

        for fault in self._faults:
            if fault.machine_id != machine.machine_id:
                continue

            if not fault.is_active(sequence):
                continue

            progress = (
                sequence - fault.start_sequence + 1
            ) / fault.duration_events

            if fault.fault_type is FaultType.OVERHEAT:
                temperature_c += 25.0 * progress

            elif fault.fault_type is FaultType.VIBRATION_DRIFT:
                vibration_mm_s += 5.0 * progress

        return TelemetryEvent(
            event_id=self._event_id(machine.machine_id, sequence),
            site_id=machine.site_id,
            machine_id=machine.machine_id,
            machine_type=machine.machine_type,
            timestamp_utc=timestamp_utc,
            temperature_c=round(temperature_c, 2),
            vibration_mm_s=round(vibration_mm_s, 2),
            pressure_bar=round(pressure_bar, 2),
            rpm=rpm,
            sequence=sequence,
            firmware_version="1.0.0",
        )

    def should_duplicate(
        self,
        machine_id: str,
        sequence: int,
    ) -> bool:
        return (
            self._decision_rng(machine_id, sequence, "duplicate").random()
            < self._config.duplicate_rate
        )

    def should_be_late(
        self,
        machine_id: str,
        sequence: int,
    ) -> bool:
        return (
            self._decision_rng(machine_id, sequence, "late").random()
            < self._config.late_event_rate
        )

    def should_be_malformed(
        self,
        machine_id: str,
        sequence: int,
    ) -> bool:
        return (
            self._decision_rng(machine_id, sequence, "malformed").random()
            < self._config.malformed_rate
        )

    def apply_late_timestamp(
        self,
        event: TelemetryEvent,
    ) -> TelemetryEvent:
        from dataclasses import replace

        return replace(
            event,
            timestamp_utc=(
                event.timestamp_utc
                - timedelta(
                    seconds=self._config.late_event_delay_seconds
                )
            ),
        )

    def malformed_payload(
        self,
        event: TelemetryEvent,
    ) -> dict[str, object]:
        return {
            "eventId": event.event_id,
            "siteId": event.site_id,
            "machineId": event.machine_id,
            "timestampUtc": event.timestamp_utc.isoformat(),
            "temperatureC": "INVALID",
            "sequence": event.sequence,
        }

    def _event_rng(
        self,
        machine_id: str,
        sequence: int,
    ) -> random.Random:
        return random.Random(
            self._stable_seed(
                str(self._config.seed),
                machine_id,
                str(sequence),
                "telemetry",
            )
        )

    def _decision_rng(
        self,
        machine_id: str,
        sequence: int,
        decision: str,
    ) -> random.Random:
        return random.Random(
            self._stable_seed(
                str(self._config.seed),
                machine_id,
                str(sequence),
                decision,
            )
        )

    def _event_id(
        self,
        machine_id: str,
        sequence: int,
    ) -> str:
        raw = (
            f"{self._config.seed}:"
            f"{machine_id}:"
            f"{sequence}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:32]

    @staticmethod
    def _stable_seed(*parts: str) -> int:
        raw = ":".join(parts).encode("utf-8")
        digest = hashlib.sha256(raw).digest()

        return int.from_bytes(
            digest[:8],
            byteorder="big",
            signed=False,
        )