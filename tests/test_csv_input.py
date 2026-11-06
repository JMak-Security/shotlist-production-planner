from __future__ import annotations

import csv
from pathlib import Path

import pytest

import shotlist.csv_input as csv_input
from shotlist.csv_input import load_shots

FIELDS = [
    "shot_id",
    "scene_id",
    "location",
    "setup",
    "cast_ids",
    "estimated_minutes",
    "notes",
]


def _write_csv(path: Path, rows: list[list[str]], fields: list[str] | None = None) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(fields or FIELDS)
        writer.writerows(rows)


def _row(shot_id: str = "SHOT_1", notes: str = "Sample note") -> list[str]:
    return [shot_id, "SCENE_1", "Studio_A", "Desk_Wide", "CAST_1;CAST_2", "45", notes]


def test_loads_utf8_bom_and_preserves_quoted_text(tmp_path: Path) -> None:
    path = tmp_path / "shots.csv"
    _write_csv(path, [_row(notes="Sample, quoted note")])
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())

    shots, digest, resolved = load_shots(path)

    assert shots[0].shot_id == "SHOT_1"
    assert shots[0].cast_ids == ("CAST_1", "CAST_2")
    assert shots[0].notes == "Sample, quoted note"
    assert len(digest) == 64
    assert resolved == path.resolve()


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (_row(notes="=SUM(A1:A2)"), "unsafe formula"),
        (_row(notes="line one\nline two"), "control character"),
        (_row(shot_id="bad id"), "shot_id"),
        (_row()[:5] + ["0", "note"], "between 1 and 240"),
        (_row()[:5] + ["not-a-number", "note"], "positive integer"),
        (_row()[:4] + ["CAST_1;cast_1"] + _row()[5:], "duplicates"),
        (_row()[:4] + ["CAST Name"] + _row()[5:], "identifiers"),
        (_row()[:2] + ["", *_row()[3:]], "required"),
    ],
)
def test_rejects_invalid_rows(tmp_path: Path, row: list[str], message: str) -> None:
    path = tmp_path / "invalid.csv"
    _write_csv(path, [row])

    with pytest.raises(ValueError, match=message):
        load_shots(path)


def test_rejects_duplicate_ids_and_invalid_headers(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.csv"
    _write_csv(duplicate, [_row("SHOT_1"), _row("shot_1")])
    with pytest.raises(ValueError, match="duplicate shot_id"):
        load_shots(duplicate)

    bad_header = tmp_path / "header.csv"
    _write_csv(bad_header, [_row()], fields=FIELDS[:-1] + ["extra"])
    with pytest.raises(ValueError, match="headers"):
        load_shots(bad_header)

    duplicate_header = tmp_path / "duplicate-header.csv"
    _write_csv(duplicate_header, [_row()], fields=FIELDS[:-1] + ["shot_id"])
    with pytest.raises(ValueError, match="duplicate headers"):
        load_shots(duplicate_header)


def test_rejects_malformed_encoding_csv_and_empty_data(tmp_path: Path) -> None:
    invalid_encoding = tmp_path / "encoding.csv"
    invalid_encoding.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="UTF-8"):
        load_shots(invalid_encoding)

    malformed = tmp_path / "malformed.csv"
    malformed.write_text(",".join(FIELDS) + '\n"unterminated', encoding="utf-8")
    with pytest.raises(ValueError, match="malformed CSV"):
        load_shots(malformed)

    empty = tmp_path / "empty.csv"
    _write_csv(empty, [])
    with pytest.raises(ValueError, match="no shots"):
        load_shots(empty)


def test_enforces_input_size_shot_count_and_symlink_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "shots.csv"
    _write_csv(path, [_row()])
    monkeypatch.setattr(csv_input, "MAX_INPUT_BYTES", 10)
    with pytest.raises(ValueError, match="byte limit"):
        load_shots(path)

    monkeypatch.setattr(csv_input, "MAX_INPUT_BYTES", 1024 * 1024)
    _write_csv(path, [_row("SHOT_1"), _row("SHOT_2")])
    monkeypatch.setattr(csv_input, "MAX_SHOTS", 1)
    with pytest.raises(ValueError, match="shot limit"):
        load_shots(path)

    alias = tmp_path / "alias.csv"
    try:
        alias.symlink_to(path)
    except OSError:
        pytest.skip("symlink creation is not permitted")
    with pytest.raises(ValueError, match="symlink"):
        load_shots(alias)
