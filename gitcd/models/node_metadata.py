from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class NodeMetadata(BaseModel):
    """Represents a single dependency-tracked node (playbook, task, workflow...)."""

    name: str
    depends_on: List[str] = Field(default_factory=list)
    triggers: Dict[str, List[str]] = Field(default_factory=dict)
    triggered: bool = False
    triggered_by: List[Dict[str, str]] = Field(default_factory=list)
    stage: int | None = None

    def merge(self, details: Dict[str, Any]) -> None:
        """Merge a dict of details into this node metadata."""
        new_depends = details.get("depends_on") or []
        self.depends_on = sorted(set(self.depends_on) | set(new_depends))

        for prefix, patterns in (details.get("triggers") or {}).items():
            existing = set(self.triggers.setdefault(prefix, []))
            self.triggers[prefix] = sorted(existing | set(patterns or []))

    def mark_triggered(self, file: str, pattern: str) -> None:
        """Mark this node as triggered and record the cause."""
        self.triggered = True
        self.triggered_by.append({"file": file, "pattern": pattern})
