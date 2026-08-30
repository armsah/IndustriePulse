"""Verify historical telemetry arriving on the isolated replay Event Hub."""

from __future__ import annotations

import argparse
import json
import os
import time

from azure.eventhub import EventHubConsumerClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify telemetry received from the replay Event Hub."
    )
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    connection_string = os.environ.get(
        "INDUSTRIEPULSE_REPLAY_RECEIVER_CONNECTION_STRING"
    )
    consumer_group = os.environ.get(
        "INDUSTRIEPULSE_REPLAY_CONSUMER_GROUP",
        "replay-processor",
    )

    if not connection_string:
        raise SystemExit(
            "INDUSTRIEPULSE_REPLAY_RECEIVER_CONNECTION_STRING is required."
        )

    event_ids: set[str] = set()
    deadline = time.monotonic() + args.timeout

    client = EventHubConsumerClient.from_connection_string(
        connection_string,
        consumer_group=consumer_group,
    )
    def on_event(partition_context, event):
        if event is None:
            return

        try:
            document = json.loads(event.body_as_str())
            event_id = document.get("eventId")
            if isinstance(event_id, str) and event_id:
                event_ids.add(event_id)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

        if len(event_ids) >= args.expected_count:
            client.close()

    try:
        client.receive(
            on_event=on_event,
            starting_position="-1",
            max_wait_time=2,
        )
    except Exception:
        if len(event_ids) < args.expected_count and time.monotonic() < deadline:
            raise
    finally:
        client.close()

    result = {
        "expectedCount": args.expected_count,
        "uniqueEventIds": len(event_ids),
        "verified": len(event_ids) >= args.expected_count,
        "eventIds": sorted(event_ids),
    }

    print(json.dumps(result))

    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
