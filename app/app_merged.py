"""Streamlit entry point with crash logging and UI delegation."""
from __future__ import annotations

import importlib
import os
import traceback
from datetime import datetime

try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit unavailable during type checks
    st = None

from app._version import get_version_info as _get_version_info

_LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_PATH = os.path.join(_LOG_DIR, "ui_debug.log")


def _render_badge() -> None:
    """Render the fixed-position version badge if Streamlit is available."""
    if st is None:
        return
    try:
        info = _get_version_info()
    except Exception:
        return

    version = info.get("version", "v?")
    built = info.get("date_utc", "")
    try:
        st.markdown(
            (
                "<div style='position:fixed;top:12px;right:28px;opacity:.85;"
                "padding:2px 8px;border:1px solid #444;border-radius:12px;"
                "font-size:12px;'>"
                f"{version} • {built}</div>"
            ),
            unsafe_allow_html=True,
        )
    except Exception:
        # Streamlit might not be initialised during import/testing
        return


def _write_log(exc: BaseException) -> None:
    timestamp = datetime.utcnow().isoformat()
    with open(_LOG_PATH, "a", encoding="utf8") as handle:
        handle.write(f"=== UI DEBUG TRACE: {timestamp} ===\n")
        traceback.print_exc(file=handle)
        handle.write("\n\n")


def _safe_run(fn):
    try:
        return fn()
    except Exception as exc:  # pragma: no cover - defensive logging branch
        _write_log(exc)
        if st is not None:
            try:
                st.error(
                    "UI crashed during render. "
                    f"A diagnostic traceback was written to: {_LOG_PATH}"
                )
                with st.expander("Show last traceback (truncated):"):
                    with open(_LOG_PATH, "r", encoding="utf8") as handle:
                        data = handle.read()
                    st.code(data[-10000:])
            except Exception:
                pass
        return None


def _render_ui() -> None:
    _render_badge()
    try:
        from app.ui.entry import render as entry_render
    except Exception:
        # Fall back to importing the main UI module, which renders on import.
        importlib.import_module("app.ui.main")
    else:
        entry_render()


def render() -> None:
    """Primary entry point used by historical launchers."""
    _safe_run(_render_ui)


def main() -> None:
    """Streamlit expects a callable named main; keep it for compatibility."""
    render()


if __name__ == "__main__":
    main()
