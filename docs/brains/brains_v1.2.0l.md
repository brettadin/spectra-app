# Brains — v1.2.0l

## Release focus
- **REF 1.2.0l-A01**: Decouple overlay viewport state by axis kind so spectral zooming stops clamping time-series plots and mixed overlays declare their axis context.

## Implementation notes
- Added per-axis viewport helpers that normalize stored tuples, migrate the legacy `viewport_nm` state, and expose axis-aware getters/setters used by the sidebar, overlay tab, exports, and differential panel.
- Taught `_build_overlay_figure` to select axis-specific viewports, capture axis titles per kind, and emit a "Mixed axes" title without forcing a shared x-range when time and wavelength traces render together.
- Updated the overlay exporter to include axis kind/unit metadata and refreshed UI tests to cover time-series auto-ranging plus a mixed-axis rendering scenario.

## Testing
- `pytest tests/ui/test_auto_viewport.py tests/ui/test_overlay_full_resolution.py tests/ui/test_overlay_hover.py tests/ui/test_overlay_mixed_axes.py`

## Outstanding work
- Evaluate whether we should surface a user-selectable axis toggle for slider control when more than two axis kinds appear in future data releases.
- Monitor export consumers for compatibility with the new axis metadata payloads.

## Continuity updates
- Version bumped to v1.2.0l with refreshed patch notes, brains index entry, AI log, and handoff record.
