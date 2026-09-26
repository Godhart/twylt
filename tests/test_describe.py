from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from twylt import Requirements, Tool
from twylt.bootstrap import run_tool_file


class I(BaseModel):
    value: int


class O(BaseModel):
    value: int


class T(Tool[I, O]):
    input_model = I
    output_model = O
    description = "demo"
    requirements = Requirements("pip", "requirements.txt", "demo>=1\n")
    few_shots = [{"input": {"value": 1}, "output": {"value": 1}}]

    def biz(self, data: I) -> O:
        return O(value=data.value)


def test_requirements_contract():
    assert T.requirements_spec() == {
        "tool": "pip",
        "format": "requirements.txt",
        "content": "demo>=1\n",
    }


def test_json_spec_contract():
    spec = T.json_spec()
    assert spec["description"] == "demo"
    assert spec["requirements"]["tool"] == "pip"
    assert spec["inputSchema"]["type"] == "object"
    assert spec["outputSchema"]["type"] == "object"
    assert spec["few_shots"]


def _broken_tool(tmp_path: Path) -> Path:
    p = tmp_path / "broken.py"
    p.write_text(
        """
from twylt import Requirements, Tool
description_dummy = "ignored"
class Broken(Tool):
    description = "Broken optional tool"
    requirements = Requirements(
        tool="uv",
        format="pyproject.toml",
        content='[project]\\ndependencies=["package_that_does_not_exist_12345"]\\n',
    )
    few_shots = [{"input": {"x": 1}, "output": {"y": 2}}]

    import package_that_does_not_exist_12345

TOOL = Broken
""",
        encoding="utf-8",
    )
    return p


def test_requirements_survives_missing_optional_import(tmp_path, monkeypatch, capsys):
    p = _broken_tool(tmp_path)
    monkeypatch.setenv("INPUT_DESCRIBE", "requirements")
    run_tool_file(p)
    data = json.loads(capsys.readouterr().out)
    assert data["tool"] == "uv"
    assert data["format"] == "pyproject.toml"
    assert "package_that_does_not_exist_12345" in data["content"]


def test_json_spec_survives_missing_optional_import(tmp_path, monkeypatch, capsys):
    p = _broken_tool(tmp_path)
    monkeypatch.setenv("INPUT_DESCRIBE", "json_spec")
    run_tool_file(p)
    data = json.loads(capsys.readouterr().out)
    assert data["description"] == "Broken optional tool"
    assert data["requirements"]["tool"] == "uv"
    assert data["few_shots"]
    assert data["inputSchema"] == {}
    assert data["outputSchema"] == {}


def test_describe_always_stdout(monkeypatch, capsys):
    monkeypatch.setenv("INPUT_DESCRIBE", "requirements")
    T.run()
    out = capsys.readouterr().out
    assert json.loads(out)["tool"] == "pip"
