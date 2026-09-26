# ADR 0008: Rename project and protocol to ToolSpec

- Status: Accepted
- Date: 2026-09-24

## Context

The project began as `toolhub-toolkit`, but the protocol is now explicitly
language-independent and ToolHub is only one possible consumer. The old name
therefore incorrectly implied ownership by, or coupling to, ToolHub.

## Decision

Rename the protocol and Python reference implementation to **ToolSpec**.

Public project/package names change as follows:

- protocol: Tool Contract -> ToolSpec;
- specification document: `TOOL-CONTRACT.md` -> `TOOLSPEC.md`;
- Python distribution: `toolhub-toolkit` -> `toolspec`;
- Python import package: `toolhub_tool` -> `toolspec`.

ToolHub remains documented as one possible consumer. MCP remains an optional
mapping target and is not a dependency.

The Python distribution advances to 1.0.0 because the import/distribution
rename is intentionally breaking. The machine-readable ToolSpec format remains
1.1 because its JSON contract is unchanged by this naming migration.

## Consequences

Existing Python users must change imports from `toolhub_tool` to `toolspec` and
install the `toolspec` distribution. Consumers of the ToolSpec 1.1 JSON
contract do not need a schema migration solely because of this rename.
