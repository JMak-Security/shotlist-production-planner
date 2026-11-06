# ADR 0002: Use stable first-seen location/setup grouping

- Status: Accepted
- Date: 2026-11-06

## Context

No production constraints, cast availability, company moves, or script order were supplied. A
black-box optimization could create false confidence or invent priorities.

## Decision

Group shots by location and setup in the order each group first appears, preserving input order
within each group. Add explicit, configured setup buffers and keep them inside the daily minute cap.

## Consequences

- The schedule is deterministic and its heuristic is explainable.
- The result is a proposal, not a claim of optimality or production readiness.
- The planner does not consider cast availability, meal rules, permits, travel, or narrative order.
