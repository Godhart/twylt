from __future__ import annotations

# Deliberately keep metadata declarative: bootstrap.py can read it even if an
# optional import below is missing.
from pydantic import BaseModel, Field
from twylt import Requirements, Tool
from twylt.guardrails import Workspace


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
    version = "1.1.0"
    input_schema_name = "ListDirectoryInput"
    input_schema_version = "1.0.0"
    output_schema_name = "ListDirectoryOutput"
    output_schema_version = "1.0.0"
    description = "List entries in a directory."
    requirements = Requirements(
        tool="pip",
        format="requirements.txt",
        content="twylt>=1.1.0,<2\npydantic>=2.0\n",
    )
    few_shots = [
        {
            "input": {"path": "."},
            "output": {"entries": [{"name": "README.md", "is_dir": False}]},
        }
    ]

    def biz(self, data: Input) -> Output:
        # Policy maps business paths to the workspace and rejects escapes/links
        # when TWYLT_GUARDRAILS=1. No policy implementation is copied here.
        with Workspace(self.name) as workspace:
            base = workspace.resolve(data.path)
            entries = []
            for path in sorted(base.iterdir(), key=lambda path: path.name):
                # Check children before is_dir() can follow a filesystem link.
                workspace.inspect(path)
                entries.append(Entry(name=path.name, is_dir=path.is_dir()))
            return Output(entries=entries)


TOOL = ListDirectory

if __name__ == "__main__":
    ListDirectory.run()
