from __future__ import annotations

from collections.abc import Sequence

from industriepulse_simulator.models import Machine, MachineType


DEFAULT_SITE_IDS: tuple[str, ...] = (
    "DE-MUC-01",
    "DE-BER-01",
    "DE-HAM-01",
    "DE-FRA-01",
    "DE-STR-01",
)


def create_machine_inventory(
    machine_count: int,
    site_ids: Sequence[str] = DEFAULT_SITE_IDS,
) -> list[Machine]:
    if machine_count <= 0:
        raise ValueError("machine_count must be greater than zero")

    if not site_ids:
        raise ValueError("at least one site_id is required")

    machine_types = tuple(MachineType)
    machines: list[Machine] = []

    for index in range(machine_count):
        site_id = site_ids[index % len(site_ids)]
        machine_type = machine_types[index % len(machine_types)]

        machines.append(
            Machine(
                site_id=site_id,
                machine_id=f"{machine_type.value}-{index + 1:05d}",
                machine_type=machine_type,
            )
        )

    return machines