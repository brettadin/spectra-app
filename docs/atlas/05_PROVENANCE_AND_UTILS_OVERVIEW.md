# 05_PROVENANCE_AND_UTILS_OVERVIEW (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:51:22Z  
**Author:** v1.1.4

Purpose: define how provenance is recorded, merged, and exposed so we can audit every pixel on screen without spelunking through stack traces.

**Golden rule:** client-side `app/utils/provenance.py` is a *shim only*. All real work happens in `app/server/provenance.py`.

---

## Components
- `app/utils/provenance.py` — legacy import compatibility and tiny helpers. No business logic.
- `app/server/provenance.py` — merge engine. Knows how to attach trace-level provenance into a session manifest.
- `app/server/models.py` — Spectrum model that carries units and pointers to provenance entries.
- `app/server/fetch_archives.py` and `app/server/fetchers/*` — produce provenance payloads for archives.

## Data flow
1) Panel or fetch routine calls the **shim**: `write_provenance(manifest, trace_id, prov)`.
2) Shim delegates to server merger `merge_trace_provenance` if available, else performs a minimal in-place update.
3) UI can surface the updated manifest under a drawer.

## Why this separation
- Avoid circular imports between UI, utils, and server.
- Keep all mutation logic in one place (server), so we don’t get N slightly-different provenance structures.
- Make it safe to import utils anywhere without side effects.
