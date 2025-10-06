# Overlay workspace reference

The overlay tab is the heart of Spectra App. It renders every trace that is
currently loaded and keeps controls close to the chart so you can stay in the
analysis flow. Feature roadmaps that align with SpecViz are summarised in the
[Spectra ↔ SpecViz parity matrix](../research/specviz_improvement_backlog.md#spectra--specviz-parity-matrix).

> **Attribution.** Viewer comparisons draw on the SpecViz guides curated by the
> [jdaviz authors](https://github.com/spacetelescope/jdaviz).

## Plot controls

- **Legend toggle** – click a trace name in the legend to hide or restore it
  temporarily. The overlay visibility form beneath the chart offers a
  persistent toggle that syncs with the legend state.
- **Zoom and pan** – use the Plotly toolbar or mouse gestures to inspect a
  specific wavelength range. The sidebar viewport slider clamps what gets
  plotted without altering the underlying data.
- **Normalization** – choose between unit-vector, max scaling, z-score, or raw
  flux. The selection applies consistently across the overlay, similarity, and
  differential views.

## Managing overlays

The **Overlay visibility** form lists every loaded trace, including those
fetched from archives or generated in the differential tab. Select which traces
should remain visible and apply the change to update the chart in one go. The
summary table above the form records label, type, provenance source, and point
count for quick triage. Entries sourced from the target library only appear here
if they advertise a 1-D dataproduct (spectra, SEDs, or time-series); image/cube
rows stay in the library list with a disabled Overlay button so users know why
they cannot be enqueued.

Use **Remove overlays** to delete one or more traces when the workspace gets
crowded. Removing an overlay also clears any cached similarity scores that
referenced it.

## Exporting what you see

The **Export view** button produces three artifacts:

1. A CSV containing the currently visible traces cropped to the viewport and
   converted into the displayed wavelength units.
2. A PNG screenshot of the chart (requires Kaleido in the environment).
3. A JSON manifest that bundles provenance, export metadata, and normalization
   settings so the view can be reconstructed later.

Exports live in the `exports/` folder relative to the app, with timestamps to
keep runs separate.
