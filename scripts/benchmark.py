"""Reproducible synthetic end-to-end shot-list planning benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import statistics
import tempfile
import time
from datetime import time as clock_time
from pathlib import Path

from shotlist.models import PlanOptions
from shotlist.pipeline import run_plan

HEADERS = [
    "shot_id",
    "scene_id",
    "location",
    "setup",
    "cast_ids",
    "estimated_minutes",
    "notes",
]


def _create_fixture(path: Path, shot_count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(HEADERS)
        for index in range(shot_count):
            writer.writerow(
                [
                    f"SHOT_{index + 1:04d}",
                    f"SCENE_{index % 80 + 1:03d}",
                    f"LOCATION_{index % 10 + 1:02d}",
                    f"SETUP_{index % 5 + 1:02d}",
                    f"CAST_{index % 20 + 1:02d}",
                    5 + index % 20,
                    "Synthetic benchmark estimate",
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=500)
    parser.add_argument("--runs", type=int, default=3)
    arguments = parser.parse_args()
    if not 1 <= arguments.shots <= 500:
        parser.error("--shots must be between 1 and 500")
    if not 1 <= arguments.runs <= 10:
        parser.error("--runs must be between 1 and 10")

    durations: list[float] = []
    with tempfile.TemporaryDirectory(prefix="shotlist-benchmark-") as temporary:
        root = Path(temporary)
        input_path = root / "synthetic.csv"
        _create_fixture(input_path, arguments.shots)
        options = PlanOptions(
            start_time=clock_time(8, 0),
            max_day_minutes=720,
            setup_change_minutes=10,
        )
        for run in range(arguments.runs):
            started = time.perf_counter()
            manifest = run_plan(input_path, root / f"output-{run + 1}", options)
            durations.append(time.perf_counter() - started)
            if manifest["summary"]["shot_count"] != arguments.shots:
                raise RuntimeError("benchmark processed an unexpected shot count")

    median_seconds = statistics.median(durations)
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "shots": arguments.shots,
                "runs": arguments.runs,
                "seconds": [round(value, 6) for value in durations],
                "median_seconds": round(median_seconds, 6),
                "median_shots_per_second": round(arguments.shots / median_seconds, 2),
                "settings": {
                    "start_time": "08:00",
                    "max_day_minutes": 720,
                    "setup_change_minutes": 10,
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
