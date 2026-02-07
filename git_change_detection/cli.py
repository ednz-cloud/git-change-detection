import fnmatch
import os
from pathlib import Path

import typer
from jsonschema import validate, ValidationError

from git_change_detection.models.dependency_graph import DependencyGraph
from git_change_detection.utils.git import get_changed_files
from git_change_detection.utils.io import load_metadata_file, load_schema
from git_change_detection.utils.output import render_output

app = typer.Typer(help="GitCD: dependency-aware change detection for Git.")


@app.command()
def detect(
    first_commit: str = typer.Argument(..., help="First commit in diff"),
    last_commit: str = typer.Argument(..., help="Last commit in diff"),
    metadata_files: list[Path] = typer.Option(
        ...,
        "--metadata",
        "-m",
        help="Metadata files to load",
        exists=True,
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


@app.command(name="validate")
def validate_cmd(
    metadata_files: list[Path] = typer.Option(
        ...,
        "--metadata",
        "-m",
        help="Metadata files to validate",
        exists=True,
    ),
):
    """
    Validate metadata files for schema compliance, missing dependencies, and cycles.
    """
    schema = load_schema()
    has_errors = False

    for path in metadata_files:
        try:
            data = load_metadata_file(path)
            validate(instance=data, schema=schema)
            typer.echo(f"✓ {path}: schema valid")
        except ValidationError as e:
            typer.echo(f"✗ {path}: schema error - {e.message}")
            has_errors = True
        except Exception as e:
            typer.echo(f"✗ {path}: failed to load - {e}")
            has_errors = True

    graph = DependencyGraph()
    try:
        graph.load_files(metadata_files)
    except Exception as e:
        typer.echo(f"✗ Failed to build graph: {e}")
        raise typer.Exit(code=1)

    missing = graph.find_missing_dependencies()
    if missing:
        has_errors = True
        typer.echo("\n✗ Missing dependencies:")
        for node, deps in missing.items():
            typer.echo(f"  {node} depends on non-existent: {', '.join(deps)}")

    cycles = graph.detect_cycles()
    if cycles:
        has_errors = True
        typer.echo("\n✗ Dependency cycles detected:")
        for cycle in cycles:
            typer.echo(f"  {' → '.join(cycle)}")

    if has_errors:
        raise typer.Exit(code=1)

    typer.echo("\n✓ All validations passed")
