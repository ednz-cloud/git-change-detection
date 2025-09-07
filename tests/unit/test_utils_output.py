import json
import pytest
from gitcd.models.dependency_graph import DependencyGraph
from gitcd.models.node_metadata import NodeMetadata
from gitcd.utils.output import render_output  # adjust import if needed


def make_graph(triggered=False):
    """Helper to create a simple graph with two nodes, optionally triggering one."""
    g = DependencyGraph()
    g.nodes["node1"] = NodeMetadata(name="node1")
    g.nodes["node2"] = NodeMetadata(name="node2")
    if triggered:
        g.nodes["node1"].mark_triggered("file1.py", "src/*.py")
    return g


@pytest.mark.parametrize(
    "fmt, triggered, expected_files, expected_nodes",
    [
        ("json", True, ["file1.py"], ["node1"]),
        ("table", True, ["file1.py"], ["node1"]),
        ("table", False, ["file2.txt"], ["node2"]),
    ],
)
def test_render_output_variants(fmt, triggered, expected_files, expected_nodes, capsys):
    """Test render_output for multiple output formats and trigger states."""
    graph = make_graph(triggered=triggered)
    changed_files = expected_files
    stages = [expected_nodes]
    cycles = [["node1", "node2", "node1"]] if triggered else []

    render_output(graph, changed_files, cycles, stages, fmt=fmt)
    out = capsys.readouterr().out

    if fmt == "json":
        data = json.loads(out)
        for node_name in expected_nodes:
            if triggered:
                assert node_name in data
                assert data[node_name]["triggered"] is True
    else:
        # Table output checks
        assert "Changed files" in out
        for f in expected_files:
            assert f in out
        assert "Deployment Stages" in out
        for stage_node in expected_nodes:
            assert stage_node in out
        if triggered:
            assert "Triggered Nodes" in out
            assert "node1" in out
            assert "file1.py" in out
            assert "src/*.py" in out
        else:
            assert "(none)" in out


def test_render_output_with_cycles(capsys):
    """Ensure cycles are correctly printed in table output."""
    graph = make_graph(triggered=True)
    changed_files = ["file1.py"]
    stages = [["node1"]]
    cycles = [["node1", "node2", "node1"]]

    render_output(graph, changed_files, cycles, stages, fmt="table")
    out = capsys.readouterr().out
    assert "Dependency cycles detected" in out
    assert "node1 → node2 → node1" in out
