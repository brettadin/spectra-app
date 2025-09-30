from types import SimpleNamespace


import numpy as np

import pytest

from app.ui import main


@pytest.fixture(autouse=True)
def session_state(monkeypatch):
    state = {"display_full_resolution": True}
    monkeypatch.setattr(main, "st", SimpleNamespace(session_state=state))
    yield state


def test_full_resolution_preference_returns_all_points(session_state):
    wavelengths = np.linspace(400.0, 800.0, 15000)
    flux = np.sin(wavelengths / 20.0)

    trace = main.OverlayTrace(
        trace_id="full-res",
        label="High density",
        wavelength_nm=tuple(float(value) for value in wavelengths.tolist()),
        flux=tuple(float(value) for value in flux.tolist()),
    )

    sampled_w, sampled_f, hover, dense = trace.sample(
        (None, None), max_points=None, include_hover=True
    )

    assert dense is True
    assert hover is None
    assert sampled_f.size == wavelengths.size
    assert sampled_w.size == wavelengths.size

    fig, _ = main._build_overlay_figure(
        overlays=[trace],
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="none",
        viewport=(None, None),
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
    )

    plotted_trace = fig.data[0]
    assert len(plotted_trace.x) == wavelengths.size
    assert len(plotted_trace.y) == wavelengths.size
