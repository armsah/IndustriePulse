from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TelemetrySink(ABC):
    @abstractmethod
    def write(self, payload: str) -> None:
        """Write one serialized telemetry payload."""

    def close(self) -> None:
        """Release sink resources if required."""


class StdoutSink(TelemetrySink):
    def write(self, payload: str) -> None:
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

    def write(self, payload: str) -> None:
        self._file.write(payload)
        self._file.write("\n")

    def close(self) -> None:
        self._file.close()