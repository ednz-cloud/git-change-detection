from __future__ import annotations
import json
from typing import Literal
from git_change_detection.models.dependency_graph import DependencyGraph
from rich.console import Console
from rich.table import Table


def render_output(
    graph: DependencyGraph,
    changed_files: list[str],
    cycles: list[list[str]],
    stages: list[list[str]],
    fmt: Literal["table", "json"] = "table",
) -> None:
    """
    Render the analysis results to either rich tables (default) or JSON.

    Args:
        graph: The dependency graph after processing.
        changed_files: Files detected as changed between commits.
        cycles: List of dependency cycles (if any).
        stages: Ordered deployment stages with triggered nodes.
        fmt: Output format ("table" or "json").
    """
    if fmt == "json":
        print(
            json.dumps(
                {n: node.model_dump() for n, node in graph.nodes.items()}, indent=2
            )
        )
        return

    console = Console()

    console.print("\n[bold]Changed files[/bold]")
    for f in changed_files:
        console.print(f"  {f}")

    console.print("\n[bold]Triggered Nodes[/bold]")
    triggered = [n for n, node in graph.nodes.items() if node.triggered]
    if triggered:
        t = Table(
            show_header=True,
            header_style="bold cyan",
            show_lines=True,
        )
        t.add_column("Node", style="magenta")
        t.add_column("File", style="green")
        t.add_column("Pattern", style="yellow")

        for n in triggered:
            node = graph.nodes[n]
            files = sorted({t["file"] for t in node.triggered_by})
            patterns = sorted({t["pattern"] for t in node.triggered_by})
            t.add_row(node.name, "\n".join(files), "\n".join(patterns))
        console.print(t)
    else:
        console.print("[dim](none)[/dim]")

    if cycles:
        console.print("\n[red]Dependency cycles detected:[/red]")
        for c in cycles:
            console.print(" → ".join(c))

    console.print("\n[bold]Deployment Stages[/bold]")
    for i, stage in enumerate(stages, 1):
        console.print(
            f"  Stage {i}: {', '.join(stage)}"  # pylint: disable=inconsistent-quotes
        )
