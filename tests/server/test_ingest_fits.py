import numpy as np
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
