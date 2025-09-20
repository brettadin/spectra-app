# Atlas 08e – ESO (European Southern Observatory)

## 1) What ESO Is (and why we care)
ESO operates major ground-based facilities in Chile (VLT, VISTA, VST, APEX, ALMA with partners). Its **Science Archive Facility (SAF)** hosts raw and pipeline-calibrated data for instruments like **X-Shooter, UVES, MUSE, FORS**, plus survey products. For the Spectra App, ESO is our high‑S/N, wide‑wavelength, ground-based counterpart to space archives.

---

## 2) Entry points
- **Science Portal (Phase 3 products)**: curated, pipeline or survey high‑level data.  
  `https://archive.eso.org/scienceportal/`
- **Raw/Calibrated (Request Handler)**: direct programmatic downloads via request IDs.  
  `https://archive.eso.org/cms/eso-data/eso-archive-request-handler.html`
- **TAP/ObsCore (VO)**: Table Access Protocol for metadata filtering by instrument, target, time, sky region.  
  TAP service base: `https://archive.eso.org/tap_obs` (ObsCore)
- **Instrument pages**: documentation, pipelines, caveats, QC reports (UVES, X-Shooter, MUSE).
- **Programmatic (astroquery.eso)**: scripted queries + authenticated downloads.

---

## 3) Data landscape
- **Raw**: science exposures, calibrations, acquisition frames.
- **Pipeline products** (“Phase 3”):
  - **MUSE**: data cubes, extracted spectra, maps.
  - **X-Shooter**: 3‑arm spectra (UVB/VIS/NIR), often merged; R ~ 4k–18k.
  - **UVES**: high‑res echelle, R ~ 40k–110k.
  - **FORS**: imaging + low‑res spectroscopy.
  - **Surveys**: e.g., public spectral libraries and value‑added catalogs.
- **File formats**: FITS primary + extensions; binary tables (wavelength, flux, error), cubes (MUSE).

> Units: flux typically in erg s^-1 cm^-2 Å^-1; wavelengths may be **air** or **vacuum** depending on instrument/pipeline. Always check FITS headers (e.g., `WAVEUNIT`, `AIRORVAC`, `CTYPE1`, `SPECSYS`, `BUNIT`).

---

## 4) Access patterns we’ll support
### A. TAP/ObsCore cone + instrument filter
- Filter by **pos + radius**, **instrument**, **dataproduct_type=spectrum/cube**, **time**, **collection**.
- Returns metadata and access URLs (often `access_url`/`access_format`).

### B. astroquery.eso (username-based)
```python
from astroquery.eso import Eso
from astropy.table import Table

def eso_query_spectra(target: str, instrument='xshooter', public_only=True):
    eso = Eso()
    # Optional: eso.login('username') if you need proprietary or throttling relief
    # Search by target name then list datasets
    tbl = eso.query_surveys(target)
    # For instruments use query_instrument
    inst_tbl = eso.query_instrument(instrument, target=target)
    return tbl, inst_tbl
```
> `astroquery.eso` wraps classic services; for modern Phase 3/TAP, prefer TAP directly for bulk/typed queries.

### C. Request Handler (direct download by ID list)
- Build a list of **dataset IDs** (DPIDs for Phase 3, or file IDs for raw). Post to handler, receive a ZIP link or staged bundle.

---

## 5) Provenance musts (Atlas rules)
Record for every ESO fetch:
- **instrument**, **arm** (if applicable), **mode** (e.g., slit width), **resolution R**.
- **program ID** (e.g., 0102.B-XXXX), **PI**, **target**, **obs date/time**.
- **pipeline/calib version**, **air/vacuum flag**, **barycentric correction state**.
- **data rights**: proprietary vs public; **release date** if applicable.
- **DOI** or Phase 3 collection citation when provided.

All of the above goes into our **provenance manifest**, attached to exported CSV/PNG via the app’s “Export what I see.”

---

## 6) Quality, calibration, and caveats
- **Tellurics**: ground-based NIR/VIS can show strong atmospheric features; ESO pipelines may supply telluric standard products.
- **Barycentric correction**: not always applied; check headers (`BARYCORR`, `SPECSYS`).
- **Air vs vacuum**: UVES/X-Shooter VIS spectra often in **air wavelengths**. Convert consistently to our **canonical nm baseline** only once.
- **Order merging** (echelle): blaze residuals possible. Prefer Phase 3 merged products unless raw+DIY reduction is intended.
- **MUSE**: spaxel sampling, LSF variations across FOV; when extracting 1D spectra from cubes, record your aperture method in provenance.

---

## 7) TAP/ObsCore example (skeleton)
```python
import requests

TAP = "https://archive.eso.org/tap_obs/sync"
ADQL = """
SELECT TOP 200 * FROM ivoa.obscore
WHERE CONTAINS(POINT('ICRS', s_ra, s_dec),
               CIRCLE('ICRS', 88.7929, 7.4071, 0.02)) = 1
AND instrument_name LIKE 'X-SHOOTER%'
AND dataproduct_type = 'spectrum'
"""
r = requests.post(TAP, data={'QUERY': ADQL, 'LANG': 'ADQL', 'FORMAT': 'json'})
rows = r.json()['data'] if r.ok else []
# Each row may include access_url/access_format/obs_publisher_did, etc.
```

---

## 8) X-Shooter & UVES specifics (Spectra App notes)
- **X-Shooter**: combine UVB/VIS/NIR segments with consistent **unit resolution**; log per‑arm coverage in nm; mark any gaps. Guard against double resampling.
- **UVES**: if reduced spectra include per‑order tables, merge with blaze/continuum handling; keep **error arrays** aligned. Capture `CD1_1`/`CDELT1` vs log‑lambda conventions.

---

## 9) Integration checklist (UI + server)
- Add `fetchers/eso_fetcher.py` with:
  - `search(target | ra_dec | cone, instrument, dataproduct)` → returns minimal **UnifiedSpectrumMeta** rows.
  - `fetch(meta_row)` → downloads file, parses FITS to **UnifiedSpectrum** (wl, flux, err, unit), sets **air/vacuum** flag.
- UI “Fetch Data” panel:
  - Input: target text, resolver toggle (SIMBAD), instrument multiselect, radius, date range.
  - Results grid with **instrument**, **DPID**, **R**, **coverage (nm)**, **public/proprietary**.
  - Buttons: **Preview**, **Add to session**, **Export manifest**.
- Provenance drawer:
  - Append ESO block (fields above) and **DOI/program citation** when present.

---

## 10) Common pitfalls we’ve seen (don’t repeat them)
- Trusting FITS units without enforcing the app’s **nm baseline**. Always normalize once, then toggle view-only units.
- Dropping error arrays during resampling. Keep `ivar` or `err` alongside flux; resample consistently.
- Confusing instrument product flavors (e.g., MUSE cubes vs extracted 1D). Do not pretend a cube is a spectrum.
- Overfetching: TAP queries that return thousands of rows. Always page and prefilter by instrument + product type.

---

## 11) Minimal test plan
- UVES: fetch a public high‑res stellar spectrum; verify **air→vac** conversion and R metadata captured.
- X‑Shooter: fetch a three‑arm spectrum; verify joined coverage and consistent units.
- MUSE: fetch a cube, extract a central 1D spectrum for preview; record extraction aperture in provenance.
- Export: confirm “Export what I see” writes CSV + PNG + manifest with **ESO‑specific fields**.

---

## 12) Skeleton parser (very high level)
```python
from astropy.io import fits
import numpy as np

def parse_eso_spectrum(path):
    hdul = fits.open(path)
    # Heuristics: table extension may be 1, or data in primary for some products
    for hdu in hdul:
        if hasattr(hdu, "data") and hdu.data is not None:
            cols = getattr(hdu, "columns", None)
            if cols and all(k in cols.names for k in ("WAVE", "FLUX")):
                wl = np.asarray(hdu.data["WAVE"], dtype=float)  # unit in header
                fx = np.asarray(hdu.data["FLUX"], dtype=float)
                er = np.asarray(hdu.data["ERR"], dtype=float) if "ERR" in cols.names else None
                hdr = hdu.header
                return wl, fx, er, dict(hdr)
    # Fallbacks omitted for brevity
    raise ValueError("No recognizable ESO spectral table in FITS")
```

---

## 13) Citations & credit
Follow ESO archival data policy. Include **program ID**, **PI**, and any **Phase 3 citation** specified in product headers or portal pages. Add survey DOIs when provided.

---

## 14) Where this plugs into Atlas
This file complements 08b (MAST) and 08c/08d (SIMBAD/SDSS). Use SIMBAD to resolve names, query ESO via TAP/astroquery, and normalize units per our app’s canonical rules. Track provenance obsessively so future you doesn’t hate current you.
