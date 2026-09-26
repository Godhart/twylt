import io,json,sys
from pathlib import Path
import pytest
from pydantic import BaseModel
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION

class I(BaseModel): value:int
class O(BaseModel): doubled:int
class T(Tool[I,O]):
    name="double"; version="1.2.3"
    input_model=I; output_model=O; description="Double."
    def biz(self,data): return O(doubled=data.value*2)

def test_json_spec_version(): assert T.json_spec()["format_version"]==JSON_SPEC_FORMAT_VERSION

def test_cli_json_stdout(monkeypatch,capsys,tmp_path):
    monkeypatch.chdir(tmp_path); monkeypatch.setattr(sys,"argv",["x",'{"value":21}'])
    T.run(); assert json.loads(capsys.readouterr().out)=={"doubled":42}; assert not Path("output.json").exists()

def test_stdin_json_stdout(monkeypatch,capsys,tmp_path):
    monkeypatch.chdir(tmp_path); monkeypatch.setattr(sys,"argv",["x"]); monkeypatch.setattr(sys,"stdin",io.StringIO('{"value":7}'))
    T.run(); assert json.loads(capsys.readouterr().out)=={"doubled":14}; assert not Path("output.json").exists()

def test_cli_precedes_stdin(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x",'{"value":4}']); monkeypatch.setattr(sys,"stdin",io.StringIO('{"value":99}'))
    T.run(); assert json.loads(capsys.readouterr().out)=={"doubled":8}

def test_cli_describe_skips_input_validation(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x",'{"describe":"brief","totally_invalid":true}'])
    T.run(); assert capsys.readouterr().out.strip()=="Double."

def test_stdin_describe_skips_input_validation(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x"]); monkeypatch.setattr(sys,"stdin",io.StringIO('{"describe":"schema","garbage":[1,2]}'))
    T.run(); assert json.loads(capsys.readouterr().out)["inputSchema"]["type"]=="object"

def test_invalid_describe_is_only_describe_validation(monkeypatch):
    monkeypatch.setattr(sys,"argv",["x",'{"describe":"bad","value":"also bad"}'])
    with pytest.raises(SystemExit) as exc: T.run()
    assert exc.value.code == 4

def test_empty_describe_removed_before_input_validation(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x",'{"describe":"","value":3}'])
    T.run(); assert json.loads(capsys.readouterr().out)=={"doubled":6}

def test_json_describe_overrides_environment(monkeypatch,capsys):
    monkeypatch.setenv("INPUT_DESCRIBE","schema"); monkeypatch.setattr(sys,"argv",["x",'{"describe":"brief"}'])
    T.run(); assert capsys.readouterr().out.strip()=="Double."

def test_unreadable_non_tty_stdin_falls_back_to_legacy(monkeypatch,tmp_path):
    class Unreadable:
        def isatty(self): return False
        def read(self): raise OSError("unavailable")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys,"argv",["x"])
    monkeypatch.setattr(sys,"stdin",Unreadable())
    Path("input.json").write_text('{"value":5}',encoding="utf-8")
    T.run()
    assert json.loads(Path("output.json").read_text())=={"doubled":10}

def test_json_spec_identity():
    spec=T.json_spec()
    assert spec["name"]=="double"
    assert spec["version"]=="1.2.3"
