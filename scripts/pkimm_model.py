#!/usr/bin/env python3
"""Load vendored pkimm model/references data and answer id-resolution queries.
Reads only from pkimm-model/<version>/ — no network, no pkimm repo."""
from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml


def vendored_dir(repo_root: Path, version: str) -> Path:
    return repo_root / "pkimm-model" / version


def load_model(repo_root: Path, version: str) -> dict[str, Any]:
    return yaml.safe_load((vendored_dir(repo_root, version) / f"pkimm-model-{version}.yaml").read_text())


def load_references(repo_root: Path, version: str) -> set[str]:
    path = vendored_dir(repo_root, version) / "pkimm-references.yaml"
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text()) or {}
    return {r["id"] for r in data.get("references", []) if isinstance(r, dict) and "id" in r}


class ModelIndex:
    def __init__(self, model: dict[str, Any]) -> None:
        self._cats_by_module: dict[str, set[str]] = {}
        self._reqs_by_cat: dict[str, set[str]] = {}
        self._cat_title: dict[str, str] = {}
        self._req_desc: dict[tuple[str, str], str] = {}
        for module in model.get("modules", []):
            mid = module.get("id")
            self._cats_by_module.setdefault(mid, set())
            for cat in module.get("categories", []):
                cid = cat["id"]
                self._cats_by_module[mid].add(cid)
                self._cat_title[cid] = cat.get("name", cid)
                self._reqs_by_cat.setdefault(cid, set())
                for req in cat.get("requirements", []):
                    self._reqs_by_cat[cid].add(req["id"])
                    self._req_desc[(cid, req["id"])] = req.get("description", "")

    def category_in_module(self, module_id: str, category_id: str) -> bool:
        return category_id in self._cats_by_module.get(module_id, set())

    def requirement_in_category(self, category_id: str, requirement_id: str) -> bool:
        return requirement_id in self._reqs_by_cat.get(category_id, set())

    def category_title(self, category_id: str) -> str | None:
        return self._cat_title.get(category_id)

    def requirement_description(self, category_id: str, requirement_id: str) -> str | None:
        return self._req_desc.get((category_id, requirement_id))
