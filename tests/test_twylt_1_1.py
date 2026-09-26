from pydantic import BaseModel
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION
class I(BaseModel): value:int
class O(BaseModel): result:int
class T(Tool[I,O]):
    name="contract-test"; version="7.8.9"; description="Contract test."
    input_model=I; output_model=O
    def biz(self,data): return O(result=data.value)
def test_contract_1_1(): assert JSON_SPEC_FORMAT_VERSION == "1.8"
def test_schema_names():
    s=T.schema(); assert "inputSchema" in s and "outputSchema" in s
    assert "input_schema" not in s and "output_schema" not in s
def test_json_spec_names_and_identity():
    s=T.json_spec(); assert s["format_version"]=="1.8" and s["name"]=="contract-test" and s["version"]=="7.8.9"
    assert "inputSchema" in s and "outputSchema" in s
