# Atlas 08d – SDSS (Sloan Digital Sky Survey)

## Overview
The Sloan Digital Sky Survey (SDSS) is a cornerstone astronomical project providing wide-field imaging and spectroscopy of millions of celestial objects.  
It has released multiple **Data Releases (DRs)**, each with improved calibration, wavelength coverage, and instruments.  
SDSS data is widely used for:
- Galaxy and quasar redshifts
- Stellar population studies
- Large-scale structure mapping
- Reference spectra for astrophysical modeling

**Key importance for Spectra App**: Provides a deep archive of *stellar and galactic spectra* with well-documented provenance.

---

## Data Types
1. **Spectroscopic Data**
   - Wavelength range: ~3800–9200 Å (optical)
   - Resolution: R ≈ 2000
   - Stored in FITS files, per object
   - Includes flux, error arrays, masks, and metadata

2. **Photometric Data**
   - ugriz filters (AB magnitudes)
   - Imaging survey covering large fractions of the sky

3. **Value-Added Catalogs**
   - Redshift determinations
   - Object classifications
   - Cross-matches with external catalogs (WISE, 2MASS, etc.)

---

## Access Methods
### 1. SkyServer
- Web-based interface to explore objects interactively.
- URL: http://skyserver.sdss.org
- Provides point-and-click data browsing.

### 2. CasJobs
- Batch SQL query service.
- URL: http://skyserver.sdss.org/CasJobs/
- Allows large queries and asynchronous jobs.

### 3. Astroquery.sdss (Python)
```python
from astroquery.sdss import SDSS
from astropy import coordinates as coords

# Example: query spectrum for a known object
pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s', frame='icrs')
xid = SDSS.query_region(pos, spectro=True)
spec = SDSS.get_spectra(matches=xid)[0]

# Access FITS data
data = spec[1].data
wavelengths = 10**data['loglam']  # log10 Å
flux = data['flux']
```

---

## Provenance & Citation
- Cite the appropriate **Data Release (DR)** in any publication.
- Each DR has a DOI and publication reference (e.g., DR17: https://www.sdss4.org/dr17/).
- Provenance fields to capture:
  - Data Release number
  - Plate, MJD, Fiber ID (unique identifiers)
  - SDSS pipeline version

---

## Integration Notes
- Always resolve **log-lambda** into wavelength in Å.
- Flux calibration is in 1e-17 erg/s/cm²/Å by default.
- SDSS FITS headers contain unit metadata—trust but verify.
- Cross-match with other surveys often necessary for extended provenance.

---

## Common Pitfalls
- Mixing DRs: Different releases may reprocess the same spectra with updated calibration.
- Misinterpreting loglam: Must exponentiate to get wavelength in Å.
- SQL queries returning *photo* objects instead of *spec* objects if not careful.

---

## Skeleton for Spectra App Integration
```python
from astroquery.sdss import SDSS
from astropy.io import fits

def fetch_sdss_spectrum(ra: float, dec: float):
    from astropy import coordinates as coords
    pos = coords.SkyCoord(ra=ra, dec=dec, unit="deg", frame="icrs")
    xid = SDSS.query_region(pos, spectro=True)
    if xid is None or len(xid) == 0:
        return None
    spec = SDSS.get_spectra(matches=xid)[0]
    data = spec[1].data
    wl = 10**data['loglam']
    flux = data['flux']
    meta = spec[2].data if len(spec) > 2 else {}
    return wl, flux, meta
```

---

## Next Steps
- Build SDSS fetcher under `app/server/fetchers/sdss_fetcher.py`.
- Add provenance recorder: plate, MJD, fiber, DR number.
- Integrate into Fetch Data tab alongside MAST and SIMBAD.

---
