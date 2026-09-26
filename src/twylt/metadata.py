from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Requirements:
    tool: str = "pip"
    format: str = "requirements.txt"
    content: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)
