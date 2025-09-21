# 06_VERSIONING_SPEC (v1.1.4x)

- `app/version.json` is authoritative.
- Badge reads it at runtime; never hardcode.
- Docs and brains files include the same version prefix (v1.1.4x).
- Patch notes: one file per patch under `docs/patch_notes/` with UTC time.
