# ShotList Production Planner

## Status and scope

Design baseline for Project 9. The referenced `Qoder_Master_Prompt_9_Projects_Senior.md` is not
present in this workspace, and no scripts, call sheets, or production schedules were supplied.
The bundled CSV will therefore be synthetic and clearly labeled.

ShotList is a local command-line utility that validates a small, user-provided shot-list CSV and
creates a deterministic day-by-day schedule. It treats shot durations as user estimates, groups
work by location/setup using a documented stable heuristic, accounts for configured setup buffers,
and never claims that a proposed schedule reflects an actual production.

## Inputs and outputs

- UTF-8 CSV with the exact fields `shot_id`, `scene_id`, `location`, `setup`, `cast_ids`,
  `estimated_minutes`, and `notes`.
- Maximum 500 shots, 1 MiB input, 240 estimated minutes per shot, and 250 characters per note.
- Schedule settings are explicit CLI options: start time, maximum scheduled minutes per day, and
  setup-change buffer.
- A new output directory contains `schedule.csv`, `summary.md`, and `manifest.json`.
- No source file, absolute source path, cast name, or external service is required.

## Planning rules

1. Validate the entire input before producing output.
2. Group shots by `(location, setup)` in the order each group first appears; preserve original
   order within each group. This is a stable grouping heuristic, not a globally optimal schedule.
3. Add the configured setup buffer before the first shot of each day and whenever the group changes.
4. Do not split shots. If the next shot plus its required buffer does not fit, start a new day.
5. Each day starts at the configured clock time. The daily minute cap includes setup buffers.
6. Emit setup buffers and shots as separate schedule rows; retain user estimates as estimates.
7. Write a manifest with the input digest, settings, schedule digest, and summary counts. Do not
   include the input's absolute path.

## Validation and safety

- Reject malformed CSV, duplicate or missing headers, duplicate shot IDs, empty required fields,
  out-of-range durations, excess rows, unsupported control characters, and unsafe formula-leading
  text. Formula-like text in free-form values is neutralized in exported CSV cells.
- Reject an output path that already exists or is a symlink.
- Build output in a temporary sibling directory and rename only after all files are complete.
- No network, database, authentication, user tracking, or external script execution.
- Sample rows use fictional identifiers and estimates only. No real cast, schedule, or production
  experience is represented.

## Non-goals

- No script breakdown, location scouting, payroll, budgeting, call-time recommendation, legal
  compliance, cast/crew availability, or optimization claim.
- No calendar, spreadsheet, cloud, or production-management integration.
- No inference that user-entered estimates are accurate.

## Quality requirements

- Python 3.12+, standard-library runtime dependencies, strict typing, Ruff, and at least 85% test
  coverage.
- Deterministic grouping, schedule, summary, and manifest for the same input and options.
- Explicit validation errors; no partial final output on invalid input.

## Assumptions

- A small CSV utility is a conservative interpretation of “production planner” in the absence of
  user requirements.
- Location/setup grouping is more useful than silently reordering for an assumed narrative or cast
  constraint.
- Generated examples and benchmarks remain synthetic and do not imply real-world production use.
