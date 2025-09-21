# 03_RUNTIME_LIFECYCLE — Detailed (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:47:25Z  
**Author:** v1.1.4

This document traces exactly what happens from process start to user interaction. Think of it as a flight recorder for the app lifecycle.

---

## Lifecycle phases

1. **Process start**
   - PowerShell runner script spawns Python (usually `Start-Spectra-Patched.ps1`).
   - Environment variables (like `SPECTRA_APP_ENTRY`) are applied.
   - `app/app_patched.py` executes as `__main__`.

2. **SmartEntry boot**
   - Logs `BOOT` to `logs/ui_debug.log`.
   - Imports `app.app_merged`.
   - Calls `first_paint()` to render banner + badge.
   - Logs `IMPORT` and `FIRSTPAINT OK`.

3. **Entrypoint resolution**
   - Lists callables exported by `app.app_merged`.
   - Chooses in order: `render`, `main`, `app`, `run`, `entry`, `ui`.
   - Logs `EXPORTS [...]`.
   - If a candidate is found, logs `TRY_ENTRY <name>`.
   - If callable succeeds, logs `TRY_ENTRY_OK` and lifecycle continues.
   - If no candidate: logs `NO_EXPLICIT_ENTRY -> run_module` and executes module.

4. **Page shell construction**
   - Inside `render()`: sets Streamlit page config.
   - Reads `app/version.json` for badge.
   - Displays header, sidebar, container skeleton.
   - Logs badge load success/failure.

5. **Panel rendering**
   - Sidebar radio selects [Home | Docs | Examples].
   - Docs panel loads Markdown/docs files.
   - Examples panel loads demo spectra overlays.
   - Each wrapped in try/except to catch errors inline.

6. **Event loop**
   - User toggles dedupe scope, uploads files, changes units.
   - Each action re-triggers `render()` (Streamlit reruns script on interaction).
   - State stored in `st.session_state` ensures continuity.

7. **Shutdown**
   - On quit/stop, logs `SYS.EXIT(code)`.
   - __pycache__ may persist unless purged by patch scripts.

---

## Timeline diagram

```text
[Start-Spectra-Patched.ps1]
   │
   ▼
[Python runtime: app_patched.py __main__]
   │   └── BOOT → IMPORT app.app_merged
   │
   ▼
[First Paint] → banner+badge
   │
   ▼
[Entrypoint selection] → TRY_ENTRY render() → OK
   │
   ▼
[UI Shell]
   │   ├─ Sidebar
   │   ├─ Header + Badge
   │   └─ Main Container
   │        ├─ Docs panel
   │        └─ Examples panel
   │
   ▼
[Event loop: user actions → rerun → stateful re-render]
   │
   ▼
[Exit]
```

---

## Failure modes and where they hit

- **Blank screen at start:** `first_paint()` missing or failed silently.
- **No badge:** `version.json` unreadable or missing.
- **Docs/Examples blank:** handlers crash without try/except.
- **Dedupe scope blank:** state change not followed by repaint.
- **Dual-run warning (`sys.modules`):** import then run_module double-loads `app_merged`.

---

## Logs that confirm lifecycle health
- `BOOT ... IMPORT ... FIRSTPAINT OK` → runner alive.
- `EXPORTS [...] TRY_ENTRY_OK render` → UI root alive.
- `TRY_ENTRY_ERR` lines → pinpoint failing handler.
- `SYS.EXIT(0)` → clean shutdown.

---

## Developer obligations
- Never remove `render()`.
- Always wrap sidebar panels in try/except.
- Log every lifecycle milestone.
- Purge __pycache__ after patching SmartEntry.

---

## Acceptance criteria for lifecycle stability
- First paint always visible.
- Badge matches `app/version.json`.
- Switching panels never blanks entire screen.
- Logs show ordered sequence BOOT → IMPORT → EXPORTS → TRY_ENTRY_OK.
- Shutdown logs SYS.EXIT with a code.
