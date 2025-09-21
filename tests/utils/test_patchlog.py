from textwrap import dedent

from app.utils.patchlog import read_latest_patch_entry


def test_read_latest_patch_entry_returns_latest_version(tmp_path):
    log = tmp_path / "PATCHLOG.txt"
    log.write_text(
        dedent(
            """
            Spectra App — Patch Log (append-only)
            ===============================

            - v1.0.0a: Initial release
            - v1.0.0b minor adjustments
            - v1.0.0c – Stability pass
            """
        )
    )

    entry = read_latest_patch_entry(log)

    assert entry is not None
    assert entry.version == "v1.0.0c"
    assert entry.summary == "Stability pass"
    assert entry.raw == "v1.0.0c – Stability pass"


def test_read_latest_patch_entry_without_version(tmp_path):
    log = tmp_path / "PATCHLOG.txt"
    log.write_text(
        dedent(
            """
            Notes

            - General maintenance applied
            """
        )
    )

    entry = read_latest_patch_entry(log)

    assert entry is not None
    assert entry.version is None
    assert entry.summary == "General maintenance applied"
    assert entry.raw == "General maintenance applied"


def test_read_latest_patch_entry_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.txt"
    assert read_latest_patch_entry(missing) is None
