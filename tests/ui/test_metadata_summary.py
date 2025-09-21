import io
from textwrap import dedent

import numpy as np
import pytest
from astropy.io import fits

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
    )


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
        """
    ).encode("utf-8")

    payload = ingest_local_file("header_example.csv", content)

    assert payload["wavelength_nm"] == pytest.approx([500.0, 600.0])
    metadata = payload["metadata"]
    assert metadata["instrument"] == "HeaderSpec"
    assert metadata["telescope"] == "HeaderScope"
    assert metadata["observation_date"] == "2023-07-01"
    assert metadata["wavelength_effective_range_nm"] == [350.0, 800.0]
    assert metadata["wavelength_range_nm"] == [500.0, 600.0]
    assert metadata["data_wavelength_range_nm"] == [500.0, 600.0]
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
    assert row["Range (nm)"] == "350.00 – 800.00"

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
    assert row["Range (nm)"] == "400.00 – 400.20"

    provenance = payload["provenance"]
    assert provenance["units"]["wavelength_input"] == "Å"
    assert provenance["units"]["flux_unit"] == "erg/s/cm^2/Angstrom"
    assert provenance["hdu_name"] == "SCI"
    assert provenance["units"]["wavelength_converted_to"] == "nm"
