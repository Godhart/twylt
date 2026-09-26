# ADR 0005: CLI/stdin transport and JSON spec version

- Status: Accepted
- Date: 2026-09-24

## Decision

`json_spec` includes `format_version`, initially `"1.0"`. It versions the
machine-readable specification independently from the package version.

Invocation input precedence is: first positional CLI JSON, then non-empty
non-interactive stdin JSON, then legacy `input.json`.

CLI/stdin invocations write normal results to stdout and never to output.json.

A top-level `describe` in CLI/stdin JSON is a transport control field equivalent
to `INPUT_DESCRIBE`. A non-empty JSON value takes precedence over the
environment value. When describe is present and non-empty, dispatch occurs
before Pydantic input validation: the payload is not validated at all and
business logic is not executed. Only the describe value itself is validated
against the supported modes.

An empty `describe` is removed before ordinary input validation and does not
suppress a non-empty environment `INPUT_DESCRIBE`.

## Consequences

Describe discovery works even with absent/invalid business input. Top-level
`describe` is reserved by the CLI/stdin transport and cannot be application
input in those transports.
