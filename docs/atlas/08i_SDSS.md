# Atlas 08i — SDSS (Sloan Digital Sky Survey)

## Overview
The Sloan Digital Sky Survey (SDSS) is one of the most ambitious and influential surveys in astronomy.  
It provides **imaging, spectroscopy, and catalogs** of millions of stars, galaxies, and quasars across large areas of the sky.  
Its data releases (DR1–DR19) have become the gold standard for statistical cosmology and stellar population studies.

- Imaging in 5 bands: **u, g, r, i, z**
- Spectra covering ~380–920 nm, resolution ~2000
- Redshift catalogs for galaxies and quasars
- Stellar parameters for Milky Way studies

## APIs & Tools
SDSS offers multiple interfaces for data access:

1. **SkyServer** — Web-based SQL queries and REST API.  
   - Example REST endpoint: `http://skyserver.sdss.org/dr16/SkyServerWS/SearchTools/SqlSearch?cmd=...`
   - Supports raw SQL queries against the SDSS catalog.

2. **CasJobs** — Batch SQL query service.  
   - Allows submitting large queries asynchronously.  
   - Results stored in user space for later download.

3. **SciServer** — Integrated environment for analysis.  
   - Jupyter-based notebooks connected directly to SDSS datasets.

4. **Astroquery.sdss** — Python library wrapper.  
   - Part of `astroquery`, simplifies fetching spectra and images.

## Data Types
- **Spectra:** Optical spectra of stars, galaxies, quasars.  
  - Indexed by plate, MJD, fiber ID.
- **Images:** ugriz imaging of the sky with calibrated magnitudes.  
- **Catalogs:** redshifts, stellar parameters, morphological classifications.  
- **Cross-Match:** coordinate-based matching to external catalogs (SIMBAD, Gaia, etc.).

## Fetch Workflows

### Using Astroquery
```python
from astroquery.sdss import SDSS
from astropy import coordinates as coords

# Query by coordinates
pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s', frame='icrs')
xid = SDSS.query_region(pos, spectro=True)

# Fetch spectra
spectra = SDSS.get_spectra(matches=xid)
```

### Using REST API
```http
http://skyserver.sdss.org/dr16/SkyServerWS/SearchTools/SqlSearch?
cmd=SELECT TOP 10 ra,dec,modelMag_r FROM PhotoObj&format=csv
```

### Using CasJobs
- Submit SQL query: `SELECT TOP 100 * FROM SpecObj`  
- Wait for job completion and download results from user workspace.

## Integration Skeleton

For ingestion into the Spectra App, use a unified fetcher module:
```python
def fetch_sdss_spectrum(plate, mjd, fiber):
    from astroquery.sdss import SDSS
    return SDSS.get_spectra(plate=plate, mjd=mjd, fiberID=fiber)
```

Provenance log entry example:
```json
{
  "source": "SDSS DR16",
  "plate": 266,
  "mjd": 51602,
  "fiber": 3,
  "bands": "ugriz",
  "doi": "10.3847/1538-4365/ab0821"
}
```

## Limitations
- Query size caps on SkyServer (~500k rows).  
- CasJobs requires registration.  
- Calibration differences between data releases (DR7 Legacy vs. DR16 onwards).  
- Spectral resolution fixed (R ~ 2000), not comparable to high-res echelle data.  

## Best Practices
- Use **astroquery.sdss** for scripting and automated fetches.  
- Always **record provenance** (plate/MJD/fiber, DR version).  
- Cache spectra locally for heavy analysis.  
- Cross-match with **SIMBAD/Gaia** for context.  
- Combine ugriz photometry with MAST/ESO/GALEX for multi-band analysis.

## Role in Atlas
SDSS data plays a central role in:
- Benchmarking stellar populations.  
- Providing ground truth for exoplanet host star properties.  
- Supplying spectra to overlay with laboratory lamp lines.  
- Cross-matching with MAST/ESO/NED datasets to create holistic spectral views.

---
**References**
- [SDSS SkyServer](http://skyserver.sdss.org/)  
- [CasJobs](https://skyserver.sdss.org/casjobs/)  
- [SciServer](https://www.sciserver.org/)  
- [Astroquery SDSS Docs](https://astroquery.readthedocs.io/en/latest/sdss/sdss.html)  
