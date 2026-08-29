from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from azure.eventhub import EventData, EventHubProducerClient


class TelemetrySink(ABC):
    @abstractmethod
    def write(
        self,
        payload: str,
        partition_key: str | None = None,
    ) -> None:
        """Write one serialized telemetry payload."""

    def close(self) -> None:
        """Release sink resources if required."""


class StdoutSink(TelemetrySink):
    def write(
        self,
        payload: str,
        partition_key: str | None = None,
    ) -> None:
        print(payload)


class JsonlFileSink(TelemetrySink):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._file = self._path.open(
            mode="w",
            encoding="utf-8",
            newline="\n",
        )

    def write(
        self,
        payload: str,
        partition_key: str | None = None,
    ) -> None:
        self._file.write(payload)
        self._file.write("\n")

    def close(self) -> None:
        self._file.close()


class AzureEventHubSink(TelemetrySink):
    def __init__(
        self,
        connection_string: str,
        eventhub_name: str,
    ) -> None:
        self._producer = (
            EventHubProducerClient.from_connection_string(
                conn_str=connection_string,
                eventhub_name=eventhub_name,
            )
        )

    def write(
        self,
        payload: str,
        partition_key: str | None = None,
    ) -> None:
        if partition_key is None:
            raise ValueError(
                "Azure Event Hubs requires a partition key"
            )

        self._producer.send_event(
            EventData(payload),
            partition_key=partition_key,
        )

    def close(self) -> None:
        self._producer.close()
