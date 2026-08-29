import json
from datetime import UTC, datetime

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.serialization import event_to_json


def test_event_json_uses_expected_contract_fields() -> None:
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

    payload = json.loads(event_to_json(event))

    assert set(payload) == {
        "eventId",
        "siteId",
        "machineId",
        "machineType",
        "timestampUtc",
        "temperatureC",
        "vibrationMmS",
        "pressureBar",
        "rpm",
        "sequence",
        "firmwareVersion",
    }


def test_serialization_is_deterministic() -> None:
    machine = create_machine_inventory(1)[0]

    generator = TelemetryGenerator(
        SimulatorConfig(seed=42)
    )

    event = generator.generate(
        machine,
        sequence=1,
        timestamp_utc=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    assert event_to_json(event) == event_to_json(event)