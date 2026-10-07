# 1.1.0 — 2026-10-07

- Optional centralized cooperative guardrails; nested allowed cwd separated from workspace.
- Guard transport deletion/read/write without mutating tool class paths.
- Unified policy errors and incidents; strict ContractModel.
- Bootstrap describe via CLI/stdin survives missing business imports.
- Preserve TWYLT protocol 1.8 and previous regressions.

# Changelog

## 1.0.0 - 2026-09-26

- Renamed the project, protocol, Python distribution/import package, and specification from ToolSpec to **TWYLT**.
- TWYLT expands recursively as **TWYLT Wraps Your Local Tool**.
- Python distribution and import package are now `twylt`; this is an intentional breaking rename from `toolspec`.
- Advanced the protocol format to 1.8 because protocol-owned error `source` values now use `twylt` instead of `toolspec`.
- Renamed current environment variables to `TWYLT_DEBUG` and `TWYLT_ERROR_FORMAT`; the Python reference implementation accepts the old `TOOLSPEC_*` names as transitional fallbacks.
- Renamed the specification document to `TWYLT.md`.
- Preserved the complete pre-rename changelog and cumulative regression suite.

## 1.6.2 - 2026-09-26

- ToolSpec format remains 1.7.
- Fixed strict-model generation so Pydantic field metadata is preserved in published JSON Schema.
- Field descriptions, aliases, constraints, defaults, and JSON Schema extras now survive strict conversion.
- Added regression coverage for root, nested, input, and output schema field metadata.

## 1.6.1 - 2026-09-25

- `examples/list_directory`: `path` is now required; generated `inputSchema` lists it in `required`.

- Corrected current-version references in README, ToolSpec specification heading, and package verifier.
- Added the MIT license and package license metadata.
- Expanded release consistency tests to cover documentation, verifier, and license metadata.

- ToolSpec format remains 1.7.
- Fixed stale subprocess regression expectations after JSON became the default error format.
- Added subprocess coverage for default JSON biz errors, JSON debug traceback, and human native traceback.
- Release verification now includes testing a freshly unpacked final ZIP.
- Package version consistency remains enforced by regression tests.

## 1.6.0 - 2026-09-24

- ToolSpec format 1.7; JSON is now the default error format.
- Added error `source` and explicit stages.
- JSON mode wraps `biz()` exceptions with exit 5; ToolSpec protocol failures use exit 4.
- Human mode preserves native biz exception behavior.
- Added ADR 0014 and cumulative regression tests.

## 1.5.0 - 2026-09-24

- Fixed `project.version` in `pyproject.toml` and added a version-consistency regression check.

- ToolSpec format 1.6.
- Added `--error-format human|json` and `TOOLSPEC_ERROR_FORMAT`.
- CLI format selection overrides environment; default remains human.
- JSON debug output remains valid JSON with traceback in `error.traceback`.
- Retained `last_error` for Python embedding.
- Added ADR 0013 and cumulative regression tests.

## 1.4.0 - 2026-09-24

- ToolSpec format 1.5.
- Human-readable validation diagnostics on stderr and normalized machine error data.
- Input/output stages with exit statuses 2/3.
- Debug via `--debug` and `TOOLSPEC_DEBUG`.
- Added ADR 0012 and regression coverage.

## 1.3.0 - 2026-09-24

- ToolSpec format 1.4.
- Reject undeclared input/output fields recursively.
- Generated schemas now expose `additionalProperties: false` consistently with runtime validation.
- Original user Pydantic models are not mutated.
- Added ADR 0011 and regression coverage.

## 1.2.0 - 2026-09-24

- ToolSpec format 1.3.
- Renamed `x-toolspec-version` to `x-schema-version`; no legacy wire alias.
- Python schema-version declarations remain unchanged.
- Added ADR 0010 and regression coverage.

## 1.1.0 - 2026-09-24

- Advanced ToolSpec format to 1.2.
- Added independent input/output schema names and versions.
- Emit schema identity as `$id` and version as `x-schema-version`.
- Added Python schema identity declarations, ADR 0009 and regression tests.

## 1.0.0 - 2026-09-24

- Renamed the project and protocol to **ToolSpec**.
- Renamed the Python distribution from `toolhub-toolkit` to `toolspec`.
- Renamed the Python import package from `toolhub_tool` to `toolspec`.
- Renamed `TOOL-CONTRACT.md` to `TOOLSPEC.md`.
- ToolHub is explicitly one possible consumer rather than part of the protocol identity.
- ToolSpec machine-readable format remains version 1.1.
- Added ADR 0008 documenting the breaking rename.

## 0.5.0 - 2026-09-24

- Added standalone `TOOLSPEC.md`.
- ToolSpec format version is 1.1.
- Renamed public schema keys to `inputSchema` and `outputSchema` for MCP alignment.
- Kept Python `input_model`/`output_model` unchanged.
- MCP remains optional and is not a protocol dependency.
- Added ADR 0007 and cumulative regression coverage.

## 0.4.0 - 2026-09-24

- Added concrete tool `name` and `version` metadata.
- Added `name` and `version` to `json_spec` only.
- Added `-h`/`--help`, `--version`, and `-v` service CLI options.
- Service CLI options execute before transports, validation, and business logic.
- Added ADR 0006 and cumulative regression coverage.

## 0.3.0 - 2026-09-24

- Added `format_version` to `json_spec`.
- Added positional CLI JSON and stdin JSON input.
- CLI/stdin results are emitted to stdout.
- Added JSON `describe` transport control equivalent to `INPUT_DESCRIBE`.
- Describe dispatch precedes and skips all Pydantic business-input validation.
- Added ADR 0005 and protocol regression tests.
- Preserved cumulative regression tests.

## 0.2.2 - 2026-09-23

- Fixed Hatchling package selection for `src/toolspec`.
- Added packaging regression tests and real wheel/editable smoke verification.
- Editable verification installs the test extra with `pip install -e '.[test]'`.
- Added ADR 0004.
- Preserved the full 0.2.1 regression suite.

## 0.2.1 - 2026-09-23

- Restored and adapted the 0.1.x regression test baseline.
- Kept all 0.2.0 tests for requirements/json_spec and missing dependencies.
- Added ADR 0003 establishing cumulative regression tests as project policy.

## 0.2.0 - 2026-09-23

- Added `INPUT_DESCRIBE=requirements`.
- Added `INPUT_DESCRIBE=json_spec`.
- Describe output is always written to stdout.
- Added AST bootstrap so requirements can be returned before optional
  dependencies are importable.
- `json_spec` preserves description/requirements/few_shots and returns empty
  schemas on `ImportError` / `ModuleNotFoundError`.
- Added ADR 0002 and tests for missing optional dependencies.
