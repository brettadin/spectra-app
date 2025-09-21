# 04_UI_SHELL_AND_ERROR_HANDLING (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:48:19Z  
**Author:** v1.1.4

This is the canonical spec for the visible frame of the app and how it refuses to die on user errors.

---

## Shell responsibilities
- Set page config early (`wide`, title).
- Draw version badge from `app/version.json`.
- Build a header and persistent sidebar.
- Expose a main container that never disappears, even when panels throw.

## Sidebar routing
- Radio or tabs for: **Home**, **Docs**, **Examples** (can expand later).
- State key: `st.session_state['page']` stores current selection.
- On change, re-render the same shell then call the selected panel.

## Badge rules
- Badge must read `app/version.json` at runtime.
- If read fails, show a warning badge with `?` and continue.
- Position: fixed top-right; small font; no overlap with Streamlit menu.

## Container contract
- `shell_container = st.container()` created before panel dispatch.
- All panels write into `shell_container`.
- If a panel fails, `shell_container.error(...)` is used and the shell persists.

---

## Error handling patterns
Wrap every panel body:

```python
def render_docs(container):
    try:
        # expensive IO, parsing, etc.
        container.markdown(load_docs())
    except FileNotFoundError as e:
        container.warning(f"Docs not found: {e}")
    except Exception as e:
        container.error(f"Docs error: {e}")
```

Switching scope/units must also protect the frame:

```python
def on_scope_change(new_scope):
    try:
        st.session_state['dedupe_scope'] = new_scope
        st.experimental_rerun()
    except Exception as e:
        st.session_state['last_error'] = str(e)
```

---

## Anti-blank guarantees
- The shell (header + badge + sidebar + container) is created before any IO.
- The container remains in the DOM; only its inside changes.
- Panels are pure functions of state; they cannot alter shell layout.
- No panel is allowed to call `st.stop()` without drawing an error first.

---

## Minimal reference implementation (UI root)
```python
import streamlit as st, json, pathlib

def _badge():
    ver = {"version":"v?.?.?", "patch":"", "timestamp":""}
    try:
        vpath = pathlib.Path(__file__).resolve().with_name("version.json")
        ver = json.loads(vpath.read_text(encoding="utf-8"))
    except Exception as e:
        st.warning(f"Badge read failed: {e}")
    st.markdown(
        f"<div style='position:fixed;top:8px;right:12px;opacity:0.85;font-size:12px;'>"
        f"{ver.get('version','?')} {ver.get('patch','')}"
        f"</div>", unsafe_allow_html=True)
    return ver

def render():
    st.set_page_config(page_title="Spectra App", layout="wide")
    _badge()
    st.header("Spectra")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home","Docs","Examples"], index=0, key="page")

    container = st.container()
    if page == "Home":
        container.info("Home ready.")
    elif page == "Docs":
        try:
            container.markdown("## Docs panel body")
        except Exception as e:
            container.error(f"Docs error: {e}")
    elif page == "Examples":
        try:
            container.success("Examples panel body")
        except Exception as e:
            container.error(f"Examples error: {e}")
```
