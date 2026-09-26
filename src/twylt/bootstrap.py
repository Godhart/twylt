from __future__ import annotations

import ast
import importlib.util
import json
import os
import runpy
import sys
from pathlib import Path
from typing import Any

from .protocol import TWYLT_FORMAT_VERSION

_STATIC_NAMES = {"name", "version", "description", "requirements", "few_shots"}


def _literal(node: ast.AST) -> Any:
    return ast.literal_eval(node)


def _requirements_to_dict(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {
            "tool": str(value.get("tool", "")),
            "format": str(value.get("format", "")),
            "content": str(value.get("content", "")),
        }
    return {
        "tool": str(getattr(value, "tool", "")),
        "format": str(getattr(value, "format", "")),
        "content": str(getattr(value, "content", "")),
    }


def extract_static_metadata(path: str | Path) -> dict[str, Any]:
    """Extract Tool class metadata without importing the tool module.

    Supported values are intentionally declarative literals. `requirements`
    may also be written as Requirements(tool=..., format=..., content=...).
    """
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, Any] = {
        "name": "tool",
        "version": "0.0.0",
        "description": "",
        "requirements": {"tool": "", "format": "", "content": ""},
        "few_shots": [],
    }

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            name = None
            value_node = None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                name, value_node = stmt.targets[0].id, stmt.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name, value_node = stmt.target.id, stmt.value

            if name not in _STATIC_NAMES or value_node is None:
                continue

            if name == "requirements" and isinstance(value_node, ast.Call):
                if isinstance(value_node.func, ast.Name) and value_node.func.id == "Requirements":
                    kwargs = {kw.arg: _literal(kw.value) for kw in value_node.keywords if kw.arg}
                    result[name] = {
                        "tool": str(kwargs.get("tool", "")),
                        "format": str(kwargs.get("format", "")),
                        "content": str(kwargs.get("content", "")),
                    }
                    continue

            try:
                value = _literal(value_node)
            except (ValueError, TypeError):
                continue

            result[name] = _requirements_to_dict(value) if name == "requirements" else value

    return result


def _print(value: Any) -> None:
    if isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def run_tool_file(path: str | Path) -> None:
    """Entry point used by a tiny launcher placed before optional imports."""
    path = Path(path)
    mode = os.environ.get("INPUT_DESCRIBE", "")

    if mode in {"requirements", "json_spec"}:
        static = extract_static_metadata(path)

        if mode == "requirements":
            _print(static["requirements"])
            return

        try:
            namespace = runpy.run_path(str(path), run_name="__toolhub_describe__")
            tool_cls = namespace.get("TOOL")
            if tool_cls is None:
                raise RuntimeError("Tool module must expose TOOL = <ToolSubclass>")
            schemas = tool_cls.schema()
        except (ImportError, ModuleNotFoundError):
            schemas = {"inputSchema": {}, "outputSchema": {}}

        _print({
            "format_version": TWYLT_FORMAT_VERSION,
            "name": static.get("name", "tool"),
            "version": static.get("version", "0.0.0"),
            "description": static["description"],
            "requirements": static["requirements"],
            "inputSchema": schemas["inputSchema"],
            "outputSchema": schemas["outputSchema"],
            "few_shots": static["few_shots"],
        })
        return

    # All other modes preserve normal Python import/error semantics.
    namespace = runpy.run_path(str(path), run_name="__main__")
