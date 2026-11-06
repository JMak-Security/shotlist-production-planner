from __future__ import annotations

from pathlib import Path

import pytest

from shotlist.cli import main


def test_cli_builds_a_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "shots.csv"
    source.write_text(
        "shot_id,scene_id,location,setup,cast_ids,estimated_minutes,notes\n"
        "SHOT_1,SCENE_1,Studio_A,Desk,CAST_1,45,Synthetic\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["shotlist", "plan", str(source), "--output", str(output), "--start-time", "09:15"],
    )

    assert main() == 0
    assert '"shots": 1' in capsys.readouterr().out
    assert (output / "schedule.csv").is_file()


def test_cli_reports_validation_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["shotlist", "plan", str(empty), "--output", str(tmp_path / "out")],
    )

    assert main() == 2
    assert "input file is empty" in capsys.readouterr().err
