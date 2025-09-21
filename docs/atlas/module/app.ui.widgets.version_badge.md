# Module Report — app.ui.widgets.version_badge (v1.1.4x)

**Module path:** `app/ui/widgets/version_badge.py` (or equivalent inline)  
**Purpose:** Read `app/version.json` and render a top-right badge.  
**Last reviewed (UTC):** 2025-09-20T04:27:59Z

## Behavior
- Read `version.json` at runtime; display `version` + `patch` in the corner.
- If file missing or parse fails, render a warning badge with a fallback like `v?.? (badge error)` and log.
