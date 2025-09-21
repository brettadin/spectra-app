# 02_ENTRYPOINT_CONTRACT — Detailed (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:37:40Z  
**Author:** v1.1.4

This is the non-negotiable pact between the *runner* and the *UI root*. Break it and you get the celebrated Blank White Page of Despair.

---

## What the runner promises
- It logs to `logs/ui_debug.log` with ISO UTC.
- It imports exactly one UI root: `app.app_merged`.
- It calls one exported callable — default `render()` — or, if none found, it runs the module as `__main__` and still paints a visible frame.
- It draws a first paint header before delegation (title + version badge) so users never stare at nothing.

## What the UI root promises
- Export a callable: `render()`. Legacy names allowed for migration: `main`, `app`, `run`, `entry`, `ui`.
- Do no Streamlit work on import. All drawing happens inside the callable(s).
- Always construct a page shell: header, version badge (from `app/version.json`), sidebar, and a main container.
- Panel handlers (docs/examples) run inside the main container and must catch/print errors inline.

---

## Reference pseudocode (runner)

```python
# app/app_patched.py
import importlib, pathlib, datetime, traceback, runpy, os

LOG = pathlib.Path(__file__).resolve().parents[1] / "logs" / "ui_debug.log"
def _ts(): return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
def _log(msg): 
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text((LOG.read_text(encoding="utf-8") if LOG.exists() else "") + f"{_ts()} {msg}\n", encoding="utf-8")
    except Exception:
        pass

def first_paint():
    import streamlit as st, json, pathlib
    ver = {"version":"?", "patch":"?", "timestamp":""}
    try:
        vpath = pathlib.Path(__file__).resolve().parents[0] / "version.json"
        ver = json.loads(vpath.read_text(encoding="utf-8"))
    except Exception as e:
        st.warning(f"Version badge error: {e}")
    st.set_page_config(page_title="Spectra App", layout="wide")
    st.markdown(
        f"<div style='position:fixed;top:8px;right:12px;opacity:0.8;font-size:12px;'>"
        f"{ver.get('version','?')} {ver.get('patch','')}"
        f"</div>", unsafe_allow_html=True)
    st.header("Spectra")
    st.caption("Booting UI…")

def main():
    _log("SMARTENTRY BOOT")
    m = importlib.import_module("app.app_merged")
    _log(f"IMPORT app.app_merged")
    # visible frame
    try:
        first_paint()
        _log("FIRSTPAINT OK")
    except Exception as e:
        _log(f"FIRSTPAINT ERR {e!r}")

    candidates = ["render","main","app","run","entry","ui"]
    exports = [n for n,o in vars(m).items() if callable(o) and not n.startswith("_")]
    _log(f"EXPORTS {exports}")
    for name in candidates:
        if name in exports:
            _log(f"TRY_ENTRY {name}")
            try:
                getattr(m, name)()
                _log(f"TRY_ENTRY_OK {name}")
                return
            except SystemExit as se:
                _log(f"TRY_ENTRY_SYS_EXIT {name} code={getattr(se,'code',None)}")
                return
            except Exception:
                _log("TRY_ENTRY_ERR " + name + "\n" + traceback.format_exc())

    _log("NO_EXPLICIT_ENTRY -> RUN_MODULE __main__")
    runpy.run_module("app.app_merged", run_name="__main__")

if __name__ == "__main__":
    main()
```

> The runner paints first, then delegates. If delegation misfires, users still see the banner and badge, not a void.

---

## Reference pseudocode (UI root)

```python
# app/app_merged.py
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
        f"</div>",
        unsafe_allow_html=True,
    )
    return ver

def render():
    st.set_page_config(page_title="Spectra App", layout="wide")
    _ = _badge()
    st.header("Spectra")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home","Docs","Examples"], index=0)

    container = st.container()
    if page == "Home":
        container.info("Home ready.")
    elif page == "Docs":
        try:
            container.write("Docs panel")
        except Exception as e:
            container.error(f"Docs error: {e}")
    else:
        try:
            container.write("Examples panel")
        except Exception as e:
            container.error(f"Examples error: {e}")
```

---

## Anti‑patterns (and why they bit us)
- Import-time layout: Streamlit calls in module top-level leave nothing to render when handlers crash.
- Dual-run of same module: `import_module` then `runpy.run_module` creates warnings and state weirdness.
- Silent handler failures: exceptions swallowed with no `st.error` gives a blank screen and an empty log.
- Version badge hardcoded: it quietly desyncs from `version.json` and lies to users.

---

## Verification checklist
- At app start, you see header + badge even if the UI root fails.
- `ui_debug.log` shows `SMARTENTRY BOOT`, `IMPORT`, `EXPORTS`, and either `TRY_ENTRY_OK render` or `RUN_MODULE __main__`.
- Changing `app/version.json` updates the badge on refresh.
- Clicking Docs/Examples never blanks the page; failures show inline red panels.

---

## Failure scenarios table (what to do)
- No callable exported: Add `render()` to `app_merged` or wire `app.ui.entry.render()`; confirm log shows EXPORTS includes 'render'.
- Blank on Docs/Examples: Wrap panel body in try/except; re-render page shell regardless.
- Badge not visible: `version.json` missing or path wrong; show warn badge and log the exception.
- Scope/Units toggle blanks: state purge not followed by frame re-render; always repaint after state change.
