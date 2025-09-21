# PATCH_NOTES_v1.1.4
Date (UTC): 2025-09-19T23:43:59Z

## Added
- v1.1.4 scaffolding for modular data fetching: `app/server/fetchers/` (MAST, SIMBAD, ESO stubs), `fetch_archives.py` router.
- Unified spectrum model (`app/server/models.py`) and provenance merger (`app/server/provenance.py`).

## Changed
- `app/version.json` bumped to v1.1.4.

## Fixed
- Documentation alignment for v1.1.4; extended UI contract (to be enforced in verifier).

## Known Issues
- Fetchers are stubs pending astroquery/requests wiring and archive parsing.
- UI integration points for a “Fetch Data” section exist in plan; actual UI wiring will be applied in subsequent patch steps within v1.1.4.

## Verification
- Run: `RUN_CMDS/Verify-Project.ps1` then start the app. No behavioral regressions should occur from adding server-side modules.
