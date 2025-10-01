import io
from textwrap import dedent

import numpy as np
import pytest
from astropy.io import fits
from streamlit.testing.v1 import AppTest

from app.ui.main import OverlayTrace, _build_metadata_summary_rows
from app.utils.local_ingest import ingest_local_file


def _overlay_from_payload(payload: dict) -> OverlayTrace:
    return OverlayTrace(
        trace_id="test",
        label=payload.get("label", "Spectrum"),
        wavelength_nm=tuple(payload.get("wavelength_nm") or ()),
        flux=tuple(payload.get("flux") or ()),
        kind=payload.get("kind", "spectrum"),
        provider=payload.get("provider"),
        summary=payload.get("summary"),
        metadata=dict(payload.get("metadata") or {}),
        provenance=dict(payload.get("provenance") or {}),
        hover=tuple(payload.get("hover") or ()) if payload.get("hover") else None,
        flux_unit=payload.get("flux_unit", "arb"),
        flux_kind=payload.get("flux_kind", "relative"),
        axis=payload.get("axis", "emission"),
        axis_kind=payload.get("axis_kind")
        or ((payload.get("metadata") or {}).get("axis_kind") if isinstance(payload.get("metadata"), dict) else "wavelength"),
    )


def _render_overlay_tab_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.main import _render_overlay_tab

    _render_overlay_tab({"version": "vtest"})


def test_metadata_summary_ascii_upload_header_units():
    content = dedent(
        """
        # Instrument: HeaderSpec
        # Telescope: HeaderScope
        # UTDATE=2023-07-01
        # Range: 350 - 800 nm
        # Flux Units: photons/s
        Wavelength (Angstrom),Flux
        5000,10
        6000,20
        7000,30
        """
    ).encode("utf-8")

    payload = ingest_local_file("header_example.csv", content)

    assert payload["wavelength_nm"] == pytest.approx([500.0, 600.0, 700.0])
    metadata = payload["metadata"]
    assert metadata["instrument"] == "HeaderSpec"
    assert metadata["telescope"] == "HeaderScope"
    assert metadata["observation_date"] == "2023-07-01"
    assert metadata["wavelength_effective_range_nm"] == [350.0, 800.0]
    assert metadata["wavelength_range_nm"] == [500.0, 700.0]
    assert metadata["data_wavelength_range_nm"] == [500.0, 700.0]
    assert payload["flux_unit"] == "photons/s"
    assert metadata["reported_flux_unit"] == "photons/s"

    overlay = _overlay_from_payload(payload)
    rows = _build_metadata_summary_rows([overlay])
    assert len(rows) == 1
    row = rows[0]
    assert row["Instrument"] == "HeaderSpec"
    assert row["Telescope"] == "HeaderScope"
    assert row["Observation"] == "2023-07-01"
    assert row["Flux unit"] == "photons/s"
    assert row["Axis range"] == "350.00 – 800.00 nm"

    provenance = payload["provenance"]
    assert provenance["units"]["wavelength_converted_to"] == "nm"
    assert provenance["units"]["flux_unit"] == "photons/s"
    assert "wavelength_unit" in provenance.get("conversions", {})


def test_metadata_summary_fits_upload_populates_rows():
    flux_values = np.array([1.0, 1.1, 1.2], dtype=float)

    sci_header = fits.Header()
    sci_header["CRVAL1"] = 4000.0
    sci_header["CDELT1"] = 1.0
    sci_header["CRPIX1"] = 1.0
    sci_header["CUNIT1"] = "Angstrom"
    sci_header["BUNIT"] = "erg/s/cm^2/Angstrom"
    sci_header["OBJECT"] = "Beta"
    sci_header["INSTRUME"] = "SpecFit"
    sci_header["TELESCOP"] = "ScopeFit"
    sci_header["DATE-OBS"] = "2023-02-03"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), sci_hdu])
    bio = io.BytesIO()
    hdul.writeto(bio)
    hdul.close()

    payload = ingest_local_file("beta.fits", bio.getvalue())

    assert payload["label"] == "Beta"
    assert payload["flux_unit"] == "erg/s/cm^2/Angstrom"
    assert payload["wavelength_nm"] == pytest.approx([400.0, 400.1, 400.2])
    metadata = payload["metadata"]
    assert metadata["instrument"] == "SpecFit"
    assert metadata["telescope"] == "ScopeFit"
    assert metadata["observation_date"] == "2023-02-03"
    assert metadata["data_wavelength_range_nm"] == pytest.approx([400.0, 400.2])

    overlay = _overlay_from_payload(payload)
    rows = _build_metadata_summary_rows([overlay])
    row = rows[0]
    assert row["Instrument"] == "SpecFit"
    assert row["Telescope"] == "ScopeFit"
    assert row["Observation"] == "2023-02-03"
    assert row["Flux unit"] == "erg/s/cm^2/Angstrom"
    assert row["Axis range"] == "400.00 – 400.20 nm"

    provenance = payload["provenance"]
    assert provenance["units"]["wavelength_input"] in {"Å", "Angstrom"}
    assert provenance["units"]["flux_unit"] == "erg/s/cm^2/Angstrom"
    assert provenance["hdu_name"] == "SCI"
    assert provenance["units"]["wavelength_converted_to"] == "nm"


def test_metadata_summary_time_series_axis():
    payload = {
        "label": "Light Curve",
        "wavelength_nm": [0.0, 1.0, 2.0],
        "flux": [5.0, 5.5, 5.2],
        "axis_kind": "time",
        "metadata": {
            "axis_kind": "time",
            "time_range": [0.0, 2.0],
            "time_unit": "day",
            "time_original_unit": "BJD - 2457000, days",
        },
        "provenance": {
            "units": {
                "time_converted_to": "day",
                "time_original_unit": "BJD - 2457000, days",
            }
        },
    }

    overlay = _overlay_from_payload(payload)
    rows = _build_metadata_summary_rows([overlay])
    assert rows[0]["Axis range"] == "0.0000 – 2.0000 BJD - 2457000, days"


def test_overlay_tab_retains_metadata_and_line_tables():
    app = AppTest.from_function(_render_overlay_tab_entrypoint)

    spectral_overlay = OverlayTrace(
        trace_id="spec-1",
        label="Spectrum",
        wavelength_nm=(500.0, 510.0, 520.0),
        flux=(1.0, 1.1, 0.9),
        metadata={
            "instrument": "SpecOne",
            "telescope": "ScopeOne",
            "observation_date": "2025-10-05",
        },
        provenance={"units": {"wavelength_converted_to": "nm"}},
    )
    line_overlay = OverlayTrace(
        trace_id="line-1",
        label="Lines",
        wavelength_nm=(500.1,),
        flux=(0.0,),
        kind="lines",
        metadata={
            "lines": [
                {
                    "wavelength_nm": 500.1,
                    "observed_wavelength_nm": 500.2,
                    "ritz_wavelength_nm": 500.15,
                    "relative_intensity": 0.8,
                    "relative_intensity_normalized": 0.9,
                    "lower_level": "a",
                    "upper_level": "b",
                    "transition_type": "E1",
                }
            ]
        },
    )

    app.session_state.overlay_traces = [spectral_overlay, line_overlay]
    app.session_state.viewport_nm = (None, None)
    app.session_state.auto_viewport = True
    app.session_state.display_units = "nm"
    app.session_state.display_mode = "Flux (raw)"
    app.session_state.normalization_mode = "unit"
    app.session_state.differential_mode = "Off"
    app.session_state.reference_trace_id = spectral_overlay.trace_id

    app.run()

    assert not app.exception

    headings = [block.body for block in app.markdown]
    assert "#### Metadata summary" in headings
    expander_labels = [exp.label for exp in app.expander]
    assert "Line metadata tables" in expander_labels
