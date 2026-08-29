from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from industriepulse_simulator.partitioning import analyze_distribution


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze candidate IndustriePulse partition-key distributions."
    )

    parser.add_argument(
        "--machines",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--partitions",
        type=int,
        nargs="+",
        default=[4, 8, 16],
    )

    parser.add_argument(
        "--result",
        type=Path,
        default=Path("partition-analysis-result.json"),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    results = []

    for partition_count in args.partitions:
        for strategy in ("machineId", "siteId"):
            results.append(
                analyze_distribution(
                    machine_count=args.machines,
                    partition_count=partition_count,
                    strategy=strategy,
                )
            )

    payload = {
        "note": (
            "SHA-256 modulo partition count is a deterministic local distribution "
            "model. It does not reproduce Azure Event Hubs' internal hash function."
        ),
        "results": [asdict(result) for result in results],
    }

    args.result.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print("IndustriePulse Partition-Key Analysis")
    print("=" * 64)

    for result in results:
        print(
            f"{result.strategy:9} "
            f"partitions={result.partition_count:2} "
            f"used={result.used_partitions:2} "
            f"min={result.minimum:4} "
            f"max={result.maximum:4} "
            f"max/mean={result.max_to_mean_ratio:.3f} "
            f"cv={result.coefficient_of_variation:.3f}"
        )

    print(f"\nResult written to: {args.result}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())