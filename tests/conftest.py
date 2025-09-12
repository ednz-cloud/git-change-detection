import pytest
from git_change_detection.models.node_metadata import NodeMetadata


@pytest.fixture
def simple_node():
    return NodeMetadata(name="node1")


@pytest.fixture
def node_with_deps():
    return NodeMetadata(name="node2", depends_on=["node1"], triggers={"src": ["*.py"]})


@pytest.fixture
def multiple_nodes():
    return [
        NodeMetadata(name="a", depends_on=[]),
        NodeMetadata(name="b", depends_on=["a"]),
        NodeMetadata(name="c", depends_on=["b"]),
    ]
