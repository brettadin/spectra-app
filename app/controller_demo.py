from __future__ import annotations

import numpy as np

from .ui.controller import (
    DIFFERENTIAL_OPERATIONS,
    WorkspaceController,
    build_differential_summary,
    build_overlay_figure,
    compute_differential_result,
    prepare_similarity_inputs,
)

VIEWPORT_STATE_KEY = "viewport_axes"


def main() -> None:
    """Demonstrate using the UI controller without Streamlit widgets."""

    state: dict[str, object] = {}
    controller = WorkspaceController(state, VIEWPORT_STATE_KEY)
    controller.ensure_defaults()

    wavelengths = np.linspace(400.0, 700.0, 512)
    flux_a = np.sin(wavelengths / 45.0) + 1.2
    flux_b = np.cos(wavelengths / 55.0) + 1.1

    controller.add_overlay("Synthetic A", wavelengths, flux_a)
    controller.add_overlay("Synthetic B", wavelengths, flux_b)

    overlays = controller.get_overlays()
    viewport_store = controller.get_viewport_store()

    fig, axis_title = build_overlay_figure(
        overlays,
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="unit",
        viewport_by_kind=viewport_store,
        reference=overlays[0],
        differential_mode="Off",
        version_tag="demo",
        full_resolution=True,
    )
    print(f"Overlay figure traces: {len(fig.data)} • Axis: {axis_title}")

    operation_label = next(iter(DIFFERENTIAL_OPERATIONS))
    result = compute_differential_result(
        overlays[0],
        overlays[1],
        operation_label,
        sample_points=800,
        normalization="unit",
    )
    summary = build_differential_summary(result)
    print("Differential summary:")
    print(summary.to_string(index=False))

    vectors, viewport, options, cache = prepare_similarity_inputs(
        state, overlays, viewport_store
    )
    cache.reset()
    print(
        "Similarity prepared",
        len(vectors),
        "vectors • primary metric:",
        options.primary_metric,
        "• viewport:",
        viewport,
    )


if __name__ == "__main__":  # pragma: no cover - manual demonstration entrypoint
    main()
