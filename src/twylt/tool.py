from __future__ import annotations
import io, json, os, sys
from copy import copy
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin, Annotated, Union
from types import UnionType
from pydantic import BaseModel, ConfigDict, create_model, ValidationError
from .guardrails import Policy, WorkspaceDenied, GuardrailsConfigError
from .metadata import Requirements
from .protocol import TWYLT_FORMAT_VERSION

InputT=TypeVar("InputT",bound=BaseModel)
OutputT=TypeVar("OutputT",bound=BaseModel)
JSON_SPEC_FORMAT_VERSION=TWYLT_FORMAT_VERSION
DESCRIBE_MODES=frozenset({"brief","schema","requirements","json_spec","few_shots"})

_STRICT_MODEL_CACHE: dict[type[BaseModel], type[BaseModel]] = {}

def _strict_annotation(annotation: Any) -> Any:
    """Recursively replace Pydantic model types with extra-forbid variants."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _strict_model(annotation)
    origin=get_origin(annotation)
    if origin is None:
        return annotation
    args=get_args(annotation)
    if origin is Annotated:
        base, *meta=args
        return Annotated[_strict_annotation(base), *meta]
    strict_args=tuple(_strict_annotation(a) for a in args)
    try:
        if origin in (Union, UnionType):
            result=strict_args[0]
            for arg in strict_args[1:]:
                result=result | arg
            return result
        return origin[strict_args[0]] if len(strict_args)==1 else origin[strict_args]
    except (TypeError, AttributeError):
        return annotation

def _strict_model(model: type[BaseModel]) -> type[BaseModel]:
    cached=_STRICT_MODEL_CACHE.get(model)
    if cached is not None:
        return cached

    # Break direct/self references while building; model_rebuild below resolves
    # normal forward references. A temporary cache entry also avoids repeated work.
    fields={}
    for name, field in model.model_fields.items():
        annotation=_strict_annotation(field.annotation)
        # Preserve the complete Pydantic FieldInfo.  Reconstructing a field from
        # only its default loses schema metadata such as description, aliases,
        # constraints, examples, deprecation markers, and JSON Schema extras.
        field_info=copy(field)
        field_info.annotation=annotation
        fields[name]=(annotation, field_info)

    config=dict(model.model_config)
    config["extra"]="forbid"
    strict=create_model(
        f"{model.__name__}TWYLTStrict",
        __config__=ConfigDict(**config),
        __module__=model.__module__,
        **fields,
    )
    _STRICT_MODEL_CACHE[model]=strict
    strict.model_rebuild()
    return strict


def _validation_path(loc):
    out=""
    for part in loc:
        out += f"[{part}]" if isinstance(part,int) else ("." if out else "")+str(part)
    return out or "<root>"

_ERROR_MAP={
 "missing":("required","Required field is missing"),
 "extra_forbidden":("unknown_field","Unknown field"),
 "int_parsing":("invalid_integer","Expected an integer"),
 "int_type":("invalid_integer","Expected an integer"),
 "float_parsing":("invalid_number","Expected a number"),
 "float_type":("invalid_number","Expected a number"),
 "bool_parsing":("invalid_boolean","Expected a boolean"),
 "bool_type":("invalid_boolean","Expected a boolean"),
 "string_type":("invalid_string","Expected a string"),
}

def _normalize_validation(exc,stage):
    issues=[]
    for e in exc.errors(include_url=False):
        raw=e.get("type","validation_error")
        code,msg=_ERROR_MAP.get(raw,(raw,e.get("msg","Invalid value")))
        item={"path":_validation_path(e.get("loc",())),"code":code,"message":msg}
        if "input" in e:
            try: json.dumps(e["input"]); item["value"]=e["input"]
            except (TypeError,ValueError): item["value"]=repr(e["input"])
        issues.append(item)
    return {"error":{"type":"validation_error","source":"twylt","stage":stage,
            "message":f"{stage.capitalize()} validation failed","errors":issues}}

def _normalized_error(error_type,source,stage,message,*,exception=None):
    error={"type":error_type,"source":source,"stage":stage,"message":message}
    if exception is not None:
        error["exception"]={"type":type(exception).__name__,"message":str(exception)}
    return {"error":error}

def _human_validation(error):
    e=error["error"]; lines=[e["message"],""]
    for issue in e["errors"]:
        lines += [f"  • {issue['path']}",f"    {issue['message']}",""]
    n=len(e["errors"]); lines.append(f"{n} validation error"+("" if n==1 else "s"))
    return "\n".join(lines)

class Tool(ABC,Generic[InputT,OutputT]):
    input_model: ClassVar[type[BaseModel]]
    output_model: ClassVar[type[BaseModel]]
    name: ClassVar[str]="tool"
    version: ClassVar[str]="0.0.0"
    description: ClassVar[str]=""
    input_schema_name: ClassVar[str | None]=None
    input_schema_version: ClassVar[str | None]=None
    output_schema_name: ClassVar[str | None]=None
    output_schema_version: ClassVar[str | None]=None
    requirements: ClassVar[Requirements]=Requirements()
    few_shots: ClassVar[list[dict[str,Any]]]=[]
    input_path: ClassVar[Path]=Path("input.json")
    output_path: ClassVar[Path]=Path("output.json")
    last_error: ClassVar[dict[str,Any] | None]=None

    @abstractmethod
    def biz(self,data:InputT)->OutputT: raise NotImplementedError

    @classmethod
    def brief(cls): return cls.description

    @staticmethod
    def _schema_with_identity(schema: dict[str, Any], name: str | None, version: str | None)->dict[str,Any]:
        result=dict(schema)
        if name is not None:
            result["$id"]=name
        if version is not None:
            result["x-schema-version"]=version
        return result

    @classmethod
    def _strict_input_model(cls)->type[BaseModel]:
        return _strict_model(cls.input_model)

    @classmethod
    def _strict_output_model(cls)->type[BaseModel]:
        return _strict_model(cls.output_model)

    @classmethod
    def schema(cls)->dict[str,Any]:
        return {
            "inputSchema": cls._schema_with_identity(
                cls._strict_input_model().model_json_schema(), cls.input_schema_name, cls.input_schema_version
            ),
            "outputSchema": cls._schema_with_identity(
                cls._strict_output_model().model_json_schema(), cls.output_schema_name, cls.output_schema_version
            ),
        }

    @classmethod
    def requirements_spec(cls):
        v=cls.requirements
        return v.as_dict() if isinstance(v,Requirements) else dict(v)

    @classmethod
    def json_spec(cls):
        s=cls.schema()
        return {"format_version":JSON_SPEC_FORMAT_VERSION,
                "name":cls.name,
                "version":cls.version,
                "description":cls.description,
                "requirements":cls.requirements_spec(),
                "inputSchema":s["inputSchema"],
                "outputSchema":s["outputSchema"],
                "few_shots":cls.few_shots}

    @classmethod
    def _validate_describe(cls,value:Any, *, env_style:bool=False)->str:
        if not isinstance(value,str) or value not in DESCRIBE_MODES:
            allowed=", ".join(sorted(DESCRIBE_MODES))
            prefix="Unsupported INPUT_DESCRIBE" if env_style else "Unsupported describe mode"
            raise ValueError(f"{prefix}: {value!r}. Allowed: {allowed}")
        return value

    @classmethod
    def _describe(cls,mode:str, *, env_style:bool=False):
        mode=cls._validate_describe(mode,env_style=env_style)
        if mode=="brief": return cls.brief()
        if mode=="schema": return cls.schema()
        if mode=="requirements": return cls.requirements_spec()
        if mode=="json_spec": return cls.json_spec()
        return cls.few_shots

    @classmethod
    def _print(cls,value):
        print(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2))

    @classmethod
    def _help_text(cls)->str:
        return f"""{cls.name} {cls.version}

{cls.description}

Usage:
  tool.py '<json>'              Read input JSON from first positional argument;
                                write result to stdout
  echo '<json>' | tool.py       Read input JSON from stdin; write result to stdout
  tool.py                       Read input.json; write output.json

Description:
  INPUT_DESCRIBE=<mode> tool.py
  tool.py '{{"describe":"<mode>"}}'

Describe modes:
  brief
  schema
  requirements
  few_shots
  json_spec

Options:
  -h, --help       Show this help
  --version        Show tool name and version
  -v               Show version only
  --debug          Include traceback for validation errors
  --error-format F  Validation error format: human or json
"""

    @classmethod
    def _handle_cli_option(cls)->bool:
        if len(sys.argv) < 2:
            return False
        arg=sys.argv[1]
        if arg in ("-h","--help"):
            print(cls._help_text(),end="")
            return True
        if arg=="--version":
            print(f"{cls.name} {cls.version}")
            return True
        if arg=="-v":
            print(cls.version)
            return True
        return False

    @classmethod
    def _transport_payload(cls):
        if len(sys.argv)>1:
            arg=sys.argv[1]
            # A positional transport argument is recognized only when it looks
            # like a JSON object. Unrelated host-process arguments (pytest -q,
            # interpreter flags, wrappers) preserve legacy file/env behavior.
            if arg.lstrip().startswith("{"):
                v=json.loads(arg)
                if not isinstance(v,dict): raise ValueError("CLI input JSON must be an object")
                return v,"cli"
        if not sys.stdin.isatty():
            try:
                raw=sys.stdin.read()
            except (OSError, io.UnsupportedOperation):
                raw=""
            if raw.strip():
                v=json.loads(raw)
                if not isinstance(v,dict): raise ValueError("stdin input JSON must be an object")
                return v,"stdin"
        return None,None

    @classmethod
    def _load_file_input(cls):
        return cls._strict_input_model().model_validate(json.loads(Policy(cls.name).transport_path(cls.input_path).read_text(encoding="utf-8")))

    @classmethod
    def _write_output(cls,value):
        Policy(cls.name).transport_path(cls.output_path).write_text(json.dumps(value.model_dump(mode="json"),ensure_ascii=False,indent=2),encoding="utf-8")

    @classmethod
    def _debug_enabled(cls, cli_debug=False):
        env=os.environ.get("TWYLT_DEBUG", os.environ.get("TOOLSPEC_DEBUG", "")).strip().lower()
        return cli_debug or env in {"1","true","yes","on"}

    @classmethod
    def _execution_options(cls):
        args=list(sys.argv[1:])
        cli_debug=False
        cli_format=None
        clean=[]
        i=0
        while i < len(args):
            arg=args[i]
            if arg=="--debug":
                cli_debug=True
            elif arg=="--error-format":
                if i+1>=len(args):
                    raise ValueError("--error-format requires human or json")
                cli_format=args[i+1]; i+=1
            elif arg.startswith("--error-format="):
                cli_format=arg.split("=",1)[1]
            else:
                clean.append(arg)
            i+=1
        fmt=cli_format if cli_format is not None else os.environ.get("TWYLT_ERROR_FORMAT", os.environ.get("TOOLSPEC_ERROR_FORMAT", "json"))
        fmt=fmt.strip().lower()
        if fmt not in {"human","json"}:
            raise ValueError(f"Unsupported error format: {fmt!r}. Allowed: human, json")
        return cls._debug_enabled(cli_debug),fmt,[sys.argv[0],*clean]

    @classmethod
    def _report_validation(cls,exc,stage,debug=False,error_format="human"):
        import traceback
        cls.last_error=_normalize_validation(exc,stage)
        if error_format=="json":
            rendered=json.loads(json.dumps(cls.last_error,ensure_ascii=False))
            if debug:
                rendered["error"]["traceback"]="".join(
                    traceback.format_exception(type(exc),exc,exc.__traceback__)
                )
            print(json.dumps(rendered,ensure_ascii=False),file=sys.stderr)
        else:
            print(_human_validation(cls.last_error),file=sys.stderr)
            if debug:
                traceback.print_exception(type(exc),exc,exc.__traceback__,file=sys.stderr)

    @classmethod
    def _report_exception(cls,exc,error_type,source,stage,message,debug=False,error_format="json"):
        import traceback
        cls.last_error=_normalized_error(error_type,source,stage,message,exception=exc)
        if isinstance(exc, WorkspaceDenied):
            cls.last_error['error'].update(code=exc.code, incident_id=exc.incident_id)
        if error_format=="json":
            rendered=json.loads(json.dumps(cls.last_error,ensure_ascii=False))
            if debug:
                rendered["error"]["traceback"]="".join(traceback.format_exception(type(exc),exc,exc.__traceback__))
            print(json.dumps(rendered,ensure_ascii=False),file=sys.stderr)
        else:
            traceback.print_exception(type(exc),exc,exc.__traceback__,file=sys.stderr)

    @classmethod
    def run(cls):
        original_argv=sys.argv
        debug,error_format,clean_argv=cls._execution_options()
        sys.argv=clean_argv
        try:
            if cls._handle_cli_option(): return
            try:
                payload,source=cls._transport_payload()
            except Exception as exc:
                cls._report_exception(exc,"protocol_error","twylt","transport","Failed to read or parse input",debug,error_format)
                raise SystemExit(4)
            json_describe=payload.get("describe") if payload is not None else None
            env_describe=os.environ.get("INPUT_DESCRIBE","")
            describe=json_describe if json_describe not in (None,"") else env_describe
            if describe not in (None,""):
                try:
                    cls._print(cls._describe(describe,env_style=(json_describe in (None,""))))
                except Exception as exc:
                    cls._report_exception(exc,"protocol_error","twylt","describe","Failed to process describe request",debug,error_format)
                    raise SystemExit(4)
                return
            if source is not None:
                clean=dict(payload); clean.pop("describe",None)
                try: data=cls._strict_input_model().model_validate(clean)
                except ValidationError as exc:
                    cls._report_validation(exc,"input",debug,error_format); raise SystemExit(2)
                try:
                    Policy(cls.name)
                    produced=cls().biz(data)
                except (WorkspaceDenied, GuardrailsConfigError):
                    raise
                except Exception as exc:
                    if error_format=="json":
                        cls._report_exception(exc,"execution_error","tool","biz","Tool execution failed",debug,error_format)
                        raise SystemExit(5)
                    raise
                raw=produced.model_dump(mode="python") if isinstance(produced,BaseModel) else produced
                try: result=cls._strict_output_model().model_validate(raw)
                except ValidationError as exc:
                    cls._report_validation(exc,"output",debug,error_format); raise SystemExit(3)
                cls._print(result.model_dump(mode="json")); return
            try:
                policy = Policy(cls.name)
                policy.transport_path(cls.input_path)
                policy.transport_path(cls.output_path).unlink(missing_ok=True)
            except (WorkspaceDenied, GuardrailsConfigError) as exc:
                cls._report_exception(exc,"guardrails_error","twylt","transport","Transport policy denied",debug,error_format)
                raise SystemExit(6)
            try: data=cls._load_file_input()
            except ValidationError as exc:
                cls._report_validation(exc,"input",debug,error_format); raise SystemExit(2)
            except (WorkspaceDenied, GuardrailsConfigError):
                raise
            except Exception as exc:
                cls._report_exception(exc,"protocol_error","twylt","transport","Failed to read or parse input",debug,error_format)
                raise SystemExit(4)
            try:
                Policy(cls.name)
                produced=cls().biz(data)
            except (WorkspaceDenied, GuardrailsConfigError):
                raise
            except Exception as exc:
                if error_format=="json":
                    cls._report_exception(exc,"execution_error","tool","biz","Tool execution failed",debug,error_format)
                    raise SystemExit(5)
                raise
            raw=produced.model_dump(mode="python") if isinstance(produced,BaseModel) else produced
            try: result=cls._strict_output_model().model_validate(raw)
            except ValidationError as exc:
                cls._report_validation(exc,"output",debug,error_format); raise SystemExit(3)
            cls._write_output(result)
        except (WorkspaceDenied, GuardrailsConfigError) as exc:
            cls._report_exception(exc,"guardrails_error","twylt","guardrails","Policy denied",debug,error_format)
            raise SystemExit(6)
        finally:
            sys.argv=original_argv
