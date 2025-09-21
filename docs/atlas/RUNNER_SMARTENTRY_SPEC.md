# RUNNER_SMARTENTRY_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:37:40Z  
**Author:** v1.1.4

The SmartEntry runner exists to make launch deterministic and logged.

## Responsibilities
- Create `logs/ui_debug.log` if missing.
- Log key milestones: BOOT, IMPORT, EXPORTS, TRY_ENTRY/OK/ERR, FIRSTPAINT, RUN_MODULE fallback.
- Paint a minimal frame before delegation.
- Prefer `render()` if exported; support legacy names during migration.
- Fallback to `run_module('app.app_merged')` if nothing callable exists.

## Non‑Responsibilities
- No business logic. No data loading. No Streamlit sidebar/controls beyond the first paint.
- No guessing at multiple modules. Exactly one UI root: `app.app_merged`.
