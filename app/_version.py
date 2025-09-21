from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from app.utils.patchlog import read_latest_patch_entry

_DEFAULT: Dict[str, str] = {
    "version": "v0.0.0-dev",
    "date_utc": "unknown",
    "summary": "",
}
_PATCHLOG_PATH = Path(__file__).resolve().parent.parent / "PATCHLOG.txt"


def _load_version_json() -> Dict[str, str]:
    path = Path(__file__).parent / "version.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}

    version = str(data.get("version") or _DEFAULT["version"])
    date = str(data.get("date_utc") or _DEFAULT["date_utc"])
    summary = str(data.get("summary") or _DEFAULT["summary"]).strip()
    return {"version": version, "date_utc": date, "summary": summary}


def get_version_info() -> Dict[str, str]:
    info = _load_version_json()

    entry = read_latest_patch_entry(_PATCHLOG_PATH)
    summary_from_version = info.get("summary", "")

    patch_version = info.get("version", _DEFAULT["version"])
    patch_summary = summary_from_version
    patch_raw = ""

    if entry:
        if entry.version:
            patch_version = entry.version
        if entry.summary:
            patch_summary = entry.summary
        patch_raw = entry.raw

    patch_version_text = str(patch_version or info.get("version") or _DEFAULT["version"])
    patch_summary_text = str(patch_summary or summary_from_version or "").strip()

    if not patch_raw:
        if patch_summary_text and patch_version_text:
            patch_raw = f"{patch_version_text}: {patch_summary_text}"
        elif patch_summary_text:
            patch_raw = patch_summary_text
        else:
            patch_raw = patch_version_text

    if not info.get("summary") and patch_summary_text:
        info["summary"] = patch_summary_text

    info["patch_version"] = patch_version_text
    info["patch_summary"] = patch_summary_text
    info["patch_raw"] = patch_raw

    return info
