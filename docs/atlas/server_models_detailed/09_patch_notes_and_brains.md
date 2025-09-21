**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 09 - PATCH NOTES & BRAINS (Server)
This file is designed to be appended to `docs/brains/` or `docs/patch_notes/` when server patches are applied. Include both formal patch notes and an informal 'brains' note for future AI readers.

## Patch notes template
- Version: vX.Y.Z
- Date (UTC):
- Summary:
- Added:
- Changed:
- Fixed:
- Known Issues:
- Verification steps:

## Brains note (example)
Use plain language. Example:
- "We added a server-side provenance merger to centralize provenance. The UI should call utils.write_provenance which delegates to this module. If you change the shape of the manifest, update the shim and the UI drawer."

## Commit & tagging policy
- Tag hotfixes as `v1.1.4c{#}` and include brief rationale in commit message.
- Always attach the patch zip containing changed files in the release artifacts.
