from types import SimpleNamespace

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
