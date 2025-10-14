import numpy as np
import streamlit as st
from streamlit.testing.v1 import AppTest

from app.similarity import SimilarityCache
from app.ui.main import OverlayTrace, _compute_differential_result


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


def _image_overlay(trace_id: str) -> OverlayTrace:
    return OverlayTrace(
        trace_id=trace_id,
        label=f"Image {trace_id}",
        wavelength_nm=tuple(),
        flux=tuple(),
        kind="image",
        axis_kind="image",
        image={"data": [[1.0, 2.0], [3.0, 4.0]]},
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

    from collections import deque

    button_nodes = []
    queue: deque = deque([app._tree.root])
    while queue:
        node = queue.popleft()
        node_type = getattr(node, "type", None)
        if node_type == "button" and getattr(node, "form_id", None) == "differential_compute_form":
            button_nodes.append(node)
        children = getattr(node, "children", None)
        if isinstance(children, dict):
            queue.extend(children.values())

    assert len(button_nodes) == 1


def test_reference_controls_render_in_differential_tab():
    app = AppTest.from_function(_render_differential_tab_entrypoint)

    app.session_state.overlay_traces = [
        _simple_overlay("a"),
        _simple_overlay("b"),
    ]
    app.session_state.reference_trace_id = "b"
    app.session_state.normalization_mode = "unit"

    app.run()

    reference_select = [
        select for select in app.selectbox if select.label == "Reference trace"
    ]
    assert reference_select, "Reference selectbox should be rendered in differential tab"
    assert reference_select[0].value == "b"

    button_labels = [button.label for button in app.button]
    assert "Clear overlays" not in button_labels


def test_differential_controls_shifted_into_tab():
    app = AppTest.from_function(_render_differential_tab_entrypoint)

    app.session_state.overlay_traces = [
        _simple_overlay("a"),
        _simple_overlay("b"),
    ]
    app.session_state.reference_trace_id = "a"

    app.run()

    select_labels = [select.label for select in app.selectbox]
    assert "Normalization" in select_labels
    assert "Differential mode" in select_labels
    assert "Similarity normalization" in select_labels

    multiselect_labels = [multi.label for multi in getattr(app, "multiselect", [])]
    assert "Metrics" in multiselect_labels

    slider_labels = [slider.label for slider in app.slider]
    assert "Line peak count" in slider_labels


def test_similarity_panel_renders_with_differential_inputs():
    app = AppTest.from_function(_render_differential_tab_entrypoint)

    app.session_state.overlay_traces = [
        _simple_overlay("a"),
        _simple_overlay("b"),
        _simple_overlay("c"),
    ]
    app.session_state.reference_trace_id = "a"
    app.session_state.normalization_mode = "unit"
    app.session_state.similarity_cache = SimilarityCache()
    app.session_state.similarity_metrics = ["cosine", "line_match"]
    app.session_state.similarity_primary_metric = "cosine"
    app.session_state.similarity_line_peaks = 5

    app.run()

    assert not app.exception

    headings = [block.body for block in app.markdown]
    assert "### Similarity analysis" in headings


def test_differential_tab_handles_image_overlays():
    app = AppTest.from_function(_render_differential_tab_entrypoint)

    app.session_state.overlay_traces = [
        _simple_overlay("a"),
        _simple_overlay("b"),
        _image_overlay("img"),
    ]
    app.session_state.reference_trace_id = "a"
    app.session_state.normalization_mode = "unit"
    app.session_state.similarity_cache = SimilarityCache()

    app.run()

    assert not app.exception


def test_compute_differential_result_prefers_wavenumber_display():
    st.session_state.clear()
    st.session_state["display_units"] = "cm^-1"

    wn_points = np.array([2400.0, 2320.0, 2240.0])
    wavelengths_nm = tuple(float(1e7 / value) for value in wn_points)
    trans_flux_a = (0.92, 0.35, 0.88)
    trans_flux_b = (0.94, 0.40, 0.90)

    metadata = {
        "original_wavelength_unit": "cm^-1",
        "flux_unit_input": "Transmittance",
    }

    trace_a = OverlayTrace(
        trace_id="a",
        label="Trace A",
        wavelength_nm=wavelengths_nm,
        flux=trans_flux_a,
        metadata=dict(metadata),
        flux_unit="Transmittance",
    )
    trace_b = OverlayTrace(
        trace_id="b",
        label="Trace B",
        wavelength_nm=wavelengths_nm,
        flux=trans_flux_b,
        metadata=dict(metadata),
        flux_unit="Transmittance",
    )

    result = _compute_differential_result(
        trace_a,
        trace_b,
        "Subtract (A − B)",
        sample_points=3,
        normalization="unit",
    )

    assert result.display_unit == "cm^-1"
    assert result.display_axis_reversed is True
    assert result.grid_cm_1 and len(result.grid_cm_1) == 3
    assert len(result.values_a_display) == len(result.values_a)
    assert max(result.values_a_display) <= 0.0
