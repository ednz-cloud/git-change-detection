import tempfile
import json
import yaml
import pytest
from pathlib import Path
from git_change_detection.utils.io import load_metadata_file


@pytest.mark.parametrize(
    "content, suffix, expected",
    [
        ({"foo": "bar"}, ".yaml", {"foo": "bar"}),
        ({"foo": "bar"}, ".json", {"foo": "bar"}),
        ('foo = "bar"\n', ".toml", {"foo": "bar"}),
    ],
)
def test_load_metadata_file_variants(content, suffix, expected):
    mode = "w" if isinstance(content, (dict)) else "w+b"
    with tempfile.NamedTemporaryFile(mode, suffix=suffix) as f:
        if suffix == ".toml":
            f.write(content.encode())
        elif suffix == ".json":
            json.dump(content, f)
        else:  # yaml
            yaml.dump(content, f)
        f.flush()
        result = load_metadata_file(Path(f.name))
    assert result == expected


def test_unsupported_extension():
    with tempfile.NamedTemporaryFile("w", suffix=".txt") as f:
        f.write("whatever")
        f.flush()
        with pytest.raises(ValueError):
            load_metadata_file(Path(f.name))
