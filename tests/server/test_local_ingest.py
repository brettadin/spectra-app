import gzip
import io
import zipfile
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
import pytest
from astropy import units as u
from astropy.io import fits

import app.utils.local_ingest as local_ingest
from app.server.ingest_ascii import parse_ascii, parse_ascii_segments
from app.utils.local_ingest import ingest_local_file


@pytest.fixture(autouse=True)
def temp_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "spectra_cache"
    cache_dir.mkdir()
    monkeypatch.setenv("SPECTRA_CACHE_DIR", str(cache_dir))
    yield cache_dir


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
        5010,1.7
        """
    ).encode("utf-8")

    payload = ingest_local_file("example.csv", content)

    assert payload["label"] == "Vega"
    assert payload["provider"] == "LOCAL"
    assert payload["flux_unit"] == "10^-16 erg/s/cm^2/Å"
    assert payload["flux_kind"] == "absolute"
    assert payload["wavelength_nm"] == [500.0, 500.5, 501.0]
    assert payload["wavelength"]["unit"] == "nm"
    assert payload["wavelength"]["values"] == [500.0, 500.5, 501.0]
    assert payload["wavelength_quantity"].unit.is_equivalent(u.nm)
    assert payload["wavelength_quantity"].to_value(u.nm) == pytest.approx(
        payload["wavelength_nm"]
    )
    assert payload["flux"] == [1.2, 1.5, 1.7]

    metadata = payload["metadata"]
    assert metadata["instrument"] == "ExampleSpec"
    assert metadata["telescope"] == "ExampleScope"
    assert metadata["observation_date"] == "2023-08-01T12:34:56Z"
    assert metadata["target"] == "Vega"
    assert metadata["wavelength_range_nm"] == [500.0, 501.0]
    assert metadata["filename"] == "example.csv"

    provenance = payload["provenance"]
    assert provenance["format"] == "ascii"
    assert provenance["filename"] == "example.csv"
    assert provenance["orientation"] == "row"
    assert provenance["ingest"]["method"] == "local_upload"

    summary = payload["summary"]
    assert "3 samples" in summary
    assert "500.00–501.00 nm" in summary
    assert "Flux: 10^-16 erg/s/cm^2/Å" in summary


def test_ingest_local_ascii_multiple_flux_columns():
    content = dedent(
        """
        Wavelength (nm),Paschen Flux (arb),Balmer Flux (arb),Sum Flux (arb),Velocity (km/s)
        400,0.10,0.05,0.15,30
        405,0.12,0.06,0.18,32
        410,0.08,0.07,0.15,31
        415,0.09,0.08,0.17,29
        """
    ).strip()

    dataframe = pd.read_csv(io.StringIO(content))
    parsed = parse_ascii(
        dataframe,
        content_bytes=content.encode("utf-8"),
        column_labels=list(dataframe.columns),
        filename="series.csv",
    )

    assert parsed["flux"] == [0.10, 0.12, 0.08, 0.09]

    extras = parsed.get("additional_traces")
    assert isinstance(extras, list)
    assert len(extras) == 2

    labels = {entry["label"] for entry in extras}
    assert labels == {"Balmer Flux (arb)", "Sum Flux (arb)"}

    for entry in extras:
        assert entry["wavelength_nm"] == [400.0, 405.0, 410.0, 415.0]
        assert entry["metadata"]["points"] == 4
        assert entry["downsample"]
        assert "4 samples" in entry["summary"]

    assert "Velocity (km/s)" not in labels


def test_ingest_local_ascii_filters_non_flux_numeric_columns():
    content = dedent(
        """
        Wavelength (nm),Flux (10^-16 erg/s/cm^2/Å),Continuum (10^-16 erg/s/cm^2/Å),Sun,Temperature (K),Quality Flag,Radial Velocity (km/s)
        400,0.10,0.12,1.0,5000,0,30
        405,0.12,0.11,1.0,5050,1,32
        410,0.08,0.09,1.0,5075,0,31
        415,0.09,0.10,1.0,5100,0,29
        """
    ).strip()

    dataframe = pd.read_csv(io.StringIO(content))
    parsed = parse_ascii(
        dataframe,
        content_bytes=content.encode("utf-8"),
        column_labels=list(dataframe.columns),
        filename="continuum.csv",
    )

    extras = parsed.get("additional_traces")
    assert isinstance(extras, list)
    assert len(extras) == 1

    labels = {entry["label"] for entry in extras}
    assert labels == {"Continuum (10^-16 erg/s/cm^2/Å)"}

    continuum_entry = extras[0]
    assert continuum_entry["flux"] == [0.12, 0.11, 0.09, 0.10]

    non_flux_headers = {
        "Temperature (K)",
        "Quality Flag",
        "Sun",
        "Radial Velocity (km/s)",
    }
    for header in non_flux_headers:
        assert header not in labels


def test_ingest_local_ascii_prefers_irradiance_column():
    content = dedent(
        """
        Wavelength (nm),Sun,Irradiance (W/m^2/nm)
        400,0.10,0.15
        405,0.12,0.18
        410,0.08,0.14
        """
    ).strip()

    dataframe = pd.read_csv(io.StringIO(content))
    parsed = parse_ascii(
        dataframe,
        content_bytes=content.encode("utf-8"),
        column_labels=list(dataframe.columns),
        filename="solar.csv",
    )

    assert parsed["flux"] == [0.15, 0.18, 0.14]
    assert parsed["metadata"]["flux_column"] == "Irradiance (W/m^2/nm)"


@pytest.mark.parametrize(
    "columns, expected",
    [
        (
            ["Wavelength (nm)", "Sun", "Irradiance (W/m^2/nm)"],
            "Irradiance (W/m^2/nm)",
        ),
        (
            ["Wavelength (nm)", "Observer", "Spectral Power (W/m^2/nm)"],
            "Spectral Power (W/m^2/nm)",
        ),
        (
            ["Wavelength (nm)", "Solar Radiance"],
            "Solar Radiance",
        ),
    ],
)
def test_ingest_local_ascii_prefers_flux_keyword_variants(columns, expected):
    header = ",".join(columns)
    rows = []
    wavelengths = [400, 405, 410]
    for idx, wavelength in enumerate(wavelengths):
        values = [str(wavelength)]
        for col_idx in range(1, len(columns)):
            values.append(f"{0.1 + 0.05 * (idx + col_idx):.2f}")
        rows.append(",".join(values))

    content = "\n".join([header, *rows])

    dataframe = pd.read_csv(io.StringIO(content))
    parsed = parse_ascii(
        dataframe,
        content_bytes=content.encode("utf-8"),
        column_labels=list(dataframe.columns),
        filename="solar_variants.csv",
    )

    assert parsed["flux"] == dataframe[expected].tolist()
    assert parsed["metadata"]["flux_column"] == expected


def test_parse_ascii_segments_handles_variable_whitespace():
    segment = dedent(
        """
        # Source: Atlas
        # Flux Unit: relative

        380.0    0.5   1.0
        380.5\t0.55\t0.9
        381.0      0.6
        """
    ).encode("utf-8")

    parsed = parse_ascii_segments(
        [("segment.txt", segment)], root_filename="segment.txt", chunk_size=2
    )

    assert parsed["wavelength_nm"] == pytest.approx([380.0, 380.5, 381.0])
    assert parsed["flux"] == pytest.approx([0.5, 0.55, 0.6])
    metadata = parsed["metadata"]
    assert metadata["points"] == 3
    assert metadata["flux_unit"] == "relative"
    assert metadata["dense_chunk_size"] == 2
    assert parsed["downsample"]
    assert parsed["provenance"]["chunks"]


def test_parse_ascii_segments_converts_angstrom_to_nm():
    segment = dedent(
        """
        # Wavelength Unit: Angstrom
        5000 1.0
        5005 1.1
        """
    ).encode("utf-8")

    parsed = parse_ascii_segments(
        [("segment.txt", segment)], root_filename="segment.txt"
    )

    assert parsed["wavelength_nm"] == pytest.approx([500.0, 500.5])
    metadata = parsed["metadata"]
    assert metadata["original_wavelength_unit"] == "Angstrom"
    units = parsed["provenance"].get("units", {})
    assert units.get("wavelength_input") in {"Angstrom", "Å"}
    assert units.get("wavelength_reported") == "Angstrom"
    assert units.get("wavelength_converted_to") == "nm"


def test_parse_ascii_segments_wavenumber_sorted_to_nm():
    segment = dedent(
        """
        # Wavelength Unit: cm^-1
        20000 1.0
        10000 0.5
        """
    ).encode("utf-8")

    parsed = parse_ascii_segments(
        [("segment.txt", segment)], root_filename="segment.txt"
    )

    assert parsed["wavelength_nm"] == pytest.approx([500.0, 1000.0])
    assert parsed["flux"] == pytest.approx([1.0, 0.5])
    dense = parsed["provenance"].get("dense_parser", {})
    assert dense.get("unique_samples") == 2


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
        15000,0.8
        10000,0.5
        """
    ).encode("utf-8")

    payload = ingest_local_file("wavenumber.csv", content)

    assert payload["wavelength_nm"] == pytest.approx([500.0, 666.6666667, 1000.0])
    assert payload["wavelength_quantity"].to_value(u.nm) == pytest.approx(
        payload["wavelength_nm"]
    )
    assert payload["wavelength"]["unit"] == "nm"
    assert payload["wavelength"]["values"] == pytest.approx(
        [500.0, 666.6666667, 1000.0]
    )
    metadata = payload["metadata"]
    assert metadata["original_wavelength_unit"].lower() == "cm-1"
    reported_normalized = metadata["reported_wavelength_unit"].lower().replace(" ", "")
    assert reported_normalized in {"cm-1", "cm^-1"}


def test_ingest_local_ascii_micron_unit():
    content = dedent(
        """
        # Target: InfraredSource
        Wavelength (micron),Flux
        0.5,10
        0.75,12
        1.0,14
        """
    ).encode("utf-8")

    payload = ingest_local_file("infrared.csv", content)

    expected_nm = [500.0, 750.0, 1000.0]
    assert payload["wavelength_nm"] == pytest.approx(expected_nm)
    assert payload["wavelength"]["unit"] == "nm"
    assert payload["wavelength"]["values"] == pytest.approx(expected_nm)
    assert payload["flux"] == [10.0, 12.0, 14.0]


def test_ingest_local_ascii_gzip_round_trip():
    content = gzip.compress(
        dedent(
            """
            Wavelength (nm),Flux
            400,1.0
            405,0.5
            410,0.25
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


def test_ingest_local_zip_merges_segments():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("chunk_a.txt", "380 0.5 1\n381 0.6 0.9\n")
        archive.writestr("chunk_b.txt", "382 0.7 0.8\n")

    payload = ingest_local_file("atlas.zip", buffer.getvalue())

    assert payload["wavelength_nm"] == pytest.approx([380.0, 381.0, 382.0])
    assert payload["flux"] == pytest.approx([0.5, 0.6, 0.7])
    assert payload["downsample"]

    metadata = payload["metadata"]
    assert metadata["segments"] == ["chunk_a.txt", "chunk_b.txt"]
    assert metadata["cache_dataset_id"]

    provenance = payload["provenance"]
    cache_info = provenance.get("cache")
    assert cache_info is not None
    cache_path = Path(cache_info["path"])
    assert cache_path.exists()
    chunks = list(cache_path.glob("chunk_*.npz"))
    assert chunks


def test_ingest_local_dense_ascii_uses_cache(monkeypatch):
    monkeypatch.setattr(local_ingest, "_DENSE_SIZE_THRESHOLD", 0)
    monkeypatch.setattr(local_ingest, "_DENSE_LINE_THRESHOLD", 0)
    lines = "\n".join(
        f"{380.0 + 0.1 * idx:.1f} {0.5 + 0.01 * idx:.3f} {1.0 - 0.001 * idx:.3f}"
        for idx in range(20)
    )
    content = f"# Source: Dense\n{lines}\n".encode("utf-8")

    payload = ingest_local_file("dense.txt", content)

    assert payload["downsample"]
    metadata = payload["metadata"]
    assert metadata["cache_dataset_id"]

    cache_info = payload["provenance"].get("cache")
    assert cache_info is not None
    cache_path = Path(cache_info["path"])
    assert cache_path.exists()


def test_dense_parser_fallback_to_table(monkeypatch):
    monkeypatch.setattr(local_ingest, "_DENSE_SIZE_THRESHOLD", 0)
    monkeypatch.setattr(local_ingest, "_DENSE_LINE_THRESHOLD", 0)

    def failing_segments(*args, **kwargs):
        raise ValueError("No numeric samples detected across ASCII segments")

    monkeypatch.setattr(local_ingest, "parse_ascii_segments", failing_segments)

    content = dedent(
        """
        wavelength (nm), irradiance (W/m^2/nm)
        202,0.0097
        202.001,0.0098
        202.002,0.0099
        """
    ).encode("utf-8")

    payload = ingest_local_file("sun.csv", content)

    assert payload["wavelength_nm"] == pytest.approx([202.0, 202.001, 202.002])
    fallback = payload.get("provenance", {}).get("dense_parser_fallback")
    assert fallback["method"] == "read_table"
    assert "No numeric samples" in fallback["error"]


def test_zip_dense_parser_fallback(monkeypatch):
    def failing_segments(*args, **kwargs):
        raise ValueError("No numeric samples detected across ASCII segments")

    monkeypatch.setattr(local_ingest, "parse_ascii_segments", failing_segments)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "segment.txt",
            "wavelength (nm),flux\n202,0.01\n202.1,0.011\n202.2,0.012\n",
            compress_type=zipfile.ZIP_DEFLATED,
        )

    payload = ingest_local_file("sun_segments.zip", buffer.getvalue())

    assert payload["wavelength_nm"] == pytest.approx([202.0, 202.1, 202.2])

    metadata = payload.get("metadata", {})
    assert metadata.get("segments") == ["segment.txt"]
    fallback = payload.get("provenance", {}).get("dense_parser_fallback")
    assert fallback["method"] == "read_table"
    assert fallback["selected_segment"] == "segment.txt"



def test_reject_metadata_like_tables():
    content = dedent(
        """
        RA (2000),DEC (2000)
        10,20
        30,40
        """
    ).encode("utf-8")

    with pytest.raises(local_ingest.LocalIngestError) as excinfo:
        ingest_local_file("metadata.csv", content)

    assert "contains only" in str(excinfo.value)

def test_ingest_local_dense_ascii_falls_back_for_tab_delimited(monkeypatch):
    monkeypatch.setattr(local_ingest, "_DENSE_SIZE_THRESHOLD", 0)
    monkeypatch.setattr(local_ingest, "_DENSE_LINE_THRESHOLD", 0)

    def failing_parse_ascii_segments(*args, **kwargs):
        raise ValueError("No numeric samples detected across ASCII segments")

    monkeypatch.setattr(local_ingest, "parse_ascii_segments", failing_parse_ascii_segments)

    tab_path = Path(__file__).resolve().parents[1] / "data" / "tab_header.tsv"
    content = tab_path.read_bytes()

    payload = ingest_local_file("tab_header.csv", content)

    assert payload["wavelength_nm"] == [500.0, 505.0]
    assert payload["flux"] == [1.2, 1.3]
    assert payload["metadata"]["filename"] == "tab_header.csv"
    assert payload["provenance"]["filename"] == "tab_header.csv"



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
    assert metadata["original_wavelength_unit"] == "Angstrom"

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
    assert metadata["original_wavelength_unit"] == "Angstrom"
    assert metadata["reported_wavelength_unit"] == "Angstrom"
    assert metadata["points"] == 3

    provenance = payload["provenance"]
    assert provenance["data_mode"] == "table"
    assert provenance["column_mapping"]["wavelength"] == "WAVELENGTH"
    assert provenance["column_mapping"]["flux"] == "FLUX"


def test_ingest_local_fits_event_table_bins_counts():
    size = 2048
    rng = np.random.default_rng(12345)
    wavelengths = rng.uniform(1200.0, 1250.0, size)
    rawx = rng.integers(0, 32, size, dtype=np.int16)
    rawy = rng.integers(0, 32, size, dtype=np.int16)
    times = np.linspace(0.0, 600.0, size, dtype=float)

    columns = [
        fits.Column(name="TIME", array=times, format="D", unit="s"),
        fits.Column(name="RAWX", array=rawx, format="I", unit="pixel"),
        fits.Column(name="RAWY", array=rawy, format="I", unit="pixel"),
        fits.Column(name="WAVELENGTH", array=wavelengths, format="D", unit="Angstrom"),
    ]

    table_hdu = fits.BinTableHDU.from_columns(columns, name="EVENTS")
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])

    bio = io.BytesIO()
    hdul.writeto(bio)
    hdul.close()

    payload = ingest_local_file("event_spectrum.fits", bio.getvalue())

    assert payload["flux_unit"] == "count"
    assert payload["flux_kind"] == "relative"
    assert sum(payload["flux"]) == pytest.approx(size)

    metadata = payload["metadata"]
    assert metadata["points"] == len(payload["flux"])
    assert metadata["reported_flux_unit"] == "pixel"

    provenance = payload["provenance"]
    assert provenance["column_mapping"]["flux"] == "RAWX"
    assert provenance["event_table"]["flux_source_column"] == "RAWX"
    assert provenance["event_table"]["derived_flux_unit"] == "count"
    assert provenance["event_table"]["binning"]["original_samples"] == size
    assert provenance["units"]["flux_input"] == "pixel"
    assert provenance["units"]["flux_derived"] == "count"
    assert provenance["conversions"]["flux_unit"] == {"from": "pixel", "to": "count"}
