# Atlas 08k — WISE / AllWISE / NEOWISE

## Overview
**WISE** (Wide-field Infrared Survey Explorer) mapped the whole sky in the infrared. Its main catalogs:
- **AllWISE** (post-cryogenic reprocessing; legacy static catalog)
- **NEOWISE/NEOWISE-R** (reactivation mission; *time-domain* single-epoch source lists)

**Bands (Vega):**
- **W1** 3.4 µm, **W2** 4.6 µm, **W3** 12 µm, **W4** 22 µm  
Angular FWHM roughly 6.1″ (W1/W2), 6.5″ (W3), 12.0″ (W4).

WISE is indispensable for stellar/galactic SEDs, dust, AGN selection, and variability (NEOWISE).

---

## Where the data lives (IRSA/IPAC)
- **IRSA Gator** search portal (catalogs)  
- **WISE Image Service** (coadds and single-exposure images)  
- **VO services**: cone search, TAP (via IRSA), SIAP for images

Programmatic access in Python is cleanest via **`astroquery.ipac.irsa`** (`Irsa`).

---

## Primary tables (IRSA names)
- **AllWISE Source Catalog**: `allwise_p3as_psd` (profile-fit photometry; static)  
- **AllWISE Multiepoch Photometry**: `allwise_p3me` (per-detection time series for AllWISE era)  
- **NEOWISE-R Single Exposure (L1b) Source Table**: `neowiser_p1bs_psd` (time-domain since 2013)  
- **AllWISE Reject Table**: `allwise_p3as_psr` (poor fits / artifacts; rarely needed)

Important columns you’ll use a lot:
- `ra`, `dec`
- `w1mpro`, `w2mpro`, `w3mpro`, `w4mpro` (Vega mags; profile-fit)
- `w?sigmpro` (mag uncertainties), `w?snr` (SNR), `w?chi2`
- `cc_flags` (artifact flags), `ext_flg` (extendedness), `ph_qual` (photometry quality)
- epoch columns for NEOWISE single-exposure rows

---

## Quick-start: Astroquery examples

### 1) AllWISE cone around a target name
```python
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u

Irsa.ROW_LIMIT = 2000  # be nice
coord = SkyCoord.from_name("Vega")
tbl = Irsa.query_region(coord, radius=0.02*u.deg, catalog="allwise_p3as_psd")
tbl.pprint(max_lines=5)
```

### 2) NEOWISE single-epoch time series (variability)
```python
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u

coord = SkyCoord.from_name("Vega")
neo = Irsa.query_region(coord, radius=0.01*u.deg, catalog="neowiser_p1bs_psd")
# Filter to the closest match (example heuristic)
import numpy as np
d2 = ( (neo["ra"]-coord.ra.deg)**2 + (neo["dec"]-coord.dec.deg)**2 )
neo = neo[d2.argmin()==d2]
neo.pprint(max_lines=10)
```

### 3) AllWISE multiepoch photometry join (if you have the source `designation`)
```python
from astroquery.ipac.irsa import Irsa
designation = "J183656.32+384701.2"  # example
me = Irsa.query_region_async(f"select * from allwise_p3me where designation='{designation}'")
# For large pulls, prefer TAP or staged queries.
```

> Tip: For serious workloads, switch to IRSA TAP with async jobs (via `pyvo`) or use paged queries.

---

## Integrating WISE into Spectra App

### Fetcher skeleton
```python
# app/server/fetchers/fetch_wise.py
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
import astropy.units as u

def fetch_allwise_cone(name_or_coord: str, radius_arcmin: float = 1.0, limit: int = 500):
    Irsa.ROW_LIMIT = limit
    coord = SkyCoord.from_name(name_or_coord) if isinstance(name_or_coord, str) else name_or_coord
    res = Irsa.query_region(coord, radius=radius_arcmin*u.arcmin, catalog="allwise_p3as_psd")
    return res

def fetch_neowise_single_epoch(name_or_coord: str, radius_arcmin: float = 0.5, limit: int = 500):
    Irsa.ROW_LIMIT = limit
    coord = SkyCoord.from_name(name_or_coord) if isinstance(name_or_coord, str) else name_or_coord
    return Irsa.query_region(coord, radius=radius_arcmin*u.arcmin, catalog="neowiser_p1bs_psd")
```

### Normalizing photometry into SED points
Convert Vega mags to flux density (Jy):  
\( F_\nu = F_{\nu,0} \times 10^{-0.4 m} \) where \(F_{\nu,0}\) is the band zero-point.  
Use IRSA-provided zero points from metadata to avoid stale hard-codes. Store:
```json
{
  "mission": "WISE",
  "release": "AllWISE/NEOWISE",
  "table": "allwise_p3as_psd",
  "bands": ["W1","W2","W3","W4"],
  "phot_system": "Vega",
  "zp_source": "IRSA metadata",
  "processing": ["profile-fit magnitudes -> Jy"]
}
```

### Provenance merge
- Log IRSA table name, query footprint, match radius.
- Keep artifact flags (`cc_flags`, `ph_qual`) in exports.
- If SED points are filtered, record the **criteria** in the manifest (e.g., `ph_qual in {'A','B'}`, `cc_flags == '0000'`).

---

## Strengths
- **All-sky** IR photometry, uniform bands.
- **Time-domain** via NEOWISE for mid-IR variability.
- Great for **dusty sources, AGN, YSOs**, star/galaxy separation.

## Weaknesses / Pitfalls
- **Confusion** and blending in crowded fields (6–12″ PSF).
- **Saturation** and non-linearity for bright objects; check `ph_qual`, `w?flux` fallbacks.
- Artifacts near bright stars (diffraction spikes, persistence) flagged by `cc_flags`.
- Extended sources: profile-fit mags underestimate total flux; consider **unWISE** coadds or elliptical apertures.

---

## Best Practices
- Always enforce **quality cuts** before ingest: good `ph_qual`, clean `cc_flags`, reasonable `snr`.
- Cross-match to SIMBAD/Gaia to confirm identifications.
- Cache results; NEOWISE queries can be large.
- Store **Vega-to-Jy conversion details** in the provenance manifest.
- For extended sources, supplement with **unWISE** or aperture photometry.

---

## References (for later citation in exports)
- WISE mission: Wright et al. 2010, AJ, 140, 1868
- NEOWISE reactivation: Mainzer et al. 2014, ApJ, 792, 30
- IRSA WISE services: https://irsa.ipac.caltech.edu/Missions/wise.html
- Astroquery IRSA docs: https://astroquery.readthedocs.io/en/latest/ipac/irsa/irsa.html
