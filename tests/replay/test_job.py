import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastavro import writer

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.replay.job import HistoricalReplayJob


CAPTURE_SCHEMA = {
    "type": "record",
    "name": "EventData",
    "fields": [
        {"name": "SequenceNumber", "type": "long"},
        {"name": "Offset", "type": "string"},
        {"name": "EnqueuedTimeUtc", "type": "string"},
        {"name": "SystemProperties", "type": {"type": "map", "values": "bytes"}},
        {"name": "Properties", "type": {"type": "map", "values": "bytes"}},
        {"name": "Body", "type": "bytes"},
    ],
}


def make_avro(records):
    stream = io.BytesIO()
    writer(stream, CAPTURE_SCHEMA, records)
    return stream.getvalue()


def test_replay_job_replays_valid_capture_record():
    telemetry = json.dumps({
        "eventId": "historical-001",
        "machineId": "CNC-00001",
        "sequence": 42,
    }).encode("utf-8")

    avro = make_avro([{
        "SequenceNumber": 1,
        "Offset": "0",
        "EnqueuedTimeUtc": "2026-08-30T10:00:00Z",
        "SystemProperties": {},
        "Properties": {},
        "Body": telemetry,
    }])

    blob = MagicMock()
    blob.name = "namespace/telemetry/0/2026/08/30/12/00/00"

    container = MagicMock()
    container.list_blobs.return_value = [blob]
    container.download_blob.return_value.readall.return_value = avro

    batch = MagicMock()
    producer = MagicMock()
    producer.create_batch.return_value = batch

    result = HistoricalReplayJob(container, producer).run()

    assert result.blobs_scanned == 1
    assert result.records_seen == 1
    assert result.records_replayed == 1
    assert result.records_rejected == 0

    producer.create_batch.assert_called_once_with(
        partition_key="CNC-00001"
    )
    batch.add.assert_called_once()
    producer.send_batch.assert_called_once_with(batch)


def test_replay_job_rejects_invalid_historical_record():
    avro = make_avro([{
        "SequenceNumber": 1,
        "Offset": "0",
        "EnqueuedTimeUtc": "2026-08-30T10:00:00Z",
        "SystemProperties": {},
        "Properties": {},
        "Body": b"{broken",
    }])

    blob = MagicMock()
    blob.name = "namespace/telemetry/0/2026/08/30/12/00/00"

    container = MagicMock()
    container.list_blobs.return_value = [blob]
    container.download_blob.return_value.readall.return_value = avro

    producer = MagicMock()

    result = HistoricalReplayJob(container, producer).run()

    assert result.records_seen == 1
    assert result.records_replayed == 0
    assert result.records_rejected == 1
    producer.send_batch.assert_not_called()
