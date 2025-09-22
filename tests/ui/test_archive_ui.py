from __future__ import annotations

from typing import Callable, List

from app import archive_ui as archive_ui_module
from app.providers.base import ProviderHit


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _DummyFigure:
    def add_trace(self, *args, **kwargs):
        return None

    def update_layout(self, *args, **kwargs):
        return None


def _patch_streamlit(monkeypatch, tabs_callback: Callable[[List[str]], List[_DummyContext]]):
    st = archive_ui_module.st
    monkeypatch.setattr(archive_ui_module.go, "Figure", lambda *a, **k: _DummyFigure())
    monkeypatch.setattr(archive_ui_module.go, "Scatter", lambda *a, **k: object())
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "tabs", tabs_callback)
    monkeypatch.setattr(st, "form", lambda *a, **k: _DummyContext())
    monkeypatch.setattr(st, "text_input", lambda *a, **k: "")
    monkeypatch.setattr(st, "slider", lambda *a, **k: k.get("value", 3))
    monkeypatch.setattr(st, "form_submit_button", lambda *a, **k: False)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "dataframe", lambda *a, **k: None)
    monkeypatch.setattr(st, "expander", lambda *a, **k: _DummyContext())
    monkeypatch.setattr(st, "plotly_chart", lambda *a, **k: None)
    monkeypatch.setattr(st, "columns", lambda *a, **k: [_DummyContext(), _DummyContext()])
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "json", lambda *a, **k: None)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    return st.session_state


def test_archive_ui_exposes_all_archives_tab(monkeypatch):
    captured_labels: List[str] = []

    def fake_tabs(labels: List[str]):
        captured_labels.extend(labels)
        return [_DummyContext() for _ in labels]

    _patch_streamlit(monkeypatch, fake_tabs)

    ui = archive_ui_module.ArchiveUI(add_overlay=lambda payload: (True, "ok"))
    ui.render()

    assert captured_labels[0] == "All Archives"
    assert captured_labels == [
        "All Archives",
        "MAST",
        "ESO",
        "SDSS",
        "DOI",
    ]


def test_archive_ui_all_tab_dispatches_combined_search(monkeypatch):
    captured_labels: List[str] = []

    def fake_tabs(labels: List[str]):
        captured_labels.extend(labels)
        return [_DummyContext() for _ in labels]

    session_state = _patch_streamlit(monkeypatch, fake_tabs)

    text_values = iter(
        [
            " Vega ",
            "STIS",
            "",
            "",
            "",
            "",
            "",
            "",
            "10.1234/foo",
            "Example DOI",
        ]
    )
    slider_values = iter([3, 3, 3, 3])
    submit_values = iter([True, False, False, False, False])

    st = archive_ui_module.st
    monkeypatch.setattr(st, "text_input", lambda *a, **k: next(text_values))
    monkeypatch.setattr(st, "slider", lambda *a, **k: next(slider_values))
    monkeypatch.setattr(st, "form_submit_button", lambda *a, **k: next(submit_values))

    hits = [
        ProviderHit(
            provider="MAST",
            identifier="mast-1",
            label="Vega (MAST)",
            summary="CALSPEC standard",
            wavelengths_nm=(500.0, 510.0),
            flux=(1.0, 0.9),
            metadata={"target_name": "Vega"},
            provenance={
                "archive": "MAST",
                "access_url": "https://example.test/mast",
                "fetched_at_utc": "2025-09-22T00:00:00Z",
            },
        )
    ]

    provider_calls: List[tuple[str, object]] = []

    def fake_search(name: str, query):
        provider_calls.append((name, query))
        return hits

    monkeypatch.setattr(archive_ui_module, "provider_search", fake_search)

    ui = archive_ui_module.ArchiveUI(add_overlay=lambda payload: (True, "ok"))
    ui.render()

    assert captured_labels[0] == "All Archives"
    assert provider_calls and provider_calls[0][0] == "ALL"
    query = provider_calls[0][1]
    assert query.target == "Vega"
    assert query.instrument == "STIS"
    assert query.limit == 3
    assert session_state["archive_results_all"] == hits
    assert session_state["archive_query_all"] == {
        "target": "Vega",
        "text": "",
        "instrument": "STIS",
        "doi": "",
        "limit": 3,
        "wavelength_range": (None, None),
    }
