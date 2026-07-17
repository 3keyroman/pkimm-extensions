import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def test_pqc_extension_validates_against_vendored_schema():
    schema = json.loads((ROOT / "pkimm-model/extension.schema-1.0.0.json").read_text())
    ext = yaml.safe_load((ROOT / "pqc/pqc-extension.yaml").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(ext), key=str)
    assert errors == [], [e.message for e in errors]


def test_pqc_documentation_url_is_new_path():
    ext = yaml.safe_load((ROOT / "pqc/pqc-extension.yaml").read_text())
    assert ext["extension"]["documentation"] == "https://pkic.org/wg/pkimm/extensions/pqc/"


def test_no_stale_catalog_paths_in_migrated_files():
    for rel in ["pqc/_index.md", "pqc/pqc-extension.yaml"]:
        text = (ROOT / rel).read_text()
        assert "model/extensions/catalog" not in text, rel
