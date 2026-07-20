#!/usr/bin/env python3
"""Generate the catalog table (root _index.md) from catalog.yaml and each
<id>/definition/_index.md from its <id>-extension.yaml. Idempotent; preserves
existing front-matter `date`."""
from __future__ import annotations
import argparse
import datetime as dt
import re
from pathlib import Path
from typing import Any

import yaml

from scripts import pkimm_model as pm

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DATE_LINE_RE = re.compile(r"^date:\s*(.+)$", re.MULTILINE)
STATUS_BADGE = {
    "under-development": "Under development",
    "release-candidate": "Release candidate",
    "stable": "Stable",
    "deprecated": "Deprecated",
}


def _existing_date(path: Path) -> str | None:
    if not path.exists():
        return None
    m = FRONT_MATTER_RE.match(path.read_text())
    if not m:
        return None
    d = DATE_LINE_RE.search(m.group(1))
    return d.group(1).strip() if d else None


def _flatten(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def render_catalog_table(catalog: dict[str, Any], existing_date: str | None = None) -> str:
    date_val = existing_date or dt.date.today().isoformat() + "T00:00:00Z"
    lines = [
        "---", f"date: {date_val}", "title: Extensions", "weight: 1", "sideMenu: true", "---",
        "", "# Extensions", "",
        "Official catalog of extensions to the PKI Maturity Model. Extensions add optional, "
        "pluggable criteria and weight overlays without changing the core model.",
        "", "| Extension | Version | Status | Compatibility | Definition | Summary |",
        "|---|---|---|---|---|---|",
    ]
    for e in catalog.get("extensions", []):
        badge = STATUS_BADGE.get(e["status"], e["status"])
        compat = ", ".join(e.get("compatibility", []))
        lines.append(f"| [{_flatten(e['name'])}](./{e['id']}/) | {e['version']} | {badge} | {compat} | [YAML](./{e['definition']}) | {_flatten(e['summary'])} |")
    lines.append("")
    return "\n".join(lines)


def _overlay_value(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "multiplier":
        return f"×{node.get('multiplier')}"
    if t == "addition":
        return f"+{node.get('addition')}"
    if t == "override":
        return f"={node.get('override')}"
    return "—"


def render_definition(ext: dict[str, Any], idx_by_version: dict[str, "pm.ModelIndex"], existing_date: str | None = None) -> str:
    date_val = existing_date or dt.date.today().isoformat() + "T00:00:00Z"
    meta = ext["extension"]
    idx = idx_by_version[meta["compatibility"][0]]
    lines = [
        "---", f"date: {date_val}", "title: Definition", "weight: 2", "---",
        "", f"# {meta['name']} — definition", "",
        "> This page is generated from the extension YAML. Do not edit by hand.", "",
        f"- **Extension id:** `{meta['id']}`",
        f"- **Version:** {meta['version']}",
        f"- **Compatibility:** {', '.join(meta['compatibility'])}",
        "", "## Relevance", "",
        "Extension-specific maturity criteria attached to model categories.", "",
    ]
    for module in ext.get("relevance", {}).get("modules", []):
        for cat in module.get("categories", []):
            title = idx.category_title(cat["id"]) or cat["id"]
            lines += [f"### {title} (`{cat['id']}`) — weight {cat['weight']}", "",
                      "| Level | Name | Description |", "|---|---|---|"]
            for lvl in cat.get("levels", []):
                lines.append(f"| {lvl['number']} | {_flatten(lvl['name'])} | {_flatten(lvl['description'])} |")
            lines.append("")
            if cat.get("guidance"):
                lines += ["**Guidance** — " + _flatten(cat["guidance"]), ""]
            if cat.get("assessment"):
                lines += ["**Assessment** — " + _flatten(cat["assessment"]), ""]
    lines += ["## Overlays", "",
              "Weight adjustments applied to model categories/requirements.", "",
              "| Target | Type | Value | Rationale |", "|---|---|---|---|"]
    for module in ext.get("overlays", {}).get("modules", []):
        for cat in module.get("categories", []):
            title = idx.category_title(cat["id"]) or cat["id"]
            if cat.get("type"):
                lines.append(f"| category `{cat['id']}` ({title}) | {cat['type']} | {_overlay_value(cat)} | {_flatten(cat.get('rationale',''))} |")
            for req in cat.get("requirements", []) or []:
                desc = idx.requirement_description(cat["id"], req["id"]) or ""
                target = f"requirement `{req['id']}`" + (f" ({_flatten(desc)})" if desc else "")
                lines.append(f"| {target} | {req['type']} | {_overlay_value(req)} | {_flatten(req.get('rationale',''))} |")
    lines.append("")
    return "\n".join(lines)


def generate(repo_root: Path) -> None:
    catalog = yaml.safe_load((repo_root / "catalog.yaml").read_text())
    root_index = repo_root / "_index.md"
    root_index.write_text(render_catalog_table(catalog, _existing_date(root_index)))
    for entry in catalog.get("extensions", []):
        def_path = repo_root / entry["definition"]
        if not def_path.exists():
            continue
        ext = yaml.safe_load(def_path.read_text())
        idx_by_version = {v: pm.ModelIndex(pm.load_model(repo_root, v)) for v in ext["extension"]["compatibility"]}
        out = def_path.parent / "definition" / "_index.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_definition(ext, idx_by_version, _existing_date(out)))


def _main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".")
    generate(Path(p.parse_args().repo_root).resolve())


if __name__ == "__main__":
    _main()
