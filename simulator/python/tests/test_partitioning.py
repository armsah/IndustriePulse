import pytest

from industriepulse_simulator.partitioning import (
    analyze_distribution,
    stable_partition,
)


def test_stable_partition_is_deterministic() -> None:
    first = stable_partition("CNC-00001", 8)
    second = stable_partition("CNC-00001", 8)

    assert first == second


@pytest.mark.parametrize("partition_count", [1, 4, 8, 16])
def test_partition_is_within_range(partition_count: int) -> None:
    partition = stable_partition("CNC-00001", partition_count)

    assert 0 <= partition < partition_count


def test_partition_count_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="partition_count must be greater than zero",
    ):
        stable_partition("CNC-00001", 0)


def test_machine_id_uses_all_eight_partitions() -> None:
    result = analyze_distribution(
        machine_count=5000,
        partition_count=8,
        strategy="machineId",
    )

    assert result.used_partitions == 8


def test_site_id_cannot_use_more_partitions_than_sites() -> None:
    result = analyze_distribution(
        machine_count=5000,
        partition_count=8,
        strategy="siteId",
    )

    assert result.used_partitions <= 5


def test_machine_id_distribution_is_more_balanced_than_site_id() -> None:
    machine_result = analyze_distribution(
        machine_count=5000,
        partition_count=8,
        strategy="machineId",
    )

    site_result = analyze_distribution(
        machine_count=5000,
        partition_count=8,
        strategy="siteId",
    )

    assert (
        machine_result.coefficient_of_variation
        < site_result.coefficient_of_variation
    )


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported strategy",
    ):
        analyze_distribution(
            machine_count=100,
            partition_count=4,
            strategy="unknown",
        )