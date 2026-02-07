import json
import pytest
import yaml
from jsonschema import validate, ValidationError
from pathlib import Path

from git_change_detection.utils.io import load_schema

SCHEMA = load_schema()


@pytest.mark.parametrize(
    "file",
    [
        "tests/fixtures/valid_metadata.yml",
        "tests/fixtures/valid_metadata.json",
    ],
)
def test_valid_metadata(file):
    ext = Path(file).suffix
    with open(file, encoding="UTF-8") as f:
        data = yaml.safe_load(f) if ext in (".yml", ".yaml") else json.load(f)
    validate(instance=data, schema=SCHEMA)


@pytest.mark.parametrize(
    "file",
    [
        "tests/fixtures/invalid_metadata.yml",
        "tests/fixtures/invalid_metadata.json",
    ],
)
def test_invalid_metadata(file):
    ext = Path(file).suffix
    with open(file, encoding="UTF-8") as f:
        data = yaml.safe_load(f) if ext in (".yml", ".yaml") else json.load(f)
    with pytest.raises(ValidationError):
        validate(instance=data, schema=SCHEMA)
