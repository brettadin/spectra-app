# Brains — v1.1.5f
_Last updated (UTC): 2025-09-23T12:00:00Z_

## Purpose
This entry records the **Spectra App v1.1.5f** release. The focus is to stop
merge-conflict markers from ever shipping by enforcing repository checks and to
propagate the guardrails through the continuity documents.

## Canonical Continuity Sources
- `docs/brains/brains_v1.1.5f.md` (this document)
- `docs/brains/brains_INDEX.md` (version matrix)
- `docs/brains/ai_handoff.md` (handoff bridge)
- `docs/PATCH_NOTES/v1.1.5f.txt` (paired patch notes)
- `tests/test_continuity.py`, `PATCHLOG.txt`, `app/version.json`

## Non-Breakable Invariants
1. **No conflict markers** — The repository must never contain `<<<<<<<`/`>>>>>>>`
   segments. `test_repository_has_no_merge_conflict_markers` is the enforcement
   point and may not be removed or bypassed.
2. **Continuity alignment** — Version metadata (`app/version.json`), patch notes,
   brains index/logs, and the AI handoff bridge must point to the same semantic
   version.
3. **Append-only logs** — Patch logs and brains entries stay append-only; do not
   rewrite historical context when adding new guards or documentation.

## v1.1.5f Scope
- Added `test_repository_has_no_merge_conflict_markers` to fail CI when merge
  conflict markers appear anywhere in the tracked tree.
- Advanced `PATCHLOG.txt`, the brains index, and patch notes to document the new
  safeguard alongside the version metadata update.

## Implementation Notes
- The test walks the repository, skipping `.git`, cache directories, generated
  exports, and obvious binary formats while scanning UTF-8 text for conflict
  markers. Any hit aborts the test suite with a clear message.
- Continuity artifacts were bumped to v1.1.5f with aligned timestamps and
  summaries. No runtime code paths were modified beyond the new guard.

## Verification
- `pytest`

## Follow-up
- Extend repository hygiene checks to cover stray large binary files or
  accidental credential commits.
- Consider wiring the conflict-marker scan into local pre-commit tooling for
  faster feedback outside CI.
