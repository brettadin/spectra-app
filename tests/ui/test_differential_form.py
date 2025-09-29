from streamlit.testing.v1 import AppTest

from app.ui.main import OverlayTrace


def _render_differential_tab_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.main import _render_differential_tab

    _render_differential_tab()


def _simple_overlay(trace_id: str) -> OverlayTrace:
    return OverlayTrace(
        trace_id=trace_id,
        label=f"Trace {trace_id}",
        wavelength_nm=(500.0, 600.0, 700.0),
        flux=(1.0, 1.2, 0.8),
    )


def test_differential_form_has_single_submit_button():
    app = AppTest.from_function(_render_differential_tab_entrypoint)

    app.session_state.overlay_traces = [
        _simple_overlay("a"),
        _simple_overlay("b"),
    ]
    app.session_state.reference_trace_id = "a"
    app.session_state.normalization_mode = "unit"

    app.run()

    assert not app.exception

    # The form should render without raising a DuplicateWidgetID error from
    # multiple submit buttons with identical labels/keys.
