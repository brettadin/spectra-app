# Brains — v1.2.0h

## Release focus
- **REF 1.2.0h-A01**: Surface the curated example quick-add tools directly in the sidebar controls so loading spectra no longer requires switching tabs.

## Implementation notes
- Insert the examples quick-add button, favourites, recents, and reference trace tools beneath the display controls in `_render_settings_group`, collapsing optional lists into expanders for breathing room.
- Replace the Library tab's embedded examples panel with sidebar-focused guidance so users learn where the controls moved.
- Update the UI contract JSON to include the new "Examples library" sidebar section and bump the contract version tag.
- Add Streamlit AppTest coverage for the sidebar panel plus a regression that the Library tab copy points to the sidebar.

## Testing
- `pytest tests/ui/test_sidebar_examples.py`
- `pytest tests/ui/test_sidebar_line_catalog.py`

## Outstanding work
- Extend the example browser sheet with richer previews once the sidebar layout stabilises.
- Consider a compact mode toggle for the sidebar when multiple expanders are open simultaneously.

## Continuity updates
- Version bumped to v1.2.0h with refreshed patch notes (md/txt), patch log, UI contract, and AI activity log entries.
