import json
from unittest.mock import MagicMock, patch

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
def test_cli_rejects_event_hub_without_connection_string(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "INDUSTRIEPULSE_EVENTHUB_CONNECTION_STRING",
        raising=False,
    )

    with pytest.raises(SystemExit):
        main(
            [
                "--machines",
                "1",
                "--cycles",
                "1",
                "--event-hub-name",
                "telemetry",
            ]
        )


def test_cli_rejects_multiple_output_destinations(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv(
        "INDUSTRIEPULSE_EVENTHUB_CONNECTION_STRING",
        "Endpoint=mock;",
    )

    with pytest.raises(SystemExit):
        main(
            [
                "--machines",
                "1",
                "--cycles",
                "1",
                "--output",
                str(tmp_path / "telemetry.jsonl"),
                "--event-hub-name",
                "telemetry",
            ]
        )


def test_cli_uses_event_hub_sink(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "INDUSTRIEPULSE_EVENTHUB_CONNECTION_STRING",
        "Endpoint=mock;",
    )

    sink = MagicMock()

    with patch(
        "industriepulse_simulator.cli.AzureEventHubSink",
        return_value=sink,
    ) as sink_type:
        exit_code = main(
            [
                "--machines",
                "1",
                "--cycles",
                "1",
                "--late-event-rate",
                "0",
                "--duplicate-rate",
                "0",
                "--malformed-rate",
                "0",
                "--missing-event-rate",
                "0",
                "--event-hub-name",
                "telemetry",
            ]
        )

    assert exit_code == 0

    sink_type.assert_called_once_with(
        connection_string="Endpoint=mock;",
        eventhub_name="telemetry",
    )

    sink.write.assert_called_once()
    sink.close.assert_called_once_with()
