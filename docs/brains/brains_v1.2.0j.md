# Brains — v1.2.0j

## Release focus
- **REF 1.2.0j-A01**: Consolidate similarity analysis with differential tooling so users compare spectra from a single workspace.

## Implementation notes
- Lift the similarity vector prep and `render_similarity_panel` call from `_render_overlay_tab` into `_render_differential_tab`, gating the panel on having at least two spectral overlays.
- Share the viewport defaults from overlay state so similarity metrics continue to respect the active zoom window.
- Preserve overlay metadata and line tables by leaving their renderers untouched and adding coverage to detect accidental removal.

## Testing
- `pytest tests/ui/test_differential_form.py`
- `pytest tests/ui/test_metadata_summary.py`

## Outstanding work
- Explore inline guidance in the differential tab to explain how similarity metrics complement the computed differential curve.
- Continue monitoring doc search service availability noted in earlier logs.

## Continuity updates
- Version bumped to v1.2.0j with refreshed patch notes, patch log entry, brains index update, and AI activity log section.
