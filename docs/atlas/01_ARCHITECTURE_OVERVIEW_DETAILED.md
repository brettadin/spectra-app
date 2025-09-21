# 01_ARCHITECTURE_OVERVIEW — Detailed (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:34:48Z  
**Author:** v1.1.4

This is the ground-truth map of layers, ownership, and call flows as intended for v1.1.4x. It’s opinionated on purpose so future edits don’t turn the UI into a ghost.

## Layer stack (top → bottom)

1. **Runner**
   - **Module:** `app/app_patched.py`
   - **Role:** Tiny dispatcher. Logs to `logs/ui_debug.log`, renders a minimal first frame, then delegates to the UI root callable (`render()`).
   - **Anti-goals:** no business logic, no guessing silently, no dual-run of the same module via `import_module` + `runpy`.

2. **UI Root**
   - **Module:** `app/app_merged.py`
   - **Export:** `render()` (canonical). Legacy allowed: `main`, `app`, `run`, `entry`, `ui`.
   - **Role:** Build page shell and route to panels (Home, Docs, Examples). Badge always visible.

3. **UI Pages**
   - **Dir:** `app/ui/`
   - **Modules:** `entry.py`, `main.py`, optional `docs_panel.py`, `examples_panel.py`, and `widgets/*`.
   - **Rule:** No import-time drawing. All Streamlit calls happen inside functions called by `render()`.

4. **Utilities**
   - **Module:** `app/utils/provenance.py` (shim only).
   - **Role:** Thin compatibility layer; delegates merge to server-side provenance.

5. **Server**
   - **Dir:** `app/server/`
   - **Modules:** `provenance.py`, `models.py`, `fetchers/*` + `fetch_archives.py`.
   - **Role:** Data model, provenance merge, and archive fetch routing (MAST/SIMBAD/ESO stubs).

6. **Launchers & Patch Scripts**
   - **Dir:** `RUN_CMDS/`
   - **Rule:** Idempotent, minimal, compatible with restricted execution policy (no `-AsUTC`). Write a one-liner to log on success.

7. **Docs**
   - **Dir:** `docs/` (brains, atlas, patch notes).
   - **Rule:** Docs version string must match `app/version.json` patch stream.

8. **Logs**
   - **File:** `logs/ui_debug.log`.
   - **Role:** The single pane of truth for dispatcher + UI route events.

## Topology (ASCII)

```
streamlit -> app/app_patched.py  --logs--> logs/ui_debug.log
              | 
              v
           import app/app_merged.py
              |
              v
          call render() ---------------> widgets/version_badge -> read app/version.json
              |                                     |
              |                                     v
              +--> sidebar routes ------> panels (docs | examples | home)
              |           |                     |         |
              |           v                     v         v
              |       handlers()           file IO     sample IO
              |           |                     |         |
              |           +--> try/except + st.error + log (no blank page)
              |
              +--> utils/provenance (shim) ----> server/provenance.merge()
                                                       |
                                                       v
                                                models.Spectrum + manifest
```

## Ownership & boundaries

- **Runner owns:** logging, first paint, choosing the entry callable. Nothing else.
- **UI Root owns:** shell, routing, badge, error containment.
- **Panels own:** their container area only; they never control the full page lifecycle.
- **Server owns:** data normalization + provenance merge; never calls Streamlit.
- **Scripts own:** mechanical edits and startup convenience; never embed business logic.

## Cross-layer invariants

- Exactly one callable entrypoint. If multiple exist, the runner logs choices and uses `render()`.
- First paint must happen before any deep logic.
- A panel exception never blanks the page. It becomes an inline error and a log line.
- `version.json` drives the badge; if missing, show a warning badge, don’t fail silently.
- Provenance merge lives server-side; the utils shim stays tiny and unescaped.

## Minimal acceptance for any change touching these layers

1. Start app → **see badge** and a visible shell.
2. Click Docs, Examples, toggle Dedupe scope → frame persists; on error see inline `st.error`.
3. `logs/ui_debug.log` contains: SMARTENTRY BOOT, IMPORT, EXPORTS, TRY_ENTRY/OK, FIRSTPAINT OK, HANDLER_OK/ERR.
4. `app/version.json` value matches the on-screen badge.
