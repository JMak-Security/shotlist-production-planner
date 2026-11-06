# ADR 0003: Use synthetic example rows

- Status: Accepted
- Date: 2026-11-06

## Context

No user-provided scripts, call sheets, schedules, or licensed production data were supplied.

## Decision

Bundle a clearly labeled, deterministic sample CSV with fictional scene, location, setup, cast, and
duration values. Do not present it as a real production.

## Consequences

- Tests and demonstrations are reproducible without personal data.
- The examples do not evidence actual production experience.
- Real users must provide and validate their own estimates and constraints.
