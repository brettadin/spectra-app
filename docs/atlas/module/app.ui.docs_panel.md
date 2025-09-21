# Module Report — app.ui.docs_panel (v1.1.4x)

**Module path:** (commonly `app/ui/docs_panel.py` or inline in `main.py`)  
**Purpose:** Render project docs browser.  
**Last reviewed (UTC):** 2025-09-20T04:27:59Z

## Required behavior
- Never clear the whole page; render within a container.
- If file read fails, render `st.error` with the path and exception, and log to `ui_debug.log`.

## Known issues
- Handler switched the route and returned early after an exception, leaving no frame.
- Fix by ensuring the main `render()` always paints a skeleton before dispatching to panels.
