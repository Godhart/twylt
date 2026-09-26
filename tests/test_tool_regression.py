import json
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from twylt import Tool


class Input(BaseModel):
    value: int


class Output(BaseModel):
    doubled: int


class DemoTool(Tool[Input, Output]):
    input_model = Input
    output_model = Output
    description = "Double an integer."
    few_shots = [
        {"input": {"value": 2}, "output": {"doubled": 4}},
    ]

    def biz(self, data: Input) -> Output:
        return Output(doubled=data.value * 2)


def test_brief_regression():
    assert DemoTool.brief() == "Double an integer."


def test_schema_regression():
    schema = DemoTool.schema()
    assert schema["inputSchema"]["type"] == "object"
    assert schema["outputSchema"]["type"] == "object"
    assert "value" in schema["inputSchema"]["properties"]
    assert "doubled" in schema["outputSchema"]["properties"]


def test_few_shots_regression():
    assert DemoTool.few_shots == [
        {"input": {"value": 2}, "output": {"doubled": 4}},
    ]


def test_input_pydantic_validation_regression():
    with pytest.raises(ValidationError):
        DemoTool.input_model.model_validate({"value": "not-an-int"})


def test_output_pydantic_validation_regression():
    with pytest.raises(ValidationError):
        DemoTool.output_model.model_validate({"doubled": "not-an-int"})


def test_json_input_output_protocol_regression(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("input.json").write_text('{"value": 21}', encoding="utf-8")
    DemoTool.run()
    assert json.loads(Path("output.json").read_text(encoding="utf-8")) == {"doubled": 42}


def test_execute_removes_stale_output_before_failure_regression(tmp_path, monkeypatch):
    class Failing(DemoTool):
        def biz(self, data):
            raise RuntimeError("boom")

    monkeypatch.chdir(tmp_path)
    Path("input.json").write_text('{"value": 1}', encoding="utf-8")
    Path("output.json").write_text('{"stale": true}', encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        Failing.run()
    assert exc.value.code == 5
    assert not Path("output.json").exists()


def test_invalid_input_does_not_create_output_regression(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("input.json").write_text('{"value": "bad"}', encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        DemoTool.run()
    assert exc.value.code == 2
    assert not Path("output.json").exists()
