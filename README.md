# ShotList Production Planner

ShotList validates a bounded CSV shot list and builds a deterministic proposed daily schedule,
summary, and provenance manifest. It is a local planning aid, not production advice: shot durations
are user estimates, and the grouping rule is a simple heuristic rather than an optimization claim.

The bundled rows use synthetic scene, location, setup, cast, and duration values. No real scripts,
call sheets, crew data, or production experience are represented.

## Requirements

- Python 3.12+
- Standard-library runtime; no network or external service
- UTF-8 CSV with the exact fields shown in `samples\sample_shot_list.csv`
- Maximum 500 rows, 1 MiB per file, 240 estimated minutes per shot, and 250 characters per note

## Install and run

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
shotlist plan samples\sample_shot_list.csv --output output\sample-plan
```

The output directory must be new. It contains:

- `schedule.csv` — proposed time rows for setup buffers and shots
- `summary.md` — day totals with explicit estimate/heuristic caveats
- `manifest.json` — input digest, settings, counts, and output digests (no absolute input path)

Options:

```powershell
shotlist plan INPUT.csv --output OUTPUT_DIR --start-time 08:00 --max-day-minutes 480 --setup-change-minutes 15
```

The planner groups shots by `(location, setup)` in the order each group first appears, preserving
input order inside each group. It adds the configured buffer before the first shot of each day and
whenever the group changes. The daily minute cap includes these buffers; shots are not split. The
rule does not consider cast availability, travel, meal rules, permits, or narrative order.

CSV text that could be interpreted as a spreadsheet formula is rejected. Input control characters,
duplicate IDs, malformed rows, invalid estimates, symlink inputs, and oversized files fail with an
explicit error before output is created. Source files are never modified.

## Docker

```powershell
New-Item -ItemType Directory -Force output
docker compose run --rm shotlist
```

The container reads the synthetic sample through a read-only mount, runs as UID 10001, drops all
Linux capabilities, has no network, uses a read-only root filesystem, and writes only to the output
mount and temporary `/tmp`. Set a new output name when repeating the run:
`$env:SHOTLIST_OUTPUT_NAME = "sample-plan-2"`.

## Development checks

```powershell
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest --cov --cov-report=term-missing
python -m build
pip-audit --skip-editable
cyclonedx-py environment --pyproject pyproject.toml --of JSON --output-file sbom.json
```

## Limitations

The CSV schema is intentionally small. Schedule rows are proposals based only on the supplied
estimates and settings. The application does not know whether a scene, setup, cast, timing, or
location is feasible. Review and adjust any output before real-world use.

See [DESIGN.md](DESIGN.md) and [ADRs](docs/adr/) for the requirements and assumptions.
