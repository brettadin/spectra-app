# Developer Notes — Spectra App

This project enforces patch-only development. Every change must be recorded in `PATCHLOG.txt` with:
- Version (increment patch only, e.g., v1.1.2 → v1.1.3)
- Date (UTC)
- Summary of changes
- Known issues
- Next planned steps

**Rules for future AI devs:**
- Do not overwrite PATCHLOG.txt — always append.
- If delivering a patch bundle, include an updated PATCHLOG.txt in the correct location.
- Keep run instructions in `RUN-LOCAL.txt` and `RUN-BUILD.txt` up to date if anything changes.
- Every patch should regenerate `CHECKSUMS.txt`.

Last maintained: 2025-09-19 20:15:00Z
