---
date: "2026-05-13T7:00:00Z"
title: Extension documentation template
build:
  render: never
  list: never
---

# Extension documentation template

Template for an extension's hand-authored overview page (`<id>/_index.md`).

## How to author a new extension

- Create a folder `<id>/` at the repo root and add `<id>/<id>-extension.yaml`
  (validated against `pkimm-model/extension.schema-1.0.0.json`).
- Add the hand-authored overview to `<id>/_index.md` following the structure below.
- Add a manifest entry to `catalog.yaml` — do **not** hand-edit the catalog table;
  it is generated. `status` is one of `under-development`, `release-candidate`,
  `stable`, `deprecated`.
- Run `python -m scripts.generate_catalog_docs` to (re)generate the catalog table and
  `<id>/definition/_index.md`.
- Run `python -m scripts.check_extensions` — it must report `0 error(s)`.

---

# *[Extension name]*

*[One-paragraph overview.]*

## Status
*[Use one of: `Under development`, `Release candidate`, `Stable`, `Deprecated`.]*

## Scope
*[Audiences and coverage.]*

## References
*[Key references.]*

## Attribution
*[Author/working-group attribution.]*
