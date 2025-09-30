import numpy as np
import pytest
from astropy.io import fits

from app.server.ingest_fits import parse_fits


def test_parse_fits_uses_first_data_extension(tmp_path):
    flux_values = np.array([1.0, 2.0, 3.0], dtype=float)

    primary_hdu = fits.PrimaryHDU()
    primary_hdu.header["CRVAL1"] = 999.0
    primary_hdu.header["CDELT1"] = 5.0

    sci_header = fits.Header()
    sci_header["CRVAL1"] = 400.0
    sci_header["CDELT1"] = 0.5
    sci_header["CRPIX1"] = 1.0
    sci_header["CUNIT1"] = "nm"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")

    hdul = fits.HDUList([primary_hdu, sci_hdu])
    fits_path = tmp_path / "extension_data.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    result = parse_fits(str(fits_path))

    expected_wavelength = [400.0 + 0.5 * i for i in range(flux_values.size)]

    assert result["flux"] == flux_values.tolist()
    assert result["wavelength_nm"] == expected_wavelength
    assert result["flux_unit"] == "arb"
    assert result["flux_kind"] == "relative"
    assert result["metadata"]["original_wavelength_unit"] == "nm"
    assert result["metadata"]["wavelength_range_nm"] == [400.0, 401.0]
    assert result["provenance"]["data_mode"] == "image"


def test_parse_fits_flattens_multidimensional_table(tmp_path):
    wavelengths = np.array(
        [
            [400.0, 401.0, 402.0, 403.0],
            [500.0, 501.0, 502.0, 503.0],
            [600.0, 601.0, 602.0, 603.0],
        ],
        dtype=float,
    )
    flux = np.array(
        [
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
        ],
        dtype=float,
    )

    columns = [
        fits.Column(name="WAVELENGTH", array=wavelengths, format="4D", unit="nm"),
        fits.Column(name="FLUX", array=flux, format="4D"),
    ]
    table_hdu = fits.BinTableHDU.from_columns(columns)

    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    fits_path = tmp_path / "multidimensional_table.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    result = parse_fits(str(fits_path))

    assert result["flux"] == flux.reshape(-1).tolist()
    assert result["wavelength_nm"] == wavelengths.reshape(-1).tolist()
    assert result["metadata"]["points"] == flux.size
    assert result["provenance"]["row_count"] == wavelengths.shape[0]


def test_parse_fits_collapses_image_data(tmp_path):
    flux_values = np.array(
        [
            [1.0, 3.0, 5.0, 7.0],
            [2.0, 4.0, 6.0, 8.0],
        ],
        dtype=float,
    )

    sci_header = fits.Header()
    sci_header["CRVAL1"] = 100.0
    sci_header["CDELT1"] = 0.5
    sci_header["CRPIX1"] = 1.0
    sci_header["CUNIT1"] = "nm"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")
    primary_hdu = fits.PrimaryHDU()

    hdul = fits.HDUList([primary_hdu, sci_hdu])
    fits_path = tmp_path / "two_dimensional_image.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    result = parse_fits(str(fits_path))

    expected_flux = flux_values.mean(axis=0)
    expected_wavelength = [100.0 + 0.5 * i for i in range(flux_values.shape[1])]

    assert result["flux"] == expected_flux.tolist()
    assert result["wavelength_nm"] == expected_wavelength
    assert result["metadata"]["points"] == flux_values.shape[1]

    collapse_meta = result["provenance"].get("image_collapse", {})
    assert collapse_meta.get("original_shape") == [2, 4]
    assert collapse_meta.get("collapsed_axes") == [0]


def test_parse_fits_rejects_nonspectral_image_axis(tmp_path):
    flux_values = np.array([1.0, 2.0, 3.0], dtype=float)

    sci_header = fits.Header()
    sci_header["CRVAL1"] = -1.0
    sci_header["CDELT1"] = 1.0
    sci_header["CRPIX1"] = 1.0
    sci_header["CTYPE1"] = "RA---TAN"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), sci_hdu])
    fits_path = tmp_path / "ra_axis_image.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    with pytest.raises(ValueError) as excinfo:
        parse_fits(str(fits_path))

    message = str(excinfo.value)
    assert "does not describe a spectral axis" in message
    assert "CTYPE1='RA---TAN'" in message


def test_parse_fits_accepts_convertible_units_without_spectral_ctype(tmp_path):
    flux_values = np.array([1.0, 2.0, 3.0], dtype=float)

    sci_header = fits.Header()
    sci_header["CRVAL1"] = 1000.0
    sci_header["CDELT1"] = 1.0
    sci_header["CRPIX1"] = 1.0
    sci_header["CTYPE1"] = "LINEAR"
    sci_header["CUNIT1"] = "angstrom"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), sci_hdu])
    fits_path = tmp_path / "linear_angstrom.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    result = parse_fits(str(fits_path))

    expected_wavelength_nm = [100.0 + i * 0.1 for i in range(flux_values.size)]
    assert result["wavelength_nm"] == pytest.approx(expected_wavelength_nm)



def test_parse_fits_rejects_table_with_nonspectral_units(tmp_path):
    time = np.array([0.0, 1.0, 2.0], dtype=float)
    flux = np.array([10.0, 11.0, 12.0], dtype=float)

    columns = [
        fits.Column(name="TIME", array=time, format="D", unit="BJD - 2457000, days"),
        fits.Column(name="SAP_FLUX", array=flux, format="D", unit="e-/s"),
    ]

    table_hdu = fits.BinTableHDU.from_columns(columns)
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    fits_path = tmp_path / "tess_like_lightcurve.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    with pytest.raises(ValueError) as excinfo:
        parse_fits(str(fits_path))

    message = str(excinfo.value)
    assert "TIME" in message
    assert "BJD" in message


def test_parse_fits_assumes_nm_for_wavelength_column_without_units(tmp_path):
    wavelengths = np.array([400.0, 500.0, 600.0], dtype=float)
    flux = np.array([1.0, 2.0, 3.0], dtype=float)

    columns = [
        fits.Column(name="WAVE", array=wavelengths, format="D"),
        fits.Column(name="FLUX", array=flux, format="D"),
    ]

    table_hdu = fits.BinTableHDU.from_columns(columns)
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    fits_path = tmp_path / "unitless_wavelength_table.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    result = parse_fits(str(fits_path))

    assert result["wavelength_nm"] == wavelengths.tolist()
    assert result["metadata"]["original_wavelength_unit"] == "nm"
    assert result["metadata"].get("reported_wavelength_unit") is None

    unit_resolution = result["provenance"].get("wavelength_unit_resolution", {})
    assert unit_resolution.get("assumed") == "nm"
    assert unit_resolution.get("assumed_from") == "column_name"


def test_parse_fits_rejects_table_with_nonpositive_wavelengths(tmp_path):
    wavelengths = np.array([-50.0, -10.0, 0.0], dtype=float)
    flux = np.array([1.0, 2.0, 3.0], dtype=float)

    columns = [
        fits.Column(name="WAVE", array=wavelengths, format="D", unit="nm"),
        fits.Column(name="FLUX", array=flux, format="D"),
    ]

    table_hdu = fits.BinTableHDU.from_columns(columns)
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    fits_path = tmp_path / "negative_wavelength_table.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    with pytest.raises(ValueError) as excinfo:
        parse_fits(str(fits_path))

    message = str(excinfo.value)
    assert "no positive wavelengths" in message
    assert "conversion to nm" in message


def test_parse_fits_rejects_table_with_negative_wavelengths_after_conversion(tmp_path):
    wavelengths = np.array([-500.0, -100.0], dtype=float)
    flux = np.array([1.0, 2.0], dtype=float)

    columns = [
        fits.Column(name="WAVE", array=wavelengths, format="D", unit="angstrom"),
        fits.Column(name="FLUX", array=flux, format="D"),
    ]

    table_hdu = fits.BinTableHDU.from_columns(columns)
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    fits_path = tmp_path / "negative_wavelength_angstrom_table.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    with pytest.raises(ValueError) as excinfo:
        parse_fits(str(fits_path))

    message = str(excinfo.value)
    assert "no positive wavelengths" in message
    assert "conversion to nm" in message


def test_parse_fits_rejects_table_with_negative_wavelengths_microns(tmp_path):
    wavelengths = np.array([-2.0, -1.0], dtype=float)
    flux = np.array([1.0, 2.0], dtype=float)

    columns = [
        fits.Column(name="WAVE", array=wavelengths, format="D", unit="micron"),
        fits.Column(name="FLUX", array=flux, format="D"),
    ]

    table_hdu = fits.BinTableHDU.from_columns(columns)
    hdul = fits.HDUList([fits.PrimaryHDU(), table_hdu])
    fits_path = tmp_path / "negative_wavelength_micron_table.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    with pytest.raises(ValueError) as excinfo:
        parse_fits(str(fits_path))

    message = str(excinfo.value)
    assert "no positive wavelengths" in message
    assert "conversion to nm" in message


def test_parse_fits_rejects_image_with_nonpositive_wavelengths(tmp_path):
    flux_values = np.array([1.0, 2.0, 3.0], dtype=float)

    sci_header = fits.Header()
    sci_header["CRVAL1"] = -5.0
    sci_header["CDELT1"] = 1.0
    sci_header["CRPIX1"] = 1.0
    sci_header["CUNIT1"] = "nm"

    sci_hdu = fits.ImageHDU(data=flux_values, header=sci_header, name="SCI")
    hdul = fits.HDUList([fits.PrimaryHDU(), sci_hdu])
    fits_path = tmp_path / "negative_wavelength_image.fits"
    hdul.writeto(fits_path, overwrite=True)
    hdul.close()

    with pytest.raises(ValueError) as excinfo:
        parse_fits(str(fits_path))

    message = str(excinfo.value)
    assert "positive-wavelength" in message
