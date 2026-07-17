#!/usr/bin/env python3
"""Validate pkimm-extensions against its schema, the vendored pkimm model, and
internal parity rules. Hermetic. Exits non-zero on any error."""
from __future__ import annotations
import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts import pkimm_model as pm
from scripts import generate_catalog_docs as gen


@dataclasses.dataclass
class Issue:
    severity: str
    message: str


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def _validate_schema(data: Any, schema_path: Path, label: str) -> list[Issue]:
    schema = json.loads(schema_path.read_text())
    return [Issue("error", f"{label}: schema violation: {e.message}")
            for e in sorted(Draft202012Validator(schema).iter_errors(data), key=str)]


def check_all(repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    catalog_path = repo_root / "catalog.yaml"
    if not catalog_path.exists():
        return [Issue("error", "catalog.yaml not found")]
    catalog = _load_yaml(catalog_path)

    issues += _validate_schema(catalog, repo_root / "catalog.schema-1.0.0.json", "catalog.yaml")

    entries = catalog.get("extensions", [])
    ids = [e.get("id") for e in entries]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        issues.append(Issue("error", f"duplicate extension id '{dup}' in catalog.yaml"))

    ext_schema_path = repo_root / "pkimm-model" / "extension.schema-1.0.0.json"

    for entry in entries:
        ext_id = entry.get("id", "?")
        def_path = repo_root / entry.get("definition", "")
        if not def_path.exists():
            issues.append(Issue("error", f"{ext_id}: definition file '{entry.get('definition')}' does not exist"))
            continue
        ext = _load_yaml(def_path)
        issues += _validate_schema(ext, ext_schema_path, f"{ext_id} extension")
        meta = ext.get("extension", {})
        if meta.get("id") != entry.get("id"):
            issues.append(Issue("error", f"{ext_id}: manifest id != extension.id ({meta.get('id')})"))
        if meta.get("version") != entry.get("version"):
            issues.append(Issue("error", f"{ext_id}: manifest version {entry.get('version')} != extension.version {meta.get('version')}"))
        if sorted(meta.get("compatibility", [])) != sorted(entry.get("compatibility", [])):
            issues.append(Issue("error", f"{ext_id}: manifest compatibility != extension.compatibility"))

        for cv in meta.get("compatibility", []):
            issues += _require_vendored_files(repo_root, cv, ext_id)
            model_yaml = pm.vendored_dir(repo_root, cv) / f"pkimm-model-{cv}.yaml"
            if not model_yaml.exists():
                continue
            model = pm.load_model(repo_root, cv)
            if model.get("version") != cv:
                issues.append(Issue("error", f"{ext_id}: vendored model {cv} declares version {model.get('version')}"))
            idx = pm.ModelIndex(model)
            ref_ids = pm.load_references(repo_root, cv) | {
                r["id"] for r in ext.get("references", []) if isinstance(r, dict) and "id" in r}
            issues += _check_relevance(ext_id, ext, idx, ref_ids)
            issues += _check_overlays(ext_id, ext, idx)

    issues += _check_vendored_integrity(repo_root)
    issues += _check_generated_parity(repo_root, catalog)
    return issues


def _require_vendored_files(repo_root: Path, ver: str, ext_id: str) -> list[Issue]:
    d = pm.vendored_dir(repo_root, ver)
    required = [f"pkimm-model-{ver}.yaml", "pkimm-references.yaml"]
    return [Issue("error", f"{ext_id}: compatibility '{ver}' missing vendored file pkimm-model/{ver}/{name}")
            for name in required if not (d / name).exists()]


def _check_relevance(ext_id, ext, idx, ref_ids) -> list[Issue]:
    out: list[Issue] = []
    for module in ext.get("relevance", {}).get("modules", []):
        mid = module.get("id")
        for cat in module.get("categories", []):
            cid = cat.get("id")
            if not idx.category_in_module(mid, cid):
                out.append(Issue("error", f"{ext_id}: relevance category '{cid}' is not in module '{mid}'"))
            for rid in cat.get("references", []) or []:
                if rid not in ref_ids:
                    out.append(Issue("error", f"{ext_id}: relevance category '{cid}' cites unknown reference '{rid}'"))
    return out


def _check_overlays(ext_id, ext, idx) -> list[Issue]:
    out: list[Issue] = []
    for module in ext.get("overlays", {}).get("modules", []):
        mid = module.get("id")
        for cat in module.get("categories", []):
            cid = cat.get("id")
            if not idx.category_in_module(mid, cid):
                out.append(Issue("error", f"{ext_id}: overlay category '{cid}' is not in module '{mid}'"))
                continue
            for req in cat.get("requirements", []) or []:
                if not idx.requirement_in_category(cid, req.get("id")):
                    out.append(Issue("error", f"{ext_id}: overlay requirement '{req.get('id')}' is not in category '{cid}'"))
    return out


def _check_vendored_integrity(repo_root: Path) -> list[Issue]:
    out: list[Issue] = []
    base = repo_root / "pkimm-model"
    if not base.exists():
        return [Issue("error", "pkimm-model/ vendored dir missing")]
    for ver_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        ver = ver_dir.name
        model_yaml = ver_dir / f"pkimm-model-{ver}.yaml"
        if model_yaml.exists():
            actual = (yaml.safe_load(model_yaml.read_text()) or {}).get("version")
            if str(actual) != ver:
                out.append(Issue("error", f"pkimm-model/{ver}/ contains model version '{actual}' (expected '{ver}')"))
    return out


def _check_generated_parity(repo_root: Path, catalog: dict) -> list[Issue]:
    out: list[Issue] = []
    root_index = repo_root / "_index.md"
    expected = gen.render_catalog_table(catalog, gen._existing_date(root_index))
    if not root_index.exists() or root_index.read_text() != expected:
        out.append(Issue("error", "_index.md is stale — re-run generate_catalog_docs"))
    for entry in catalog.get("extensions", []):
        def_path = repo_root / entry.get("definition", "")
        if not def_path.exists():
            continue
        ext = yaml.safe_load(def_path.read_text())
        idx_by_version = {v: pm.ModelIndex(pm.load_model(repo_root, v))
                          for v in ext["extension"]["compatibility"]
                          if (pm.vendored_dir(repo_root, v) / f"pkimm-model-{v}.yaml").exists()}
        if not idx_by_version:
            continue
        out_path = def_path.parent / "definition" / "_index.md"
        expected_def = gen.render_definition(ext, idx_by_version, gen._existing_date(out_path))
        if not out_path.exists() or out_path.read_text() != expected_def:
            out.append(Issue("error", f"{entry['id']}: definition/_index.md is stale — re-run generate_catalog_docs"))
    return out


def _main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".")
    issues = check_all(Path(p.parse_args().repo_root).resolve())
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    for i in issues:
        print(("ERROR  " if i.severity == "error" else "WARN   ") + i.message)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(_main())
