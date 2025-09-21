# Module Report — app.ui.widgets.units_and_dedupe (v1.1.4x)

**Module path:** `app/ui/widgets/units_and_dedupe.py` (or equivalent inline)  
**Purpose:** Unit cycling and duplicate ingest scope controls.  
**Last reviewed (UTC):** 2025-09-20T04:27:59Z

## Behavior
- Unit cycle path: nm → Å → µm → cm⁻¹ → nm. Axes update idempotently.
- Dedupe scope: Global | Session | Off. A session purge occurs if override is requested; provenance note is recorded.

## Known issues
- Switching scope to Off triggered a blank page in some builds. Reason: unhandled state reset.
- Fix: wrap state changes in try/except; after purge, re-render the frame unconditionally and show a toast about the change.
