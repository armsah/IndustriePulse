import json
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.replay.capture import CaptureRecordError, decode_capture_record


def test_decode_capture_record_preserves_body_and_machine_partition_key():
    payload = {
        "eventId": "historical-001",
        "siteId": "site-01",
        "machineId": "CNC-00001",
        "sequence": 42,
    }

    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    decoded_body, partition_key = decode_capture_record({"Body": body})

    assert decoded_body == body
    assert partition_key == "CNC-00001"


def test_decode_capture_record_rejects_missing_body():
    with pytest.raises(CaptureRecordError, match="Body must be bytes"):
        decode_capture_record({})


def test_decode_capture_record_rejects_malformed_json():
    with pytest.raises(CaptureRecordError, match="not valid JSON"):
        decode_capture_record({"Body": b"{broken"})


def test_decode_capture_record_rejects_missing_machine_id():
    body = json.dumps({"eventId": "historical-002"}).encode("utf-8")

    with pytest.raises(CaptureRecordError, match="machineId"):
        decode_capture_record({"Body": body})
