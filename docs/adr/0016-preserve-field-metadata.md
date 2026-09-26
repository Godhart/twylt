# ADR 0016: Preserve field metadata in strict contract models

- Status: Accepted
- Date: 2026-09-26

ToolSpec derives strict Pydantic models to enforce closed-object contracts. Rebuilding fields from
only `(annotation, default)` discarded `FieldInfo` metadata and therefore removed descriptions and
other schema annotations. Strict model construction now copies each original `FieldInfo`, replaces
only its annotation with the recursively strict annotation, and passes the copied field to
`create_model`.

This preserves descriptions, aliases, constraints, defaults, examples and JSON Schema extras while
retaining `extra="forbid"` semantics. Python reference version: 1.6.2. ToolSpec protocol remains 1.7.
