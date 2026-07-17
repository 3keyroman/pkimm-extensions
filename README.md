# PKI MM Extensions

Official catalog of extensions to the [PKI Maturity Model](https://pkic.org/wg/pkimm/model/).
Extensions add optional, pluggable criteria and weight overlays to the model without
changing it. Rendered at https://pkic.org/wg/pkimm/extensions/.

- `catalog.yaml` — machine-readable manifest of catalog extensions.
- `<id>/<id>-extension.yaml` — the definition of each extension (source of truth).
- `<id>/_index.md` — hand-authored overview; `<id>/definition/_index.md` — generated.
- `pkimm-model/` — vendored, pinned copies of the pkimm model data used for validation.

## Developing

    pip install -r scripts/requirements-dev.txt
    python -m scripts.generate_catalog_docs     # regenerate table + definition pages
    pytest scripts/ -q                          # unit tests
    python -m scripts.check_extensions          # full validation (CI gate)

The extension framework/schema is defined in the pkimm repository; this repo vendors the
schema and model data it validates against under `pkimm-model/`.
