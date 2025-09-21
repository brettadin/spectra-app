# Module Report — app.ui.main (v1.1.4x)

**Module path:** `app/ui/main.py`  
**Purpose:** Build the main page layout: controls, data panels, and drawers.  
**Last reviewed (UTC):** 2025-09-20T04:27:59Z

## Public API (expected)
- `render(state=None)` — build the entire page.
- Optional `docs_panel()`, `examples_panel()`, or route functions used by the sidebar.

## Import-time side effects
- Must not render on import. If legacy code does, fence with `if st.session_state.get('_ALLOW_IMPORT_PAINT'):` as a temporary migration, but move to `render()`.

## Handlers and blank screen root cause
- Clicking Docs/Examples sometimes blanked the page because handler exceptions were swallowed and nothing else rendered.
- Wrap handler bodies with `try/except` and always leave a visible frame.

## Tests
- Toggle each sidebar route and confirm: either content appears or an inline red error panel with stack context does.
