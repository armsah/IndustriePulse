from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from statistics import pstdev

from industriepulse_simulator.inventory import create_machine_inventory


@dataclass(frozen=True, slots=True)
class DistributionResult:
    strategy: str
    partition_count: int
    machine_count: int
    counts: list[int]
    minimum: int
    maximum: int
    mean: float
    max_to_mean_ratio: float
    coefficient_of_variation: float
    used_partitions: int


def stable_partition(key: str, partition_count: int) -> int:
    if partition_count <= 0:
        raise ValueError("partition_count must be greater than zero")

    digest = hashlib.sha256(key.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], byteorder="big")

    return value % partition_count


def partition_key(machine, strategy: str) -> str:
    if strategy == "machineId":
        return machine.machine_id

    if strategy == "siteId":
        return machine.site_id

    raise ValueError(f"unsupported strategy: {strategy}")


def analyze_distribution(
    machine_count: int,
    partition_count: int,
    strategy: str,
) -> DistributionResult:
    machines = create_machine_inventory(machine_count)

    counts_by_partition = Counter(
        stable_partition(
            partition_key(machine, strategy),
            partition_count,
        )
        for machine in machines
    )

    counts = [
        counts_by_partition.get(partition, 0)
        for partition in range(partition_count)
    ]

    mean = machine_count / partition_count
    standard_deviation = pstdev(counts)

    return DistributionResult(
        strategy=strategy,
        partition_count=partition_count,
        machine_count=machine_count,
        counts=counts,
        minimum=min(counts),
        maximum=max(counts),
        mean=round(mean, 2),
        max_to_mean_ratio=round(max(counts) / mean, 4),
        coefficient_of_variation=round(
            standard_deviation / mean,
            4,
        ),
        used_partitions=sum(1 for count in counts if count > 0),
    )