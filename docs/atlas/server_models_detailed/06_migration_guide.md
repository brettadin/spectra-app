**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 06 - MIGRATION & ROLLBACK GUIDE (Server)
How to evolve server models safely and roll back when CI misses something.

## Before merging
- Add unit tests covering new behavior.
- Add `upgrade_manifest` that can read both old and new manifest formats.
- Keep shims for at least 2 release cycles; don't delete compatibility helpers early.

## Rollback plan
- `git revert` the merging PR.
- If deployment already happened and users ran new code, provide a CLI tool `scripts/normalize_manifest.py --from v1.1.3 --to v1.1.4` to backfill missing fields.
- Mark any breaking changes in `CHANGELOG.md` with the `BREAKING:` prefix.

## Emergency hotfix
- If a release triggers UI blank pages due to import-time errors, replace `app_patched.py` with the strong import guard (SmartEntry) and deploy as hotfix; then iterate on server code offline.
