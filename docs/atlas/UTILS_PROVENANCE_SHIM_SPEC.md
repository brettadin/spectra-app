# UTILS_PROVENANCE_SHIM_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:51:22Z  
**Author:** v1.1.4

**File:** `app/utils/provenance.py`

### Required API
- `write_provenance(manifest: dict, trace_id: str, prov: dict) -> dict`
- Optional compatibility alias: `append_provenance = write_provenance`

### Behavior
- Try to import `merge_trace_provenance` from `app.server.provenance`.
- If import succeeds, delegate and return the result.
- If it fails (module missing, import error), do a minimal safe in-place merge:
  - Ensure `manifest['traces'][trace_id]['fetch_provenance']` exists.
  - Update it with `prov or {}`.
- Absolutely **no** escaped triple quotes, f-string garbage, or logging side effects.

### Reference implementation (correct, copy-safe)
```python
# Provenance shim (v1.1.4x): legacy import path, minimal logic.
try:
    from app.server.provenance import merge_trace_provenance as _merge
except Exception:
    _merge = None

def write_provenance(manifest: dict, trace_id: str, prov: dict) -> dict:
    if _merge is not None:
        return _merge(manifest, trace_id, prov)
    traces = manifest.setdefault("traces", {})
    entry = traces.setdefault(trace_id, {})
    entry.setdefault("fetch_provenance", {}).update(prov or {})
    return manifest

# Compatibility alias for older callers
append_provenance = write_provenance
```
