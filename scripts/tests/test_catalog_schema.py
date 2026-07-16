import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def test_catalog_yaml_matches_schema():
    schema = json.loads((ROOT / "catalog.schema-1.0.0.json").read_text())
    data = yaml.safe_load((ROOT / "catalog.yaml").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=str)
    assert errors == [], [e.message for e in errors]
