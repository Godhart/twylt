import json
import os
from pathlib import Path

import twylt
from pydantic import BaseModel
from twylt import Tool
from twylt.protocol import TWYLT_FORMAT_VERSION, TOOL_CONTRACT_FORMAT_VERSION


class Input(BaseModel):
    value: int


class Output(BaseModel):
    value: int


class RenameTool(Tool[Input, Output]):
    input_model = Input
    output_model = Output

    def biz(self, data):
        return Output(value=data.value)


def test_twylt_identity_and_protocol_version():
    assert twylt.__version__ == "1.0.0"
    assert TWYLT_FORMAT_VERSION == "1.8"
    assert TOOL_CONTRACT_FORMAT_VERSION == TWYLT_FORMAT_VERSION


def test_protocol_owned_validation_source_is_twylt(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["tool.py", '{"value":"nope"}'])
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    try:
        RenameTool.run()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected SystemExit")
    error = json.loads(capsys.readouterr().err)["error"]
    assert error["source"] == "twylt"


def test_new_environment_name_wins_over_legacy(monkeypatch):
    monkeypatch.setenv("TOOLSPEC_ERROR_FORMAT", "human")
    monkeypatch.setenv("TWYLT_ERROR_FORMAT", "json")
    _, fmt, _ = RenameTool._execution_options()
    assert fmt == "json"


def test_legacy_environment_name_is_transitional_fallback(monkeypatch):
    monkeypatch.delenv("TWYLT_ERROR_FORMAT", raising=False)
    monkeypatch.setenv("TOOLSPEC_ERROR_FORMAT", "human")
    _, fmt, _ = RenameTool._execution_options()
    assert fmt == "human"


def test_old_import_package_is_not_shipped():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "src" / "toolspec").exists()
