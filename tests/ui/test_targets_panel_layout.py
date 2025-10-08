"""Layout regressions for the target catalog panel."""

from streamlit.testing.v1 import AppTest


def _render_targets_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.targets import render_targets_panel

    render_targets_panel("data_registry", expanded=True)


def test_targets_panel_exposes_search_and_filters():
    app = AppTest.from_function(_render_targets_entrypoint)

    app.run()

    search_labels = [control.label for control in app.text_input]
    assert "Find a target" in search_labels

    checkbox_labels = {control.label for control in app.checkbox}
    assert "Has curated MAST data" in checkbox_labels
    assert "Has known planets" in checkbox_labels


def test_targets_panel_surfaces_manifest_summary():
    app = AppTest.from_function(_render_targets_entrypoint)

    app.run()

    metric_map = {metric.label: metric.value for metric in app.metric}
    assert "Curated spectra" in metric_map
    assert "Total MAST hits" in metric_map
    assert "Known planets" in metric_map

    captions = [caption.body for caption in app.caption]
    assert any("MAST" in body for body in captions)


def test_targets_panel_groups_products_by_collection():
    app = AppTest.from_function(_render_targets_entrypoint)

    app.run()

    selectboxes = {control.label for control in app.selectbox}
    assert "Pick a target" in selectboxes
    assert "Filter by collection" in selectboxes

    subheaders = [getattr(block, "body", "") for block in getattr(app, "subheader", [])]
    assert any("Curated MAST spectra" in body for body in subheaders)

    markdown_blocks = [block.body for block in app.markdown]
    assert any(
        body.startswith("**Curated selection") or body.startswith("**CALSPEC")
        for body in markdown_blocks
    )


def test_targets_panel_catalog_table_is_optional():
    app = AppTest.from_function(_render_targets_entrypoint)

    app.run()

    expander_labels = [exp.label for exp in app.expander]
    assert expander_labels.count("Browse catalog entries") == 1

    # The catalog table remains available, but should no longer dominate the layout.
    assert len(app.dataframe) == 1
