"""Deterministic location/setup grouping and day scheduling."""

from __future__ import annotations

from collections import defaultdict
from datetime import time

from shotlist.models import PlanOptions, ScheduleRow, Shot


def parse_start_time(value: str) -> time:
    try:
        parsed = time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("start_time must use 24-hour HH:MM format") from exc
    if len(value) != 5 or value[2] != ":" or parsed.second or parsed.microsecond:
        raise ValueError("start_time must use 24-hour HH:MM format")
    return parsed


def validate_options(options: PlanOptions) -> None:
    if options.start_time.second or options.start_time.microsecond:
        raise ValueError("start_time must use whole minutes")
    if not 60 <= options.max_day_minutes <= 720:
        raise ValueError("max_day_minutes must be between 60 and 720")
    if not 0 <= options.setup_change_minutes <= 120:
        raise ValueError("setup_change_minutes must be between 0 and 120")
    start_minute = options.start_time.hour * 60 + options.start_time.minute
    if start_minute + options.max_day_minutes > 24 * 60:
        raise ValueError("the configured day would extend past midnight")


def _clock_text(minutes_after_midnight: int) -> str:
    hours, minutes = divmod(minutes_after_midnight, 60)
    return f"{hours:02d}:{minutes:02d}"


def plan_shots(shots: list[Shot], options: PlanOptions) -> list[ScheduleRow]:
    validate_options(options)
    if not shots:
        raise ValueError("at least one shot is required")
    if any(
        shot.estimated_minutes + options.setup_change_minutes > options.max_day_minutes
        for shot in shots
    ):
        raise ValueError("a shot and its required setup buffer cannot fit in one scheduled day")

    groups: dict[tuple[str, str], list[Shot]] = defaultdict(list)
    for shot in shots:
        groups[(shot.location, shot.setup)].append(shot)
    ordered_shots = [shot for group in groups.values() for shot in group]

    base_minute = options.start_time.hour * 60 + options.start_time.minute
    day = 1
    used_minutes = 0
    clock = base_minute
    last_group: tuple[str, str] | None = None
    schedule: list[ScheduleRow] = []

    def append_row(
        activity: str,
        duration: int,
        shot: Shot | None,
        group: tuple[str, str],
    ) -> None:
        nonlocal clock, used_minutes
        start = clock
        clock += duration
        used_minutes += duration
        schedule.append(
            ScheduleRow(
                day=day,
                start_time=_clock_text(start),
                end_time=_clock_text(clock),
                activity=activity,
                shot_id=shot.shot_id if shot else "",
                scene_id=shot.scene_id if shot else "",
                location=group[0],
                setup=group[1],
                cast_ids=";".join(shot.cast_ids) if shot else "",
                duration_minutes=duration,
                notes=shot.notes if shot else "Configured setup-change buffer",
            )
        )

    for shot in ordered_shots:
        group = (shot.location, shot.setup)
        buffer = options.setup_change_minutes if group != last_group else 0
        if used_minutes + buffer + shot.estimated_minutes > options.max_day_minutes:
            day += 1
            used_minutes = 0
            clock = base_minute
            last_group = None
            buffer = options.setup_change_minutes
        if buffer:
            append_row("setup", buffer, None, group)
        append_row("shot", shot.estimated_minutes, shot, group)
        last_group = group
    return schedule


def summarize_schedule(schedule: list[ScheduleRow]) -> dict[int, tuple[int, int, int]]:
    totals: dict[int, list[int]] = {}
    for row in schedule:
        totals.setdefault(row.day, [0, 0, 0])
        if row.activity == "shot":
            totals[row.day][0] += 1
            totals[row.day][1] += row.duration_minutes
        else:
            totals[row.day][2] += row.duration_minutes
    return {day: (values[0], values[1], values[2]) for day, values in totals.items()}
