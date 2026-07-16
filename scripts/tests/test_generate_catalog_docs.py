import shutil
from pathlib import Path

import yaml

import scripts.generate_catalog_docs as g
import scripts.pkimm_model as pm

ROOT = Path(__file__).resolve().parents[2]

SEED = [
    "catalog.yaml",
    "pqc/pqc-extension.yaml",
    "pkimm-model/2.0.0/pkimm-model-2.0.0.yaml",
    "pkimm-model/2.0.0/pkimm-references.yaml",
]


def test_table_lists_pqc():
    catalog = yaml.safe_load((ROOT / "catalog.yaml").read_text())
    md = g.render_catalog_table(catalog)
    assert "title: Extensions" in md
    assert "sideMenu: true" in md
    assert "PQC Readiness Extension" in md
    assert "Under development" in md  # badge label for under-development
    assert "pqc/pqc-extension.yaml" in md  # YAML download link


def test_definition_renders_criteria_and_overlays():
    ext = yaml.safe_load((ROOT / "pqc/pqc-extension.yaml").read_text())
    idx = {"2.0.0": pm.ModelIndex(pm.load_model(ROOT, "2.0.0"))}
    md = g.render_definition(ext, idx)
    assert "title: Definition" in md
    assert "Strategy and vision" in md   # category title resolved from the model
    assert "## Overlays" in md


def test_generate_writes_and_is_idempotent(tmp_path: Path):
    for rel in SEED:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, dst)

    g.generate(tmp_path)
    assert (tmp_path / "_index.md").exists()
    assert (tmp_path / "pqc/definition/_index.md").exists()
    first_index = (tmp_path / "_index.md").read_text()
    first_def = (tmp_path / "pqc/definition/_index.md").read_text()

    g.generate(tmp_path)
    assert (tmp_path / "_index.md").read_text() == first_index
    assert (tmp_path / "pqc/definition/_index.md").read_text() == first_def
