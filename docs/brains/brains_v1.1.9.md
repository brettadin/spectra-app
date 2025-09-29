# Brains — v1.1.9

## Release focus
- Overlay buttons in the Target catalog now carry unique Streamlit keys and queue remote spectra for ingestion.
- Ledger lock is controlled via the `duplicate_ledger_lock` session variable; the checkbox only reflects state and no longer mutates widget keys.
- The main loop now processes `ingest_queue` items by downloading spectra and passing them through the local ingest pipeline.
- Local ingest rejects metadata-only tables (<3 samples) so overlays plotted from MAST products stay astrophysically plausible.

## Add new targets via `targets.yaml`
1. Append the target metadata to `targets.yaml`, filling in identifiers and any curated product manifests.
2. Run `python tools/build_registry.py --roster targets.yaml --out data_registry` to regenerate the catalog and per-target manifests.
3. Verify the generated `data_registry/<Target>/manifest.json` includes datasets (MAST, ESO, CARMENES) and summaries before committing.
4. Start the app and confirm the target appears in the sidebar catalog with expected summary text and overlay controls.

## Troubleshooting: `NoResultsWarning`
- **Meaning:** The catalog manifest returned zero curated products for the selected provider (MAST, ESO, or CARMENES). This is surfaced as a `NoResultsWarning` when providers respond with empty datasets.
- **Steps:**
  - Confirm the provider is live by querying it directly (e.g., run the associated fetcher script or review provider logs).
  - Inspect the target's manifest under `data_registry/<Target>/manifest.json` to ensure dataset sections populated during the registry build.
  - If only one provider is empty, add or refresh curated product lists for that provider and rebuild the registry.
  - For persistent provider outages, note the warning in release docs and advise operators to retry once services recover.

## Continuity
- Update docs/handoffs.md with the new overlay queue flow and recovery guidance.
- Refresh `CHANGELOG.md`, `PATCHLOG.txt`, and `app/version.json` for v1.1.9.
- Patch notes: `docs/PATCH_NOTES/v1.1.9.txt` and `docs/patch_notes/PATCH_NOTES_v1.1.9.md`.
