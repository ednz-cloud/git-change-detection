import json
import tomllib
from importlib import resources
from pathlib import Path
from typing import Any, Dict

import yaml


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema for metadata validation."""
    schema_file = resources.files("git_change_detection.schemas").joinpath("metadata.schema.json")
    return json.loads(schema_file.read_text(encoding="utf-8"))


def load_metadata_file(path: Path) -> Dict[str, Any]:
    """Load a metadata file in YAML, JSON, or TOML format."""
    suffix = path.suffix.lower()
    with path.open("rb") as f:  # rb so tomllib works
        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(f) or {}
        elif suffix == ".json":
            return json.load(f)
        elif suffix == ".toml":
            return tomllib.load(f)
        else:
            raise ValueError(f"Unsupported metadata format: {path}")
