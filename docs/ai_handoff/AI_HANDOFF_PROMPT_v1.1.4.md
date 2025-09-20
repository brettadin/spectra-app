# AI Handoff Prompt — v1.1.4
_Last updated: 2025-09-19T23:43:59Z_

This is a patch-only project. Do not rewrite the app. Extend it.

## Do Not Break
Overlay, Differential, Export, unit conversions, duplicate guard. Round-trip units via canonical nm baseline.

## What to Ship in v1.1.4
- Modular fetchers under `app/server/fetchers/` with a router in `fetch_archives.py`.
- Keep fetched data indistinguishable from uploads: normalize to nm, attach full provenance, register in duplicate ledger.
- Minimal UI extension: a “Fetch Data” section that calls the router and adds traces to Overlay.
- Update `docs/brains/v1.1.4 brains.md`, `docs/patches/PATCH_NOTES_v1.1.4.md`, `app/version.json`, `CHECKSUMS.txt`.
- Extend `ui_contract.json` to include: fetch tab present, provenance in export, differential A/B persistence and epsilon guard.

## Provenance
Every fetched trace must include: archive, target, instrument, obs_id/program, DOI, access URL, citation text, fetched_at_utc, file_hash_sha256, units_original, app_version.

## Verification
Run project and UI contract verifiers; export and confirm manifest carries fetch_provenance.
