# Brains — v1.2.0g

## Release focus
- **REF 1.2.0g-A01**: Keep the NIST line catalog workflow discoverable by relocating it into the sidebar controls and documenting the new placement.

## Implementation notes
- Moved `_render_line_catalog_group` into the `_render_settings_group` sidebar container so the NIST form sits with network toggles and other fetch-affecting controls.
- Trimmed the Library tab copy now that line catalogs are no longer rendered there to avoid misleading guidance.
- Added Streamlit `AppTest` coverage that asserts the sidebar renders the NIST form when online and replaces it with the offline notice once archive fetchers are disabled.
- Refreshed `docs/ui_contract.json` to enumerate the sidebar sections (including the new Line catalogs entry) and bumped all continuity artefacts for v1.2.0g.

## Testing
- `pytest tests/ui/test_sidebar_line_catalog.py`

## Outstanding work
- Extend the UI contract verifier script to parse the JSON artefact directly so docs and automation cannot diverge on required sections.
- Continue the SIMBAD resolver integration outlined in the v1.2 blueprint once sidebar controls settle.

## Continuity updates
- Version bumped to v1.2.0g with updates to patch notes (md/txt), patch log, AI log, and the brains index.
