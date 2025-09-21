# 05 - Utilities & Provenance System

This document maps the **utilities** (`utils/`) and **provenance system** in the Spectra App.  
These pieces are small, but they glue together critical functions like logging, compatibility shims, and trace lineage.

---

## 📂 app/utils/

### provenance.py
- **Purpose**: Compatibility layer for provenance (metadata about spectra fetch, transforms, units, etc.).
- **Main exports historically**:
  - `write_provenance(manifest, trace_id, prov)` - shim for updating manifest provenance.
  - `ProvenanceRecord` (older versions referenced it, but current builds moved record-keeping into `server/provenance.py`).
- **Shim strategy**:
  - Attempts to import `merge_trace_provenance` from `app/server/provenance.py`.
  - If not found, falls back to a minimal local dictionary update.
  - Example fallback logic:
    ```python
    traces = manifest.setdefault("traces", {})
    entry = traces.setdefault(trace_id, {})
    entry.setdefault("fetch_provenance", {}).update(prov or {})
    ```
- **Why it exists**:  
  Older code still imported `app.utils.provenance.write_provenance`.  
  Instead of refactoring everything, we **preserve old imports** and forward them to the new system.

- **Known Issues**:
  - **Stray edits introduced syntax errors** (escaped quotes, stray `f`, broken indentation).  
    These caused multiple blank-screen failures in v1.1.4a-c.
  - Fix was to enforce **clean shim replacement scripts** in PowerShell (regex find/replace).

---

## 📂 app/server/

### provenance.py
- **Purpose**: Centralized provenance system introduced in v1.1.4.
- **Core function**: `merge_trace_provenance(manifest, trace_id, prov)`
  - Ensures provenance from multiple stages (fetch -> ingest -> transform -> export) are merged consistently.
  - Maintains `"traces"` dictionary in `manifest.json` export.
  - Keeps full lineage for reproducibility.

- **Design decision**:
  - All new code should call **`server.provenance.merge_trace_provenance`**.
  - Legacy calls are caught by the shim in `utils/provenance.py`.

- **Integration points**:
  - Overlay/Differential tabs when ingesting or deriving new traces.
  - Export manifest generator (`export what I see` bundles provenance per trace).

---

## ⚠️ Observed Failures & Lessons

1. **Missing append_provenance**  
   - At one point, code attempted `from app.utils.provenance import append_provenance` (never defined).  
   - Breakage occurred until we standardized on `write_provenance` + shim.

2. **Escaped triple quotes bug**  
   - Auto-injected shim inserted `\\\"\\\"\\\"` instead of `"""`.  
   - Caused **SyntaxError** until cleaned.

3. **Stray character bug**  
   - A single stray `f` at file top of `provenance.py` crashed app instantly.  
   - Reinforces the need for **Verify-Project.ps1** and **lint checks** before shipping.

4. **Blank-screen on UI load**  
   - When provenance imports failed, app would start but render blank, with no error banners.  
   - Solution: defensive imports + robust logging (`ui_debug.log`).

---

## ✅ Best Practices Going Forward

- **Never remove old imports** - Always shim forward.
- **Use idempotent repair scripts** (regex-based PowerShell/py) to enforce clean `write_provenance` block.
- **UI contract includes provenance**:
  - Must always appear in export manifest.
  - If provenance import fails, **show error banner instead of blank page**.
- **Future plan**:  
  - Consolidate provenance into a visible **Provenance Drawer** in UI.  
  - Expose per-trace provenance lineage interactively.

---

## 🔑 Takeaway

The provenance system is small but critical.  
Every failure of this file has historically blanked the UI.  
Future developers must:
- **Respect the shim pattern.**
- **Never break imports.**
- **Always preserve provenance in exports and logs.**
