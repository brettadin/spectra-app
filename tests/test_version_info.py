from app import _version
from app.utils.patchlog import PatchEntry


def test_get_version_info_includes_patch_metadata(monkeypatch):
    def fake_read_latest(path):
        return PatchEntry(version="v9.9.9z", summary="Test summary", raw="v9.9.9z: Test summary")

    monkeypatch.setattr(_version, "read_latest_patch_entry", fake_read_latest)

    info = _version.get_version_info()

    assert info["version"]
    assert info["patch_version"] == "v9.9.9z"
    assert info["patch_summary"] == "Test summary"
    assert info["patch_raw"] == "v9.9.9z: Test summary"


def test_get_version_info_falls_back_when_patch_missing(monkeypatch):
    monkeypatch.setattr(_version, "read_latest_patch_entry", lambda path: None)

    info = _version.get_version_info()

    assert info["patch_version"] == info["version"]
    assert info["patch_raw"]
    # Summary fallback may be empty if neither version.json nor patch log provide one.
    assert info["patch_summary"] == info.get("summary", "")
