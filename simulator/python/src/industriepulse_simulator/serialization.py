from __future__ import annotations

import json
from typing import Any

from industriepulse_simulator.models import TelemetryEvent


def event_to_dict(event: TelemetryEvent) -> dict[str, Any]:
    return {
        "eventId": event.event_id,
        "siteId": event.site_id,
        "machineId": event.machine_id,
        "machineType": event.machine_type.value,
        "timestampUtc": event.timestamp_utc.isoformat(),
        "temperatureC": event.temperature_c,
        "vibrationMmS": event.vibration_mm_s,
        "pressureBar": event.pressure_bar,
        "rpm": event.rpm,
        "sequence": event.sequence,
        "firmwareVersion": event.firmware_version,
    }


def event_to_json(event: TelemetryEvent) -> str:
    return json.dumps(
        event_to_dict(event),
        separators=(",", ":"),
        sort_keys=True,
    )