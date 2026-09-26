# ADR 0006: Tool identity and CLI service options

- Status: Accepted
- Date: 2026-09-24

## Decision

Each Tool class declares `name` and `version`. They identify the concrete tool,
not the toolspec package. `json_spec` exposes both fields. Existing
specialized describe formats (`brief`, `schema`, `requirements`, `few_shots`)
remain unchanged for backward compatibility.

The runner recognizes these service options before any CLI JSON parsing, stdin
reading, input.json access, Pydantic validation, or business execution:

- `-h`, `--help`: name, version, brief description, transport principles,
  describe mechanisms/modes, and service options.
- `--version`: `<name> <version>`.
- `-v`: version only.

## Consequences

Tool discovery can distinguish toolkit/spec versions from the concrete tool
version. Shell users can inspect a tool without satisfying its runtime input
contract or providing stdin.
