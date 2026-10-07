# TWYLT 1.1.0

**TWYLT — TWYLT Wraps Your Local Tool.**

TWYLT is a small, language-independent protocol for turning ordinary executables into self-describing JSON tools. This repository contains the Python reference implementation.

A TWYLT tool can publish its identity, requirements, input/output JSON Schemas and examples, then accept validated JSON input and return validated JSON output. The protocol does not depend on ToolHub, MCP, an LLM, or any particular agent framework.

**Python package:** `twylt` 1.1.0  
**TWYLT protocol:** 1.8

## Quick start

Install the package:

```bash
pip install twylt
```

Define a tool:

```python
from pydantic import BaseModel, Field
from twylt import Tool


class Input(BaseModel):
    text: str = Field(..., description="Text to repeat")


class Output(BaseModel):
    text: str = Field(..., description="Repeated text")


class Echo(Tool[Input, Output]):
    input_model = Input
    output_model = Output

    name = "echo"
    version = "1.1.0"
    description = "Return the supplied text."

    def biz(self, data: Input) -> Output:
        return Output(text=data.text)


if __name__ == "__main__":
    Echo.run()
```

Run it with JSON:

```bash
python echo.py '{"text":"hello"}'
```

```json
{"text":"hello"}
```

Ask the executable to describe itself:

```bash
python echo.py '{"describe":"json_spec"}'
```

The response includes the tool identity, requirements, `inputSchema`, `outputSchema`, examples, and the TWYLT protocol version.

## The contract

A Python tool subclasses `Tool`, declares Pydantic `input_model` and `output_model`, supplies metadata, and implements `biz()`. TWYLT handles the protocol around that business logic: discovery, transports, validation, schema publication and normalized errors.

The complete language-independent protocol is specified in [`TWYLT.md`](TWYLT.md). The Python API is the reference implementation, not the definition of the protocol.

### Self-description

TWYLT supports five describe modes:

| Mode | Result |
| --- | --- |
| `brief` | Short human-readable tool description |
| `schema` | `inputSchema` and `outputSchema` |
| `requirements` | Dependency installation metadata |
| `few_shots` | Example input/output pairs |
| `json_spec` | Complete machine-readable tool description |

Description can be requested through JSON:

```bash
python tool.py '{"describe":"schema"}'
python tool.py '{"describe":"requirements"}'
python tool.py '{"describe":"json_spec"}'
```

For compatibility with executable discovery, `INPUT_DESCRIBE` is also supported:

```bash
INPUT_DESCRIBE=json_spec python tool.py
```

A non-empty describe request is processed before business-input validation and never calls `biz()`.

### Input and output

For normal execution, input is selected in this order:

1. first positional CLI JSON object;
2. non-empty JSON from stdin;
3. `input.json`.

CLI and stdin execution return JSON on stdout. File-mode execution writes `output.json`.

```bash
python tool.py '{"path":"."}'
printf '%s' '{"path":"."}' | python tool.py
```

Object contracts are strict recursively: undeclared fields are rejected on both input and output. Published JSON Schemas reflect the same behavior with `additionalProperties: false`.

### Schema identity

Input and output contracts may be versioned independently from both the tool and the TWYLT protocol:

```python
class MyTool(Tool[Input, Output]):
    input_schema_name = "MyToolInput"
    input_schema_version = "1.1.0"
    output_schema_name = "MyToolOutput"
    output_schema_version = "1.1.0"
```

These become JSON Schema `$id` and `x-schema-version`. Pydantic field metadata such as descriptions, aliases, constraints, defaults and JSON Schema extras is preserved in the published schemas.

## Errors and exit codes

Errors are written to stderr; stdout remains reserved for successful JSON results. JSON is the default error representation.

```json
{
  "error": {
    "type": "validation_error",
    "source": "twylt",
    "stage": "input",
    "message": "Input validation failed",
    "errors": []
  }
}
```

`source: "twylt"` identifies protocol/framework failures; `source: "tool"` identifies failures from business logic. Stages are `transport`, `describe`, `input`, `biz`, and `output`.

| Exit code | Meaning |
| ---: | --- |
| `0` | success |
| `2` | input validation failure |
| `3` | output validation failure |
| `4` | transport/protocol/describe failure |
| `5` | business execution failure |

Use `--error-format human` for human/native diagnostics. `--debug` adds traceback information; the environment equivalents are `TWYLT_ERROR_FORMAT` and `TWYLT_DEBUG`.

## Service CLI

Every tool also exposes service options before normal transport processing:

```bash
python tool.py --help
python tool.py --version
python tool.py -v
```

`--version` prints the tool name and version; `-v` prints only its version.

## Dependency-independent discovery

A launcher can inspect static metadata before importing the complete tool module:

```python
from pathlib import Path
from twylt.bootstrap import run_tool_file

run_tool_file(Path(__file__).with_name("tool.py"))
```

This allows `requirements` discovery even when optional runtime dependencies of the tool are not installed. If full loading for `json_spec` fails because such a dependency is unavailable, statically discoverable metadata is still returned and unavailable schemas are represented as `{}`.

See [`examples/list_directory`](examples/list_directory) for a complete example.

## Relationship to MCP and ToolHub

TWYLT is deliberately independent of both. ToolHub is one possible consumer. An MCP adapter can mechanically map `name`, `description`, `inputSchema`, and `outputSchema` to MCP Tool fields and map executable invocation to `tools/call`, without making MCP part of the TWYLT runtime contract.

## Development

Create an environment and run the cumulative regression suite:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip build
python -m pip install -e '.[test]'
python -m pytest -q
```

Build the distributions:

```bash
python -m build
```

Before a release, both the source tree and the final packaged artifact must pass the complete cumulative test suite. `scripts/verify_package.py` additionally verifies package installation and version metadata.

## Project documentation

- [`TWYLT.md`](TWYLT.md) — language-independent protocol specification.
- [`CHANGELOG.md`](CHANGELOG.md) — release history, including the former ToolSpec releases.
- [`docs/adr`](docs/adr) — architecture decision records and rationale.
- [`examples/list_directory`](examples/list_directory) — complete example tool.

TWYLT 1.0.0 succeeds ToolSpec 1.6.2. The first protocol version under the TWYLT name is 1.8; historical names remain in the changelog and ADRs intentionally.

## Moar TWYLT related resources

Check [`RESOURCES.md`](RESOURCES.md) for other than Python TWYLT implementations, ready made toolpacks with TWYLT under the hood and other related sources

## License

MIT. See [`LICENSE`](LICENSE).

## Guardrails in 1.1.0

Optional cooperative filesystem/transport/network checks are provided by
`twylt.guardrails`. Disabled by default, enabled in toolhub-images 0.3.0.
`TWYLT_ALLOWED_CWD` includes subdirectories without extending the business workspace.
See [configuration and API](docs/GUARDRAILS.md) and [migration](MIGRATION.md).
