import json

import pytest

from industriepulse_simulator.cli import (
    main,
    parse_start_time,
)


def test_cli_writes_expected_number_of_events(
    tmp_path,
) -> None:
    output_file = tmp_path / "telemetry.jsonl"

    exit_code = main(
        [
            "--machines",
            "10",
            "--cycles",
            "3",
            "--seed",
            "42",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0

    lines = output_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 30


def test_cli_output_is_reproducible(tmp_path) -> None:
    first_file = tmp_path / "first.jsonl"
    second_file = tmp_path / "second.jsonl"

    common_args = [
        "--machines",
        "20",
        "--cycles",
        "5",
        "--seed",
        "12345",
    ]

    main(
        common_args
        + [
            "--output",
            str(first_file),
        ]
    )

    main(
        common_args
        + [
            "--output",
            str(second_file),
        ]
    )

    assert (
        first_file.read_bytes()
        == second_file.read_bytes()
    )


def test_cli_event_contract(tmp_path) -> None:
    output_file = tmp_path / "telemetry.jsonl"

    main(
        [
            "--machines",
            "1",
            "--cycles",
            "1",
            "--output",
            str(output_file),
        ]
    )

    payload = json.loads(
        output_file.read_text(
            encoding="utf-8"
        ).strip()
    )

    assert payload["machineId"] == "CNC-00001"
    assert payload["sequence"] == 1
    assert payload["siteId"] == "DE-MUC-01"


@pytest.mark.parametrize(
    "machine_count",
    ["0", "-1"],
)
def test_cli_rejects_invalid_machine_count(
    machine_count,
) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "--machines",
                machine_count,
            ]
        )


def test_start_time_requires_timezone() -> None:
    with pytest.raises(
        ValueError,
        match="timezone",
    ):
        parse_start_time(
            "2026-01-01T00:00:00"
        )