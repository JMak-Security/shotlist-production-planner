from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import time
from pathlib import Path

import pytest

from shotlist.models import PlanOptions
from shotlist.pipeline import _safe_csv_text, run_plan

HEADER = "shot_id,scene_id,location,setup,cast_ids,estimated_minutes,notes\n"
ROW = "SHOT_1,SCENE_1,Studio_A,Desk,CAST_1,45,Synthetic estimate\n"


def _input(path: Path, rows: str = ROW) -> Path:
    path.write_text(HEADER + rows, encoding="utf-8")
    return path


def test_pipeline_outputs_deterministic_schedule_and_provenance(tmp_path: Path) -> None:
    source = _input(tmp_path / "shots.csv", ROW + "SHOT_2,SCENE_2,Studio_B,Door,CAST_2,30,Sample\n")
    options = PlanOptions(time(8, 0), max_day_minutes=480, setup_change_minutes=15)

    first = run_plan(source, tmp_path / "first", options)
    second = run_plan(source, tmp_path / "second", options)
    schedule_path = tmp_path / "first" / "schedule.csv"
    schedule_bytes = schedule_path.read_bytes()
    summary_bytes = (tmp_path / "first" / "summary.md").read_bytes()

    assert first == second
    assert hashlib.sha256(schedule_bytes).hexdigest() == first["schedule_sha256"]
    assert hashlib.sha256(summary_bytes).hexdigest() == first["summary_sha256"]
    assert first["summary"] == {
        "shot_count": 2,
        "day_count": 1,
        "estimated_shot_minutes": 75,
        "setup_buffer_minutes": 30,
        "scheduled_minutes": 105,
    }
    assert str(source.resolve()) not in json.dumps(first)
    with schedule_path.open(encoding="utf-8", newline="") as schedule_file:
        rows = list(csv.DictReader(schedule_file))
    assert [row["activity"] for row in rows] == ["setup", "shot", "setup", "shot"]
    assert "user estimates" in summary_bytes.decode("utf-8")
    assert json.loads((tmp_path / "first" / "manifest.json").read_text(encoding="utf-8")) == first


def test_rejects_invalid_input_and_existing_output_before_writing(tmp_path: Path) -> None:
    invalid_source = _input(tmp_path / "invalid.csv", ROW + ROW)
    output = tmp_path / "invalid-output"
    with pytest.raises(ValueError, match="duplicate shot_id"):
        run_plan(invalid_source, output, PlanOptions(time(8, 0), 480, 15))
    assert not output.exists()

    valid_source = _input(tmp_path / "valid.csv")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        run_plan(valid_source, existing, PlanOptions(time(8, 0), 480, 15))


def test_cleans_staging_directory_when_atomic_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _input(tmp_path / "shots.csv")
    output = tmp_path / "out"

    def fail_rename(
        source_path: str | os.PathLike[str], target_path: str | os.PathLike[str]
    ) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(os, "replace", fail_rename)
    with pytest.raises(OSError, match="simulated rename failure"):
        run_plan(source, output, PlanOptions(time(8, 0), 480, 15))
    assert not output.exists()
    assert not list(tmp_path.glob(".out.staging-*"))


def test_formula_text_is_neutralized_if_rendered(tmp_path: Path) -> None:
    assert _safe_csv_text("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert _safe_csv_text("ordinary note") == "ordinary note"
