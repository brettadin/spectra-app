# Atlas 08b -- MAST Deep Dive

## 1. What MAST Is

-   NASA's **Mikulski Archive for Space Telescopes (MAST)**.
-   Central archive for HST, Kepler, TESS, JWST, GALEX, IUE, and others.
-   Stores calibrated science-ready data and raw exposures.

------------------------------------------------------------------------

## 2. Access Methods

-   **Web portal**: https://mast.stsci.edu/\
-   **API**: MAST API (`/api/v0/invoke`), usually JSON query endpoints.\
-   **Python**: `astroquery.mast` module, integrates with Astropy
    tables.\
-   **Direct downloads**: via DOI, or through manifest `.csv`/`.fits`.

------------------------------------------------------------------------

## 3. Query Patterns

-   **By Object Name** (resolved via SIMBAD or NED under the hood).\
-   **By Coordinates** (RA/Dec, radius search).\
-   **By Mission** (HST, JWST, etc.) with filters: wavelength, date,
    instrument, proposal ID.\
-   **By DOI or Dataset ID** (absolute provenance lock).

### Example (Python Astroquery)

``` python
from astroquery.mast import Observations

# Search by target name
obs = Observations.query_object("Betelgeuse", radius="0.02 deg")

# Download science products
products = Observations.get_product_list(obs[:5])
Observations.download_products(products, download_dir="mast_data")
```

------------------------------------------------------------------------

## 4. Data Formats

-   **FITS**: primary science data + headers (instrument, calibration,
    provenance).\
-   **CSV/TSV**: catalogs, high-level data products (HLA/HLA).\
-   **VOtables**: Virtual Observatory integration.\
-   **JSON**: API responses for programmatic pipelines.

------------------------------------------------------------------------

## 5. Provenance & Metadata

Each dataset has: - DOI (persistent link).\
- Proposal ID (linked to PI, papers).\
- Instrument + detector details.\
- Pipeline calibration version.

Provenance tree: `raw → calibrated → high-level science product`.

------------------------------------------------------------------------

## 6. Best Practices

-   Always request **only calibrated data** unless explicitly testing
    reduction.\
-   Use **DOI links** in exports to preserve reproducibility.\
-   Keep a **manifest** per fetch session:
    -   query used,\
    -   date/time,\
    -   app version,\
    -   dataset IDs.

------------------------------------------------------------------------

## 7. Known Issues

-   Queries can return **thousands of rows**; paging required.\
-   Large downloads need token-based authentication.\
-   Some JWST datasets are proprietary until release date.

------------------------------------------------------------------------

## 8. How This Ties Into Spectra App

Our **Fetch tab** should: - Wrap `astroquery.mast`.\
- Provide filters: object, radius, instrument, mission.\
- Show **preview plots** (spectrum, lightcurve if available).\
- Record DOI + query → export into provenance manifest.
