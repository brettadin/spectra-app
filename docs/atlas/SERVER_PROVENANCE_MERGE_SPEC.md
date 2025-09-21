# SERVER_PROVENANCE_MERGE_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:51:22Z  
**Author:** v1.1.4

**File:** `app/server/provenance.py`

### Required API
- `merge_trace_provenance(manifest: dict, trace_id: str, prov: dict) -> dict`

### Responsibilities
- Validate inputs (types, required keys).
- Initialize manifest structure if missing: `{ 'session': {...}, 'traces': {} }`.
- Merge provenance into `traces[trace_id]['fetch_provenance']`.
- Record a `last_updated` UTC timestamp.

### Minimal schema
```json
{
  "session": {
    "started": "2025-09-20T00:00:00Z",
    "last_updated": "2025-09-20T00:05:00Z"
  },
  "traces": {
    "abc123": {
      "fetch_provenance": {
        "source": "MAST",
        "query": {"target": "Vega", "instrument": "STIS"},
        "doi": "doi:10.xxxx/yyy",
        "fetched_at": "2025-09-20T00:01:00Z"
      }
    }
  }
}
```

### Reference implementation (pseudocode)
```python
from datetime import datetime, timezone

def merge_trace_provenance(manifest: dict, trace_id: str, prov: dict) -> dict:
    if manifest is None:
        manifest = {}
    session = manifest.setdefault("session", {})
    session.setdefault("started", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    traces = manifest.setdefault("traces", {})
    entry = traces.setdefault(trace_id, {})
    fp = entry.setdefault("fetch_provenance", {})
    if prov:
        fp.update(prov)
    session["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return manifest
```
