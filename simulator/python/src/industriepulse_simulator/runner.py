from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.models import Machine
from industriepulse_simulator.serialization import event_to_json
from industriepulse_simulator.sinks import TelemetrySink


@dataclass(frozen=True, slots=True)
class RunStats:
    logical_events: int
    emitted_records: int
    missing_events: int
    duplicate_records: int
    late_events: int
    malformed_records: int


class SimulatorRunner:
    def __init__(
        self,
        machines: list[Machine],
        generator: TelemetryGenerator,
        sink: TelemetrySink,
        interval_seconds: float,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        self._machines = machines
        self._generator = generator
        self._sink = sink
        self._interval_seconds = interval_seconds

    def run_cycles(
        self,
        cycles: int,
        start_time_utc: datetime,
    ) -> RunStats:
        if cycles <= 0:
            raise ValueError(
                "cycles must be greater than zero"
            )

        logical_events = 0
        emitted_records = 0
        missing_events = 0
        duplicate_records = 0
        late_events = 0
        malformed_records = 0

        try:
            for cycle_index in range(cycles):
                sequence = cycle_index + 1

                timestamp_utc = (
                    start_time_utc
                    + timedelta(
                        seconds=(
                            cycle_index
                            * self._interval_seconds
                        )
                    )
                )

                for machine in self._machines:
                    logical_events += 1

                    if self._generator.should_be_missing(
                        machine,
                        sequence,
                    ):
                        missing_events += 1
                        continue

                    event = self._generator.generate(
                        machine,
                        sequence=sequence,
                        timestamp_utc=timestamp_utc,
                    )

                    if self._generator.should_be_late(
                        machine.machine_id,
                        sequence,
                    ):
                        event = (
                            self._generator
                            .apply_late_timestamp(event)
                        )
                        late_events += 1

                    if self._generator.should_be_malformed(
                        machine.machine_id,
                        sequence,
                    ):
                        malformed_payload = (
                            self._generator
                            .malformed_payload(event)
                        )

                        payload = json.dumps(
                            malformed_payload,
                            separators=(",", ":"),
                            sort_keys=True,
                        )

                        malformed_records += 1
                    else:
                        payload = event_to_json(event)

                    self._sink.write(
                        payload,
                        partition_key=machine.machine_id,
                    )
                    emitted_records += 1

                    if self._generator.should_duplicate(
                        machine.machine_id,
                        sequence,
                    ):
                        self._sink.write(
                        payload,
                        partition_key=machine.machine_id,
                    )
                        emitted_records += 1
                        duplicate_records += 1

            return RunStats(
                logical_events=logical_events,
                emitted_records=emitted_records,
                missing_events=missing_events,
                duplicate_records=duplicate_records,
                late_events=late_events,
                malformed_records=malformed_records,
            )
        finally:
            self._sink.close()
