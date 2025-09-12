import json
import yaml
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

with open("schemas/metadata.schema.json", encoding="UTF-8") as f:
    SCHEMA = json.load(f)


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
