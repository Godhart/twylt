import json,sys
import pytest
from pydantic import BaseModel
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION
class I(BaseModel): value:int
class O(BaseModel): value:int
class T(Tool[I,O]):
    input_model=I; output_model=O
    def biz(self,data): return O(value=data.value)
def test_format_1_7(): assert JSON_SPEC_FORMAT_VERSION=="1.8"
def test_validation_source(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x",'{"value":"bad"}'])
    with pytest.raises(SystemExit) as e:T.run()
    assert e.value.code==2
    z=json.loads(capsys.readouterr().err)["error"]; assert z["source"]=="twylt" and z["stage"]=="input"
def test_biz_default_json(monkeypatch,capsys):
    class B(T):
        def biz(self,data): raise FileNotFoundError("config.json")
    monkeypatch.setattr(sys,"argv",["x",'{"value":1}'])
    with pytest.raises(SystemExit) as e:B.run()
    assert e.value.code==5
    z=json.loads(capsys.readouterr().err)["error"]
    assert z["type"]=="execution_error" and z["source"]=="tool" and z["stage"]=="biz"
    assert z["exception"]=={"type":"FileNotFoundError","message":"config.json"}
def test_biz_debug_json(monkeypatch,capsys):
    class B(T):
        def biz(self,data): raise RuntimeError("boom")
    monkeypatch.setattr(sys,"argv",["x","--debug",'{"value":1}'])
    with pytest.raises(SystemExit):B.run()
    assert "Traceback" in json.loads(capsys.readouterr().err)["error"]["traceback"]
def test_biz_human_native(monkeypatch):
    class B(T):
        def biz(self,data): raise RuntimeError("boom")
    monkeypatch.setattr(sys,"argv",["x","--error-format","human",'{"value":1}'])
    with pytest.raises(RuntimeError,match="boom"):B.run()
def test_transport_json(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x",'{bad'])
    with pytest.raises(SystemExit) as e:T.run()
    assert e.value.code==4
    z=json.loads(capsys.readouterr().err)["error"]; assert z["source"]=="twylt" and z["stage"]=="transport"
def test_describe_json(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["x",'{"describe":"nope"}'])
    with pytest.raises(SystemExit) as e:T.run()
    assert e.value.code==4
    assert json.loads(capsys.readouterr().err)["error"]["stage"]=="describe"
def test_baseexceptions_not_caught(monkeypatch):
    class S(T):
        def biz(self,data): raise SystemExit(99)
    monkeypatch.setattr(sys,"argv",["x",'{"value":1}'])
    with pytest.raises(SystemExit) as e:S.run()
    assert e.value.code==99
def test_output_source(monkeypatch,capsys):
    class B(T):
        def biz(self,data): return {"value":"bad"}
    monkeypatch.setattr(sys,"argv",["x",'{"value":1}'])
    with pytest.raises(SystemExit) as e:B.run()
    assert e.value.code==3
    z=json.loads(capsys.readouterr().err)["error"]; assert z["source"]=="twylt" and z["stage"]=="output"
