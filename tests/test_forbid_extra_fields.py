import pytest
from pydantic import BaseModel, ValidationError
from twylt import Tool
from twylt.tool import JSON_SPEC_FORMAT_VERSION

class Child(BaseModel):
    value: int

class Input(BaseModel):
    child: Child
    label: str = "x"

class Output(BaseModel):
    child: Child

class StrictTool(Tool[Input, Output]):
    input_model=Input
    output_model=Output
    def biz(self,data):
        return Output(child=data.child)

def test_format_1_4():
    assert JSON_SPEC_FORMAT_VERSION=="1.8"

def test_top_level_input_extra_forbidden():
    with pytest.raises(ValidationError) as e:
        StrictTool._strict_input_model().model_validate({"child":{"value":1},"unknown":2})
    assert "extra_forbidden" in str(e.value)

def test_nested_input_extra_forbidden():
    with pytest.raises(ValidationError) as e:
        StrictTool._strict_input_model().model_validate({"child":{"value":1,"unknown":2}})
    assert "extra_forbidden" in str(e.value)

def test_top_level_output_extra_forbidden():
    with pytest.raises(ValidationError):
        StrictTool._strict_output_model().model_validate({"child":{"value":1},"unknown":2})

def test_nested_output_extra_forbidden():
    with pytest.raises(ValidationError):
        StrictTool._strict_output_model().model_validate({"child":{"value":1,"unknown":2}})

def test_input_schema_matches_runtime_policy():
    s=StrictTool.schema()["inputSchema"]
    assert s["additionalProperties"] is False
    child=s["$defs"]["ChildTWYLTStrict"]
    assert child["additionalProperties"] is False

def test_output_schema_matches_runtime_policy():
    s=StrictTool.schema()["outputSchema"]
    assert s["additionalProperties"] is False
    child=s["$defs"]["ChildTWYLTStrict"]
    assert child["additionalProperties"] is False

def test_original_models_are_not_mutated():
    assert Input.model_config.get("extra") != "forbid"
    assert Child.model_config.get("extra") != "forbid"
