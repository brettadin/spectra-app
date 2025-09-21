# Atlas 08h — NED (NASA/IPAC Extragalactic Database)

## Overview
The NASA/IPAC Extragalactic Database (NED) is a comprehensive resource for extragalactic objects — galaxies, quasars, AGN, clusters.  
It functions as a cross-identification hub, literature reference index, and photometric/redshift database.  
NED does **not usually provide raw spectra** directly, but instead aggregates references and links to archives that hold the data.

---

## APIs & Services
- **Cone Search Service**: Query all objects within a sky region (RA, Dec, radius).
- **Name Resolver**: Given an object name (e.g., *M31*), resolve to precise coordinates and aliases.
- **Redshift/Velocity Data**: Returns systemic velocities, z values, references.
- **Photometric Data**: Multi-wavelength photometric measurements across catalogs.
- **Cross-ID Service**: Match identifiers across multiple catalogs (SDSS, 2MASS, etc.).
- **References API**: Retrieve associated literature entries.

---

## Data Types
- **Core Properties**: RA, Dec, z, velocity, distance estimates.
- **Cross-Identifications**: Links across other catalogs/databases.
- **Photometry**: Magnitudes and flux densities across many bands.
- **Spectroscopic References**: Literature links to spectral measurements.
- **Morphology**: Galaxy classification when available.

---

## Integration into the Spectra App
- **Use Case**: When a user uploads or requests a galaxy spectrum, the app can use NED to:
  1. Confirm object identity (cross-ID).
  2. Retrieve redshift to rest-frame shift spectra.
  3. Provide photometric context alongside the spectrum.
  4. Add literature provenance into export manifest.

- **Workflow**:  
  - Step 1: Resolve object name → coordinates.  
  - Step 2: Use cone search to confirm neighbors / duplicates.  
  - Step 3: Store redshift + velocity for later corrections.  
  - Step 4: Merge provenance logs into manifest.

---

## Example: Python Skeleton with Astroquery

```python
from astroquery.ned import Ned

# Name resolver
result_table = Ned.query_object("M87")
print(result_table)

# Position-based cone search
cone = Ned.query_region("12h30m49.4s +12d23m28s", radius=0.1)
print(cone)

# Redshift information
redshift = Ned.get_table("M87", table="redshifts")
print(redshift)
```

---

## Limitations
- Large queries may time out — batch them carefully.
- NED data is reference-based; **actual spectra are usually external**.
- Sky coverage is biased to published studies, not uniform all-sky like Gaia.

---

## Best Practices for Use
- Always store **cross-IDs** in provenance for traceability.  
- Cache frequent queries to avoid duplicate API calls.  
- For spectra: treat NED as a **pointer service** (use it to find where spectra live, then fetch via MAST, ESO, etc.).  
- Provide fallback to the **NED web interface** in exports when API coverage is incomplete.

---

## References
- [NED Home](https://ned.ipac.caltech.edu/)  
- [NED Services Overview](https://ned.ipac.caltech.edu/help/)  
- [Astroquery NED Docs](https://astroquery.readthedocs.io/en/latest/ned/ned.html)

