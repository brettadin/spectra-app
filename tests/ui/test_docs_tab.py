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
        "version": "v1.2.1",
        "patch_version": "v1.2.1",
        "patch_summary": "(REF 1.2.1-A01): relocate overlay trace helpers onto OverlayTrace, add a direct `_build_overlay_figure` regression, and roll continuity collateral.",
        "patch_raw": "v1.2.1 (REF 1.2.1-A01): relocate overlay trace helpers onto OverlayTrace, add a direct `_build_overlay_figure` regression, and roll continuity collateral.",
    }

    main_module._render_docs_tab(version_info)

    assert captured_info
    assert (
        captured_info[0]
        == "v1.2.1 (REF 1.2.1-A01): relocate overlay trace helpers onto OverlayTrace, add a direct `_build_overlay_figure` regression, and roll continuity collateral."
    )


def test_header_prefers_patch_version(monkeypatch):
    captured_caption: list[str] = []

    st = main_module.st
    monkeypatch.setattr(st, "title", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda msg, *a, **k: captured_caption.append(msg))

    version_info = {
        "version": "v0.0.0-dev",
        "patch_version": "v1.2.1",
        "patch_summary": "(REF 1.2.1-A01): relocate overlay trace helpers onto OverlayTrace, add a direct `_build_overlay_figure` regression, and roll continuity collateral.",
        "patch_raw": "v1.2.1 (REF 1.2.1-A01): relocate overlay trace helpers onto OverlayTrace, add a direct `_build_overlay_figure` regression, and roll continuity collateral.",
        "date_utc": "2025-10-17T09:30:00Z",
    }

    main_module._render_app_header(version_info)

    assert captured_caption
    assert captured_caption[0].startswith("v1.2.1 • Updated 2025-10-17 09:30 UTC")
    assert "relocate overlay trace helpers" in captured_caption[0]


def test_resolve_patch_metadata_returns_current_patch_line():
    from app import _version

    version_info = _version.get_version_info()
    patch_version, patch_summary, patch_line = main_module._resolve_patch_metadata(version_info)

    assert patch_version == "v1.2.1aa"
    assert (
        patch_summary
        == "(IR health hotfix): convert IR JCAMP Y-units to A10 with provenance, verify FIRSTY vs scaled samples, flip cm⁻¹ axes only when descending, and expose a ?health=1 Streamlit endpoint."
    )
    assert (
        patch_line
        == "v1.2.1aa (IR health hotfix): convert IR JCAMP Y-units to A10 with provenance, verify FIRSTY vs scaled samples, flip cm⁻¹ axes only when descending, and expose a ?health=1 Streamlit endpoint."
    )
