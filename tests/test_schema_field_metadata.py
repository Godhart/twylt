from pydantic import BaseModel, Field
from twylt import Tool


class Child(BaseModel):
    count: int = Field(
        ...,
        description="Number of child items",
        ge=1,
        json_schema_extra={"x-unit": "items"},
    )


class Input(BaseModel):
    path: str = Field(..., description="Directory to scan", min_length=1)
    child: Child = Field(..., description="Nested options")
    mode: str = Field("normal", description="Scan mode", alias="scanMode")


class Output(BaseModel):
    total: int = Field(..., description="Number of entries", ge=0)


class MetadataTool(Tool[Input, Output]):
    input_model = Input
    output_model = Output

    def biz(self, data):
        return Output(total=0)


def test_root_field_descriptions_are_preserved():
    schema = MetadataTool.schema()["inputSchema"]
    assert schema["properties"]["path"]["description"] == "Directory to scan"
    assert schema["properties"]["child"]["description"] == "Nested options"
    assert schema["properties"]["scanMode"]["description"] == "Scan mode"


def test_nested_field_description_and_schema_extras_are_preserved():
    schema = MetadataTool.schema()["inputSchema"]
    child_ref = schema["properties"]["child"]["$ref"].split("/")[-1]
    child = schema["$defs"][child_ref]
    assert child["properties"]["count"]["description"] == "Number of child items"
    assert child["properties"]["count"]["minimum"] == 1
    assert child["properties"]["count"]["x-unit"] == "items"


def test_constraints_alias_and_default_are_preserved():
    schema = MetadataTool.schema()["inputSchema"]
    assert schema["properties"]["path"]["minLength"] == 1
    assert "scanMode" in schema["properties"]
    assert schema["properties"]["scanMode"]["default"] == "normal"


def test_output_field_description_is_preserved():
    schema = MetadataTool.schema()["outputSchema"]
    assert schema["properties"]["total"]["description"] == "Number of entries"
    assert schema["properties"]["total"]["minimum"] == 0
