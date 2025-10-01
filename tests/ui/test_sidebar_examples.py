from streamlit.testing.v1 import AppTest


def _render_sidebar_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.main import _ensure_session_state, _render_settings_group

    _ensure_session_state()
    container = st.sidebar.container()
    _render_settings_group(container)


def _render_library_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.main import _ensure_session_state, _render_library_tab

    _ensure_session_state()
    _render_library_tab()


def test_sidebar_examples_controls_render():
    app = AppTest.from_function(_render_sidebar_entrypoint)
    app.session_state.network_available = True
    app.session_state.example_favourites = ["sirius-stis"]
    app.session_state.example_recent = ["sirius-stis"]

    app.run()

    button_labels = [button.label for button in app.sidebar.button]
    assert "Browse example library" in button_labels

    form_blocks = app.sidebar.get("form")
    form_ids = {block.proto.form.form_id for block in form_blocks}
    assert "example_quick_add_form" in form_ids
    assert "example_favourites_form" in form_ids
    assert "example_recent_form" in form_ids


def test_library_tab_points_to_sidebar(monkeypatch):
    import app.ui.main as main

    monkeypatch.setattr(main, "render_targets_panel", lambda *_, **__: None)
    monkeypatch.setattr(main, "_render_uploads_group", lambda container: container.write("Uploads"))

    app = AppTest.from_function(_render_library_entrypoint)

    app.run()

    info_messages = {info.body for info in app.info}
    assert any("examples" in message.lower() and "sidebar" in message.lower() for message in info_messages)
