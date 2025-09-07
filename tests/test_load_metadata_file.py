from pathlib import Path
import tempfile
import json
import yaml
import pytest
from gitcd.utils.io import load_metadata_file


def test_load_yaml():
    data = {"foo": "bar"}
    with tempfile.NamedTemporaryFile("w", suffix=".yaml") as f:
        yaml.dump(data, f)
        f.flush()
        result = load_metadata_file(Path(f.name))
    assert result == data


def test_load_json():
    data = {"foo": "bar"}
    with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
        json.dump(data, f)
        f.flush()
        result = load_metadata_file(Path(f.name))
    assert result == data


def test_load_toml():
    data = {"foo": "bar"}
    toml_content = 'foo = "bar"\n'
    with tempfile.NamedTemporaryFile("w+b", suffix=".toml") as f:
        f.write(toml_content.encode())
        f.flush()
        result = load_metadata_file(Path(f.name))
    assert result == data


def test_unsupported_extension():
    with tempfile.NamedTemporaryFile("w", suffix=".txt") as f:
        f.write("whatever")
        f.flush()

        with pytest.raises(ValueError):
            load_metadata_file(Path(f.name))
