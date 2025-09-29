from types import SimpleNamespace


import numpy as np

import pytest

from app.ui import main
from app.utils.downsample import build_downsample_tiers

import pytest

from app.ui import main



@pytest.fixture(autouse=True)
def reset_session_state(monkeypatch):
    dummy_state = {}
    monkeypatch.setattr(main, "st", SimpleNamespace(session_state=dummy_state))
    yield dummy_state


def test_add_overlay_payload_handles_additional_traces(reset_session_state):
    payload = {
        "label": "Series",
        "wavelength_nm": [400.0, 405.0, 410.0, 415.0],
        "flux": [0.10, 0.12, 0.08, 0.09],
        "flux_unit": "arb",
        "flux_kind": "relative",
        "kind": "spectrum",
        "provider": "LOCAL",
        "summary": "4 samples",
        "additional_traces": [
            {
                "label": "Balmer",
                "wavelength_nm": [400.0, 405.0, 410.0, 415.0],
                "flux": [0.05, 0.06, 0.07, 0.08],
                "flux_unit": "arb",
                "flux_kind": "relative",
                "axis": "emission",
            },
            {
                "label": "Sum",
                "wavelength_nm": [400.0, 405.0, 410.0, 415.0],
                "flux": [0.15, 0.18, 0.15, 0.17],
                "flux_unit": "arb",
                "flux_kind": "relative",
                "axis": "emission",
            },
        ],
    }

    added, message = main._add_overlay_payload(payload)

    assert added is True
    assert "added 2 additional series" in message

    overlays = main._get_overlays()
    assert len(overlays) == 3
    labels = {trace.label for trace in overlays}
    assert labels == {"Series", "Balmer", "Sum"}



def test_overlay_sampling_respects_viewport_density(reset_session_state):
    wavelengths = np.linspace(300.0, 900.0, 5000, dtype=float)
    flux = np.exp(-0.5 * ((wavelengths - 600.0) / 20.0) ** 2)

    tiers = build_downsample_tiers(wavelengths, flux, strategy="lttb")
    downsample_map = {
        tier: (tuple(result.wavelength_nm), tuple(result.flux))
        for tier, result in tiers.items()
    }

    trace = main.OverlayTrace(
        trace_id="test",
        label="Test",
        wavelength_nm=tuple(float(value) for value in wavelengths.tolist()),
        flux=tuple(float(value) for value in flux.tolist()),
        downsample=downsample_map,
    )

    viewport = (550.0, 650.0)
    sampled_w, sampled_f, hover, dense = trace.sample(viewport, max_points=256)

    assert dense is False
    assert hover is None
    assert len(sampled_w) == 256
    assert sampled_w[0] >= viewport[0] - 1e-6
    assert sampled_w[-1] <= viewport[1] + 1e-6
    assert sampled_f.size == sampled_w.size

