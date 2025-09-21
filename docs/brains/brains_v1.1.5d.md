# Brains — v1.1.5d
_Last updated (UTC): 2025-09-22T00:00:00Z_

## Purpose
This log records the corrective maintenance for **Spectra App v1.1.5d**. The
focus is on restoring export functionality after missing imports slipped into
v1.1.5c and aligning the in-app documentation tab with the newly rebuilt
Spectra Atlas pages.

## Canonical Continuity Sources
- `docs/brains/brains_v1.1.5d.md` (this document)
- `docs/brains/brains_INDEX.md` (continuity table)
- `docs/brains/ai_handoff.md` (AI guardrails)
- `docs/PATCH_NOTES/v1.1.5d.txt` (paired notes)
- `app/export_manifest.py`, `app/ui/main.py`, `app/utils/duplicate_ledger.py`
  (modules modified in this patch)

## Non-Breakable Invariants
1. **Export provenance** — Every export manifest must include a UTC timestamp and
   retain per-trace provenance records. Removing `time` imports or mutating the
   manifest schema without updating the export tests is prohibited.
2. **Ledger integrity** — The duplicate upload ledger persists across sessions
   and must not raise `NameError` because of missing imports. Any future changes
   must keep the ledger thread-safe and JSON-backed.
3. **Docs discoverability** — The Docs tab must surface the Spectra Atlas pages
   with rendered markdown titles. Regression to raw code blocks or missing Atlas
   entries is not allowed.

## v1.1.5d Scope
- Import Python's `time` module in `app/export_manifest.py` so manifests can be
  timestamped again after the v1.1.5c refactor.
- Import `hashlib`, `json`, and `threading` in `app/utils/duplicate_ledger.py`
  and tidy its helpers to avoid runtime crashes when the ledger is invoked.
- Replace the Docs tab select box with Atlas-aware options that load markdown
  content instead of raw code, keeping legacy guides accessible under a separate
  category.

## Implementation Notes
- `_gather_document_options` builds the Docs tab menu by scanning
  `docs/atlas/*.md` and falling back to legacy pages that still live under
  `docs/`. `_extract_doc_title` pulls the first heading to keep titles in sync.
- Export manifest timestamps are produced via `time.strftime(..., time.gmtime())`
  so downstream automations remain UTC-consistent.
- The duplicate ledger now writes JSON with indentation for manual inspection
  while continuing to guard file access with a module-level lock.

## Verification
- `pytest`
- Manual Streamlit smoke test: load the Docs tab, verify Atlas pages render with
  markdown formatting, trigger an overlay export, and confirm manifest JSON is
  written alongside CSV/PNG outputs.

## Follow-up
- Add Streamlit integration coverage for `_gather_document_options` once a
  lightweight UI testing harness is available.
- Consider surfacing ledger statistics (entries, last write) in the duplicate
  policy sidebar to aid operators during ingestion-heavy sessions.
