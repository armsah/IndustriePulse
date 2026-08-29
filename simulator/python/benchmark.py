from __future__ import annotations

import argparse
import json
import os
import time
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.serialization import event_to_json


def positive_int(value: str) -> int:
    parsed = int(value)

    if parsed <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero"
        )

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark IndustriePulse telemetry generation."
    )

    parser.add_argument(
        "--machines",
        type=positive_int,
        default=10_000,
    )

    parser.add_argument(
        "--cycles",
        type=positive_int,
        default=10,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--result",
        type=Path,
        default=Path("benchmark-result.json"),
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    config = SimulatorConfig(seed=args.seed)
    generator = TelemetryGenerator(config)

    tracemalloc.start()

    benchmark_started = time.perf_counter()

    inventory_started = time.perf_counter()

    machines = create_machine_inventory(
        args.machines
    )

    inventory_seconds = (
        time.perf_counter()
        - inventory_started
    )

    generation_started = time.perf_counter()

    event_count = 0
    payload_bytes = 0

    start_time = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    for sequence in range(
        1,
        args.cycles + 1,
    ):
        for machine in machines:
            event = generator.generate(
                machine=machine,
                sequence=sequence,
                timestamp_utc=start_time,
            )

            payload = event_to_json(event)

            payload_bytes += len(
                payload.encode("utf-8")
            )

            event_count += 1

    generation_seconds = (
        time.perf_counter()
        - generation_started
    )

    total_seconds = (
        time.perf_counter()
        - benchmark_started
    )

    current_memory, peak_memory = (
        tracemalloc.get_traced_memory()
    )

    tracemalloc.stop()

    events_per_second = (
        event_count / generation_seconds
    )

    average_payload_bytes = (
        payload_bytes / event_count
    )

    payload_mb_per_second = (
        payload_bytes
        / generation_seconds
        / 1_000_000
    )

    result = {
        "machines": args.machines,
        "cycles": args.cycles,
        "events": event_count,
        "seed": args.seed,
        "inventorySeconds": round(
            inventory_seconds,
            4,
        ),
        "generationSeconds": round(
            generation_seconds,
            4,
        ),
        "totalSeconds": round(
            total_seconds,
            4,
        ),
        "eventsPerSecond": round(
            events_per_second,
            2,
        ),
        "averagePayloadBytes": round(
            average_payload_bytes,
            2,
        ),
        "payloadMBPerSecond": round(
            payload_mb_per_second,
            3,
        ),
        "currentPythonMemoryMB": round(
            current_memory
            / 1024
            / 1024,
            2,
        ),
        "peakPythonMemoryMB": round(
            peak_memory
            / 1024
            / 1024,
            2,
        ),
        "pythonPid": os.getpid(),
    }

    args.result.write_text(
        json.dumps(
            result,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("IndustriePulse Local Benchmark")
    print("=" * 36)
    print(
        f"Machines:              "
        f"{args.machines:,}"
    )
    print(
        f"Cycles:                "
        f"{args.cycles:,}"
    )
    print(
        f"Events generated:      "
        f"{event_count:,}"
    )
    print(
        f"Generation time:       "
        f"{generation_seconds:.3f} s"
    )
    print(
        f"Generation throughput: "
        f"{events_per_second:,.0f} events/s"
    )
    print(
        f"Average payload:       "
        f"{average_payload_bytes:.1f} bytes"
    )
    print(
        f"Payload throughput:    "
        f"{payload_mb_per_second:.3f} MB/s"
    )
    print(
        f"Peak Python memory:    "
        f"{peak_memory / 1024 / 1024:.2f} MB"
    )
    print()
    print(
        f"Result written to: "
        f"{args.result}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())