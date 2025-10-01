from streamlit.testing.v1 import AppTest


def _render_sidebar_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.main import _ensure_session_state, _render_settings_group

    _ensure_session_state()
    container = st.sidebar.container()
    _render_settings_group(container)


def _simple_overlay(trace_id: str):
    from app.ui.main import OverlayTrace

    return OverlayTrace(
        trace_id=trace_id,
        label=f"Trace {trace_id}",
        wavelength_nm=(500.0, 600.0, 700.0),
        flux=(1.0, 1.1, 0.9),
    )


def test_clear_overlays_button_present_in_sidebar():
    app = AppTest.from_function(_render_sidebar_entrypoint)

    app.session_state.overlay_traces = [
        _simple_overlay("a"),
        _simple_overlay("b"),
    ]

    app.run()

    sidebar_buttons = [button.label for button in app.sidebar.button]
    assert "Clear overlays" in sidebar_buttons

    sidebar_selects = [select.label for select in getattr(app.sidebar, "selectbox", [])]
    assert "Normalization" not in sidebar_selects
    assert "Differential mode" not in sidebar_selects


