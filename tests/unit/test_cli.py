import json
import pytest
from typer.testing import CliRunner
from gitcd import cli
from gitcd.models.node_metadata import NodeMetadata


runner = CliRunner()


@pytest.fixture
def mock_graph(mocker):
    """Fixture to mock DependencyGraph + get_changed_files behavior."""
    mock_graph = mocker.patch("gitcd.cli.DependencyGraph", autospec=True).return_value
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

    mocker.patch("gitcd.cli.get_changed_files", return_value=["src/foo.py"])
    result = runner.invoke(cli.app, ["a", "b", "-m", str(metadata)])

    assert result.exit_code == 0
    assert "node1" in result.stdout


def test_detect_json_output(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch("gitcd.cli.get_changed_files", return_value=["src/foo.py"])
    result = runner.invoke(cli.app, ["a", "b", "-m", str(metadata), "--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "node1" in data


def test_detect_error_path(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch("gitcd.cli.get_changed_files", side_effect=RuntimeError("bad repo"))
    result = runner.invoke(cli.app, ["a", "b", "-m", str(metadata)])

    assert result.exit_code == 1
    assert "Error: bad repo" in result.stdout


def test_detect_no_triggers(mocker, tmp_path):
    metadata = tmp_path / "meta.yaml"
    metadata.write_text("node1:\n  triggers:\n    src: ['*.py']")

    mocker.patch("gitcd.cli.get_changed_files", return_value=["other/file.txt"])
    result = runner.invoke(cli.app, ["a", "b", "-m", str(metadata)])

    assert result.exit_code == 0
    assert "(none)" in result.stdout


def test_detect_missing_metadata_flag():
    result = runner.invoke(cli.app, ["a", "b"])

    # Typer should exit with code 2 (typical for missing required argument)
    assert result.exit_code == 2
