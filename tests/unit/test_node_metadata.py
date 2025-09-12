import pytest
from git_change_detection.models.node_metadata import NodeMetadata


@pytest.mark.parametrize(
    "name, depends_on, triggers",
    [
        ("playbook1", [], {}),
        ("playbook2", ["a"], {"src": ["*.py"]}),
    ],
)
def test_initialization(name, depends_on, triggers):
    node = NodeMetadata(name=name, depends_on=depends_on, triggers=triggers)
    assert node.name == name
    assert node.depends_on == depends_on
    assert node.triggers == triggers
    assert node.triggered is False
    assert node.triggered_by == []
    assert node.stage is None


def test_merge_dependencies_and_triggers():
    node = NodeMetadata(name="playbook1", depends_on=["a"], triggers={"src": ["*.py"]})

    node.merge(
        {
            "depends_on": ["b", "a"],
            "triggers": {"src": ["*.yaml", "*.py"], "config": ["*.json"]},
        }
    )

    assert set(node.depends_on) == {"a", "b"}

    assert set(node.triggers["src"]) == {"*.py", "*.yaml"}
    assert node.triggers["config"] == ["*.json"]


@pytest.mark.parametrize(
    "file, pattern",
    [
        ("file1.py", "src/*.py"),
        ("file2.yaml", "config/*.yaml"),
    ],
)
def test_mark_triggered(file, pattern):
    node = NodeMetadata(name="playbook1")
    node.mark_triggered(file, pattern)
    assert node.triggered is True
    assert node.triggered_by == [{"file": file, "pattern": pattern}]


def test_merge_and_trigger_combined():
    node = NodeMetadata(name="playbook1", depends_on=["a"], triggers={"src": ["*.py"]})
    node.merge({"depends_on": ["b"], "triggers": {"src": ["*.yaml"]}})
    node.mark_triggered("file2.yaml", "src/*.yaml")

    assert set(node.depends_on) == {"a", "b"}
    assert set(node.triggers["src"]) == {"*.py", "*.yaml"}
    assert node.triggered is True
    assert node.triggered_by == [{"file": "file2.yaml", "pattern": "src/*.yaml"}]
