Brains — v1.1.7 # MAKE NEW BRAINS EACH TIME YOU MAKE A CHANGE. DO NOT OVER WRITE PREVIOUS BRAINS


Last updated (UTC): 2025-09-22
Purpose

v1.1.7 evolves the Spectra App by introducing a meta‑archive search and setting the stage for dynamic star‑name resolution. The goal of this patch is to reduce reliance on hard‑coded catalogues by aggregating queries across MAST, ESO and SDSS providers and presenting results to the user in a single tab. No existing overlay, differential or export behaviours should break.
Canonical Continuity Sources

    docs/brains/brains_v1.1.7.md (this file)

    docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.7.md (handoff instructions)

    docs/patch_notes/PATCH_NOTES_v1.1.7.md (implementation details)

    docs/PATCH_NOTES/v1.1.7.txt (summary)

    app/version.json must read "v1.1.7" and propagate into exports

    The existing brains, AI handoff and patch notes for v1.1.6b remain valid; carry forward non‑breakable invariants.

Non‑Breakable Invariants

The invariants established in v1.1.6b still apply:

    Overlay, differential and export flows continue to operate correctly. The new provider must produce ProviderHit objects that integrate seamlessly with the dedupe ledger and differential math. Unit conversions remain idempotent around the canonical nm baseline.

    Provenance: every fetched trace records archive name, access URL, DOI, citation and SHA‑256 hashes. The combined provider must merge provenance from each underlying provider without loss.

    Duplicate guard: adding multiple hits from different providers for the same physical target should not multiply labels unless the user explicitly ingests duplicates. The ledger keys off the file hash and archive identifiers.

    Continuity docs: cross‑links between brains, patch notes and AI handoff prompts must stay synchronized.

Current State Summary (pre‑v1.1.7)

    Each provider (MAST, ESO, SDSS) exposes a search() that matches against a fixed catalogue of targets or spectra. Providers normalise wavelengths to nm and attach provenance metadata.

    The archive UI displays a tab per provider plus a DOI resolver. Users must run separate searches to interrogate each archive.

    There is no dynamic name resolver; the SIMBAD fetcher is a stub returning empty arrays
    GitHub
    .

v1.1.7 Scope

Goal: Provide a unified “All Archives” search and prepare for arbitrary target resolution.

    Implement a combined provider that loops through MAST, ESO and SDSS searches and concatenates results.

    Register the new provider under the identifier ALL and expose a human‑readable label in provider listings.

    Update the archive UI to add an “All Archives” tab that uses the existing search form (target, instrument, limit) and calls the combined provider.

    Leave DOI resolution unchanged; it remains its own tab.

    Do not change the underlying curated target lists in this patch; focus on plumbing and UI. The next patch will enhance simbad.py to resolve arbitrary star names via the CDS Sesame service.

Architecture Decisions

    Meta‑provider design: Rather than modifying each provider to handle dynamic resolution, a dedicated combined provider aggregates results. This isolates cross‑archive behaviour and avoids coupling providers together. It also allows incremental adoption; new providers can register themselves without changing the combined provider’s interface.

    Lazy import: To avoid circular imports, the provider registry uses None as a placeholder for ALL and loads combined on demand via a lazy import. This pattern keeps module load time low.

    UI integration: The archive UI enumerates providers explicitly; we include ALL at the top of the tuple so the tab order is All Archives, MAST, ESO, SDSS, DOI.

    Error handling: The combined provider captures exceptions from individual providers and continues. This ensures a network failure or missing target in one archive does not abort the entire search.

    Future star resolver: The SIMBAD fetcher stub must be replaced with a real resolver that queries the CDS Sesame service for RA/DEC given a name and returns metadata. The combined provider will call this resolver when no curated matches exist.

Implementation Summary (REF 1.1.7-A01)

    Implemented `app/providers/combined.py` to iterate across MAST, ESO and SDSS providers, logging and skipping individual failures so aggregated searches continue.

    Updated `app/providers/__init__.py` with a lazily imported `ALL` entry and surfaced the "All Archives" label for UI consumers.

    Extended `app/archive_ui.py` to include the "All Archives" tab ahead of the individual archives, reuse the standard search form and dispatch `provider_search("ALL", query)`.

    Added regression tests covering combined provider aggregation/error handling (`tests/providers/test_combined_provider.py`) and Streamlit tab/search wiring (`tests/ui/test_archive_ui.py`).

    Refreshed continuity collateral: brains index, patch notes (Markdown + txt), AI handoff bridge, `PATCHLOG.txt`, and `app/version.json` now point to v1.1.7.

Verification

    Automated: `pytest` covers the new provider and UI behaviour (see `tests/providers/test_combined_provider.py` and `tests/ui/test_archive_ui.py`).

    Manual: Streamlit smoke test recommended — load the Archive tab, ensure "All Archives" appears first, run a Vega search, and confirm hits from multiple providers appear with intact provenance and overlay actions.

Data Model Impact

The data model defined in v1.1.6 remains unchanged. ProviderHit and ProviderQuery classes continue to carry wavelength arrays, flux arrays, metadata and provenance. The combined provider simply yields more ProviderHit instances. Future work will extend the model to include RA/DEC metadata resolved via SIMBAD.
Follow‑Up Considerations

    SIMBAD resolution (REF 1.1.7‑A01): Expand app/server/fetchers/simbad.py to query https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/<target> and parse RA/DEC. Incorporate results into ProviderHit.meta for cross‑matching.

    Instrument and wavelength filters: Add UI controls to filter aggregated hits by instrument label and wavelength range. This may require exposing effective ranges in the summary tables.

    Performance: Explore concurrency (e.g. asyncio.gather) to fetch provider results in parallel. Evaluate caching using st.cache_data for repeated queries.

    Index update: After finalizing the patch, update docs/brains/brains_INDEX.md to include the v1.1.7 row and link to the new continuity documents.

