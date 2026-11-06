from __future__ import annotations

from datetime import time

import pytest

from shotlist.models import PlanOptions, Shot
from shotlist.planner import parse_start_time, plan_shots, summarize_schedule


def _shot(
    shot_id: str,
    location: str,
    setup: str,
    duration: int = 45,
) -> Shot:
    return Shot(
        shot_id=shot_id,
        scene_id=f"SC_{shot_id}",
        location=location,
        setup=setup,
        cast_ids=("CAST_1",),
        estimated_minutes=duration,
        notes="Synthetic",
    )


def test_groups_in_first_seen_order_and_splits_with_buffers() -> None:
    shots = [
        _shot("SHOT_1", "Studio_A", "Desk"),
        _shot("SHOT_2", "Studio_B", "Door"),
        _shot("SHOT_3", "Studio_A", "Desk"),
    ]
    options = PlanOptions(time(8, 0), max_day_minutes=120, setup_change_minutes=15)

    schedule = plan_shots(shots, options)

    assert [row.shot_id for row in schedule if row.activity == "shot"] == [
        "SHOT_1",
        "SHOT_3",
        "SHOT_2",
    ]
    assert [row.day for row in schedule if row.activity == "shot"] == [1, 1, 2]
    assert [row.duration_minutes for row in schedule if row.activity == "setup"] == [15, 15]
    assert summarize_schedule(schedule) == {1: (2, 90, 15), 2: (1, 45, 15)}
    for day in {row.day for row in schedule}:
        assert sum(row.duration_minutes for row in schedule if row.day == day) <= 120


def test_zero_setup_buffer_and_exact_day_fit() -> None:
    options = PlanOptions(time(8, 0), max_day_minutes=60, setup_change_minutes=0)
    schedule = plan_shots([_shot("SHOT_1", "A", "A", 60)], options)
    assert len(schedule) == 1
    assert schedule[0].start_time == "08:00"
    assert schedule[0].end_time == "09:00"


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (PlanOptions(time(8, 0), 59, 0), "max_day_minutes"),
        (PlanOptions(time(8, 0), 480, 121), "setup_change_minutes"),
        (PlanOptions(time(20, 0), 300, 0), "past midnight"),
        (PlanOptions(time(8, 0, 1), 480, 0), "whole minutes"),
    ],
)
def test_rejects_invalid_plan_options(options: PlanOptions, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        plan_shots([_shot("SHOT_1", "A", "A")], options)


def test_rejects_shot_that_cannot_fit_and_empty_plan() -> None:
    with pytest.raises(ValueError, match="cannot fit"):
        plan_shots(
            [_shot("SHOT_1", "A", "A", 55)],
            PlanOptions(time(8, 0), max_day_minutes=60, setup_change_minutes=10),
        )
    with pytest.raises(ValueError, match="at least one shot"):
        plan_shots([], PlanOptions(time(8, 0), 480, 15))


@pytest.mark.parametrize("value", ["8:00", "08:00:00", "25:00", "ab:cd"])
def test_rejects_noncanonical_start_times(value: str) -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        parse_start_time(value)


def test_accepts_canonical_start_time() -> None:
    assert parse_start_time("07:30") == time(7, 30)
