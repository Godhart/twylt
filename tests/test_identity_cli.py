import io, json, sys
from pydantic import BaseModel
from twylt import Tool

class I(BaseModel): value:int
class O(BaseModel): value:int
class Named(Tool[I,O]):
    name="demo-tool"
    version="2.3.4"
    description="A demo tool."
    input_model=I
    output_model=O
    def biz(self,data): return O(value=data.value)

def invoke(monkeypatch,capsys,arg,stdin_text=None):
    monkeypatch.setattr(sys,"argv",["tool.py",arg])
    if stdin_text is not None:
        monkeypatch.setattr(sys,"stdin",io.StringIO(stdin_text))
    Named.run()
    return capsys.readouterr().out

def test_identity_only_added_to_json_spec():
    spec=Named.json_spec()
    assert spec["name"]=="demo-tool"
    assert spec["version"]=="2.3.4"
    assert "name" not in Named.schema()
    assert "version" not in Named.schema()
    assert "name" not in Named.requirements_spec()

def test_help(monkeypatch,capsys):
    out=invoke(monkeypatch,capsys,"--help",'{"value":"invalid"}')
    assert "demo-tool 2.3.4" in out
    assert "A demo tool." in out
    assert "input.json" in out and "output.json" in out
    assert "stdin" in out and "json_spec" in out
    assert "--version" in out and "-v" in out

def test_short_help(monkeypatch,capsys):
    assert invoke(monkeypatch,capsys,"-h")==Named._help_text()

def test_long_version(monkeypatch,capsys):
    assert invoke(monkeypatch,capsys,"--version",'{"value":"invalid"}')=="demo-tool 2.3.4\n"

def test_short_version(monkeypatch,capsys):
    assert invoke(monkeypatch,capsys,"-v",'{"value":"invalid"}')=="2.3.4\n"

def test_service_flags_do_not_run_business_validation(monkeypatch,capsys):
    # Invalid stdin would fail both JSON/Pydantic if the service flag were not first.
    assert invoke(monkeypatch,capsys,"--version",'not-json')=="demo-tool 2.3.4\n"
