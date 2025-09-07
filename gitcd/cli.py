import typer
from pathlib import Path
from gitcd.models.dependency_graph import DependencyGraph
from gitcd.utils.git import get_changed_files
from gitcd.utils.output import render_output
import fnmatch
import os

app = typer.Typer(help="GitCD: dependency-aware change detection for Git.")


@app.command()
def detect(
    first_commit: str = typer.Argument(..., help="First commit in diff"),
    last_commit: str = typer.Argument(..., help="Last commit in diff"),
    metadata_files: list[Path] = typer.Option(
        ..., "--metadata", "-m", help="Metadata files to load", exists=True
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
    repo: Path = typer.Option(Path.cwd(), "--repo", help="Path to Git repository"),
):
    """
    Detect changed files and resolve triggered nodes in the dependency graph.
    """
    graph = DependencyGraph()
    graph.load_files(metadata_files)
    graph.sanitize_dependencies()

    try:
        changed_files = get_changed_files(first_commit, last_commit, repo)
    except RuntimeError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    for file in changed_files:
        for node in graph.nodes.values():
            for prefix, patterns in node.triggers.items():
                for pattern in patterns:
                    if fnmatch.fnmatch(file, os.path.join(prefix, pattern)):
                        node.mark_triggered(file, os.path.join(prefix, pattern))

    cycles = graph.detect_cycles()
    stages = graph.build_triggered_stages()

    fmt = "json" if json_output else "table"
    render_output(graph, changed_files, cycles, stages, fmt)
