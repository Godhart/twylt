# ADR 0009: Independent schema identity and version

- Status: Accepted
- Date: 2026-09-24

## Decision

ToolSpec 1.2 adds optional identity and version metadata directly to each
input/output JSON Schema. `$id` carries schema identity and
`x-schema-version` carries its independently evolving contract version.

The Python reference implementation exposes `input_schema_name`,
`input_schema_version`, `output_schema_name`, and `output_schema_version`.

Schemas are not wrapped in ToolSpec-specific objects, so `inputSchema` and
`outputSchema` remain ordinary JSON Schema documents and retain straightforward
MCP mapping. Tool, protocol, input-schema and output-schema versions are
independent.
