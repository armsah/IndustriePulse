import json

from industriepulse_simulator.sinks import JsonlFileSink


def test_jsonl_sink_writes_one_payload_per_line(
    tmp_path,
) -> None:
    output_file = tmp_path / "telemetry.jsonl"

    sink = JsonlFileSink(output_file)

    sink.write(
        '{"machineId":"CNC-00001","sequence":1}'
    )

    sink.close()

    lines = output_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    payload = json.loads(lines[0])

    assert payload["machineId"] == "CNC-00001"
    assert payload["sequence"] == 1


def test_jsonl_sink_creates_parent_directories(
    tmp_path,
) -> None:
    output_file = (
        tmp_path
        / "nested"
        / "directory"
        / "telemetry.jsonl"
    )

    sink = JsonlFileSink(output_file)

    sink.write('{"sequence":1}')
    sink.close()

    assert output_file.exists()