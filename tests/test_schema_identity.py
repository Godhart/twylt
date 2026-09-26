from pydantic import BaseModel
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION

class In(BaseModel): value:int
class Out(BaseModel): result:int

class T(Tool[In,Out]):
    name="identified"; version="4.0.0"; description="Schema identity test."
    input_schema_name="ExampleInput"; input_schema_version="2.1.0"
    output_schema_name="ExampleOutput"; output_schema_version="3.2.0"
    input_model=In; output_model=Out
    def biz(self,data): return Out(result=data.value)

class U(Tool[In,Out]):
    input_model=In; output_model=Out
    def biz(self,data): return Out(result=data.value)

def test_format_1_2():
    assert JSON_SPEC_FORMAT_VERSION=="1.8"
    assert T.json_spec()["format_version"]=="1.8"

def test_input_identity():
    x=T.schema()["inputSchema"]
    assert x["$id"]=="ExampleInput" and x["x-schema-version"]=="2.1.0"
    assert x["type"]=="object"

def test_output_identity():
    x=T.schema()["outputSchema"]
    assert x["$id"]=="ExampleOutput" and x["x-schema-version"]=="3.2.0"
    assert x["type"]=="object"

def test_json_spec_identity():
    x=T.json_spec()
    assert x["inputSchema"]["$id"]=="ExampleInput"
    assert x["outputSchema"]["$id"]=="ExampleOutput"

def test_identity_optional():
    x=U.schema()
    assert "$id" not in x["inputSchema"] and "x-schema-version" not in x["inputSchema"]
    assert "$id" not in x["outputSchema"] and "x-schema-version" not in x["outputSchema"]

def test_no_old_schema_version_wire_keyword():
    x=T.json_spec()
    assert "x-twylt-version" not in x["inputSchema"]
    assert "x-twylt-version" not in x["outputSchema"]
