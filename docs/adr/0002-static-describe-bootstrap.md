# ADR 0002: Static metadata bootstrap for dependency-independent describe modes

- Status: Accepted
- Date: 2026-09-23

## Context

ToolHub must be able to ask an unprepared Python tool what dependencies it
needs before those dependencies are installed.

`INPUT_DESCRIBE=requirements` therefore cannot depend on importing the complete
tool module. `json_spec` has the same requirement for `description`,
`requirements`, and `few_shots`; only Pydantic input/output schemas may degrade
when an external import is unavailable.

Describe output must always use stdout when `INPUT_DESCRIBE` is non-empty.

## Decision

Tool metadata is declared as class attributes:

- `description`
- `requirements`
- `few_shots`

`requirements` uses the small dependency-free `Requirements` value object
provided by `toolspec`.

Tools intended to support dependency bootstrap are launched through
`toolspec.bootstrap.run_tool_file()`. The bootstrap parses the tool source
with Python `ast` and extracts those three declarative attributes without
executing the module.

For `requirements`, no tool-module import is attempted.

For `json_spec`, bootstrap first obtains static metadata and then attempts to
execute the module to obtain `input_schema` and `output_schema`. If execution
fails specifically with `ImportError` or `ModuleNotFoundError`, both schemas
are returned as empty objects while the static fields are retained.

Other exceptions are not hidden. Normal execution and other describe modes
retain normal Python failure semantics.

All non-empty `INPUT_DESCRIBE` modes write their response to stdout and do not
write the normal `output.json`.

## Consequences

Positive:

- ToolHub can discover installation requirements before installing them.
- `json_spec` remains useful for an unprepared environment.
- Missing dependencies are not confused with arbitrary bugs.
- Metadata has a stable machine-readable representation.

Trade-offs:

- Bootstrap-readable metadata must remain declarative Python literals.
- `requirements` should use `Requirements(...)` with literal arguments (or a
  literal dict); dynamically computed metadata cannot be recovered before
  imports succeed.
- A tool gets the dependency-independent behavior only when launched via the
  bootstrap launcher (`run.py` in the example).

## Alternatives considered

1. Import the module and catch `ImportError`.
   Rejected for `requirements`: code before the failed import may have side
   effects, and imports can fail before the Tool subclass exists.

2. Put metadata in a separate JSON/TOML sidecar.
   Technically robust, but duplicates tool metadata and makes each ToolHub tool
   a multi-file contract.

3. Require optional imports to live inside `biz()`.
   Simple, but unnecessarily constrains tool authors and does not protect
   imports used by Pydantic model declarations.
