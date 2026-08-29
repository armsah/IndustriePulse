from __future__ import annotations

from datetime import datetime, timedelta

from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.models import Machine
from industriepulse_simulator.sinks import TelemetrySink


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
    ) -> int:
        if cycles <= 0:
            raise ValueError("cycles must be greater than zero")

        emitted = 0

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
                    event = self._generator.generate(
                        machine,
                        sequence=sequence,
                        timestamp_utc=timestamp_utc,
                    )

                    self._sink.write(event)
                    emitted += 1

            return emitted
        finally:
            self._sink.close()