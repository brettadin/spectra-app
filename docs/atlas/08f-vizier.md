# Atlas 08f — VizieR Service

## Overview
VizieR is a massive astronomical catalog service operated by CDS (Centre de Données astronomiques de Strasbourg).  
It provides access to **20,000+ astronomical catalogs**, ranging from stellar properties, variable star databases, survey photometry (e.g., SDSS, Gaia, 2MASS), exoplanet tables, and mission-specific catalogs.

In the Atlas workflow, VizieR complements SIMBAD and MAST by providing **structured, tabular data** about objects or populations, whereas SIMBAD focuses on cross-identifications and bibliographic data, and MAST specializes in mission archives.

---

## Why It Matters
- Enables retrieval of **photometric data across many bands** (useful for SED building).  
- Provides **survey catalogs** (Gaia DR3, 2MASS, Pan-STARRS, etc.).  
- Facilitates **bulk queries** (e.g., all stars in a region, all exoplanet hosts with properties).  
- Can be cross-matched with SIMBAD and MAST for richer provenance.

---

## Access Methods
### 1. Web Interface
- Base: [http://vizier.u-strasbg.fr/](http://vizier.u-strasbg.fr/)  
- Provides catalog browsing, advanced query forms, cone search (RA, Dec, radius).

### 2. Programmatic (Astroquery)
Astroquery has a `vizier` module:

```python
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

# Example: Query Gaia DR3 for a 2 arcmin region around Betelgeuse
coord = SkyCoord.from_name("Betelgeuse")
viz = Vizier(columns=["RA_ICRS", "DE_ICRS", "Gmag"])
result = viz.query_region(coord, radius=2*u.arcmin, catalog="I/355/gaiadr3")

print(result[0][:5])  # Show first 5 entries
```

Features:
- Query by catalog ID (e.g., `I/355/gaiadr3` for Gaia DR3).  
- Search by object position (cone search).  
- Control columns returned.  
- Filter by magnitude, error, etc.

### 3. VO (Virtual Observatory) Protocols
- Supports TAP (Table Access Protocol) and cone search.  
- Can be accessed through tools like TOPCAT or `pyvo`.

---

## Example Use Cases in Our Atlas
1. **Cross-matching with Spectra**  
   - Use VizieR to pull Gaia magnitudes for stars we have spectra for.  
   - Compare observed flux vs. catalog magnitudes → calibration check.

2. **Building SEDs (Spectral Energy Distributions)**  
   - Fetch photometry across multiple catalogs (2MASS, Pan-STARRS, GALEX).  
   - Overlay with spectra to validate continuum.

3. **Exoplanet Hosts**  
   - Use VizieR to query exoplanet catalogs (e.g., ExoCat, NASA Exoplanet Archive mirrored tables).  
   - Combine with MAST for transmission spectra.

4. **Bulk Population Studies**  
   - Query all stars in a cluster region (e.g., Pleiades).  
   - Retrieve their photometry, proper motions (Gaia), etc.

---

## Strengths
- Huge variety of catalogs, often the **definitive source**.  
- Robust cross-identifiers (integrates with SIMBAD).  
- Astroquery makes it accessible from Python.  
- High stability and longevity (core CDS service).

## Weaknesses
- Catalog IDs are opaque (`I/355/gaiadr3`, `II/246/out`), need lookup.  
- Queries can time out for very large datasets.  
- Photometric systems vary — must unify zeropoints.  
- Results can be dense (dozens of tables for some catalogs).

---

## Skeleton Integration (for later implementation)
```python
# app/server/fetchers/fetch_vizier.py

from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

def fetch_vizier_catalog(target: str, catalog: str, radius_arcmin: float = 1.0):
    """
    Fetch data from Vizier around a target.

    Args:
        target: object name (resolved by SIMBAD)
        catalog: Vizier catalog ID (e.g., 'I/355/gaiadr3')
        radius_arcmin: search radius

    Returns:
        astropy.table.Table or None
    """
    coord = SkyCoord.from_name(target)
    viz = Vizier(columns=["*"])
    result = viz.query_region(coord, radius=radius_arcmin*u.arcmin, catalog=catalog)
    return result[0] if result else None
```

---

## Future Work
- Build **catalog resolver**: accept human-friendly names (“Gaia DR3”) and resolve to VizieR ID.  
- Add **cross-match utility** with SIMBAD object IDs.  
- Normalize **photometry units and bands** across catalogs.  
- Develop **caching layer** to avoid repeated queries.  
- Integrate into UI as “Fetch photometry / catalogs” panel.  

---

✅ This becomes **08f – VizieR Service** in the Atlas.
