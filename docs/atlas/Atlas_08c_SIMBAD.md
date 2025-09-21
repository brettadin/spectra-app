# Atlas 08c – SIMBAD

## 1. Purpose
SIMBAD (Set of Identifications, Measurements, and Bibliography for Astronomical Data) is a comprehensive database hosted by **CDS Strasbourg**.  
It focuses on objects *beyond the Solar System* — stars, galaxies, quasars, exoplanet host stars, clusters — and integrates identifiers, bibliographic references, and basic observational measurements.  

For our Atlas, SIMBAD serves as the **central “dictionary” of celestial objects**. It lets us:
- Translate between multiple names (e.g., *Alpha Orionis*, *Betelgeuse*, *HD 39801*).
- Fetch fundamental parameters (RA, Dec, magnitudes, object types).
- Link to references and observational catalogs for deeper data.

---

## 2. Data Types in SIMBAD
- **Identifiers**: Cross-references across 13+ million objects.
- **Coordinates**: RA/Dec, Galactic, ecliptic.
- **Object classifications**: Star, variable star, galaxy, AGN, QSO, exoplanet host, etc.
- **Photometry**: Multi-band magnitudes (V, B, G, J, H, K, etc.).
- **Radial velocities & proper motions** (where available).
- **References**: Literature links, citations, bibcodes.
- **Links to external catalogs**: Vizier tables, Gaia DR3, 2MASS, SDSS, etc.

---

## 3. API Access
CDS provides:
1. **TAP (Table Access Protocol)** via `astroquery.simbad`.
2. **VOTable / XML / JSON endpoints** for programmatic queries.
3. **Web interface** for manual exploration.

---

## 4. Example Queries

### A. Basic name resolution
```python
from astroquery.simbad import Simbad

result = Simbad.query_object("Betelgeuse")
print(result)
```

### B. Multi-object queries
```python
result = Simbad.query_objects(["Betelgeuse", "Rigel", "Sirius"])
```

### C. Custom fields
```python
Simbad.add_votable_fields("flux(V)", "flux(B)", "otype", "ra(d)", "dec(d)")
```

### D. Cone search
```python
result = Simbad.query_region("Betelgeuse", radius="0d10m0s")
```

---

## 5. Strengths
- **Universal resolver**: Works with almost any identifier or catalog name.
- **Bibliography**: Direct link to ADS bibcodes.
- **Lightweight metadata**: Efficient for object cross-referencing before heavier fetches from MAST, ESO, or Vizier.
- **Integrations**: Tight coupling with Vizier → allows fast chaining.

---

## 6. Weaknesses / Pitfalls
- **Not a spectra/photometry database**. Limited data content — mainly identifiers and summary metadata.
- **Rate limits**: ~5–10 queries/sec max recommended.
- **Inconsistent object types**: Some classifications are generic (e.g., "Star" covers many subtypes).
- **Magnitudes outdated** for some objects if no recent data ingestion.

---

## 7. Atlas Integration
- Use SIMBAD as the **first stop** for resolving user input (e.g., “Vega”, “HD 172167”).
- Return canonical IDs (e.g., Gaia DR3, 2MASS) → pass into **MAST, ESO, Vizier** modules.
- Build provenance logs:
  - “User input → Resolved via SIMBAD → Retrieved canonical IDs → Forwarded to [Archive]”.

---

## 8. Skeleton Code for Our App
```python
from astroquery.simbad import Simbad

def resolve_object(name: str) -> dict:
    """
    Resolve an astronomical object using SIMBAD.
    Returns canonical identifiers, coordinates, and photometry.
    """
    Simbad.add_votable_fields("ra(d)", "dec(d)", "otype", "flux(V)", "flux(B)")
    result = Simbad.query_object(name)
    if result is None:
        return {"error": f"Object {name} not found in SIMBAD"}
    
    return {
        "name": name,
        "ra_deg": result["RA_d"][0],
        "dec_deg": result["DEC_d"][0],
        "otype": result["OTYPE"][0],
        "mag_V": result["FLUX_V"][0],
        "mag_B": result["FLUX_B"][0],
    }
```

---

## 9. Future Expansion
- Add caching (avoid repeated SIMBAD lookups).
- Implement “resolve first” workflow in the Atlas pipeline.
- Build crosswalk: SIMBAD ↔ Gaia ↔ MAST ↔ ESO.
- Track provenance: every SIMBAD query gets logged with timestamp + bibcode reference.

---

✅ This file would be saved as:  
`Atlas_08c_SIMBAD.md`
