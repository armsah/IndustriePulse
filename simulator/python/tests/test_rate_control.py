import pytest
from datetime import UTC, datetime
from unittest.mock import patch

from industriepulse_simulator.cli import main
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


def test_runner_rejects_non_positive_target_rate() -> None:
    config = SimulatorConfig(seed=42)

    with pytest.raises(
        ValueError,
        match="target_events_per_second",
    ):
        SimulatorRunner(
            machines=create_machine_inventory(1),
            generator=TelemetryGenerator(config),
            sink=RecordingSink(),
            interval_seconds=config.interval_seconds,
            target_events_per_second=0,
        )


def test_runner_paces_to_target_rate() -> None:
    config = SimulatorConfig(
        seed=42,
        late_event_rate=0,
        duplicate_rate=0,
        malformed_rate=0,
        missing_event_rate=0,
    )

    sink = RecordingSink()

    runner = SimulatorRunner(
        machines=create_machine_inventory(1),
        generator=TelemetryGenerator(config),
        sink=sink,
        interval_seconds=config.interval_seconds,
        target_events_per_second=2,
    )

    with patch(
        "industriepulse_simulator.runner.perf_counter",
        side_effect=[100.0, 100.0, 100.5],
    ), patch(
        "industriepulse_simulator.runner.sleep"
    ) as sleep_mock:
        stats = runner.run_cycles(
            cycles=1,
            start_time_utc=datetime(
                2026,
                1,
                1,
                tzinfo=UTC,
            ),
        )

    sleep_mock.assert_called_once_with(0.5)
    assert stats.elapsed_seconds == 0.5
    assert stats.emitted_events_per_second == 2.0
    assert sink.closed is True


def test_cli_rejects_non_positive_target_rate() -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "--machines",
                "1",
                "--target-events-per-second",
                "0",
            ]
        )
