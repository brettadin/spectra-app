from __future__ import annotations

from pathlib import Path

MERGE_CONFLICT_MARKERS = ("<<<<<<<", ">>>>>>>")


def test_ui_main_has_no_merge_conflict_markers() -> None:
    """Ensure the UI entrypoint stays free of Git conflict artifacts."""
    repo_root = Path(__file__).resolve().parents[1]
    main_path = repo_root / "app" / "ui" / "main.py"
    contents = main_path.read_text(encoding="utf-8")

    for marker in MERGE_CONFLICT_MARKERS:
        assert (
            marker not in contents
        ), f"Found merge conflict marker {marker!r} in {main_path}"
