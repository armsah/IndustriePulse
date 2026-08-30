"""Decode Azure Event Hubs Capture Avro records."""

from __future__ import annotations

import json
from typing import Any


class CaptureRecordError(ValueError):
    """Raised when a captured Event Hubs record cannot be replayed."""


def decode_capture_record(record: dict[str, Any]) -> tuple[bytes, str]:
    """Return the original event body and machineId partition key."""

    body = record.get("Body")

    if not isinstance(body, (bytes, bytearray)):
        raise CaptureRecordError("Capture record Body must be bytes.")

    payload = bytes(body)

    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureRecordError("Capture record Body is not valid JSON.") from exc

    machine_id = document.get("machineId")

    if not isinstance(machine_id, str) or not machine_id.strip():
        raise CaptureRecordError("Telemetry event requires a non-empty machineId.")

    return payload, machine_id
