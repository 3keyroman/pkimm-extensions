# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The **official catalog of extensions to the PKI Maturity Model (PKIMM)**, maintained by the PKI Consortium PKIMM working group. Extensions are optional, pluggable additions that augment the model — extra maturity criteria (**relevance**) and weight adjustments (**overlays**) — without changing the core model. This repo holds the extension definitions and their documentation; it is rendered at https://pkic.org/wg/pkimm/extensions/ as a submodule of the pkic.org site.

The extension **framework** (the concept, the scoring model, and the JSON Schema `extension.schema-1.0.0.json`) is defined and versioned in the separate **`pkimm`** repository, under the stable model. This catalog repo only holds *implementations* and vendors the framework schema + model data it validates against. This separation lets extensions evolve on their own cadence without forcing a `pkimm` model release.

There is no application code here — only YAML definitions, generated markdown, JSON Schema, and Python authoring/validation scripts. Treat changes as content/data edits.

## Repository layout

- `_index.md` — **generated** catalog landing page (the table of extensions). Do not edit by hand.
- `catalog.yaml` — machine-readable manifest of catalog extensions (source of truth for the table). Consumed by downstream integrations (e.g. the self-assessment app) to discover approved extensions.
- `catalog.schema-1.0.0.json` — JSON Schema for `catalog.yaml`, independently versioned.
- `<id>/` — one folder per extension (folder name = extension `id`, kebab-case):
  - `<id>/<id>-extension.yaml` — the extension definition (source of truth), validated against the vendored `pkimm-model/extension.schema-1.0.0.json`.
  - `<id>/_index.md` — **hand-authored** editorial overview (framing, status, open questions, scope, attribution, references).
  - `<id>/definition/_index.md` — **generated** projection of the extension YAML (relevance criteria tables + overlays). Do not edit by hand.
- `templates/_index.md` — authoring template for a new extension's overview page (hidden from nav via `build: {render: never, list: never}`).
- `pkimm-model/` — vendored, pinned copies of the `pkimm` files this repo validates against:
  - `extension.schema-1.0.0.json` — the framework schema (byte copy of pkimm's; not modified here).
  - `<model-version>/` — per model version: `pkimm-model-<ver>.yaml` and `pkimm-references.yaml`. The directory name must equal the model YAML's own `version` field.
- `scripts/` — authoring + validation tooling (see below).
- `.github/workflows/check.yml` — CI: installs deps, runs `pytest`, runs the validator on every PR and push to `main`.

## Authoring workflow (YAML-first)

`catalog.yaml` and each `<id>/<id>-extension.yaml` are the source of truth; the markdown (`_index.md` table and each `<id>/definition/_index.md`) is generated from them. Never hand-edit generated files.

To add or change an extension:

1. **Edit YAML** — add/modify `<id>/<id>-extension.yaml` (validated against `pkimm-model/extension.schema-1.0.0.json`) and add/update its entry in `catalog.yaml`. Do **not** hand-edit the catalog table.
2. **Author the overview** — write/update `<id>/_index.md` (copy `templates/_index.md`). This is editorial and stays hand-authored.
3. **Regenerate** — `python -m scripts.generate_catalog_docs` rebuilds `_index.md` and every `<id>/definition/_index.md`.
4. **Validate** — `python -m scripts.check_extensions` must report `0 error(s), 0 warning(s)` before committing.

CI runs the validator on every PR/push; a stale generated file (source changed but docs not regenerated) fails the build. Run steps 3–4 locally before pushing.

**Key scripts (`scripts/`):**
- `pkimm_model.py` — loads the vendored model/references and answers parent-scoped id-resolution queries (which categories belong to which module, which requirements to which category).
- `generate_catalog_docs.py` — regenerates the catalog table and each extension's `definition/_index.md`.
- `check_extensions.py` — the CI gate. Validates: `catalog.yaml` and each extension YAML against their schemas; manifest ↔ content parity (id/version/compatibility match, definition file exists, unique ids); parent-scoped resolution of relevance/overlay category and requirement ids against the vendored model; reference resolution (inline block ∪ vendored references catalog); compatibility against the vendored model version; vendored-copy integrity (each `pkimm-model/<ver>/` folder holds model version `<ver>`); and generated-doc parity (regenerate-and-diff). Hermetic — reads only in-repo + vendored files, no network.

## Conventions

- All markdown uses Hugo-style YAML front matter (`date`, `title`, `weight`, `sideMenu`/`build` where relevant). Ordering is by `weight`.
- **Status vocabulary** (kebab-case in YAML; title-case badge on the site): `under-development`, `release-candidate`, `stable`, `deprecated`.
- Extension `id` and all referenced model category/requirement ids are stable kebab-case (`^[a-z][a-z0-9-]*$`). **Never rename an extension `id` once published** — downstream integrations and the app depend on it.
- Generated files are never hand-edited; the validator enforces this.

## Extension versioning

- **SemVer** on `extension.version`:
  - **patch** — editorial/guidance/wording fixes, no change to criteria or overlays;
  - **minor** — new, backward-compatible criteria or overlays;
  - **major** — breaking changes to relevance/overlay structure or to the meaning of scoring.
- **`status`** follows the lifecycle `under-development` → `release-candidate` → `stable` → `deprecated`.
- **`compatibility`** lists the PKIMM model version(s) an extension targets. Supporting a new model version is a deliberate change: re-vendor that model version under `pkimm-model/<ver>/` and add it to `compatibility`.
- **Governance:** an extension's owner proposes version and status changes; the PKIMM working group endorses them, the same way substantive model changes are working-group decisions. Editorial fixes are routine; structural/scoring changes are working-group decisions.

## Vendoring policy

- `pkimm-model/` holds pinned copies of the framework schema and, per model version, the model YAML + references catalog. CI never fetches these over the network.
- The vendored directory name (`2.0.0/`) must match the model YAML's own `version` field; the validator enforces this.
- Bumping to a new model version is a deliberate PR: add `pkimm-model/<new-ver>/` with that version's files and update the affected extensions' `compatibility`.

## Contribution constraints

Contributions are governed by the PKI Consortium IPR Agreement (https://pkic.org/ipr/) and the PKIMM working group charter (https://pkic.org/wg/pkimm/charter/). Substantive changes (new extensions, changes to scoring meaning, major version bumps) are working-group decisions; editorial fixes, typos, and clarifications are routine.

- **Commits & PRs:** use a single plain description of what changed — no AI/co-author attribution, no test counts, no plan/follow-up references.
- Do not commit local agent/planning scaffolding; keep it gitignored.
- Pin GitHub Actions by full commit SHA with a version comment (e.g. `actions/checkout@<sha> #v6.0.2`).
