import json
from pathlib import Path

from pydantic import BaseModel
from twylt import Tool


class Input(BaseModel):
    x: int


class Output(BaseModel):
    y: int


class Demo(Tool[Input, Output]):
    input_model = Input
    output_model = Output
    description = "demo"
    few_shots = [{"input": {"x": 1}, "output": {"y": 2}}]

    def biz(self, data):
        return Output(y=data.x + 1)


def test_brief_describe_stdout_and_no_output_regression(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("output.json").write_text("keep", encoding="utf-8")
    monkeypatch.setenv("INPUT_DESCRIBE", "brief")
    Demo.run()
    assert capsys.readouterr().out.strip() == "demo"
    assert Path("output.json").read_text() == "keep"


def test_schema_describe_stdout_and_no_output_regression(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("INPUT_DESCRIBE", "schema")
    Demo.run()
    data = json.loads(capsys.readouterr().out)
    assert data["inputSchema"]["type"] == "object"
    assert data["outputSchema"]["type"] == "object"
    assert not Path("output.json").exists()


def test_few_shots_describe_stdout_and_no_output_regression(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("INPUT_DESCRIBE", "few_shots")
    Demo.run()
    assert json.loads(capsys.readouterr().out) == Demo.few_shots
    assert not Path("output.json").exists()


def test_unknown_describe_mode_fails_regression(monkeypatch):
    import pytest
    monkeypatch.setenv("INPUT_DESCRIBE", "unknown")
    with pytest.raises(SystemExit) as exc:
        Demo.run()
    assert exc.value.code == 4
