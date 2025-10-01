# Axis-aware viewport handling — 2025-10-08
- Maintain a `viewport_axes` session map keyed by axis kind so wavelength and time traces stop overwriting each other's zoom state.
- Mixed-axis overlays reuse per-kind ranges during sampling/export while the chart surfaces a "Mixed axes" title and warning instead of forcing a shared x-range.
- Export payloads now include `axis_kind` + unit metadata, keeping time-series rows intact when spectral viewports tighten.
