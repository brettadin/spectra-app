from astropy.io import fits
import numpy as np
from .units import to_nm

def parse_fits(path: str):
    hdul = fits.open(path)
    h = hdul[0].header
    data = hdul[0].data
    crval1 = h.get('CRVAL1'); cdelt1 = h.get('CDELT1'); crpix1 = h.get('CRPIX1',1.0)
    unit = h.get('CUNIT1','nm')
    n = data.shape[-1] if data is not None else int(h.get('NAXIS1',0))
    pix = np.arange(n)
    wl = crval1 + (pix - (crpix1-1))*cdelt1
    wl_nm = to_nm(wl.tolist(), unit)
    return {'wavelength': wl_nm, 'flux': data.tolist(), 'unit_wavelength':'nm', 'unit_flux':'arb', 'meta': {'original_unit_wavelength': unit}}
