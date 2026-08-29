import pytest

from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.models import MachineType


def test_inventory_contains_requested_number_of_machines() -> None:
    machines = create_machine_inventory(5_000)

    assert len(machines) == 5_000


def test_inventory_generation_is_deterministic() -> None:
    first = create_machine_inventory(100)
    second = create_machine_inventory(100)

    assert first == second


def test_machine_ids_are_unique() -> None:
    machines = create_machine_inventory(10_000)

    machine_ids = {machine.machine_id for machine in machines}

    assert len(machine_ids) == 10_000


def test_machines_are_distributed_across_sites() -> None:
    machines = create_machine_inventory(
        machine_count=6,
        site_ids=("DE-MUC-01", "DE-BER-01"),
    )

    assert [machine.site_id for machine in machines] == [
        "DE-MUC-01",
        "DE-BER-01",
        "DE-MUC-01",
        "DE-BER-01",
        "DE-MUC-01",
        "DE-BER-01",
    ]


def test_machine_types_are_deterministic() -> None:
    machines = create_machine_inventory(3)

    assert [machine.machine_type for machine in machines] == [
        MachineType.CNC,
        MachineType.COMPRESSOR,
        MachineType.ROBOT,
    ]


@pytest.mark.parametrize("machine_count", [0, -1, -100])
def test_invalid_machine_count_is_rejected(machine_count: int) -> None:
    with pytest.raises(
        ValueError,
        match="machine_count must be greater than zero",
    ):
        create_machine_inventory(machine_count)


def test_empty_site_list_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="at least one site_id is required",
    ):
        create_machine_inventory(10, site_ids=())