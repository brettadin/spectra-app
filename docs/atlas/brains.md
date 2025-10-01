# Axis-aware viewport handling — 2025-10-08
- Maintain a `viewport_axes` session map keyed by axis kind so wavelength and time traces stop overwriting each other's zoom state.
- Mixed-axis overlays reuse per-kind ranges during sampling/export while the chart surfaces a "Mixed axes" title and warning instead of forcing a shared x-range.
- Export payloads now include `axis_kind` + unit metadata, keeping time-series rows intact when spectral viewports tighten.

## Overlay clear control relocation — 2025-10-08
- Move the destructive "Clear overlays" action into the Display & viewport cluster so overlay management lives beside viewport tools.
- Raise a transient warning banner within the overlay tab after clearing so users receive immediate confirmation in the workspace context.
- Differential tab keeps its reference selector without destructive controls, reducing the risk of accidental overlay loss while preparing comparisons.
