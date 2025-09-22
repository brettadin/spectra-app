# MAKE NEW BRAINS EACH TIME YOU MAKE A CHANGE. DO NOT OVER WRITE PREVIOUS BRAINS
# Brains — v1.1.6
_Last updated (UTC): 2025-09-22T00:00:00Z_

## Purpose
v1.1.6 removes every synthetic provider stub and replaces them with live archive-backed fetchers. SDSS, ESO, and DOI providers now download real spectra with provenance, while the CALSPEC catalog grew so the app can surface ~10 high-value stars across multiple instruments. This entry documents the data sources, cache expectations, and regression coverage introduced in the patch.

## Continuity Links
- Patch notes (txt): [docs/PATCH_NOTES/v1.1.6.txt](../PATCH_NOTES/v1.1.6.txt)
- Patch notes (md): [docs/patch_notes/PATCH_NOTES_v1.1.6.md](../patch_notes/PATCH_NOTES_v1.1.6.md)
- Brains index: [docs/brains/brains_INDEX.md](brains_INDEX.md)
- AI handoff bridge: [docs/brains/ai_handoff.md](ai_handoff.md)

## Highlights
- **New fetchers**: SDSS (DR17 BOSS spectra over HTTP), ESO PENELLOPE X-Shooter spectra (Zenodo), DOI-driven Zenodo spectra loader.
- **MAST expansion**: Added six additional CALSPEC standards (BD+17 4708, GD 71, GD 153, G191-B2B, HD 93521, Feige 110) to deliver roughly ten stellar options.
- **Provider cleanup**: ESO/SDSS/DOI providers now call their fetchers directly and build structured metadata + provenance blocks.
- **Example overlays**: Sidebar examples now execute provider lookups so the built-in spectra carry archive provenance instead of CSV stubs.
- **Regression tests**: Added pytest modules for SDSS/ESO/DOI providers to guard token matching, metadata mapping, and fetch calls.

## Implementation Notes
- Fetchers cache files beneath `data/providers/<provider>/` (now including `sdss` and `doi`). Do not delete these directories; automation asserts their presence.
- The SDSS fetcher uses HTTP (not HTTPS) endpoints because the DR17 TLS chain triggers certificate errors inside the runtime image.
- ESO/DOI fetchers parse both 3D (µm grids) and linear FITS products, normalising flux into `erg s^-1 cm^-2 nm^-1`.
- Provider search tokens include slugs, aliases, and DOIs so partial queries like `6138-56598` or `example` resolve correctly.

## Testing
Run `pytest` after modifying providers or fetchers; new tests live under `tests/providers/`.

## Follow-up Ideas
- Broaden DOI coverage beyond the two seeded Zenodo datasets.
- Consider extracting shared spectral parsing helpers into a common module to reduce duplication across fetchers.
- Wire ESO/DOI fetchers into export provenance manifests for additional audit coverage.
