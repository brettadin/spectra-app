# OVERLAY_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:59:33Z  
**Author:** v1.1.4

Uploaded or example spectra render as **independent overlays**.

## Rules
- Each overlay has its own label and color (assigned deterministically by index).
- Legend never shows empty labels; defaults to `'unlabeled-<n>'`.
- Toggle visibility per overlay; never destroys data.
- Elemental lamp lines are separate overlays per species (H, He, Ne, Hg, Xe, Sun...), not collapsed.

## Overlay manifest entry
```json
{
  "id": "overlay-3",
  "label": "IACOB O-star",
  "provenance_id": "trace_7",
  "color": "auto-3"
}
```
