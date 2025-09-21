# UI_PROVENANCE_DRAWER (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:51:22Z  
**Author:** v1.1.4

**Goal:** users can inspect the provenance manifest without leaving the app.

### Behavior
- Drawer/panel under the plot shows a JSON tree of `manifest['traces'][current_trace]`.
- Export button downloads current manifest as JSON.
- Never crashes; if manifest missing, show placeholder text and hint.

### Pseudocode
```python
import json

def show_provenance_drawer(container, manifest, trace_id):
    try:
        entry = (manifest or {}).get('traces', {}).get(trace_id, {})
        container.expander("Provenance").json(entry)
    except Exception as e:
        container.warning(f"Provenance unavailable: {e}")
```
