from streamlit.testing.v1 import AppTest


def _render_sidebar_entrypoint() -> None:
    import streamlit as st  # noqa: F401  # Re-exported for AppTest serialization

    from app.ui.main import _ensure_session_state, _render_settings_group

    _ensure_session_state()
    container = st.sidebar.container()
    _render_settings_group(container)


def test_line_catalog_form_moves_to_sidebar():
    app = AppTest.from_function(_render_sidebar_entrypoint)
    app.session_state.network_available = True

    app.run()

    form_blocks = app.sidebar.get("form")
    form_ids = {block.proto.form.form_id for block in form_blocks}

    assert "nist_overlay_form" in form_ids


def test_line_catalog_sidebar_respects_offline_toggle():
    app = AppTest.from_function(_render_sidebar_entrypoint)
    app.session_state.network_available = False

    app.run()

    form_blocks = app.sidebar.get("form")
    form_ids = {block.proto.form.form_id for block in form_blocks}

    assert "nist_overlay_form" not in form_ids

    offline_messages = {info.body for info in app.sidebar.info}
    assert any("offline" in message.lower() for message in offline_messages)
