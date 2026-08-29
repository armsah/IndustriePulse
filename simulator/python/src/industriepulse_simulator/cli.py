from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from industriepulse_simulator.config import SimulatorConfig
from industriepulse_simulator.generator import TelemetryGenerator
from industriepulse_simulator.inventory import create_machine_inventory
from industriepulse_simulator.runner import SimulatorRunner
from industriepulse_simulator.sinks import JsonlFileSink, StdoutSink


def positive_int(value: str) -> int:
    parsed = int(value)

    if parsed <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero"
        )

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="industriepulse-sim",
        description=(
            "Generate deterministic industrial telemetry "
            "for IndustriePulse."
        ),
    )

    parser.add_argument(
        "--machines",
        type=positive_int,
        default=5_000,
        help="number of virtual machines (default: 5000)",
    )

    parser.add_argument(
        "--cycles",
        type=positive_int,
        default=1,
        help="number of telemetry cycles (default: 1)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="deterministic random seed (default: 42)",
    )

    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=5.0,
        help=(
            "logical interval between telemetry cycles "
            "(default: 5.0)"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "write JSONL telemetry to this file; "
            "omit to write telemetry to stdout"
        ),
    )

    parser.add_argument(
        "--start-time",
        type=str,
        default="2026-01-01T00:00:00+00:00",
        help=(
            "ISO-8601 logical start time "
            "(default: 2026-01-01T00:00:00+00:00)"
        ),
    )

    return parser


def parse_start_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"invalid ISO-8601 start time: {value}"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
            "start time must include a timezone offset"
        )

    return parsed.astimezone(UTC)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.interval_seconds <= 0:
        parser.error(
            "--interval-seconds must be greater than zero"
        )

    try:
        start_time = parse_start_time(args.start_time)
    except ValueError as exc:
        parser.error(str(exc))

    config = SimulatorConfig(
        seed=args.seed,
        interval_seconds=args.interval_seconds,
    )

    machines = create_machine_inventory(args.machines)

    generator = TelemetryGenerator(config)

    if args.output is None:
        sink = StdoutSink()
    else:
        sink = JsonlFileSink(args.output)

    runner = SimulatorRunner(
        machines=machines,
        generator=generator,
        sink=sink,
        interval_seconds=config.interval_seconds,
    )

    emitted = runner.run_cycles(
        cycles=args.cycles,
        start_time_utc=start_time,
    )

    if args.output is not None:
        print(
            f"Emitted {emitted:,} events from "
            f"{args.machines:,} machines "
            f"across {args.cycles:,} cycle(s) "
            f"to {args.output}"
        )

    return 0