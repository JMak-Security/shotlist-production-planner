"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import time
from pathlib import Path

from shotlist.models import PlanOptions
from shotlist.pipeline import run_plan
from shotlist.planner import parse_start_time


def _start_time(value: str) -> time:
    try:
        return parse_start_time(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shotlist",
        description="Validate a CSV shot list and build a deterministic proposed schedule.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="create schedule.csv, summary.md, and manifest.json")
    plan.add_argument("input", type=Path)
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--start-time", type=_start_time, default=parse_start_time("08:00"))
    plan.add_argument("--max-day-minutes", type=int, default=480)
    plan.add_argument("--setup-change-minutes", type=int, default=15)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    options = PlanOptions(
        start_time=arguments.start_time,
        max_day_minutes=arguments.max_day_minutes,
        setup_change_minutes=arguments.setup_change_minutes,
    )
    try:
        manifest = run_plan(arguments.input, arguments.output, options)
    except (OSError, ValueError) as exc:
        print(f"shotlist: error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "shots": manifest["summary"]["shot_count"],
                "days": manifest["summary"]["day_count"],
                "output": str(arguments.output),
                "schedule": str(arguments.output / "schedule.csv"),
                "summary": str(arguments.output / "summary.md"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
