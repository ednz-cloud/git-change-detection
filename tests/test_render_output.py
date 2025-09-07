import json
from gitcd.models.dependency_graph import DependencyGraph
from gitcd.models.node_metadata import NodeMetadata
from gitcd.utils.output import render_output  # adjust import to your actual path


def make_graph(triggered=False):
    g = DependencyGraph()
    g.nodes["node1"] = NodeMetadata(name="node1")
    g.nodes["node2"] = NodeMetadata(name="node2")
    if triggered:
        g.nodes["node1"].mark_triggered("file1.py", "src/*.py")
    return g


def test_render_output_json_mode(capsys):
    graph = make_graph(triggered=True)
    render_output(graph, ["file1.py"], [], [["node1"]], fmt="json")
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "node1" in data
    assert data["node1"]["triggered"] is True
    assert data["node1"]["triggered_by"][0]["file"] == "file1.py"


def test_render_output_table_mode(capsys):
    graph = make_graph(triggered=True)
    render_output(graph, ["file1.py"], [], [["node1"]], fmt="table")
    out = capsys.readouterr().out
    # Check key sections exist
    assert "Changed files" in out
    assert "Triggered Nodes" in out
    assert "node1" in out
    assert "file1.py" in out
    assert "src/*.py" in out
    assert "Deployment Stages" in out
    assert "Stage 1: node1" in out


def test_render_output_table_no_triggers(capsys):
    graph = make_graph(triggered=False)
    render_output(graph, ["file2.txt"], [], [["node2"]], fmt="table")
    out = capsys.readouterr().out
    # Should indicate no triggered nodes
    assert "(none)" in out
    assert "file2.txt" in out
    assert "Stage 1: node2" in out


def test_render_output_with_cycles(capsys):
    graph = make_graph(triggered=True)
    render_output(graph, ["file1.py"], [["node1", "node2", "node1"]], [["node1"]])
    out = capsys.readouterr().out
    assert "Dependency cycles detected" in out
    assert "node1 → node2 → node1" in out
