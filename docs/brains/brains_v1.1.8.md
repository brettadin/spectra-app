Brains — v1.1.8 # MAKE NEW BRAINS EACH TIME YOU MAKE A CHANGE. DO NOT OVER WRITE PREVIOUS BRAINS

Last updated (UTC): 2025-09-23

Purpose

v1.1.8 focuses on hardening continuity glue that started to fray after the All Archives roll-out. Two pain points surfaced in the field:

* Streamlit’s docs/provenance tab spammed `DeprecationWarning` because it still relied on `datetime.utcfromtimestamp()`, which Python 3.12 will drop.
* FITS ingest (ESO + DOI) flooded logs with `UnitsWarning` whenever fallback `BUNIT` strings contained multiple slashes.

The goal of this patch is to eliminate those regressions without touching any overlay/differential/export logic.

Canonical Continuity Sources

    docs/brains/brains_v1.1.8.md (this file)
    docs/patch_notes/PATCH_NOTES_v1.1.8.md (implementation)
    docs/PATCH_NOTES/v1.1.8.txt (summary)
    docs/ai_handoff/AI Handoff Prompt — v1.1.8.txt (guardrails)
    PATCHLOG.txt (now lists v1.1.8 · REF 1.1.8-A01)
    app/version.json → "v1.1.8" (release metadata)
    docs/brains/brains_INDEX.md (updated continuity table)

Non-Breakable Invariants

Everything locked down in v1.1.7 still stands:

* Combined provider semantics stay untouched: dedupe ledger keys, provenance payloads, overlay/differential/export flows remain intact.
* Unit conversions always pivot around the canonical `nm` baseline. Emission/absorption axes still carry explicit units.
* Provenance manifests keep archive name, DOI, citation, URL, fetch timestamp, and SHA-256 digests.
* Duplicate guard remains enforced by hash + archive identifier.

Current State Summary (pre-v1.1.8)

* Streamlit’s Docs tab used `datetime.utcfromtimestamp()` for overlay provenance and document timestamps, producing a tsunami of warnings on Python 3.11+ and risking hard failure in 3.12.
* ESO / DOI FITS fallbacks defaulted to `"erg/s/cm2/Angstrom"`. Astropy parsed it but emitted a `UnitsWarning` for each load; when combined provider enumerated multiple records the warning noise dominated the console.
* All Archives aggregation, overlay management, and export flows otherwise remained healthy per v1.1.7.

v1.1.8 Scope

REF 1.1.8-A01 — “UTC Hygiene + FITS unit quieting”:

* Replace naive UTC conversions with timezone-aware `datetime.fromtimestamp(..., tz=timezone.utc)` in `app/ui/main.py` for differential overlay manifests and docs tab metadata. Format output as ISO-8601 `Z` or `%Y-%m-%d %H:%M UTC` exactly as before.
* Wrap FITS fallback unit parsing in ESO and DOI fetchers with a helper that suppresses `astropy.units.UnitsWarning` while still validating unexpected labels. Provide a canonical fallback (`erg s^-1 cm^-2 Angstrom^-1`) so ingest stays deterministic.
* Refresh release metadata + docs: version bump, new brains / patch notes / AI handoff, index + patch log updates.

Architecture Decisions

* Timezone handling stays localized: we only touch the UI codepaths that format strings for humans, avoiding ripple effects into export manifests that already store ISO timestamps with offsets.
* Units warning suppression is achieved via `warnings.catch_warnings` targeting `UnitsWarning`, keeping visibility for truly invalid units (still raise `EsoFetchError` / `DoiFetchError`).
* Fallback unit labels now record the canonical string (`erg s^-1 cm^-2 Angstrom^-1`) so provenance metadata stays human-readable without the problematic slash notation.

Implementation Summary

* Updated `app/ui/main.py` to use timezone-aware timestamps and keep the same rendered strings (`Z` suffix / `UTC` suffix) by normalizing ISO output.
* Added `_resolve_flux_unit()` helpers plus warning suppression to `app/server/fetchers/eso.py` and `app/server/fetchers/doi.py`; both now return canonical fallback labels and reuse the parsed unit for flux + uncertainty arrays.
* Introduced `_FALLBACK_FLUX_UNIT_LABEL`/`_FALLBACK_FLUX_UNIT` constants in both fetchers for clarity.
* Bumped `app/version.json`, extended `PATCHLOG.txt`, refreshed brains index, AI bridge, patch notes (md + txt), and the handoff prompt to cite REF 1.1.8-A01.

Verification

Automated: run `pytest` (full suite) plus lint, ensuring no regressions. The unit-parsing changes remain covered by existing ingest tests; added behaviour is defensive only.

Manual: run Streamlit locally, load the Docs tab and provenance expander—confirm no `DeprecationWarning`. Ingest an ESO/DOI fallback spectrum (one lacking `BUNIT`) and verify console stays silent while provenance still reports the fallback label. Regression-check All Archives search to ensure provenance display unaffected.

Data Model Impact

No schema changes. ProviderHit payloads now record the canonical fallback label but continue to advertise the same wavelength / flux arrays and provenance metadata.

Follow-Up Considerations

* SIMBAD resolver work from v1.1.7 remains outstanding.
* Consider centralizing FITS unit parsing in a shared utility if additional providers arrive.
* Once Python 3.12 lands, audit for any remaining `utcfromtimestamp` usages (search already clean, but re-run as part of upgrade checklist).

