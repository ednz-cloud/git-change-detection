import pytest
from gitcd.models.node_metadata import NodeMetadata
from gitcd.models.dependency_graph import DependencyGraph


@pytest.fixture
def linear_graph():
    """a -> b -> c"""
    g = DependencyGraph()
    g.nodes = {
        "a": NodeMetadata(name="a"),
        "b": NodeMetadata(name="b", depends_on=["a"]),
        "c": NodeMetadata(name="c", depends_on=["b"]),
    }
    return g


@pytest.fixture
def diamond_graph():
    """Diamond: a -> b,c -> d"""
    g = DependencyGraph()
    g.nodes = {
        "a": NodeMetadata(name="a", triggers={"src": ["*.py"]}),
        "b": NodeMetadata(name="b", depends_on=["a"]),
        "c": NodeMetadata(name="c", depends_on=["a"]),
        "d": NodeMetadata(name="d", depends_on=["b", "c"]),
    }
    return g


@pytest.fixture
def cyclic_graph():
    """Cycle: a -> b -> c -> a"""
    g = DependencyGraph()
    g.nodes = {
        "a": NodeMetadata(name="a", depends_on=["b"]),
        "b": NodeMetadata(name="b", depends_on=["c"]),
        "c": NodeMetadata(name="c", depends_on=["a"]),
    }
    return g


@pytest.fixture
def multi_cycle_graph():
    """Two cycles: a->b->c->a and x->y->x"""
    g = DependencyGraph()
    g.nodes = {
        "a": NodeMetadata(name="a", depends_on=["b"]),
        "b": NodeMetadata(name="b", depends_on=["c"]),
        "c": NodeMetadata(name="c", depends_on=["a"]),
        "x": NodeMetadata(name="x", depends_on=["y"]),
        "y": NodeMetadata(name="y", depends_on=["x"]),
    }
    return g


@pytest.fixture
def tree_graph():
    """Tree: root -> branch1, branch2 -> leaf1, leaf2"""
    g = DependencyGraph()
    g.nodes = {
        "root": NodeMetadata(name="root", triggers={"src": ["*.py"]}),
        "branch1": NodeMetadata(name="branch1", depends_on=["root"]),
        "branch2": NodeMetadata(name="branch2", depends_on=["root"]),
        "leaf1": NodeMetadata(name="leaf1", depends_on=["branch1"]),
        "leaf2": NodeMetadata(name="leaf2", depends_on=["branch2"]),
    }
    return g


def test_remove_node(fixture_linear_graph):
    graph_local = fixture_linear_graph
    graph_local.remove_node("b")
    assert "b" not in graph_local.nodes
    assert graph_local.nodes["c"].depends_on == []


def test_deep_merge_blacklist(fixture_linear_graph):
    graph_local = fixture_linear_graph
    data = {"blacklist": ["b"], "a": {"triggers": {"src": ["*.txt"]}}}
    graph_local.deep_merge(data)
    assert "b" not in graph_local.nodes
    assert graph_local.nodes["a"].triggers["src"] == ["*.txt"]


def test_mark_triggered(fixture_tree_graph):
    graph_local = fixture_tree_graph
    graph_local.mark_triggered("root", "file1.py", "src/*.py")
    assert graph_local.nodes["root"].triggered
    assert graph_local.nodes["root"].triggered_by == [
        {"file": "file1.py", "pattern": "src/*.py"}
    ]


@pytest.mark.parametrize(
    "graph_fixture_name", ["linear_graph", "diamond_graph", "tree_graph"]
)
def test_build_triggered_stages_single_trigger(request, graph_fixture_name):
    graph_local = request.getfixturevalue(graph_fixture_name)
    first_node = list(graph_local.nodes.keys())[0]
    graph_local.mark_triggered(first_node, "file1.py", "*.py")
    stages = graph_local.build_triggered_stages()

    assert stages[0] == [first_node]
    assert graph_local.nodes[first_node].stage == 1


def test_detect_cycles(fixture_cyclic_graph):
    graph_local = fixture_cyclic_graph
    cycles = graph_local.detect_cycles()
    assert any("a" in cycle for cycle in cycles)
    assert any("b" in cycle for cycle in cycles)
    assert any("c" in cycle for cycle in cycles)


def test_detect_multiple_cycles(fixture_multi_cycle_graph):
    graph_local = fixture_multi_cycle_graph
    cycles = graph_local.detect_cycles()
    found_nodes = {n for cycle in cycles for n in cycle}
    assert all(n in found_nodes for n in ["a", "b", "c", "x", "y"])


def test_build_triggered_stages_diamond(fixture_diamond_graph):
    graph_local = fixture_diamond_graph
    graph_local.mark_triggered("a", "file1.py", "src/*.py")
    stages = graph_local.build_triggered_stages()

    assert stages == [["a"]]
    assert graph_local.nodes["a"].stage == 1
    assert graph_local.nodes["b"].stage is None
    assert graph_local.nodes["c"].stage is None
    assert graph_local.nodes["d"].stage is None


def test_build_triggered_stages_tree(fixture_tree_graph):
    graph_local = fixture_tree_graph
    graph_local.mark_triggered("root", "file1.py", "src/*.py")
    stages = graph_local.build_triggered_stages()
    assert stages == [["root"]]
    assert graph_local.nodes["root"].stage == 1
    assert all(
        graph_local.nodes[n].stage is None
        for n in ["branch1", "branch2", "leaf1", "leaf2"]
    )
