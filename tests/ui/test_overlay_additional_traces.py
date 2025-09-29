import io
from textwrap import dedent
from types import SimpleNamespace


import numpy as np
import pandas as pd

import pytest

from app.server.ingest_ascii import parse_ascii
from app.ui import main
from app.utils.downsample import build_downsample_tiers



@pytest.fixture(autouse=True)
def reset_session_state(monkeypatch):
    dummy_state = {}
    monkeypatch.setattr(main, "st", SimpleNamespace(session_state=dummy_state))
    yield dummy_state


def test_add_overlay_payload_handles_additional_traces(reset_session_state):
    content = dedent(
        """
        Wavelength (nm),Flux (arb),Continuum Flux (arb),Sun,Temperature (K),Quality Flag,Velocity (km/s)
        400,0.10,0.05,1.0,5000,0,30
        405,0.12,0.06,1.0,5050,1,32
        410,0.08,0.07,1.0,5075,0,31
        415,0.09,0.08,1.0,5100,0,29
        """
    ).strip()

    dataframe = pd.read_csv(io.StringIO(content))
    parsed = parse_ascii(
        dataframe,
        content_bytes=content.encode("utf-8"),
        column_labels=list(dataframe.columns),
        filename="series.csv",
    )

    payload = {
        "label": "Series",
        "wavelength_nm": parsed["wavelength_nm"],
        "flux": parsed["flux"],
        "flux_unit": parsed["flux_unit"],
        "flux_kind": parsed["flux_kind"],
        "kind": parsed["kind"],
        "axis": parsed["axis"],
        "provider": "LOCAL",
        "summary": f"{len(parsed['wavelength_nm'])} samples",
        "additional_traces": parsed.get("additional_traces", []),
    }

    assert payload["additional_traces"]
    labels = {entry["label"] for entry in payload["additional_traces"]}
    assert labels == {"Continuum Flux (arb)"}
    assert "Sun" not in labels
    assert "Temperature (K)" not in labels

    added, message = main._add_overlay_payload(payload)

    assert added is True
    assert "added 1 additional series" in message

    overlays = main._get_overlays()
    assert len(overlays) == 2
    labels = {trace.label for trace in overlays}
    assert labels == {"Series", "Continuum Flux (arb)"}



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

