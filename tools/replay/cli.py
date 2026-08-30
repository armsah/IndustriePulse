"""IndustriePulse historical telemetry replay CLI."""

from __future__ import annotations

import argparse
import json
import os

from azure.eventhub import EventHubProducerClient
from azure.storage.blob import ContainerClient

from tools.replay.job import HistoricalReplayJob


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay captured telemetry into the isolated replay Event Hub."
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Optional capture blob prefix to limit the historical batch.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    storage_connection_string = os.environ.get(
        "INDUSTRIEPULSE_CAPTURE_STORAGE_CONNECTION_STRING"
    )
    replay_connection_string = os.environ.get(
        "INDUSTRIEPULSE_REPLAY_EVENTHUB_CONNECTION_STRING"
    )
    container_name = os.environ.get(
        "INDUSTRIEPULSE_CAPTURE_CONTAINER",
        "telemetry-capture",
    )

    if not storage_connection_string:
        raise SystemExit(
            "INDUSTRIEPULSE_CAPTURE_STORAGE_CONNECTION_STRING is required."
        )

    if not replay_connection_string:
        raise SystemExit(
            "INDUSTRIEPULSE_REPLAY_EVENTHUB_CONNECTION_STRING is required."
        )

    container = ContainerClient.from_connection_string(
        storage_connection_string,
        container_name=container_name,
    )

    producer = EventHubProducerClient.from_connection_string(
        replay_connection_string
    )

    try:
        result = HistoricalReplayJob(container, producer).run(args.prefix)
    finally:
        producer.close()
        container.close()

    print(json.dumps({
        "blobsScanned": result.blobs_scanned,
        "recordsSeen": result.records_seen,
        "recordsReplayed": result.records_replayed,
        "recordsRejected": result.records_rejected,
    }))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
