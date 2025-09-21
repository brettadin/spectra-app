# Atlas 08j — GALEX (Galaxy Evolution Explorer)

## Overview
The Galaxy Evolution Explorer (GALEX) was a NASA space telescope dedicated to ultraviolet (UV) astronomy. 
It operated from 2003 to 2013, conducting wide-field imaging and low-resolution spectroscopy in two bands:
- **FUV (Far Ultraviolet):** 1350–1750 Å
- **NUV (Near Ultraviolet):** 1750–2750 Å

GALEX provided the first all-sky UV survey, making it a cornerstone dataset for star formation, galaxy evolution, and UV-bright stellar sources.

---

## Data Access
GALEX data is archived at **MAST (Mikulski Archive for Space Telescopes)** and can also be cross-matched via:
- **MAST Portal:** https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html
- **CasJobs:** https://mastweb.stsci.edu/ps1casjobs/
- **Vizier:** GALEX catalogs hosted at CDS

Data products include:
- **Imaging:** Calibrated FUV/NUV exposures and mosaics
- **Spectroscopy:** Low-resolution slitless grism spectra
- **Catalogs:** Source catalogs with UV magnitudes, errors, quality flags

---

## Fetching GALEX Data

### Astroquery (Python)
```python
from astroquery.mast import Catalogs

# Query GALEX catalog for sources around M51
catalog_data = Catalogs.query_region("M51", radius="0.1 deg", catalog="GALEX")
print(catalog_data[:5])
```

### Direct MAST Download (curl example)
```bash
curl -O "https://mast.stsci.edu/api/v0.1/Download/file?mission=GALEX&dataset=GR6plus7&target=M51"
```

---

## Provenance & Citation
When using GALEX data:
- Always cite **Martin et al. 2005 (ApJ, 619, L1)** — GALEX mission paper
- Include dataset release notes (GR6/GR7)
- Add DOI where available from MAST

---

## Known Issues & Limitations
- Bright star artifacts (ghosts, saturation)
- FUV detector shut down in 2009 → later data only NUV
- Large PSF (~5 arcsec), lower resolution compared to HST/UVIT
- Limited spectral resolution (R ~ 100-200)

---

## Integration into Spectra App
GALEX UV data can complement:
- **SED building:** combine UV with optical (SDSS), IR (WISE), X-ray (Chandra)  
- **Overlay panel:** plot UV points alongside lamp and stellar spectra  
- **Provenance logs:** include GR version, exposure IDs, filters used  

### Skeleton Fetcher
```python
# app/server/fetchers/galex_fetcher.py

from astroquery.mast import Catalogs

def fetch_galex_region(target: str, radius: str = "0.1 deg"):
    """Fetch GALEX catalog entries for a target region."""
    try:
        results = Catalogs.query_region(target, radius=radius, catalog="GALEX")
        return results.to_pandas()
    except Exception as e:
        return {"error": str(e)}
```

---

## Why GALEX Matters for the Atlas
- Fills in the **UV regime** critical for star formation rates and hot stellar populations  
- Extends multi-wavelength Atlas coverage (UV → Optical → IR → Radio)  
- Enables **cross-mission science** when combined with SDSS, WISE, 2MASS, Chandra, HST  
- Provides large statistical samples (millions of galaxies, quasars, UV-bright stars)

---
