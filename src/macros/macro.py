import re
from dataclasses import dataclass, field
from typing import Any

MAX_NAME_LENGTH = 60
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class InvalidMacro(ValueError):
    pass


@dataclass(frozen=True)
class Macro:
    id: str
    name: str
    steps: tuple[str, ...]
    description: str = ""
    builtin: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": list(self.steps),
            "builtin": self.builtin,
        }


def slugify(name: str) -> str:
    slug = SLUG_PATTERN.sub("-", name.strip().lower()).strip("-")
    if not slug:
        raise InvalidMacro("macro name must contain letters or digits")
    return slug


def parse_steps(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        raw = raw.replace("\r\n", "\n").split("\n")
    if not isinstance(raw, list) or not all(isinstance(step, str) for step in raw):
        raise InvalidMacro("steps must be a list of strings")
    steps = tuple(step.rstrip() for step in raw)
    if not any(step.strip() for step in steps):
        raise InvalidMacro("macro needs at least one non-empty step")
    return steps


def macro_from_dict(data: dict[str, Any], macro_id: str | None = None, builtin: bool = False) -> Macro:
    name = str(data.get("name", "")).strip()
    if not name or len(name) > MAX_NAME_LENGTH:
        raise InvalidMacro(f"name must be 1-{MAX_NAME_LENGTH} characters")
    return Macro(
        id=macro_id or slugify(name),
        name=name,
        description=str(data.get("description", "")).strip(),
        steps=parse_steps(data.get("steps")),
        builtin=builtin,
    )
