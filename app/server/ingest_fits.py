from __future__ import annotations

from typing import Dict

import numpy as np
from astropy.io import fits

from .units import to_nm


def _ensure_1d(array: np.ndarray) -> np.ndarray:
    """Return a 1-D view of the provided array or raise if ambiguous."""

    if array.ndim == 0:
        return array.reshape(1)

    squeezed = np.squeeze(array)
    if squeezed.ndim == 1:
        return squeezed

    raise ValueError(
        f"FITS data is not 1-dimensional; found shape {array.shape}. "
        "Provide a FITS HDU with 1-D data for spectral ingestion."
    )


def parse_fits(path: str) -> Dict[str, object]:
    """Extract a spectrum from a FITS file into the normalised payload."""

    with fits.open(path) as hdul:
        data_hdu = next(
            (hdu for hdu in hdul if getattr(hdu, "data", None) is not None),
            None,
        )
        if data_hdu is None:
            raise ValueError("No array data found in FITS file.")

        header = data_hdu.header
        raw_data = np.ma.getdata(data_hdu.data)
        flux = _ensure_1d(np.array(raw_data, copy=True))

        if flux.size == 0:
            raise ValueError("FITS data array is empty.")

        crval1 = header.get("CRVAL1")
        cdelt1 = header.get("CDELT1")
        missing = [
            key
            for key, value in (("CRVAL1", crval1), ("CDELT1", cdelt1))
            if value is None
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(
                f"Missing WCS keyword(s) {joined} in FITS header for spectral axis."
            )

        try:
            crval1 = float(crval1)
            cdelt1 = float(cdelt1)
            crpix1 = float(header.get("CRPIX1", 1.0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid WCS keyword value in FITS header.") from exc

        unit = header.get("CUNIT1", "nm")

        pix = np.arange(flux.size, dtype=float)
        wavelengths = crval1 + (pix - (crpix1 - 1.0)) * cdelt1
        wavelength_nm = to_nm(wavelengths.tolist(), unit)

        return {
            "wavelength": wavelength_nm,
            "flux": flux.tolist(),
            "unit_wavelength": "nm",
            "unit_flux": "arb",
            "meta": {"original_unit_wavelength": unit},
        }
