import json
from datetime import UTC, datetime

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.sinks import JsonlFileSink


def test_jsonl_sink_writes_one_event_per_line(tmp_path) -> None:
    machine = create_machine_inventory(1)[0]

    event = TelemetryGenerator(
        SimulatorConfig(seed=42)
    ).generate(
        machine,
        sequence=1,
        timestamp_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    output_file = tmp_path / "telemetry.jsonl"

    sink = JsonlFileSink(output_file)
    sink.write(event)
    sink.close()

    lines = output_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    payload = json.loads(lines[0])

    assert payload["machineId"] == machine.machine_id
    assert payload["sequence"] == 1


def test_jsonl_sink_creates_parent_directories(tmp_path) -> None:
    machine = create_machine_inventory(1)[0]

    event = TelemetryGenerator(
        SimulatorConfig(seed=42)
    ).generate(
        machine,
        sequence=1,
        timestamp_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    output_file = (
        tmp_path
        / "nested"
        / "directory"
        / "telemetry.jsonl"
    )

    sink = JsonlFileSink(output_file)
    sink.write(event)
    sink.close()

    assert output_file.exists()