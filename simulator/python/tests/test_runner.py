from datetime import UTC, datetime

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.models import TelemetryEvent
from industriepulse_simulator.runner import SimulatorRunner
from industriepulse_simulator.sinks import TelemetrySink


class RecordingSink(TelemetrySink):
    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []
        self.closed = False

    def write(self, event: TelemetryEvent) -> None:
        self.events.append(event)

    def close(self) -> None:
        self.closed = True


def test_runner_emits_machine_count_times_cycles() -> None:
    machines = create_machine_inventory(10)
    sink = RecordingSink()

    runner = SimulatorRunner(
        machines=machines,
        generator=TelemetryGenerator(
            SimulatorConfig(seed=42)
        ),
        sink=sink,
        interval_seconds=5,
    )

    emitted = runner.run_cycles(
        cycles=3,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    assert emitted == 30
    assert len(sink.events) == 30
    assert sink.closed is True


def test_runner_assigns_sequence_per_cycle() -> None:
    machines = create_machine_inventory(2)
    sink = RecordingSink()

    runner = SimulatorRunner(
        machines=machines,
        generator=TelemetryGenerator(
            SimulatorConfig(seed=42)
        ),
        sink=sink,
        interval_seconds=5,
    )

    runner.run_cycles(
        cycles=3,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    assert [
        event.sequence
        for event in sink.events
    ] == [
        1,
        1,
        2,
        2,
        3,
        3,
    ]