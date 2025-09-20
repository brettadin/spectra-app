# PATCH_NOTES_v1.1.4c1 — Repair Badge Syntax
Date (UTC): 2025-09-20T01:08:15.469645Z

## Summary
- Fixes a malformed injection that produced `passtry:` in `app/app_merged.py`.
- Removes any previous broken badge block and inserts a clean version-badge snippet **after imports**.

## Details
- Looks for the unique CSS marker `position:fixed;top:12px;right:28px` and replaces the whole block with a clean one.
- Also repairs accidental `passtry:` → `pass` + `try:`.
- Leaves all widget key additions from v1.1.4c intact.

## Verification
1. Apply script (ExecutionPolicy note below).
2. Start the app — no syntax error, version pill visible, UI functional.
