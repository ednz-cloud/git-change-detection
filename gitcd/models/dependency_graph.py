from __future__ import annotations
from gitcd.utils.io import load_metadata_file
from pathlib import Path
from typing import Dict, List, Set, Any

from gitcd.models.node_metadata import (
    NodeMetadata,
)


class DependencyGraph:
    """Represents the full dependency graph of nodes."""

    def __init__(self) -> None:
        self.nodes: Dict[str, NodeMetadata] = {}
        self.blacklist: Set[str] = set()

    def remove_node(self, name: str) -> None:
        """Remove a node and clean up references."""
        if name in self.nodes:
            del self.nodes[name]
        for node in self.nodes.values():
            if name in node.depends_on:
                node.depends_on.remove(name)

    def deep_merge(self, new_data: Dict[str, Any]) -> None:
        """Merge new metadata (parsed from YAML/JSON) into the graph."""
        blacklisted = new_data.get("blacklist", [])
        self.blacklist.update(blacklisted)

        for node_name, details in new_data.items():
            if node_name == "blacklist":
                continue
            node = self.nodes.setdefault(node_name, NodeMetadata(name=node_name))
            node.merge(details)

        for name in list(self.blacklist):
            self.remove_node(name)

    def load_files(self, paths: List[Path]) -> None:
        """Load multiple metadata files into the graph."""
        for path in paths:
            data = load_metadata_file(path)
            self.deep_merge(data)

    def mark_triggered(self, node_name: str, file: str, pattern: str) -> None:
        """Mark a node as triggered by a file/pattern match."""
        if node_name in self.nodes:
            self.nodes[node_name].mark_triggered(file, pattern)

    def detect_cycles(self) -> list[list[str]]:
        cycles = []
        visited = set()
        stack = set()
        path = []

        def dfs(node_name):
            if node_name in stack:
                # found cycle
                cycle_start = path.index(node_name)
                cycles.append(path[cycle_start:] + [node_name])
                return
            if node_name in visited:
                return
            visited.add(node_name)
            stack.add(node_name)
            path.append(node_name)

            node = self.nodes.get(node_name)
            if node:
                for dep in node.depends_on:
                    dfs(dep)

            stack.remove(node_name)
            path.pop()

        for n in self.nodes:
            dfs(n)
        return cycles

    def build_triggered_stages(self):
        """Build deployment stages, only including triggered playbooks."""
        deps = {node: set(meta.depends_on) for node, meta in self.nodes.items()}
        stages: list[list[str]] = []
        assigned = set()
        stage_num = 1

        triggered_set = {node for node, meta in self.nodes.items() if meta.triggered}

        while deps:
            # Ready = deps satisfied (whether triggered or not)
            ready = [node for node, dep_set in deps.items() if dep_set <= assigned]
            if not ready:
                raise RuntimeError("Dependency resolution failed (possible cycle).")

            triggered_ready = [node for node in ready if node in triggered_set]
            if triggered_ready:
                for node in triggered_ready:
                    self.nodes[node].stage = stage_num
                stages.append(sorted(triggered_ready))

            # Mark all ready playbooks (even non-triggered) as assigned to unlock dependencies
            assigned.update(ready)

            for node in ready:
                deps.pop(node)

            stage_num += 1

        return stages
