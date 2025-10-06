from __future__ import annotations

from pathlib import Path

import pytest

from app.helpers.specviz_compat import HelperResult, SpecvizCompatError, SpecvizCompatHelper


def _write_ascii(path: Path, name: str) -> Path:
    file_path = path / name
    file_path.write_text("wavelength,flux\n400,1\n410,0.9\n420,1.05\n")
    return file_path


def test_helper_loads_paths_and_applies_label(tmp_path):
    helper = SpecvizCompatHelper()
    path = _write_ascii(tmp_path, "spec.csv")

    payload = helper.load_data([path], data_label="Custom")

    assert payload["label"] == "Custom"
    assert payload["provenance"]["helpers"][0]["helper"] == "SpecvizCompatHelper"


def test_helper_return_report(tmp_path):
    helper = SpecvizCompatHelper()
    good = _write_ascii(tmp_path, "good.csv")

    report = helper.load_data([good, tmp_path / "missing.csv"], return_report=True, allow_empty=True)

    assert report.summary["succeeded"] == 1
    assert report.summary["failed"] == 1
    success_entry = next(entry for entry in report.entries if entry.status == "success")
    assert success_entry.provenance["ingest"]["method"] == "specviz_helper"


def test_helper_diagnostics_allows_empty(tmp_path):
    helper = SpecvizCompatHelper()

    result = helper.load_data([tmp_path / "absent.csv"], diagnostics=True, allow_empty=True)

    assert isinstance(result, HelperResult)
    assert result.report.summary["failed"] == 1
    assert not result.payloads


def test_helper_directory_glob(tmp_path):
    helper = SpecvizCompatHelper()
    subdir = tmp_path / "data"
    subdir.mkdir()
    _write_ascii(subdir, "one.csv")
    (subdir / "skip.txt").write_text("not data")

    payloads = helper.load_data([], directory=subdir, glob="*.csv")

    assert isinstance(payloads, dict)
    assert payloads["label"] == "one"


def test_helper_raises_when_empty(tmp_path):
    helper = SpecvizCompatHelper()
    with pytest.raises(SpecvizCompatError):
        helper.load_data([], allow_empty=False)
