import pytest
from gitcd.models.node_metadata import NodeMetadata


def test_initialization():
    node = NodeMetadata(name="playbook1")
    assert node.name == "playbook1"
    assert node.depends_on == []
    assert node.triggers == {}
    assert node.triggered is False
    assert node.triggered_by == []
    assert node.stage is None


def test_merge_dependencies():
    node = NodeMetadata(name="playbook1", depends_on=["a"])
    node.merge({"depends_on": ["b", "a"]})
    # Should merge and deduplicate
    assert set(node.depends_on) == {"a", "b"}


def test_merge_triggers():
    node = NodeMetadata(name="playbook1", triggers={"src": ["*.py"]})
    node.merge({"triggers": {"src": ["*.yaml", "*.py"], "config": ["*.json"]}})
    # Existing triggers are merged, duplicates removed
    assert set(node.triggers["src"]) == {"*.py", "*.yaml"}
    assert node.triggers["config"] == ["*.json"]


def test_mark_triggered():
    node = NodeMetadata(name="playbook1")
    node.mark_triggered("file1.py", "src/*.py")
    assert node.triggered is True
    assert node.triggered_by == [{"file": "file1.py", "pattern": "src/*.py"}]


def test_merge_and_trigger_together():
    node = NodeMetadata(name="playbook1", depends_on=["a"], triggers={"src": ["*.py"]})
    node.merge({"depends_on": ["b"], "triggers": {"src": ["*.yaml"]}})
    node.mark_triggered("file2.yaml", "src/*.yaml")

    assert set(node.depends_on) == {"a", "b"}
    assert set(node.triggers["src"]) == {"*.py", "*.yaml"}
    assert node.triggered is True
    assert node.triggered_by == [{"file": "file2.yaml", "pattern": "src/*.yaml"}]
