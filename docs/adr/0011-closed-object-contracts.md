# ADR 0011: Closed object contracts

- Status: Accepted
- Date: 2026-09-24

## Decision

ToolSpec 1.4 rejects undeclared object properties during both input and output
validation, recursively for nested Pydantic models. Generated JSON Schema
describes the same policy using `additionalProperties: false`.

The Python reference implementation derives strict validation models rather
than requiring every tool author to configure each Pydantic model manually.
The author's original model classes are not mutated.

This is a contract change, so ToolSpec advances to 1.4 and the Python reference
implementation to 1.3.0.
