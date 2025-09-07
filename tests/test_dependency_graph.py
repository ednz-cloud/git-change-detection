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


def test_remove_node(linear_graph):
    graph = linear_graph
    graph.remove_node("b")
    assert "b" not in graph.nodes
    assert graph.nodes["c"].depends_on == []


def test_deep_merge_blacklist(linear_graph):
    graph = linear_graph
    data = {"blacklist": ["b"], "a": {"triggers": {"src": ["*.txt"]}}}
    graph.deep_merge(data)
    assert "b" not in graph.nodes
    assert graph.nodes["a"].triggers["src"] == ["*.txt"]


def test_mark_triggered(tree_graph):
    graph = tree_graph
    graph.mark_triggered("root", "file1.py", "src/*.py")
    assert graph.nodes["root"].triggered
    assert graph.nodes["root"].triggered_by == [
        {"file": "file1.py", "pattern": "src/*.py"}
    ]


@pytest.mark.parametrize(
    "graph_fixture", ["linear_graph", "diamond_graph", "tree_graph"]
)
def test_build_triggered_stages_single_trigger(request, graph_fixture):
    graph = request.getfixturevalue(graph_fixture)
    # trigger first node
    first_node = list(graph.nodes.keys())[0]
    graph.mark_triggered(first_node, "file1.py", "*.py")
    stages = graph.build_triggered_stages()

    # Only triggered node in stage 1
    assert stages[0] == [first_node]
    assert graph.nodes[first_node].stage == 1


def test_detect_cycles(cyclic_graph):
    cycles = cyclic_graph.detect_cycles()
    assert any("a" in cycle for cycle in cycles)
    assert any("b" in cycle for cycle in cycles)
    assert any("c" in cycle for cycle in cycles)


def test_detect_multiple_cycles(multi_cycle_graph):
    graph = multi_cycle_graph
    cycles = graph.detect_cycles()
    # Should detect two cycles
    found_nodes = {n for cycle in cycles for n in cycle}
    assert all(n in found_nodes for n in ["a", "b", "c", "x", "y"])


def test_build_triggered_stages_diamond(diamond_graph):
    graph = diamond_graph
    graph.mark_triggered("a", "file1.py", "src/*.py")
    stages = graph.build_triggered_stages()
    # Only "a" triggered
    assert stages == [["a"]]
    assert graph.nodes["a"].stage == 1
    assert graph.nodes["b"].stage is None
    assert graph.nodes["c"].stage is None
    assert graph.nodes["d"].stage is None


def test_build_triggered_stages_tree(tree_graph):
    graph = tree_graph
    graph.mark_triggered("root", "file1.py", "src/*.py")
    stages = graph.build_triggered_stages()
    assert stages == [["root"]]
    assert graph.nodes["root"].stage == 1
    assert all(
        graph.nodes[n].stage is None for n in ["branch1", "branch2", "leaf1", "leaf2"]
    )
