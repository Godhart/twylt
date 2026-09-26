# ADR 0010: Rename schema version extension keyword

- Status: Accepted
- Date: 2026-09-24

## Decision

ToolSpec 1.3 renames the per-schema extension keyword from
`x-toolspec-version` to `x-schema-version`. `format_version` remains the
ToolSpec protocol version. Python declarations `input_schema_version` and
`output_schema_version` are unchanged. No legacy wire alias is emitted.

This wire-format change advances ToolSpec from 1.2 to 1.3 and the Python
reference implementation from 1.1.0 to 1.2.0.
