import sys
import pytest
from pydantic import BaseModel
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION, _normalize_validation

class Child(BaseModel): count:int
class I(BaseModel): child:Child
class O(BaseModel): result:int
class T(Tool[I,O]):
    input_model=I; output_model=O
    def biz(self,data): return O(result=data.child.count)

def test_format_1_5(): assert JSON_SPEC_FORMAT_VERSION=="1.8"

def test_human_input_error(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x","--error-format","human",'{"child":{"count":"bad","extra":1},"other":2}'])
    with pytest.raises(SystemExit) as e:T.run()
    assert e.value.code==2
    c=capsys.readouterr()
    assert c.out==""
    assert "Input validation failed" in c.err and "child.count" in c.err
    assert "child.extra" in c.err and "Unknown field" in c.err
    assert "Traceback" not in c.err
    assert T.last_error["error"]["stage"]=="input"

def test_array_path():
    class II(BaseModel): items:list[Child]
    with pytest.raises(Exception) as e:
        from twylt.tool import _strict_model
        _strict_model(II).model_validate({"items":[{"count":1},{"count":"x"}]})
    assert _normalize_validation(e.value,"input")["error"]["errors"][0]["path"]=="items[1].count"

def test_cli_debug(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x","--debug","--error-format","human",'{"child":{"count":"bad"}}'])
    with pytest.raises(SystemExit):T.run()
    assert "Traceback" in capsys.readouterr().err

def test_env_debug(monkeypatch,capsys):
    monkeypatch.setenv("TWYLT_DEBUG","1")
    monkeypatch.setattr(sys,"argv",["x","--error-format","human",'{"child":{"count":"bad"}}'])
    with pytest.raises(SystemExit):T.run()
    assert "Traceback" in capsys.readouterr().err

def test_output_stage(monkeypatch,capsys):
    class Bad(T):
        def biz(self,data): return {"result":"bad"}
    monkeypatch.setattr(sys,"argv",["x","--error-format","human",'{"child":{"count":1}}'])
    with pytest.raises(SystemExit) as e:Bad.run()
    assert e.value.code==3
    assert "Output validation failed" in capsys.readouterr().err
    assert Bad.last_error["error"]["stage"]=="output"

def test_business_exception_unmasked(monkeypatch):
    class Boom(T):
        def biz(self,data): raise RuntimeError("boom")
    monkeypatch.setattr(sys,"argv",["x","--error-format","human",'{"child":{"count":1}}'])
    with pytest.raises(RuntimeError,match="boom"):Boom.run()
