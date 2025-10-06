from __future__ import annotations

from typing import Dict

import numpy as np

from app.ui.controller import (
    WorkspaceController,
    build_overlay_figure,
    prepare_similarity_inputs,
)


VIEWPORT_KEY = "viewport_axes"


def _make_controller() -> WorkspaceController:
    state: Dict[str, object] = {}
    controller = WorkspaceController(state, VIEWPORT_KEY)
    controller.ensure_defaults()
    return controller


def test_controller_can_add_overlay_and_build_figure() -> None:
    controller = _make_controller()
    wavelengths = np.linspace(400.0, 600.0, 16)
    flux = np.linspace(0.5, 1.5, 16)
    success, message = controller.add_overlay("Synthetic", wavelengths, flux)
    assert success, message

    overlays = controller.get_overlays()
    fig, axis = build_overlay_figure(
        overlays,
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="unit",
        viewport_by_kind=controller.get_viewport_store(),
        reference=overlays[0],
        differential_mode="Off",
        version_tag="test",
    )
    assert axis.startswith("Wavelength"), axis
    assert len(fig.data) == 1


def test_prepare_similarity_inputs_uses_state_cache() -> None:
    controller = _make_controller()
    wavelengths = np.linspace(400.0, 600.0, 32)
    flux_a = np.sin(wavelengths / 40.0)
    flux_b = np.cos(wavelengths / 35.0)
    controller.add_overlay("Trace A", wavelengths, flux_a)
    controller.add_overlay("Trace B", wavelengths, flux_b)

    overlays = controller.get_overlays()
    vectors, viewport, options, cache = prepare_similarity_inputs(
        controller.state, overlays, controller.get_viewport_store()
    )

    assert len(vectors) == 2
    assert options.primary_metric in options.metrics
    assert all(isinstance(value, float) for value in viewport)
    assert hasattr(cache, "reset")
    cache.compute(vectors[0], vectors[1], viewport, options)
    assert getattr(cache, "_store", {})
    cache.reset()
    assert not getattr(cache, "_store", {})
