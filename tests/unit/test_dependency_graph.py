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


@pytest.mark.parametrize(
    "graph_fixture,node_to_remove,expected_remaining_deps",
    [
        ("linear_graph", "b", {"c": []}),
    ],
)
def test_remove_node(request, graph_fixture, node_to_remove, expected_remaining_deps):
    graph = request.getfixturevalue(graph_fixture)
    graph.remove_node(node_to_remove)
    for n, deps in expected_remaining_deps.items():
        assert graph.nodes[n].depends_on == deps


@pytest.mark.parametrize(
    "graph_fixture,merge_data,node_to_check,expected_triggers",
    [
        (
            "linear_graph",
            {"blacklist": ["b"], "a": {"triggers": {"src": ["*.txt"]}}},
            "a",
            ["*.txt"],
        ),
    ],
)
def test_deep_merge_blacklist(
    request, graph_fixture, merge_data, node_to_check, expected_triggers
):
    graph = request.getfixturevalue(graph_fixture)
    graph.deep_merge(merge_data)
    assert node_to_check not in graph.nodes or node_to_check != "b"
    assert graph.nodes[node_to_check].triggers["src"] == expected_triggers


@pytest.mark.parametrize(
    "graph_fixture,node_name,file,pattern",
    [
        ("tree_graph", "root", "file1.py", "src/*.py"),
    ],
)
def test_mark_triggered(request, graph_fixture, node_name, file, pattern):
    graph = request.getfixturevalue(graph_fixture)
    graph.mark_triggered(node_name, file, pattern)
    node = graph.nodes[node_name]
    assert node.triggered
    assert node.triggered_by == [{"file": file, "pattern": pattern}]


@pytest.mark.parametrize(
    "graph_fixture", ["linear_graph", "diamond_graph", "tree_graph"]
)
def test_build_triggered_stages_single_trigger(request, graph_fixture):
    graph = request.getfixturevalue(graph_fixture)
    first_node = list(graph.nodes.keys())[0]
    graph.mark_triggered(first_node, "file1.py", "*.py")
    stages = graph.build_triggered_stages()
    assert stages[0] == [first_node]
    assert graph.nodes[first_node].stage == 1


@pytest.mark.parametrize(
    "graph_fixture,expected_nodes",
    [
        ("cyclic_graph", ["a", "b", "c"]),
    ],
)
def test_detect_cycles(request, graph_fixture, expected_nodes):
    graph = request.getfixturevalue(graph_fixture)
    cycles = graph.detect_cycles()
    found_nodes = {n for cycle in cycles for n in cycle}
    for n in expected_nodes:
        assert n in found_nodes


@pytest.mark.parametrize(
    "graph_fixture,expected_nodes",
    [
        ("multi_cycle_graph", ["a", "b", "c", "x", "y"]),
    ],
)
def test_detect_multiple_cycles(request, graph_fixture, expected_nodes):
    graph = request.getfixturevalue(graph_fixture)
    cycles = graph.detect_cycles()
    found_nodes = {n for cycle in cycles for n in cycle}
    for n in expected_nodes:
        assert n in found_nodes


@pytest.mark.parametrize(
    "graph_fixture,trigger_node,expected_stages",
    [
        ("diamond_graph", "a", [["a"]]),
        ("tree_graph", "root", [["root"]]),
    ],
)
def test_build_triggered_stages(request, graph_fixture, trigger_node, expected_stages):
    graph = request.getfixturevalue(graph_fixture)
    graph.mark_triggered(trigger_node, "file1.py", "src/*.py")
    stages = graph.build_triggered_stages()
    assert stages == expected_stages
    assert graph.nodes[trigger_node].stage == 1
