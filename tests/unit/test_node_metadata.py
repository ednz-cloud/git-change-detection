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


def test_annotations_default_empty():
    node = NodeMetadata(name="playbook1")
    assert node.annotations == {}


def test_merge_annotations_deep_merges_dicts():
    node = NodeMetadata(name="playbook1")
    node.merge({"annotations": {"owner": "a", "opts": {"timeout": 10, "tags": ["x"]}}})
    node.merge({"annotations": {"opts": {"retries": 3}, "team": "infra"}})

    assert node.annotations == {
        "owner": "a",
        "team": "infra",
        "opts": {"timeout": 10, "tags": ["x"], "retries": 3},
    }


@pytest.mark.parametrize(
    "first, second, expected",
    [
        ({"k": "a"}, {"k": "b"}, {"k": "b"}),
        ({"k": ["a"]}, {"k": ["b"]}, {"k": ["b"]}),
        ({"k": {"x": 1}}, {"k": "scalar"}, {"k": "scalar"}),
        ({"k": "scalar"}, {"k": {"x": 1}}, {"k": {"x": 1}}),
        ({"k": 1}, {"k": None}, {"k": None}),
    ],
)
def test_merge_annotations_later_value_wins(first, second, expected):
    node = NodeMetadata(name="playbook1")
    node.merge({"annotations": first})
    node.merge({"annotations": second})
    assert node.annotations == expected


def test_merge_without_annotations_keeps_existing():
    node = NodeMetadata(name="playbook1", annotations={"owner": "a"})
    node.merge({"depends_on": ["b"]})
    assert node.annotations == {"owner": "a"}


def test_merge_annotations_does_not_alias_source():
    source = {"opts": {"tags": ["x"]}}
    node = NodeMetadata(name="playbook1")
    node.merge({"annotations": source})
    node.annotations["opts"]["tags"].append("y")
    assert source == {"opts": {"tags": ["x"]}}


@pytest.mark.parametrize("annotations", [["owner"], "owner", 42])
def test_merge_annotations_rejects_non_mapping(annotations):
    node = NodeMetadata(name="playbook1")
    with pytest.raises(TypeError, match="playbook1"):
        node.merge({"annotations": annotations})
