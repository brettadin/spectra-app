from types import SimpleNamespace

import pytest

from app.ui import main


@pytest.fixture(autouse=True)
def reset_session_state(monkeypatch):
    state = {"overlay_traces": [], "display_full_resolution": False}
    monkeypatch.setattr(main, "st", SimpleNamespace(session_state=state))
    yield state


def test_add_overlay_payload_rejects_time_series(reset_session_state):
    payload = {
        "label": "TESS Light Curve",
        "wavelength_nm": [0.0, 0.5, 1.0],
        "flux": [1200.0, 1195.0, 1187.0],
        "axis_kind": "time",
        "metadata": {"axis_kind": "time", "time_unit": "day"},
    }

    added, message = main._add_overlay_payload(payload)

    assert added is False
    assert "Time-series overlays are not supported" in message
    assert main._get_overlays() == []


def test_grouping_and_rendering_ignore_time_traces(reset_session_state):
    spectral_trace = main.OverlayTrace(
        trace_id="spec",
        label="Spectral",
        wavelength_nm=(500.0, 505.0, 510.0),
        flux=(1.0, 0.9, 1.1),
        axis_kind="wavelength",
    )
    time_trace = main.OverlayTrace(
        trace_id="time",
        label="Time",
        wavelength_nm=(0.0, 1.0, 2.0),
        flux=(1200.0, 1180.0, 1170.0),
        axis_kind="time",
    )

    groups = main._group_overlays_by_axis_kind([spectral_trace, time_trace])
    assert "time" not in groups
    assert groups["wavelength"] == [spectral_trace]

    viewport = {"wavelength": (None, None)}
    fig, axis_title = main._build_overlay_figure(
        [spectral_trace, time_trace],
        "nm",
        "Flux (raw)",
        "unit",
        viewport,
        reference=spectral_trace,
        differential_mode="Off",
        version_tag="vtest",
    )

    assert len(fig.data) == 1
    assert fig.data[0].name == "Spectral"
    assert axis_title.startswith("Wavelength")
