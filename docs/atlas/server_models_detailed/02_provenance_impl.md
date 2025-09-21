**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 02 - PROVENANCE IMPLEMENTATION (Deep)
This file details both the shim and the server merge, edge-cases, and audit expectations.

## Shim: `app/utils/provenance.py`
**Goal:** import-safe, zero side-effects at import time, minimal logic.
Reference implementation (copy into file):
```python
try:
    from app.server.provenance import merge_trace_provenance as _merge
except Exception:
    _merge = None

def write_provenance(manifest: dict, trace_id: str, prov: dict) -> dict:
    if _merge is not None:
        return _merge(manifest, trace_id, prov)
    traces = manifest.setdefault('traces', {})
    entry = traces.setdefault(trace_id, {})
    entry.setdefault('fetch_provenance', {}).update(prov or {})
    return manifest

append_provenance = write_provenance
```
### Crucial rules
- No module-level logging, no raw file IO at import time.
- Always tolerate `manifest` being None.
- Keep the shim tiny; server must do heavy lifting.

## Server merge: `app/server/provenance.py`
### API
`merge_trace_provenance(manifest: dict, trace_id: str, prov: dict) -> dict`

### Contract & behavior
- Ensure `manifest` is a dict. If None, initialize to `{}`.
- Guarantee `manifest['session']` exists and has `started` and `last_updated` timestamps in UTC ISO8601.
- Ensure `manifest['traces']` is a dict.
- The trace entry: `manifest['traces'][trace_id]['fetch_provenance']` is updated (shallow merge) — keys in incoming `prov` overwrite existing keys if present, except for nested merges of `query` and `ids` where a union or authoritative overwrite policy should be chosen (prefer overwrite unless explicit merge field set).
- Update `manifest['session']['last_updated']` to now.
- Return the mutated manifest (allow in-place updates).

### Validation & errors
- If `trace_id` is missing or not a str, raise `ValueError('invalid trace id')`.
- If `prov` is not a dict, raise `ValueError('prov must be dict')`.
- Never let exceptions propagate beyond the function in production UI calls: UI handler must wrap calls and surface human-readable messages.

### Idempotency & concurrency
- Merge engine should be idempotent for identical prov payloads.
- If concurrent merges possible (multi-thread or external API), consider optimistic locking by including a `version` or `fetched_at` check, but for now ensure last-write-wins with timestamps recorded.

## Provenance schema (recommended)
```
manifest: {
  session: { started:str, last_updated:str },
  traces: {
     trace_id: {
         fetch_provenance: { source, query, ids, doi, url, fetched_at, notes, ... },
         derived: {...}   # optional derived products
     }
  }
}
```

## Export & display
- UI drawer should present the `fetch_provenance` object for the selected trace.
- Add an "Export manifest" button that dumps the entire `manifest` as JSON with a filename `provenance_<iso>.json`.
