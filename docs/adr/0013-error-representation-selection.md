# ADR 0013: Error representation selection

- Status: Accepted
- Date: 2026-09-24

ToolSpec 1.6 defines explicit human/JSON rendering selection for validation failures. `--error-format` overrides `TOOLSPEC_ERROR_FORMAT`; default is human. Both formats use stderr. JSON debug diagnostics put the traceback inside `error.traceback` so stderr remains one valid JSON document. Python `last_error` is retained. Reference implementation version: 1.5.0.
