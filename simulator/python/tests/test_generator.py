from datetime import UTC, datetime

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.faults import Fault, FaultType
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory


START_TIME = datetime(
    2026,
    1,
    1,
    12,
    0,
    0,
    tzinfo=UTC,
)


def test_same_seed_produces_identical_event() -> None:
    machine = create_machine_inventory(1)[0]

    first_generator = TelemetryGenerator(
        SimulatorConfig(seed=12345)
    )
    second_generator = TelemetryGenerator(
        SimulatorConfig(seed=12345)
    )

    first = first_generator.generate(
        machine,
        sequence=1,
        timestamp_utc=START_TIME,
    )

    second = second_generator.generate(
        machine,
        sequence=1,
        timestamp_utc=START_TIME,
    )

    assert first == second


def test_different_seed_changes_generated_telemetry() -> None:
    machine = create_machine_inventory(1)[0]

    first = TelemetryGenerator(
        SimulatorConfig(seed=1)
    ).generate(
        machine,
        sequence=1,
        timestamp_utc=START_TIME,
    )

    second = TelemetryGenerator(
        SimulatorConfig(seed=2)
    ).generate(
        machine,
        sequence=1,
        timestamp_utc=START_TIME,
    )

    assert first != second


def test_event_id_is_deterministic() -> None:
    machine = create_machine_inventory(1)[0]

    generator = TelemetryGenerator(
        SimulatorConfig(seed=42)
    )

    first = generator.generate(
        machine,
        sequence=100,
        timestamp_utc=START_TIME,
    )

    second = generator.generate(
        machine,
        sequence=100,
        timestamp_utc=START_TIME,
    )

    assert first.event_id == second.event_id


def test_sequence_changes_event_id() -> None:
    machine = create_machine_inventory(1)[0]

    generator = TelemetryGenerator(
        SimulatorConfig(seed=42)
    )

    first = generator.generate(
        machine,
        sequence=1,
        timestamp_utc=START_TIME,
    )

    second = generator.generate(
        machine,
        sequence=2,
        timestamp_utc=START_TIME,
    )

    assert first.event_id != second.event_id


def test_overheat_fault_increases_temperature() -> None:
    machine = create_machine_inventory(1)[0]

    normal_generator = TelemetryGenerator(
        SimulatorConfig(seed=42)
    )

    fault_generator = TelemetryGenerator(
        SimulatorConfig(seed=42),
        faults=(
            Fault(
                machine_id=machine.machine_id,
                fault_type=FaultType.OVERHEAT,
                start_sequence=10,
                duration_events=10,
            ),
        ),
    )

    normal = normal_generator.generate(
        machine,
        sequence=15,
        timestamp_utc=START_TIME,
    )

    faulty = fault_generator.generate(
        machine,
        sequence=15,
        timestamp_utc=START_TIME,
    )

    assert faulty.temperature_c > normal.temperature_c


def test_vibration_drift_increases_vibration() -> None:
    machine = create_machine_inventory(1)[0]

    normal_generator = TelemetryGenerator(
        SimulatorConfig(seed=42)
    )

    fault_generator = TelemetryGenerator(
        SimulatorConfig(seed=42),
        faults=(
            Fault(
                machine_id=machine.machine_id,
                fault_type=FaultType.VIBRATION_DRIFT,
                start_sequence=5,
                duration_events=20,
            ),
        ),
    )

    normal = normal_generator.generate(
        machine,
        sequence=15,
        timestamp_utc=START_TIME,
    )

    faulty = fault_generator.generate(
        machine,
        sequence=15,
        timestamp_utc=START_TIME,
    )

    assert faulty.vibration_mm_s > normal.vibration_mm_s


def test_fault_is_not_active_before_start_sequence() -> None:
    machine = create_machine_inventory(1)[0]

    normal_generator = TelemetryGenerator(
        SimulatorConfig(seed=42)
    )

    fault_generator = TelemetryGenerator(
        SimulatorConfig(seed=42),
        faults=(
            Fault(
                machine_id=machine.machine_id,
                fault_type=FaultType.OVERHEAT,
                start_sequence=10,
                duration_events=10,
            ),
        ),
    )

    normal = normal_generator.generate(
        machine,
        sequence=9,
        timestamp_utc=START_TIME,
    )

    faulty = fault_generator.generate(
        machine,
        sequence=9,
        timestamp_utc=START_TIME,
    )

    assert faulty == normal


def test_late_timestamp_moves_event_backwards() -> None:
    machine = create_machine_inventory(1)[0]

    generator = TelemetryGenerator(
        SimulatorConfig(
            seed=42,
            late_event_delay_seconds=30,
        )
    )

    event = generator.generate(
        machine,
        sequence=1,
        timestamp_utc=START_TIME,
    )

    late = generator.apply_late_timestamp(event)

    assert (
        event.timestamp_utc - late.timestamp_utc
    ).total_seconds() == 30


def test_fault_decisions_are_reproducible() -> None:
    first = TelemetryGenerator(
        SimulatorConfig(seed=999)
    )

    second = TelemetryGenerator(
        SimulatorConfig(seed=999)
    )

    first_results = [
        (
            first.should_duplicate("CNC-00001", sequence),
            first.should_be_late("CNC-00001", sequence),
            first.should_be_malformed("CNC-00001", sequence),
        )
        for sequence in range(1, 1_000)
    ]

    second_results = [
        (
            second.should_duplicate("CNC-00001", sequence),
            second.should_be_late("CNC-00001", sequence),
            second.should_be_malformed("CNC-00001", sequence),
        )
        for sequence in range(1, 1_000)
    ]

    assert first_results == second_results


def test_fault_decisions_do_not_depend_on_call_order() -> None:
    generator = TelemetryGenerator(
        SimulatorConfig(seed=123)
    )

    first = generator.should_be_late(
        "CNC-00001",
        500,
    )

    for sequence in range(1, 500):
        generator.should_be_late(
            "CNC-00001",
            sequence,
        )

    second = generator.should_be_late(
        "CNC-00001",
        500,
    )

    assert first == second