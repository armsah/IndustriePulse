from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from industriepulse_simulator.models import TelemetryEvent
from industriepulse_simulator.serialization import event_to_json


class TelemetrySink(ABC):
    @abstractmethod
    def write(self, event: TelemetryEvent) -> None:
        """Write one telemetry event."""

    def close(self) -> None:
        """Release sink resources if required."""


class StdoutSink(TelemetrySink):
    def write(self, event: TelemetryEvent) -> None:
        print(event_to_json(event))


class JsonlFileSink(TelemetrySink):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._path.open(
            mode="w",
            encoding="utf-8",
            newline="\n",
        )

    def write(self, event: TelemetryEvent) -> None:
        self._file.write(event_to_json(event))
        self._file.write("\n")

    def close(self) -> None:
        self._file.close()