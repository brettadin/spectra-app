# PANEL_CONTRACTS (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:48:19Z  
**Author:** v1.1.4

**Goal:** panels are drop-in and cannot crash the whole page.

## Each panel must provide
- `render_<name>(container)` callable.
- No Streamlit calls at import time.
- Error handling inside the callable.
- No direct manipulation of global layout.

## Optional hooks
- `load_state()` — read `st.session_state` and normalize defaults.
- `on_event(event)` — handlers for button/radio/select.
