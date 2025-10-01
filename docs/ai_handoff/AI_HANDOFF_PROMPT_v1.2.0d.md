# AI Handoff Prompt — v1.2.0d

## Snapshot
- Version: v1.2.0d (REF 1.2.0d-A01)
- Focus: Ensure the Docs tab banner mirrors live patch metadata and add coverage so future releases stay aligned.

## Completed in this patch
1. `_render_docs_tab` now receives `version_info` from the entrypoint and renders the `patch_raw` line (or summary fallback) produced by `_resolve_patch_metadata`.
2. Added `tests/ui/test_docs_tab.py` to lock the banner against `_resolve_patch_metadata` output using a patched Streamlit environment.
3. Bumped `app/version.json` to v1.2.0d and refreshed `PATCHLOG.txt`, patch notes (md/txt), brains, and the AI activity log.

## Outstanding priorities
- Continue the v1.2 backlog: SIMBAD resolver integration, ingestion refactors, and provenance enrichment noted in prior brains/handoff docs.
- Restore documentation search tooling so the required RAG workflow becomes automated (faiss/sentence-transformers currently missing in the environment).
- Expand Docs tab coverage with end-to-end smoke tests that render real markdown entries once the library grows.

## Suggested next steps
- Re-run the documentation search server setup (install `faiss`, `sentence-transformers`) to satisfy the AGENTS.md search requirement.
- Audit other UI banners/tooltips that still embed static version strings and migrate them to `_resolve_patch_metadata` helpers.
- Pair the new regression test with a contract test that ensures downloads/last-updated captions continue to render for real docs.
