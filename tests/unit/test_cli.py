import json
import pytest
from typer.testing import CliRunner
from git_change_detection import cli
from git_change_detection.models.node_metadata import NodeMetadata


runner = CliRunner()


@pytest.fixture
def mock_graph(mocker):
    """Fixture to mock DependencyGraph + get_changed_files behavior."""
    mock_graph = mocker.patch(
        "git_change_detection.cli.DependencyGraph", autospec=True
    ).return_value
    mock_graph.load_files.return_value = None
    mock_graph.sanitize_dependencies.return_value = None
    mock_graph.detect_cycles.return_value = []
    mock_graph.build_triggered_stages.return_value = [["node1"]]
    mock_graph.nodes = {
        "node1": NodeMetadata(name="node1", triggers={"src": ["*.py"]}, triggered=False)
    }
    return mock_graph


def test_detect_happy_path(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch("git_change_detection.cli.get_changed_files", return_value=["src/foo.py"])
    result = runner.invoke(cli.app, ["detect", "a", "b", "-m", str(metadata)])

    assert result.exit_code == 0
    assert "node1" in result.stdout


def test_detect_json_output(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch("git_change_detection.cli.get_changed_files", return_value=["src/foo.py"])
    result = runner.invoke(cli.app, ["detect", "a", "b", "-m", str(metadata), "--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "node1" in data


def test_detect_error_path(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch(
        "git_change_detection.cli.get_changed_files",
        side_effect=RuntimeError("bad repo"),
    )
    result = runner.invoke(cli.app, ["detect", "a", "b", "-m", str(metadata)])

    assert result.exit_code == 1
    assert "Error: bad repo" in result.stdout


def test_detect_no_triggers(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch("git_change_detection.cli.get_changed_files", return_value=["other/file.txt"])
    result = runner.invoke(cli.app, ["detect", "a", "b", "-m", str(metadata)])

    assert result.exit_code == 0
    assert "(none)" in result.stdout


def test_detect_missing_metadata_flag():
    result = runner.invoke(cli.app, ["detect", "a", "b"])

    # Typer should exit with code 2 (typical for missing required argument)
    assert result.exit_code == 2


# --- validate command tests ---


def test_validate_valid_metadata(tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    result = runner.invoke(cli.app, ["validate", "-m", str(metadata)])

    assert result.exit_code == 0
    assert "schema valid" in result.stdout
    assert "All validations passed" in result.stdout


def test_validate_invalid_schema(tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers: not_a_dict")

    result = runner.invoke(cli.app, ["validate", "-m", str(metadata)])

    assert result.exit_code == 1
    assert "schema error" in result.stdout


def test_validate_missing_dependencies(tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text(
        "node1:\n  depends_on:\n    - nonexistent_node\n  triggers:\n    src: ['*.py']"
    )

    result = runner.invoke(cli.app, ["validate", "-m", str(metadata)])

    assert result.exit_code == 1
    assert "Missing dependencies" in result.stdout
    assert "nonexistent_node" in result.stdout


def test_validate_cycle_detection(tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text(
        "node_a:\n"
        "  depends_on: [node_b]\n"
        "  triggers:\n"
        "    src: ['a.py']\n"
        "node_b:\n"
        "  depends_on: [node_a]\n"
        "  triggers:\n"
        "    src: ['b.py']"
    )

    result = runner.invoke(cli.app, ["validate", "-m", str(metadata)])

    assert result.exit_code == 1
    assert "cycles detected" in result.stdout


def test_validate_multiple_files(tmp_path):
    meta1 = tmp_path / "meta1.yaml"
    meta1.write_text("node1:\n  triggers:\n    src: ['*.py']")

    meta2 = tmp_path / "meta2.yaml"
    meta2.write_text("node2:\n  depends_on: [node1]\n  triggers:\n    lib: ['*.py']")

    result = runner.invoke(cli.app, ["validate", "-m", str(meta1), "-m", str(meta2)])

    assert result.exit_code == 0
    assert "All validations passed" in result.stdout
