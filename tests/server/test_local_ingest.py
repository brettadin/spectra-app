import gzip
import io
from textwrap import dedent

import numpy as np
import pytest
from astropy.io import fits

from app.utils.local_ingest import ingest_local_file


def test_ingest_local_ascii_populates_metadata():
    content = dedent(
        """
        # Instrument: ExampleSpec
        # Telescope: ExampleScope
        # Date-Obs: 2023-08-01T12:34:56Z
        # Target: Vega
        # Flux Units: 10^-16 erg/s/cm^2/Å
        Wavelength (Angstrom),Flux (10^-16 erg/s/cm^2/Å)
        5000,1.2
        5005,1.5
        """
    ).encode("utf-8")

    payload = ingest_local_file("example.csv", content)

    assert payload["label"] == "Vega"
    assert payload["provider"] == "LOCAL"
    assert payload["flux_unit"] == "10^-16 erg/s/cm^2/Å"
    assert payload["flux_kind"] == "absolute"
    assert payload["wavelength_nm"] == [500.0, 500.5]
    assert payload["flux"] == [1.2, 1.5]

    metadata = payload["metadata"]
    assert metadata["instrument"] == "ExampleSpec"
    assert metadata["telescope"] == "ExampleScope"
    assert metadata["observation_date"] == "2023-08-01T12:34:56Z"
    assert metadata["target"] == "Vega"
    assert metadata["wavelength_range_nm"] == [500.0, 500.5]
    assert metadata["filename"] == "example.csv"

    provenance = payload["provenance"]
    assert provenance["format"] == "ascii"
    assert provenance["filename"] == "example.csv"
    assert provenance["orientation"] == "row"
    assert provenance["ingest"]["method"] == "local_upload"

    summary = payload["summary"]
    assert "2 samples" in summary
    assert "500.00–500.50 nm" in summary
    assert "Flux: 10^-16 erg/s/cm^2/Å" in summary


def test_ingest_local_ascii_vertical_layout():
    content = dedent(
        """
        # Instrument: ColumnScope
        Wavelength (nm):
        500
        505
        510

        Flux (counts)
        10
        20
        30
        """
    ).encode("utf-8")

    payload = ingest_local_file("vertical.txt", content)

    assert payload["wavelength_nm"] == [500.0, 505.0, 510.0]
    assert payload["flux"] == [10.0, 20.0, 30.0]
    assert payload["flux_unit"] == "counts"
    assert payload["flux_kind"] == "relative"

    metadata = payload["metadata"]
    assert metadata["instrument"] == "ColumnScope"
    assert metadata["filename"] == "vertical.txt"

    provenance = payload["provenance"]
    assert provenance["orientation"] == "columnar"


def test_ingest_local_ascii_wavenumber_converts_to_nm():
    content = dedent(
        """
        # Target: SampleStar
        Wavenumber (cm^-1),Flux
        20000,1.0
        10000,0.5
        """
    ).encode("utf-8")

    payload = ingest_local_file("wavenumber.csv", content)

    assert payload["wavelength_nm"] == [500.0, 1000.0]
    metadata = payload["metadata"]
    assert metadata["original_wavelength_unit"] == "cm^-1"
    assert metadata["reported_wavelength_unit"] == "cm^-1"


def test_ingest_local_ascii_gzip_round_trip():
    content = gzip.compress(
        dedent(
            """
            Wavelength (nm),Flux
            400,1.0
            405,0.5
            """
        ).encode("utf-8")
    )

    payload = ingest_local_file("compressed.csv.gz", content)

    metadata = payload["metadata"]
    provenance = payload["provenance"]

    assert metadata["filename"] == "compressed.csv.gz"
    assert provenance["filename"] == "compressed.csv"
    assert provenance["source_filename"] == "compressed.csv.gz"
    assert provenance["ingest"]["compression"]["algorithm"] == "gzip"
    assert metadata["compression"]["algorithm"] == "gzip"


def test_ingest_local_fits_enriches_metadata():
    flux_values = np.array([1.0, 2.0, 3.0], dtype=float)

    sci_header = fits.Header()
    sci_header["CRVAL1"] = 4000.0
    sci_header["CDELT1"] = 2.0
    sci_header["CRPIX1"] = 1.0
    sci_header["CUNIT1"] = "Angstrom"
    sci_header["BUNIT"] = "Jy"
    sci_header["OBJECT"] = "TestObj"
    sci_header["INSTRUME"] = "SpecX"
    sci_header["TELESCOP"] = "ScopeY"
    sci_header["DATE-OBS"] = "2023-03-01T00:00:00"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), sci_hdu])
    bio = io.BytesIO()
    hdul.writeto(bio)
    hdul.close()

    payload = ingest_local_file("spectrum.fits", bio.getvalue())

    assert payload["label"] == "TestObj"
    assert payload["flux"] == flux_values.tolist()
    assert payload["wavelength_nm"] == pytest.approx([400.0, 400.2, 400.4])
    assert payload["flux_unit"] == "Jy"
    assert payload["flux_kind"] == "absolute"

    metadata = payload["metadata"]
    assert metadata["instrument"] == "SpecX"
    assert metadata["telescope"] == "ScopeY"
    assert metadata["observation_date"] == "2023-03-01T00:00:00"
    assert metadata["target"] == "TestObj"
    assert metadata["wavelength_range_nm"] == pytest.approx([400.0, 400.4])
    assert metadata["wavelength_step_nm"] == pytest.approx(0.2)
    assert metadata["reported_flux_unit"] == "Jy"
    assert metadata["reported_wavelength_unit"] == "Angstrom"
    assert metadata["original_wavelength_unit"] == "Å"

    provenance = payload["provenance"]
    assert provenance["format"] == "fits"
    assert provenance["filename"] == "spectrum.fits"
    assert provenance["hdu_name"] == "SCI"
    assert provenance["data_mode"] == "image"


def test_ingest_local_fits_table_handles_columns():
    wave = np.array([5000.0, 5005.0, 5010.0], dtype=float)
    flux = np.array([1.0, 1.1, 1.2], dtype=float)

    col_wave = fits.Column(name="WAVELENGTH", array=wave, format="D", unit="Angstrom")
    col_flux = fits.Column(name="FLUX", array=flux, format="D", unit="Jy")
    table_hdu = fits.BinTableHDU.from_columns([col_wave, col_flux], name="SPECTRUM")
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    bio = io.BytesIO()
    hdul.writeto(bio)
    hdul.close()

    payload = ingest_local_file("table_spectrum.fits", bio.getvalue())

    assert payload["wavelength_nm"] == pytest.approx([500.0, 500.5, 501.0])
    assert payload["flux"] == flux.tolist()
    assert payload["flux_unit"] == "Jy"

    metadata = payload["metadata"]
    assert metadata["original_wavelength_unit"] == "Å"
    assert metadata["reported_wavelength_unit"] == "Angstrom"
    assert metadata["points"] == 3

    provenance = payload["provenance"]
    assert provenance["data_mode"] == "table"
    assert provenance["column_mapping"]["wavelength"] == "WAVELENGTH"
    assert provenance["column_mapping"]["flux"] == "FLUX"
