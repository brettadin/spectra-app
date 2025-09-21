# Module Report — app.ui.entry (v1.1.4x)

**Module path:** `app/ui/entry.py`  
**Purpose:** Canonical **entrypoint** for the UI. Must export `render()` which draws the initial page frame and delegates to page sections.  
**Last reviewed (UTC):** 2025-09-20T04:27:59Z

## Public API
- `render(state=None)` — sets page config, paints the header, version badge, sidebar, and calls into `app.ui.main`.

## Import-time side effects
- Should be zero. All Streamlit calls belong inside `render()`.

## Dependencies (internal)
- `app.ui.main` — the page builder.
- `app.utils.provenance` — to expose the provenance drawer toggle.
- Reads `app/version.json` via a helper to display the badge.

## Known issues
- Missing file in some builds, causing runners to guess at other callables and end in blank screens.
- When `render()` raises, no visible error is shown; add `try/except` and use `st.error` plus log.

## Tests
- Direct call from REPL under Streamlit runner should show a visible frame even with no data.
