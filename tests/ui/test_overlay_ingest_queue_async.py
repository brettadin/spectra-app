"""Regression coverage for the asynchronous overlay ingest queue."""

from __future__ import annotations

from concurrent.futures import Future
import importlib
import logging
import threading
import time
from typing import Any, Dict, List

from streamlit.testing.v1 import AppTest


def _render_ingest_sidebar_entrypoint() -> None:
    import streamlit as st  # noqa: F401 - re-exported for AppTest serialisation

    from app.ui.main import (
        _ensure_session_state,
        _process_ingest_queue,
        _render_ingest_queue_panel,
    )

    _ensure_session_state()
    _process_ingest_queue()
    _render_ingest_queue_panel(st.sidebar.container())


def test_ingest_queue_remains_interactive_during_long_download(monkeypatch):
    """Simulate a slow download and ensure reruns stay responsive."""

    from app.ui import main as main_module

    release_download = threading.Event()
    first_request_started = threading.Event()
    request_lock = threading.Lock()
    requested_urls: List[str] = []

    class _FakeResponse:
        def __init__(self) -> None:
            self.content = b"binary-overlay"

        def raise_for_status(self) -> None:
            return None

    def _fake_requests_get(url: str, timeout: int = 60) -> _FakeResponse:
        with request_lock:
            requested_urls.append(url)
        first_request_started.set()
        release_download.wait()
        return _FakeResponse()

    monkeypatch.setattr(main_module.requests, "get", _fake_requests_get)

    def _fake_ingest_local_file(filename: str, content: bytes) -> Dict[str, Any]:
        return {
            "label": filename,
            "wavelength_nm": [500.0, 600.0, 700.0],
            "flux": [1.0, 0.9, 1.1],
        }

    monkeypatch.setattr(main_module, "ingest_local_file", _fake_ingest_local_file)

    added_payloads: List[Dict[str, Any]] = []

    def _fake_add_overlay_payload(payload: Dict[str, Any]) -> tuple[bool, str]:
        added_payloads.append(payload)
        label = payload.get("label") or "overlay"
        return True, f"Added {label}"

    monkeypatch.setattr(main_module, "_add_overlay_payload", _fake_add_overlay_payload)

    app = AppTest.from_function(_render_ingest_sidebar_entrypoint)

    try:
        app.session_state.ingest_queue = [
            {"url": "http://example.com/one.fits", "label": "One"}
        ]
        app.run()

        assert first_request_started.wait(1.0), "Background download did not start"

        captions = [caption.value for caption in app.sidebar.caption]
        assert any(
            "Downloading overlay data" in value for value in captions
        ), "Expected running download status in sidebar"

        app.session_state.ingest_queue = [
            {"url": "http://example.com/two.fits", "label": "Two"}
        ]
        app.run()

        captions = [caption.value for caption in app.sidebar.caption]
        assert any(
            "Downloading overlay data" in value for value in captions
        ), "First download status should persist across reruns"
        assert len(requested_urls) >= 2, "Second overlay should schedule while first runs"

        release_download.set()
        for _ in range(50):
            if len(added_payloads) >= 2:
                break
            time.sleep(0.05)

        app.run()

        success_messages = [message.value for message in app.sidebar.success]
        lowered_messages = [value.lower() for value in success_messages]
        assert any("added" in value for value in lowered_messages)
        assert any("one" in value for value in lowered_messages)
        assert any("two" in value for value in lowered_messages)
    finally:
        release_download.set()
        runtime = (
            app.session_state["ingest_runtime"]
            if "ingest_runtime" in app.session_state
            else {}
        )
        executor = runtime.get("executor") if isinstance(runtime, dict) else None
        if executor:
            executor.shutdown(wait=True)


def test_ingest_queue_completes_without_script_context_warning(monkeypatch, caplog):
    """Overlay jobs add payloads on the main thread without ScriptRunContext warnings."""

    from app.ui import main as main_module

    def _fake_requests_get(url: str, timeout: int = 60):
        class _FakeResponse:
            content = b"payload"

            def raise_for_status(self) -> None:
                return None

        return _FakeResponse()

    monkeypatch.setattr(main_module.requests, "get", _fake_requests_get)

    def _fake_ingest_local_file(filename: str, content: bytes) -> Dict[str, Any]:
        return {
            "label": filename,
            "wavelength_nm": [510.0, 520.0, 530.0],
            "flux": [1.0, 1.1, 0.9],
        }

    monkeypatch.setattr(main_module, "ingest_local_file", _fake_ingest_local_file)

    added_payloads: List[Dict[str, Any]] = []

    def _record_overlay_payload(payload: Dict[str, Any]) -> tuple[bool, str]:
        added_payloads.append(payload)
        label = payload.get("label") or "overlay"
        return True, f"Added {label}"

    monkeypatch.setattr(main_module, "_add_overlay_payload", _record_overlay_payload)

    app = AppTest.from_function(_render_ingest_sidebar_entrypoint)

    caplog.set_level(logging.WARNING)
    try:
        with caplog.at_level(logging.WARNING):
            app.session_state.ingest_queue = [
                {"url": "http://example.com/three.fits", "label": "Three"}
            ]
            app.run()

            for _ in range(12):
                if added_payloads:
                    break
                time.sleep(0.05)
                app.run()

        assert added_payloads, "Overlay payload should be added on the main thread"
        assert "ScriptRunContext" not in caplog.text
    finally:
        runtime = (
            app.session_state["ingest_runtime"]
            if "ingest_runtime" in app.session_state
            else {}
        )
        executor = runtime.get("executor") if isinstance(runtime, dict) else None
        if executor:
            executor.shutdown(wait=True)


def test_refresh_ingest_jobs_accepts_legacy_result(monkeypatch):
    """Legacy ingest results with status/detail/payload attributes are accepted."""

    from app.ui import main as main_module

    payload = {"label": "Legacy", "flux": [1.0], "wavelength_nm": [500.0]}

    class LegacyOverlayIngestResult:
        def __init__(self, status: str, detail: str, payload: Dict[str, Any]):
            self.status = status
            self.detail = detail
            self.payload = payload

    legacy_result = LegacyOverlayIngestResult(
        "success", "Prepared Legacy", dict(payload)
    )

    future = Future()
    future.set_result(legacy_result)

    added_payloads: List[Dict[str, Any]] = []

    def _fake_add_overlay_payload(data: Dict[str, Any]) -> tuple[bool, str]:
        added_payloads.append(data)
        label = data.get("label") or "overlay"
        return True, f"Added {label}"

    monkeypatch.setattr(main_module, "_add_overlay_payload", _fake_add_overlay_payload)

    runtime = {
        "lock": threading.Lock(),
        "jobs": {
            "legacy": {
                "id": "legacy",
                "status": "queued",
                "detail": "Waiting to start",
                "progress": 0.0,
                "submitted_at": time.time(),
                "started_at": None,
                "finished_at": None,
            }
        },
        "futures": {"legacy": future},
    }

    main_module._refresh_ingest_jobs(runtime)

    assert added_payloads == [payload]
    job = runtime["jobs"]["legacy"]
    assert job["status"] == "success"
    assert "Added Legacy" in job["detail"]


def test_refresh_ingest_jobs_handles_result_after_rerun(monkeypatch):
    """Completed futures from a previous run continue to add overlays."""

    from app.ui import main as main_module

    payload = {"label": "Rerun", "flux": [0.1], "wavelength_nm": [400.0]}

    # Capture the original dataclass before simulating a rerun.
    result_factory = main_module.OverlayIngestResult

    future: Future = Future()

    # Reload the module to simulate a Streamlit rerun creating a new module object.
    reloaded_main = importlib.reload(main_module)

    future.set_result(
        result_factory(status="success", detail="Prepared Rerun", payload=dict(payload))
    )

    added_payloads: List[Dict[str, Any]] = []

    def _fake_add_overlay_payload(data: Dict[str, Any]) -> tuple[bool, str]:
        added_payloads.append(data)
        label = data.get("label") or "overlay"
        return True, f"Added {label}"

    monkeypatch.setattr(reloaded_main, "_add_overlay_payload", _fake_add_overlay_payload)

    runtime = {
        "lock": threading.Lock(),
        "jobs": {
            "rerun": {
                "id": "rerun",
                "status": "queued",
                "detail": "Waiting to start",
                "progress": 0.0,
                "submitted_at": time.time(),
                "started_at": None,
                "finished_at": None,
            }
        },
        "futures": {"rerun": future},
    }

    reloaded_main._refresh_ingest_jobs(runtime)

    assert added_payloads == [payload]
    job = runtime["jobs"]["rerun"]
    assert job["status"] == "success"
    assert "Unexpected ingest result" not in job["detail"]
