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
