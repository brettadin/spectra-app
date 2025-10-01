# Brains — v1.2.0k

## Release focus
- **REF 1.2.0k-A01**: Reshape the target catalog panel so discovery → summary → actions flows top-to-bottom with manifest metadata surfaced inline.

## Implementation notes
- Introduced a search box plus curated/planet toggles ahead of the catalog table so large registries remain navigable without scrolling past the table to select targets.
- Rendered manifest details in a dedicated container: canonical name, autop summary, metrics for curated counts / total MAST hits / planet tally, and archive availability with coordinates.
- Preserved truncated-result messaging by reusing the manifest's `mast_summary` data, now shown alongside the metrics instead of buried below the product list.
- Grouped curated MAST spectra by collection label (falling back to "Curated selection") with an optional selectbox filter; overlay actions still enqueue via the ingest queue and the unsupported tooltip text is unchanged.
- Limited per-run rendering to 200 products to keep Streamlit responsive while preserving the overall totals in captions.

## Testing
- `pytest tests/ui/test_targets_panel_layout.py`

## Outstanding work
- Continue monitoring whether MAST manifests provide richer collection metadata so the grouped labels can adopt instrument/program names automatically.
- Integrate SIMBAD-backed target search and resolver metadata once the ingestion backlog unblocks it, keeping the new layout stable.

## Continuity updates
- Version bumped to v1.2.0k with refreshed patch notes (md/txt), patch log entry, brains index row, AI handoff brief, and AI activity log section.
