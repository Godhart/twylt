# ADR 0007: Independent ToolSpec and MCP alignment

- Status: Accepted
- Date: 2026-09-24

## Decision

Define the executable protocol independently in `TOOLSPEC.md`. `toolspec` is its Python reference implementation and ToolHub is one possible consumer.

ToolSpec 1.1 renames public `input_schema`/`output_schema` to MCP-aligned `inputSchema`/`outputSchema`. Internal Python `input_model`/`output_model` remain unchanged. MCP is not a dependency or required transport.

The contract version advances 1.0 -> 1.1 and the Python package 0.4.0 -> 0.5.0. The format-version constant lives in a dependency-free module so static requirements/degraded json_spec discovery does not import Pydantic.

## Consequences

Consumers of ToolSpec 1.0 must update the two public schema keys. Implementations in other languages can conform to the standalone contract.
