# TWYLT 1.8

TWYLT is a small, language-independent contract for exposing an executable program as a self-describing JSON tool. `twylt` is the Python reference implementation. ToolHub is one possible consumer. The contract does not require ToolHub, Python, MCP, or any particular agent framework.

## Complete description

Request it with `INPUT_DESCRIBE=json_spec ./tool` or `./tool '{"describe":"json_spec"}'`.

```json
{
  "format_version": "1.8",
  "name": "example-tool",
  "version": "1.0.0",
  "description": "Example tool.",
  "requirements": {"tool":"pip","format":"requirements.txt","content":""},
  "inputSchema": {},
  "outputSchema": {},
  "few_shots": []
}
```

`format_version` versions this contract; `version` versions the concrete tool. `inputSchema` and `outputSchema` are JSON Schema documents. Their names and semantics intentionally align with MCP, but MCP is not a dependency of TWYLT.

## Describe

Modes: `brief`, `schema`, `requirements`, `few_shots`, `json_spec`. A non-empty `describe` is handled before business-input validation and execution; only the describe value is validated. Describe output always goes to stdout. `schema` uses `inputSchema` and `outputSchema`; `name` and `version` belong to the complete `json_spec` only.

## Execution

Input precedence: first positional CLI JSON object, then non-empty stdin JSON object, then `input.json`. CLI/stdin results go to stdout; file input produces `output.json`. Top-level `describe` in CLI/stdin is reserved transport metadata.

## Service options

`-h`/`--help` show identity, usage and discovery; `--version` prints `<name> <version>`; `-v` prints only the tool version. They are processed before transports and validation.

## Requirements discovery

A conforming implementation should permit `requirements` discovery without importing optional tool dependencies. If full loading for `json_spec` fails because such dependencies are unavailable, statically discoverable metadata remains available and unavailable schemas are `{}`.

## MCP relationship

A bridge may mechanically map `name`, `description`, `inputSchema`, and `outputSchema` to the corresponding MCP Tool fields and map executable invocation to `tools/call`. That bridge is optional and outside this runtime contract.

## Schema identity and version

TWYLT 1.3 allows `inputSchema` and `outputSchema` contracts to carry
independent identity and version metadata while remaining JSON Schema objects:

```json
{
  "inputSchema": {
    "$id": "ExampleInput",
    "x-schema-version": "1.0.0",
    "type": "object"
  },
  "outputSchema": {
    "$id": "ExampleOutput",
    "x-schema-version": "1.0.0",
    "type": "object"
  }
}
```

`$id` is the JSON Schema identity keyword. `x-schema-version` is a TWYLT
extension keyword for the schema contract version. Both are optional.

Tool version, TWYLT format version, input schema version, and output schema
version evolve independently. Embedding this metadata preserves direct JSON
Schema use and straightforward MCP mapping.


## Closed object contracts

TWYLT 1.4 defines declared object fields as a closed contract. Unknown
properties MUST fail input and output validation, including properties of
nested object models. Published JSON Schemas MUST describe the same behavior
with `additionalProperties: false` on those object schemas.

The Python reference implementation enforces this policy without requiring
tool authors to add `ConfigDict(extra="forbid")` to every Pydantic model.

## Validation errors

TWYLT 1.5 normalizes validation failures into an error object containing `type`, `stage`, `message`, and issue records with `path`, `code`, `message`, and optional `value`. Human diagnostics go to stderr; stdout remains reserved for successful JSON results. Input validation exits with status 2; output validation with status 3. `--debug` or `TWYLT_DEBUG=1` enables the underlying validation traceback. Unexpected business exceptions remain unmasked.

## Error representation selection

TWYLT 1.6 supports `human` and `json` validation-error renderings. The format is selected by `--error-format human|json` (also `--error-format=json`) or `TWYLT_ERROR_FORMAT`; CLI takes precedence over the environment and the default is `human`. Both renderings use stderr. In JSON mode stderr is exactly one valid JSON document. With debug enabled, the traceback is stored in `error.traceback`, preserving valid JSON. `last_error` remains available to Python embedders.

## Error origin and execution failures

TWYLT 1.7 makes `json` the default error format. Errors carry independent `source` (`twylt` or `tool`) and `stage` (`transport`, `describe`, `input`, `biz`, `output`). Exit codes are 2=input validation, 3=output validation, 4=TWYLT protocol/transport/describe failure, 5=tool business execution failure. In JSON mode ordinary `Exception` from `biz()` is wrapped as `execution_error`; debug adds `error.traceback`. Human mode preserves native business exceptions. `BaseException` subclasses are not intercepted.


## TWYLT 1.8 rename

TWYLT 1.8 is the first protocol version under the TWYLT name. It succeeds ToolSpec 1.7 without changing the core transport, describe, schema, validation, or execution model. Protocol-owned error objects now use `source: "twylt"`. The reference implementation uses `TWYLT_DEBUG` and `TWYLT_ERROR_FORMAT`; it accepts the former `TOOLSPEC_DEBUG` and `TOOLSPEC_ERROR_FORMAT` names as transitional fallbacks.
