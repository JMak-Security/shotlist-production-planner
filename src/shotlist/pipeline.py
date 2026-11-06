"""Schedule serialization, provenance, and atomic output creation."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path

from shotlist import __version__
from shotlist.csv_input import load_shots
from shotlist.models import PlanManifest, PlanOptions, ScheduleRow
from shotlist.planner import plan_shots, summarize_schedule, validate_options

SCHEDULE_FIELDS = [
    "day",
    "start_time",
    "end_time",
    "activity",
    "shot_id",
    "scene_id",
    "location",
    "setup",
    "cast_ids",
    "duration_minutes",
    "notes",
]


def _safe_csv_text(value: str) -> str:
    if value.lstrip(" \t").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def render_schedule_csv(schedule: list[ScheduleRow]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(SCHEDULE_FIELDS)
    for row in schedule:
        writer.writerow(
            [
                row.day,
                row.start_time,
                row.end_time,
                row.activity,
                row.shot_id,
                row.scene_id,
                row.location,
                row.setup,
                row.cast_ids,
                row.duration_minutes,
                _safe_csv_text(row.notes),
            ]
        )
    return buffer.getvalue().encode("utf-8")


def render_summary(schedule: list[ScheduleRow]) -> bytes:
    totals = summarize_schedule(schedule)
    shot_count = sum(values[0] for values in totals.values())
    shot_minutes = sum(values[1] for values in totals.values())
    setup_minutes = sum(values[2] for values in totals.values())
    lines = [
        "# Proposed Shot Schedule",
        "",
        "Planning aid only. Shot durations are user estimates; no real production or crew data is",
        "implied. The stable first-seen location/setup grouping is a heuristic, not an",
        "optimality claim.",
        "",
        f"- Shots: {shot_count}",
        f"- Scheduled days: {len(totals)}",
        f"- Estimated shot minutes: {shot_minutes}",
        f"- Setup-buffer minutes: {setup_minutes}",
        f"- Total scheduled minutes: {shot_minutes + setup_minutes}",
        "",
        "| Day | Shots | Estimated shot minutes | Setup-buffer minutes | Total minutes |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for day, (count, day_shot_minutes, day_setup_minutes) in totals.items():
        lines.append(
            f"| {day} | {count} | {day_shot_minutes} | {day_setup_minutes} | "
            f"{day_shot_minutes + day_setup_minutes} |"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _manifest(
    input_name: str,
    input_sha256: str,
    options: PlanOptions,
    schedule: list[ScheduleRow],
    schedule_bytes: bytes,
    summary_bytes: bytes,
) -> PlanManifest:
    totals = summarize_schedule(schedule)
    shot_count = sum(values[0] for values in totals.values())
    shot_minutes = sum(values[1] for values in totals.values())
    setup_minutes = sum(values[2] for values in totals.values())
    return PlanManifest(
        application="ShotList Production Planner",
        version=__version__,
        input_name=input_name,
        input_sha256=input_sha256,
        settings={
            "start_time": options.start_time.strftime("%H:%M"),
            "max_day_minutes": options.max_day_minutes,
            "setup_change_minutes": options.setup_change_minutes,
        },
        summary={
            "shot_count": shot_count,
            "day_count": len(totals),
            "estimated_shot_minutes": shot_minutes,
            "setup_buffer_minutes": setup_minutes,
            "scheduled_minutes": shot_minutes + setup_minutes,
        },
        schedule_sha256=hashlib.sha256(schedule_bytes).hexdigest(),
        summary_sha256=hashlib.sha256(summary_bytes).hexdigest(),
    )


def run_plan(
    input_path: Path,
    output_dir: Path,
    options: PlanOptions,
) -> PlanManifest:
    validate_options(options)
    shots, input_sha256, resolved_input = load_shots(input_path)
    if output_dir.is_symlink():
        raise ValueError("output path must not be a symlink")
    output = output_dir.resolve(strict=False)
    if output.exists():
        raise ValueError(f"output directory already exists: {output}")

    schedule = plan_shots(shots, options)
    schedule_bytes = render_schedule_csv(schedule)
    summary_bytes = render_summary(schedule)
    manifest = _manifest(
        resolved_input.name,
        input_sha256,
        options,
        schedule,
        schedule_bytes,
        summary_bytes,
    )
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        (stage / "schedule.csv").write_bytes(schedule_bytes)
        (stage / "summary.md").write_bytes(summary_bytes)
        (stage / "manifest.json").write_bytes(manifest_bytes)
        os.replace(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest
