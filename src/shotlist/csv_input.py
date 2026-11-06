"""Strict, bounded CSV input validation."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from pathlib import Path

from shotlist.models import Shot

MAX_INPUT_BYTES = 1024 * 1024
MAX_SHOTS = 500
REQUIRED_FIELDS = {
    "shot_id",
    "scene_id",
    "location",
    "setup",
    "cast_ids",
    "estimated_minutes",
    "notes",
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")
FORMULA_PREFIXES = ("=", "+", "-", "@")


def _read_input(input_path: Path) -> tuple[bytes, Path]:
    if input_path.is_symlink():
        raise ValueError("input file must not be a symlink")
    resolved = input_path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("input path must be a file")
    with resolved.open("rb") as input_file:
        contents = input_file.read(MAX_INPUT_BYTES + 1)
    if len(contents) > MAX_INPUT_BYTES:
        raise ValueError(f"input file exceeds the {MAX_INPUT_BYTES}-byte limit")
    if not contents:
        raise ValueError("input file is empty")
    return contents, resolved


def _validate_text(value: str, field: str, line_number: int, maximum: int) -> str:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"line {line_number}: {field} contains a control character")
    normalized = value.strip()
    if len(normalized) > maximum:
        raise ValueError(f"line {line_number}: {field} exceeds {maximum} characters")
    if normalized.lstrip().startswith(FORMULA_PREFIXES):
        raise ValueError(f"line {line_number}: {field} starts with unsafe formula text")
    return normalized


def _parse_row(row: list[str], headers: list[str], line_number: int) -> Shot:
    if len(row) != len(headers):
        raise ValueError(f"line {line_number}: expected {len(headers)} columns, got {len(row)}")
    if any(ord(character) < 32 or ord(character) == 127 for value in row for character in value):
        raise ValueError(f"line {line_number}: row contains a control character")
    fields = dict(zip(headers, row, strict=True))
    shot_id = fields["shot_id"].strip()
    if not IDENTIFIER.fullmatch(shot_id):
        raise ValueError(f"line {line_number}: shot_id must be a short alphanumeric identifier")
    scene_id = _validate_text(fields["scene_id"], "scene_id", line_number, 32)
    location = _validate_text(fields["location"], "location", line_number, 64)
    setup = _validate_text(fields["setup"], "setup", line_number, 64)
    notes = _validate_text(fields["notes"], "notes", line_number, 250)
    if not scene_id or not location or not setup:
        raise ValueError(f"line {line_number}: scene_id, location, and setup are required")

    raw_cast_ids = fields["cast_ids"].strip()
    if len(raw_cast_ids) > 256:
        raise ValueError(f"line {line_number}: cast_ids exceeds 256 characters")
    cast_ids = tuple(item.strip() for item in raw_cast_ids.split(";") if item.strip())
    if any(not IDENTIFIER.fullmatch(item) for item in cast_ids):
        raise ValueError(f"line {line_number}: cast_ids must be semicolon-separated identifiers")
    if len({item.casefold() for item in cast_ids}) != len(cast_ids):
        raise ValueError(f"line {line_number}: cast_ids contains duplicates")

    raw_duration = fields["estimated_minutes"].strip()
    if not raw_duration.isdecimal():
        raise ValueError(f"line {line_number}: estimated_minutes must be a positive integer")
    duration = int(raw_duration)
    if not 1 <= duration <= 240:
        raise ValueError(f"line {line_number}: estimated_minutes must be between 1 and 240")
    return Shot(
        shot_id=shot_id,
        scene_id=scene_id,
        location=location,
        setup=setup,
        cast_ids=cast_ids,
        estimated_minutes=duration,
        notes=notes,
    )


def load_shots(input_path: Path) -> tuple[list[Shot], str, Path]:
    contents, resolved = _read_input(input_path)
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("input file must be valid UTF-8 CSV") from exc

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        headers = next(reader, None)
        if headers is None:
            raise ValueError("input CSV has no header row")
        if len(headers) != len(set(headers)):
            raise ValueError("input CSV has duplicate headers")
        if set(headers) != REQUIRED_FIELDS:
            raise ValueError("input CSV headers do not match the documented fields")
        shots: list[Shot] = []
        seen_ids: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            if not row:
                continue
            shot = _parse_row(row, headers, line_number)
            folded_id = shot.shot_id.casefold()
            if folded_id in seen_ids:
                raise ValueError(f"line {line_number}: duplicate shot_id {shot.shot_id}")
            seen_ids.add(folded_id)
            shots.append(shot)
            if len(shots) > MAX_SHOTS:
                raise ValueError(f"input CSV exceeds the {MAX_SHOTS}-shot limit")
    except csv.Error as exc:
        raise ValueError(f"malformed CSV: {exc}") from exc
    if not shots:
        raise ValueError("input CSV contains no shots")
    return shots, hashlib.sha256(contents).hexdigest(), resolved
