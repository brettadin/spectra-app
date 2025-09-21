# Data Fetching Implementation Plan

## Goal
- Replace the stubbed fetchers in `app/server/fetchers/` with real archive integrations so astronomers can retrieve spectra for bright nearby stars directly inside the app instead of relying on placeholder arrays.
- Deliver a curated starter set of targets that spans ultraviolet through mid-infrared coverage and exercises the provenance contract introduced in v1.1.4/v1.1.5a of the Spectra App docs. 【F:docs/brains/v1.1.4 brains.md†L35-L71】【F:docs/brains/brains_v1.1.5a.md†L17-L59】

## Continuity Constraints
- Returned payloads must conform to the `NormalizedSpectrum` schema (canonical wavelength in nm, harmonized flux, populated provenance metadata) so downstream overlays and exports remain stable. 【F:docs/brains/v1.1.4 brains.md†L35-L103】
- Every fetcher writes cache artifacts under the provider directory announced in v1.1.5a to preserve continuity checks and reuse downloaded FITS files. 【F:docs/brains/brains_v1.1.5a.md†L17-L51】【F:data/providers/README.md†L1-L10】
- Archive modules should rely on the official APIs linked in `docs/sources/astro_data_docs.md` and document citation-ready metadata (DOI, URL, instrument, program) inside the fetch provenance block. 【F:docs/sources/astro_data_docs.md†L9-L74】【F:docs/brains/v1.1.4 brains.md†L64-L103】

## Current State
- `mast.py`, `eso.py`, and `simbad.py` return empty arrays with metadata shells; only `nist.py` performs a real network call.
- `fetch_archives.fetch_spectrum()` already routes archive keys to these modules and surfaces errors in the Streamlit sidebar, so dropping in real implementations should not require UI changes.

## Target Sample and Coverage
| Star (spectral type) | Distance (pc) | Archive & instrument/product | Approx. wavelength coverage | Why this entry | Citation |
| --- | --- | --- | --- | --- | --- |
| Sirius A (A1 V) | 2.64 | MAST HLSP CALSPEC — HST/STIS & NICMOS merged spectrum | 115–2400 nm | Bright UV/optical calibrator to validate UV sensitivity and near-IR conversions | [^calspec]
| Vega (A0 V) | 7.68 | MAST HLSP CALSPEC — HST/STIS & NICMOS | 115–2400 nm | Second CALSPEC primary; exercises duplicate-guard logic across nearly identical provenance | [^calspec]
| Arcturus (K1.5 III) | 11.3 | ESO Phase 3 — X-shooter Spectral Library DR3 | 300–2480 nm | High S/N cool giant spectrum; checks ESO TAP workflow and near-IR stitching | [^xsl]
| Tau Ceti (G8.5 V) | 3.65 | ESO Phase 3 — HARPS reduced 1D spectra (pipeline products) | 378–691 nm at R≈115,000 | Nearby solar analogue with hundreds of precise optical spectra; validates high-resolution ingestion and radial-velocity metadata | [^harps]
| Epsilon Eridani (K2 V) | 3.22 | Spitzer IRS via CASSIS HLSP | 5–37 μm | Mid-IR coverage to extend beyond near-IR; stress-tests unit conversions and flux density handling | [^cassis]

The list mixes hot standards, cool giants, solar analogues, and mid-IR dust-rich systems so that normalization, error propagation, and provenance code paths all receive realistic coverage.

## Implementation Roadmap

### 1. SIMBAD resolver (metadata baseline)
1. Use `astroquery.simbad.Simbad` with custom fields (`RA`, `DEC`, `SP_TYPE`, parallax) to normalize target identifiers before archive queries.
2. Cache the SIMBAD table under `data/providers/simbad/` with SHA-256 hashed filenames to satisfy continuity requirements while enabling offline replays.
3. Populate `target_name`, `meta['sim_id']`, `meta['ra_deg']`, `meta['dec_deg']`, and derived distance estimates in the `fetch_provenance` block so exports record the resolver that was used. 【F:docs/brains/v1.1.4 brains.md†L35-L71】

### 2. MAST CALSPEC ingestion (UV → near-IR)
1. Query `Mast.Caom.Filtered` (or the `Observations` class in `astroquery.mast`) for `obs_collection=HLSP`, `project=CALSPEC`, and the target name; request only `dataproduct_type='spectrum'` rows.
2. Download the calibrated FITS spectra through `Observations.download_products`, persisting the original file in `data/providers/mast/{target}/{product_id}.fits`.
3. Read each FITS table with `astropy.io.fits`, convert wavelength columns to nm, and flux densities to the internal baseline (`F_lambda`) using `astropy.units`.
4. Merge overlapping STIS and NICMOS segments using the overlap-scaling rules already documented for stitching so the UI receives one combined `NormalizedSpectrum` per star.
5. Record `doi` and `access_url` from the HLSP metadata, and generate concise citation text (e.g., “Bohlin et al. 2014, AJ 147, 127, doi:10.1088/0004-6256/147/6/127”). 【F:docs/brains/v1.1.4 brains.md†L64-L88】
6. Extend `scripts/fetch_samples.py` to optionally prefetch the CALSPEC stars for smoke testing.

### 3. ESO ingestion (X-shooter & HARPS)
1. Use `astroquery.eso.Eso` TAP queries to locate Phase 3 products for the desired target and instrument (`XSHOOTER`, `HARPS`). Authentication is optional because both releases are public.
2. Download 1D spectra (typically FITS binary tables) into `data/providers/eso/{target}/` and log SHA-256 hashes.
3. For X-shooter, read the UVB, VIS, and NIR arms, convert each to nm, and resample onto a single monotonically increasing grid using flux-conserving integration. Preserve separate arm provenance in the metadata.
4. For HARPS, detect blaze-corrected 1D spectra, parse the barycentric correction keywords, and populate radial-velocity metadata (`barycorr`, `rv`) in the provenance block for downstream differential operations.
5. Attach DOI/program references from the TAP response (e.g., `harps_dr1` DOI) and compose an archive-specific citation string.

### 4. Mid-infrared coverage (Spitzer IRS via IRSA/CASSIS)
1. Add a dedicated `irsa.py` fetcher that relies on `astroquery.ipac.irsa.Irsa` (or the CASSIS API) to pull low- and high-resolution IRS spectra for the target (e.g., `HD 22049`).
2. Convert wavelength grids from μm to nm, recognize flux units (Jy) and transform to `F_lambda`, preserving uncertainty vectors when available.
3. Because CASSIS bundles multiple nods/orders, implement order-aware stitching with robust scaling and document the steps in provenance.
4. Decide whether to extend the `NormalizedSpectrum.meta['archive']` enum to include `"IRSA"`; if so, update the brains spec in a subsequent patch, otherwise treat the integration as a MAST-hosted HLSP if the dataset is mirrored there.

## Normalization, Caching, and Error Handling
- Build a shared helper that accepts a FITS HDU and returns `(wavelength_nm, flux, uncertainty)` arrays along with the original units so every fetcher enforces the canonical baseline. 【F:docs/brains/v1.1.4 brains.md†L35-L71】
- Save every raw download plus a compact JSON manifest (`provenance.json`) next to the cached file detailing the DOI, access URL, SHA-256, and extraction timestamp to simplify reprocessing runs.
- Surface user-friendly error messages (network failure, missing columns) by raising `FetchError` with actionable text; the Streamlit sidebar already reports these failures.

## Provenance & Citation Handling
- Populate the `fetch_provenance` block with archive name, instrument, program/observation IDs, access URLs, DOIs, citation text, fetch timestamp, file hashes, and unit metadata so exports remain audit-ready. 【F:docs/brains/v1.1.4 brains.md†L64-L103】
- Include resolver metadata (SIMBAD identifier, coordinate epoch) and stitching decisions (`overlap_nm`, `scale_factor`, resampling kernel) to make reproducibility explicit.

## Testing & Verification
- Extend `scripts/fetch_samples.py` to download one spectrum per provider and emit a manifest diff for regression testing.
- Add unit tests that mock archive responses and verify unit conversion, provenance population, and caching behavior for each fetcher.
- Run the existing verification scripts (`RUN_CMDS/Verify-Project.ps1`, `pytest`) plus a new end-to-end smoke test that fetches Sirius and confirms the trace appears in the overlay. 【F:docs/brains/brains_v1.1.5a.md†L56-L70】

## Open Questions & Follow-ups
- Confirm target availability in each archive (especially the XSL entry for Arcturus and IRS coverage for ε Eri) and adjust the sample if any gaps appear.
- Decide whether to bundle uncertainty vectors when archives supply them (e.g., CALSPEC includes error arrays) and update downstream plotting accordingly.
- Evaluate authentication requirements for ESO TAP scripts in CI and document credential management if needed.

## References
[^calspec]: A. D. Bohlin, M. C. Harris, C. R. Deustua, et al., “Hubble Space Telescope CALSPEC Flux Standards: Sirius (and Vega)”, *Astronomical Journal*, 147, 127 (2014), doi:10.1088/0004-6256/147/6/127.
[^xsl]: A. Arentsen, A. Lançon, M. Prugniel, et al., “Stellar atmospheric parameters for 754 spectra from the X-shooter Spectral Library”, *Astronomy & Astrophysics*, 627, A138 (2019), doi:10.1051/0004-6361/201834273.
[^harps]: ESO Science Archive, “HARPS reduced data obtained by standard ESO pipeline processing”, Phase 3 Data Release (2017), doi:10.18727/archive/33.
[^cassis]: V. Lebouteiller, J. Bernard-Salas, P. W. Morris, and C. Sloan, “The Cornell Atlas of Spitzer/IRS Sources (CASSIS)”, *Astrophysical Journal Supplement Series*, 218, 21 (2015), doi:10.1088/0067-0049/218/2/21.
