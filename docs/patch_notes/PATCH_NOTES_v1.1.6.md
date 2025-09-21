# PATCH_NOTES_v1.1.6 — Live archive spectra

Date (UTC): 2025-09-22T00:00:00Z

### Added
- SDSS fetcher that downloads BOSS spectra for curated stellar plates and exposes them through the provider search.
- ESO fetcher backed by PENELLOPE X-Shooter spectra on Zenodo, including UVB and NIR arms.
- DOI fetcher/provider wiring for Zenodo-hosted spectra referenced by DOI identifiers.
- Regression tests covering SDSS, ESO, and DOI provider integrations.

### Changed
- Replaced all synthetic provider outputs with real archive-backed spectra and provenance.
- Expanded the CALSPEC target roster with additional white dwarfs and subdwarfs so MAST search offers ~10 stars.
- Updated provider cache directories and docs to track new sdss/doi caches.
- Retired synthetic example CSV overlays; sidebar examples now resolve live archive spectra with provenance.
