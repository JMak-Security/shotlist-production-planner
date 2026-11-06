# ADR 0001: Use a fixed CSV shot-list contract

- Status: Accepted
- Date: 2026-11-06

## Context

No production documents or integration requirements were supplied. A local CSV format is
transparent, inspectable, and does not require external services.

## Decision

Accept UTF-8 CSV with a fixed set of fields and explicit validation limits. Do not infer fields from
arbitrary spreadsheets or execute formulas/macros.

## Consequences

- The input contract is portable and straightforward to test.
- Spreadsheet-specific formatting, multiple worksheets, and macros are out of scope.
- Users must map their own data into the documented CSV columns.
