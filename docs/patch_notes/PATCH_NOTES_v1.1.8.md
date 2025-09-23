# Patch Notes — v1.1.8
_Last updated: 2025-09-23T00:00:00Z_

## Scope
v1.1.8 resolves the noisy warnings that appeared after the combined-provider release. The UI now emits timezone-aware UTC stamps and ESO/DOI FITS ingest no longer floods logs with `UnitsWarning` when fallback `BUNIT` strings are used. Continuity artefacts advance to the v1.1.8 release metadata.

## Highlights
- UI timestamps: `app/ui/main.py` replaces `datetime.utcfromtimestamp()` with timezone-aware `datetime.fromtimestamp(..., tz=timezone.utc)` and normalises output so ISO strings still end with `Z` / `%Y-%m-%d %H:%M UTC`.
- FITS unit parsing: `app/server/fetchers/eso.py` and `app/server/fetchers/doi.py` gain `_resolve_flux_unit()` helpers that suppress `astropy.units.UnitsWarning`, surface a canonical fallback label, and keep raising on unknown units.
- Continuity refresh: `app/version.json`, brains, patch notes (md + txt), AI handoff, brains index, and `PATCHLOG.txt` all cite **REF 1.1.8-A01**.

## Implementation Sketch
1. Update `app/ui/main.py` to call `datetime.fromtimestamp(..., tz=timezone.utc)` for differential overlay metadata and docs tab provenance stamps; strip `+00:00` to keep `Z` suffices and retain the `%Y-%m-%d %H:%M UTC` format.
2. Introduce `_FALLBACK_FLUX_UNIT_LABEL`/`_FALLBACK_FLUX_UNIT` plus `_resolve_flux_unit()` in ESO/DOI fetchers; wrap `u.Unit(...)` calls with a `UnitsWarning` filter, reuse the parsed unit for flux and uncertainty arrays, and store the canonical fallback label in `units_original`.
3. Bump `app/version.json` to `v1.1.8`, append the new entry in `PATCHLOG.txt`, publish `brains_v1.1.8.md`, `PATCH_NOTES_v1.1.8.md`, `v1.1.8.txt`, update the AI handoff bridge/prompt, and refresh `brains_INDEX.md`.

## Verification
- Automated: `pytest` (full suite) to ensure ingest math and UI plumbing continue to pass.
- Manual: Launch Streamlit, open the Docs tab after loading overlays—observe no `DeprecationWarning`. Fetch an ESO or DOI spectrum without a `BUNIT` header to confirm the console stays quiet and provenance still shows the fallback label.

## References
- Brains entry: [docs/brains/brains_v1.1.8.md](../brains/brains_v1.1.8.md)
- Patch summary (txt): [docs/PATCH_NOTES/v1.1.8.txt](../PATCH_NOTES/v1.1.8.txt)
- AI handoff prompt: [docs/ai_handoff/AI Handoff Prompt — v1.1.8.txt](../ai_handoff/AI%20Handoff%20Prompt%20—%20v1.1.8.txt)
- REF: 1.1.8-A01
