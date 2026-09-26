# ADR 0012: Validation error protocol

- Status: Accepted
- Date: 2026-09-24

ToolSpec 1.5 normalizes input/output validation failures, renders human diagnostics to stderr, reserves stdout for successful JSON, and uses exit statuses 2 and 3 respectively. Debug validation tracebacks are enabled by `--debug` or `TOOLSPEC_DEBUG`. Unexpected business exceptions remain unmasked. Python reference version: 1.4.0.
