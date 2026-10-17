from __future__ import annotations

import copy
from typing import Any

from pydantic import BaseModel, Field


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base; non-dict values in override win."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


class NodeMetadata(BaseModel):
    """Represents a single dependency-tracked node (playbook, task, workflow...)."""

    name: str
    depends_on: list[str] = Field(default_factory=list)
    triggers: dict[str, list[str]] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)
    triggered: bool = False
    triggered_by: list[dict[str, str]] = Field(default_factory=list)
    stage: int | None = None

    def merge(self, details: dict[str, Any]) -> None:
        """Merge a dict of details into this node metadata."""
        new_depends = details.get("depends_on") or []
        self.depends_on = sorted(set(self.depends_on) | set(new_depends))

        for prefix, patterns in (details.get("triggers") or {}).items():
            existing = set(self.triggers.setdefault(prefix, []))
            self.triggers[prefix] = sorted(existing | set(patterns or []))

        annotations = details.get("annotations") or {}
        if not isinstance(annotations, dict):
            raise TypeError(f"annotations of node '{self.name}' must be a mapping")
        self.annotations = _deep_merge(self.annotations, annotations)

    def mark_triggered(self, file: str, pattern: str) -> None:
        """Mark this node as triggered and record the cause."""
        self.triggered = True
        self.triggered_by.append({"file": file, "pattern": pattern})
