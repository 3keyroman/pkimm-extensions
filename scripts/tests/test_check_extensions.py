import shutil
from pathlib import Path

import pytest
import yaml

import scripts.check_extensions as ce
import scripts.generate_catalog_docs as gen

REAL_ROOT = Path(__file__).resolve().parents[2]

SEED = [
    "catalog.schema-1.0.0.json", "catalog.yaml",
    "pqc/_index.md", "pqc/pqc-extension.yaml",
    "pkimm-model/extension.schema-1.0.0.json",
    "pkimm-model/2.0.0/pkimm-model-2.0.0.yaml",
    "pkimm-model/2.0.0/pkimm-references.yaml",
]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for rel in SEED:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REAL_ROOT / rel, dst)
    gen.generate(tmp_path)  # produce _index.md + pqc/definition/_index.md
    return tmp_path


def _errors(repo: Path):
    return [i.message for i in ce.check_all(repo) if i.severity == "error"]


def test_valid_repo_has_no_errors(repo):
    assert _errors(repo) == []


def test_definition_file_missing(repo):
    (repo / "pqc/pqc-extension.yaml").unlink()
    assert any("definition" in m.lower() for m in _errors(repo))


def test_version_mismatch(repo):
    cat = yaml.safe_load((repo / "catalog.yaml").read_text())
    cat["extensions"][0]["version"] = "9.9.9"
    (repo / "catalog.yaml").write_text(yaml.safe_dump(cat))
    assert any("version" in m.lower() for m in _errors(repo))


def test_overlay_requirement_wrong_category(repo):
    ext = yaml.safe_load((repo / "pqc/pqc-extension.yaml").read_text())
    ext["overlays"]["modules"][0]["categories"][0]["requirements"] = [
        {"id": "key-inventory", "type": "multiplier", "multiplier": 2, "rationale": "x"}
    ]
    (repo / "pqc/pqc-extension.yaml").write_text(yaml.safe_dump(ext))
    gen.generate(repo)  # keep generated docs in sync so only the target error shows
    assert any("key-inventory" in m for m in _errors(repo))


def test_unknown_reference(repo):
    ext = yaml.safe_load((repo / "pqc/pqc-extension.yaml").read_text())
    ext["relevance"]["modules"][0]["categories"][0]["references"] = ["totally-unknown-ref"]
    (repo / "pqc/pqc-extension.yaml").write_text(yaml.safe_dump(ext))
    gen.generate(repo)
    assert any("totally-unknown-ref" in m for m in _errors(repo))


def test_incompatible_version(repo):
    ext = yaml.safe_load((repo / "pqc/pqc-extension.yaml").read_text())
    ext["extension"]["compatibility"] = ["1.0.0"]
    (repo / "pqc/pqc-extension.yaml").write_text(yaml.safe_dump(ext))
    cat = yaml.safe_load((repo / "catalog.yaml").read_text())
    cat["extensions"][0]["compatibility"] = ["1.0.0"]
    (repo / "catalog.yaml").write_text(yaml.safe_dump(cat))
    assert any("1.0.0" in m or "compat" in m.lower() for m in _errors(repo))


def test_stale_generated_table(repo):
    (repo / "_index.md").write_text("---\ntitle: Extensions\n---\n\n# tampered\n")
    assert any("_index.md" in m or "stale" in m.lower() for m in _errors(repo))


def test_duplicate_ids(repo):
    cat = yaml.safe_load((repo / "catalog.yaml").read_text())
    cat["extensions"].append(dict(cat["extensions"][0]))
    (repo / "catalog.yaml").write_text(yaml.safe_dump(cat))
    assert any("duplicate" in m.lower() for m in _errors(repo))


def test_vendored_model_internal_version_mismatch(repo):
    model = yaml.safe_load((repo / "pkimm-model/2.0.0/pkimm-model-2.0.0.yaml").read_text())
    model["version"] = "9.9.9"
    (repo / "pkimm-model/2.0.0/pkimm-model-2.0.0.yaml").write_text(yaml.safe_dump(model))
    assert any("version" in m.lower() and "expected" in m.lower() for m in _errors(repo))
