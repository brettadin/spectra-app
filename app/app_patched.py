"""Compatibility wrapper preserved for legacy launch scripts."""
from __future__ import annotations

import streamlit as st

from app.app_merged import main as _merged_main, render as _merged_render


DEFAULT_PAGE = "pages/overlay.py"


def _guard_streamlit_routing() -> bool:
    if "booted" not in st.session_state:
        st.session_state["booted"] = True

    if st.session_state.get("_routed") != DEFAULT_PAGE:
        st.session_state["_routed"] = DEFAULT_PAGE
        if hasattr(st, "switch_page"):
            try:
                st.switch_page(DEFAULT_PAGE)
                return False
            except Exception:
                # Ignore missing page errors; stay on the current script.
                st.session_state["_routed"] = DEFAULT_PAGE

    want: dict[str, str] = {}
    current_params = dict(st.query_params)
    if want and current_params != want:
        st.query_params.clear()
        st.query_params.update(want)
        st.stop()
    return True


def render() -> None:
    if not _guard_streamlit_routing():
        return
    _merged_render()


def main() -> None:
    if not _guard_streamlit_routing():
        return
    _merged_main()


if __name__ == "__main__":
    main()
