"""Replay Event Hubs Capture Avro files into an isolated replay Event Hub."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

from azure.eventhub import EventData
from azure.eventhub import EventHubProducerClient
from azure.storage.blob import ContainerClient
from fastavro import reader

from tools.replay.capture import CaptureRecordError, decode_capture_record


@dataclass(frozen=True)
class ReplayResult:
    blobs_scanned: int
    records_seen: int
    records_replayed: int
    records_rejected: int


class HistoricalReplayJob:
    """Replay captured telemetry into the dedicated replay Event Hub."""

    def __init__(
        self,
        container_client: ContainerClient,
        producer: EventHubProducerClient,
    ) -> None:
        self._container_client = container_client
        self._producer = producer

    def run(self, prefix: str | None = None) -> ReplayResult:
        blobs_scanned = 0
        records_seen = 0
        records_replayed = 0
        records_rejected = 0

        blobs = self._container_client.list_blobs(name_starts_with=prefix)

        for blob in blobs:
            blobs_scanned += 1
            payload = self._container_client.download_blob(blob.name).readall()

            for record in self._read_records(payload):
                records_seen += 1

                try:
                    body, machine_id = decode_capture_record(record)
                except CaptureRecordError:
                    records_rejected += 1
                    continue

                event = EventData(body)
                event.properties = {
                    "replay": True,
                    "replaySourceBlob": blob.name,
                }

                batch = self._producer.create_batch(partition_key=machine_id)
                batch.add(event)
                self._producer.send_batch(batch)
                records_replayed += 1

        return ReplayResult(
            blobs_scanned=blobs_scanned,
            records_seen=records_seen,
            records_replayed=records_replayed,
            records_rejected=records_rejected,
        )

    @staticmethod
    def _read_records(payload: bytes) -> Iterable[dict]:
        return reader(BytesIO(payload))
