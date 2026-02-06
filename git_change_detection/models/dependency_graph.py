from __future__ import annotations
from git_change_detection.utils.io import load_metadata_file
from pathlib import Path
from typing import Dict, List, Set, Any

from git_change_detection.models.node_metadata import (
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

    def sanitize_dependencies(self):
        """Remove dependencies that are not present in the graph."""
        for node in self.nodes.values():
            node.depends_on = [dep for dep in node.depends_on if dep in self.nodes]

    def detect_cycles(self) -> list[list[str]]:
        """Detect dependency cycles in the graph."""
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

    def build_triggered_stages(self) -> list[list[str]]:
        pending_deps = {node: set(meta.depends_on) for node, meta in self.nodes.items()}
        completed = set()
        triggered_nodes = {node for node, meta in self.nodes.items() if meta.triggered}
        stages: list[list[str]] = []

        while pending_deps:
            # Nodes whose dependencies have all been completed
            ready = [node for node, deps in pending_deps.items() if deps <= completed]

            if not ready:
                raise RuntimeError("Dependency resolution failed (possible cycle).")

            # Only triggered nodes go into output stages
            triggered_ready = [node for node in ready if node in triggered_nodes]
            if triggered_ready:
                stage_num = len(stages) + 1
                for node in triggered_ready:
                    self.nodes[node].stage = stage_num
                stages.append(sorted(triggered_ready))

            # Mark all ready nodes as completed to unlock their dependents
            completed.update(ready)
            for node in ready:
                del pending_deps[node]

        return stages
