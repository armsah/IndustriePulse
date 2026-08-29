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
from unittest.mock import MagicMock, patch

import pytest

from industriepulse_simulator.sinks import AzureEventHubSink


@patch(
    "industriepulse_simulator.sinks."
    "EventHubProducerClient.from_connection_string"
)
def test_eventhub_sink_creates_producer(
    from_connection_string,
) -> None:
    producer = MagicMock()
    from_connection_string.return_value = producer

    sink = AzureEventHubSink(
        connection_string="Endpoint=mock;",
        eventhub_name="telemetry",
    )

    from_connection_string.assert_called_once_with(
        conn_str="Endpoint=mock;",
        eventhub_name="telemetry",
    )

    sink.close()


@patch(
    "industriepulse_simulator.sinks."
    "EventHubProducerClient.from_connection_string"
)
def test_eventhub_sink_uses_machine_as_partition_key(
    from_connection_string,
) -> None:
    producer = MagicMock()
    from_connection_string.return_value = producer

    sink = AzureEventHubSink(
        connection_string="Endpoint=mock;",
        eventhub_name="telemetry",
    )

    sink.write(
        '{"machineId":"CNC-00001","sequence":1}',
        partition_key="CNC-00001",
    )

    producer.send_event.assert_called_once()

    args, kwargs = producer.send_event.call_args

    assert b"".join(args[0].body) == (
        b'{"machineId":"CNC-00001","sequence":1}'
    )
    assert kwargs["partition_key"] == "CNC-00001"

    sink.close()


@patch(
    "industriepulse_simulator.sinks."
    "EventHubProducerClient.from_connection_string"
)
def test_eventhub_sink_requires_partition_key(
    from_connection_string,
) -> None:
    producer = MagicMock()
    from_connection_string.return_value = producer

    sink = AzureEventHubSink(
        connection_string="Endpoint=mock;",
        eventhub_name="telemetry",
    )

    with pytest.raises(
        ValueError,
        match="partition key",
    ):
        sink.write('{"sequence":1}')

    producer.send_event.assert_not_called()

    sink.close()


@patch(
    "industriepulse_simulator.sinks."
    "EventHubProducerClient.from_connection_string"
)
def test_eventhub_sink_closes_producer(
    from_connection_string,
) -> None:
    producer = MagicMock()
    from_connection_string.return_value = producer

    sink = AzureEventHubSink(
        connection_string="Endpoint=mock;",
        eventhub_name="telemetry",
    )

    sink.close()

    producer.close.assert_called_once_with()
