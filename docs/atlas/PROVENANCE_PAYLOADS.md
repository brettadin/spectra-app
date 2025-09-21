# PROVENANCE_PAYLOADS (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:51:22Z  
**Author:** v1.1.4

**Goal:** each fetcher returns a data object + a provenance dict with uniform keys.

### Common keys
- `source` — e.g., `MAST`, `SIMBAD`, `ESO`.
- `query` — dict of the user query parameters.
- `ids` — list of relevant identifiers (target name, mission IDs).
- `doi` — canonical citation DOI if applicable.
- `url` — landing or API URL used.
- `fetched_at` — UTC ISO timestamp.
- `notes` — optional text, e.g., “normalized to vacuum wavelengths.”

### Example (MAST stub)
```python
def fetch_from_mast(target: str):
    spectrum = {"wavelength_nm": [...], "flux": [...]}  # normalized
    prov = {
        "source": "MAST",
        "query": {"target": target},
        "ids": ["Vega"],
        "doi": None,
        "url": "https://mast.stsci.edu/api/...",
        "fetched_at": "2025-09-20T00:00:00Z",
        "notes": "demo payload"
    }
    return spectrum, prov
```
