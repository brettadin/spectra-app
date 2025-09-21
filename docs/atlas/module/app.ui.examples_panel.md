# Module Report — app.ui.examples_panel (v1.1.4x)

**Module path:** (commonly `app/ui/examples_panel.py` or inline in `main.py`)  
**Purpose:** Render example datasets list and load on selection.  
**Last reviewed (UTC):** 2025-09-20T04:27:59Z

## Required behavior
- Loading an example must catch file/parse errors and render an inline error with provenance of the source path.
- Keep previously rendered frame visible even when an example fails.

## Known issues
- Example selection that raises during load left a blank page. Wrap in `try/except` and display an error block with the failing example ID.
