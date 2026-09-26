import json,sys
import pytest
from pydantic import BaseModel
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION

class I(BaseModel): count:int
class O(BaseModel): result:int
class T(Tool[I,O]):
    input_model=I; output_model=O
    def biz(self,data): return O(result=data.count)

def invoke(monkeypatch,capsys,args,env=None):
    monkeypatch.delenv("TWYLT_ERROR_FORMAT",raising=False)
    if env is not None: monkeypatch.setenv("TWYLT_ERROR_FORMAT",env)
    monkeypatch.setattr(sys,"argv",["x",*args])
    with pytest.raises(SystemExit) as e:T.run()
    return e.value.code,capsys.readouterr()

def test_format_1_6(): assert JSON_SPEC_FORMAT_VERSION=="1.8"

def test_default_is_json(monkeypatch,capsys):
    code,c=invoke(monkeypatch,capsys,['{"count":"x"}'])
    assert code==2
    assert json.loads(c.err)["error"]["stage"]=="input"

def test_json_cli(monkeypatch,capsys):
    code,c=invoke(monkeypatch,capsys,["--error-format","json",'{"count":"x"}'])
    assert code==2 and c.out==""
    e=json.loads(c.err)["error"]
    assert e["type"]=="validation_error" and e["stage"]=="input"
    assert e["errors"][0]["path"]=="count"
    assert "traceback" not in e

def test_json_cli_equals(monkeypatch,capsys):
    _,c=invoke(monkeypatch,capsys,["--error-format=json",'{"count":"x"}'])
    assert json.loads(c.err)["error"]["stage"]=="input"

def test_json_env(monkeypatch,capsys):
    _,c=invoke(monkeypatch,capsys,['{"count":"x"}'],"json")
    assert json.loads(c.err)["error"]["stage"]=="input"

def test_cli_overrides_env(monkeypatch,capsys):
    _,c=invoke(monkeypatch,capsys,["--error-format","human",'{"count":"x"}'],"json")
    assert "Input validation failed" in c.err
    with pytest.raises(json.JSONDecodeError):json.loads(c.err)

def test_json_debug_stays_valid_json_cli(monkeypatch,capsys):
    _,c=invoke(monkeypatch,capsys,["--debug","--error-format","json",'{"count":"x"}'])
    e=json.loads(c.err)["error"]
    assert "Traceback" in e["traceback"]
    assert json.loads(c.err)["error"]["traceback"]==e["traceback"]

def test_json_debug_stays_valid_json_env(monkeypatch,capsys):
    monkeypatch.setenv("TWYLT_DEBUG","1")
    _,c=invoke(monkeypatch,capsys,['{"count":"x"}'],"json")
    assert "traceback" in json.loads(c.err)["error"]

def test_invalid_format_rejected(monkeypatch):
    monkeypatch.setattr(sys,"argv",["x","--error-format","xml",'{"count":"x"}'])
    with pytest.raises(ValueError,match="Unsupported error format"):T.run()

def test_missing_format_value_rejected(monkeypatch):
    monkeypatch.setattr(sys,"argv",["x","--error-format"])
    with pytest.raises(ValueError,match="requires"):T.run()

def test_output_json_error(monkeypatch,capsys):
    class Bad(T):
        def biz(self,data): return {"result":"bad"}
    monkeypatch.setattr(sys,"argv",["x","--error-format","json",'{"count":1}'])
    with pytest.raises(SystemExit) as e:Bad.run()
    assert e.value.code==3
    assert json.loads(capsys.readouterr().err)["error"]["stage"]=="output"

def test_success_ignores_error_format(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x","--error-format","json",'{"count":2}'])
    T.run(); c=capsys.readouterr()
    assert json.loads(c.out)=={"result":2} and c.err==""
