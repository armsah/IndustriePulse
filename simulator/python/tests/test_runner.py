import json
from datetime import UTC, datetime

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.runner import SimulatorRunner
from industriepulse_simulator.sinks import TelemetrySink


class RecordingSink(TelemetrySink):
    def __init__(self) -> None:
        self.payloads: list[str] = []
        self.closed = False

    def write(
        self,
        payload: str,
        partition_key: str | None = None,
    ) -> None:
        self.payloads.append(payload)

    def close(self) -> None:
        self.closed = True

def create_runner(
    config: SimulatorConfig,
    machine_count: int = 2,
) -> tuple[SimulatorRunner, RecordingSink]:
    sink = RecordingSink()

    runner = SimulatorRunner(
        machines=create_machine_inventory(machine_count),
        generator=TelemetryGenerator(config),
        sink=sink,
        interval_seconds=config.interval_seconds,
    )

    return runner, sink


def test_runner_emits_machine_count_times_cycles() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=0,
        duplicate_rate=0,
        malformed_rate=0,
        missing_event_rate=0,
    )

    runner, sink = create_runner(
        config,
        machine_count=10,
    )

    stats = runner.run_cycles(
        cycles=3,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    assert stats.logical_events == 30
    assert stats.emitted_records == 30
    assert len(sink.payloads) == 30
    assert sink.closed is True


def test_runner_assigns_sequence_per_cycle() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=0,
        duplicate_rate=0,
        malformed_rate=0,
        missing_event_rate=0,
    )

    runner, sink = create_runner(config)

    runner.run_cycles(
        cycles=3,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    sequences = [
        json.loads(payload)["sequence"]
        for payload in sink.payloads
    ]

    assert sequences == [
        1,
        1,
        2,
        2,
        3,
        3,
    ]


def test_runner_emits_identical_duplicate() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=0,
        duplicate_rate=1,
        malformed_rate=0,
        missing_event_rate=0,
    )

    runner, sink = create_runner(
        config,
        machine_count=1,
    )

    stats = runner.run_cycles(
        cycles=1,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    assert stats.logical_events == 1
    assert stats.emitted_records == 2
    assert stats.duplicate_records == 1
    assert sink.payloads[0] == sink.payloads[1]


def test_runner_injects_late_timestamp() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=1,
        duplicate_rate=0,
        malformed_rate=0,
        missing_event_rate=0,
        late_event_delay_seconds=30,
    )

    runner, sink = create_runner(
        config,
        machine_count=1,
    )

    stats = runner.run_cycles(
        cycles=1,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    payload = json.loads(sink.payloads[0])

    assert stats.late_events == 1
    assert (
        payload["timestampUtc"]
        == "2025-12-31T23:59:30+00:00"
    )


def test_runner_emits_malformed_payload() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=0,
        duplicate_rate=0,
        malformed_rate=1,
        missing_event_rate=0,
    )

    runner, sink = create_runner(
        config,
        machine_count=1,
    )

    stats = runner.run_cycles(
        cycles=1,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    payload = json.loads(sink.payloads[0])

    assert stats.malformed_records == 1
    assert payload["temperatureC"] == "INVALID"


def test_runner_skips_missing_event() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=0,
        duplicate_rate=0,
        malformed_rate=0,
        missing_event_rate=1,
    )

    runner, sink = create_runner(
        config,
        machine_count=5,
    )

    stats = runner.run_cycles(
        cycles=2,
        start_time_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    assert stats.logical_events == 10
    assert stats.missing_events == 10
    assert stats.emitted_records == 0
    assert sink.payloads == []
