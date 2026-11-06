"""Shot-list, planning, and output data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import TypedDict


@dataclass(frozen=True)
class Shot:
    shot_id: str
    scene_id: str
    location: str
    setup: str
    cast_ids: tuple[str, ...]
    estimated_minutes: int
    notes: str


@dataclass(frozen=True)
class PlanOptions:
    start_time: time
    max_day_minutes: int
    setup_change_minutes: int


@dataclass(frozen=True)
class ScheduleRow:
    day: int
    start_time: str
    end_time: str
    activity: str
    shot_id: str
    scene_id: str
    location: str
    setup: str
    cast_ids: str
    duration_minutes: int
    notes: str


class PlanSettings(TypedDict):
    start_time: str
    max_day_minutes: int
    setup_change_minutes: int


class PlanSummary(TypedDict):
    shot_count: int
    day_count: int
    estimated_shot_minutes: int
    setup_buffer_minutes: int
    scheduled_minutes: int


class PlanManifest(TypedDict):
    application: str
    version: str
    input_name: str
    input_sha256: str
    settings: PlanSettings
    summary: PlanSummary
    schedule_sha256: str
    summary_sha256: str
