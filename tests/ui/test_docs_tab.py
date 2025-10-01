from __future__ import annotations

from pathlib import Path

from app.ui import main as main_module


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_docs_tab_banner_uses_patch_metadata(monkeypatch, tmp_path):
    doc_path = tmp_path / "guide.md"
    doc_path.write_text("# Test guide", encoding="utf-8")

    custom_library = (
        main_module.DocCategory(
            title="Guides",
            description="Docs for testing.",
            entries=(
                main_module.DocEntry(
                    title="Intro",
                    path=Path(doc_path),
                    description="Intro guide.",
                ),
            ),
        ),
    )
    monkeypatch.setattr(main_module, "DOC_LIBRARY", custom_library)

    captured_info: list[str] = []
    st = main_module.st
    monkeypatch.setattr(st, "header", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda msg, *a, **k: captured_info.append(msg))
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "selectbox", lambda label, options, **k: options[0])
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "json", lambda *a, **k: None)
    monkeypatch.setattr(st, "expander", lambda *a, **k: _DummyContext())
    monkeypatch.setattr(st, "session_state", {}, raising=False)

    monkeypatch.setattr(main_module, "_get_overlays", lambda: [])

    version_info = {
        "version": "v1.2.0d",
        "patch_version": "v1.2.0d",
        "patch_summary": "Docs tab banner pulls from patch log",
        "patch_raw": "v1.2.0d: Docs tab banner pulls from patch log",
    }

    main_module._render_docs_tab(version_info)

    assert captured_info
    assert captured_info[0] == "v1.2.0d: Docs tab banner pulls from patch log"


def test_header_prefers_patch_version(monkeypatch):
    captured_caption: list[str] = []

    st = main_module.st
    monkeypatch.setattr(st, "title", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda msg, *a, **k: captured_caption.append(msg))

    version_info = {
        "version": "v0.0.0-dev",
        "patch_version": "v1.2.0e",
        "patch_summary": "(REF 1.2.0e-A01): Header pulls from patch metadata",
        "patch_raw": "v1.2.0e (REF 1.2.0e-A01): Header pulls from patch metadata",
        "date_utc": "2025-10-02T18:30:00Z",
    }

    main_module._render_app_header(version_info)

    assert captured_caption
    assert captured_caption[0].startswith("v1.2.0e • Updated 2025-10-02 18:30 UTC")
    assert "Header pulls from patch metadata" in captured_caption[0]
