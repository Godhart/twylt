from __future__ import annotations

# Deliberately keep metadata declarative: bootstrap.py can read it even if an
# optional import below is missing.
from pathlib import Path

from pydantic import BaseModel, Field
from twylt import Requirements, Tool


class Input(BaseModel):
    path: str = Field(..., description="Directory to list")


class Entry(BaseModel):
    name: str
    is_dir: bool


class Output(BaseModel):
    entries: list[Entry]


class ListDirectory(Tool[Input, Output]):
    input_model = Input
    output_model = Output

    name = "list-directory"
    version = "1.0.0"
    input_schema_name = "ListDirectoryInput"
    input_schema_version = "1.0.0"
    output_schema_name = "ListDirectoryOutput"
    output_schema_version = "1.0.0"
    description = "List entries in a directory."
    requirements = Requirements(
        tool="pip",
        format="requirements.txt",
        content="pydantic>=2.0\n",
    )
    few_shots = [
        {
            "input": {"path": "."},
            "output": {"entries": [{"name": "README.md", "is_dir": False}]},
        }
    ]

    def biz(self, data: Input) -> Output:
        base = Path(data.path)
        return Output(
            entries=[
                Entry(name=p.name, is_dir=p.is_dir())
                for p in sorted(base.iterdir(), key=lambda p: p.name)
            ]
        )


TOOL = ListDirectory

if __name__ == "__main__":
    ListDirectory.run()
