from __future__ import annotations
import json
from pathlib import Path

_DEFAULT = {"version": "v0.0.0-dev", "date_utc": "unknown", "summary": ""}

def get_version_info() -> dict:
    p = Path(__file__).parent / "version.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "version" not in data:
            return _DEFAULT
        return {
            "version": str(data.get("version", _DEFAULT["version"])),
            "date_utc": str(data.get("date_utc", _DEFAULT["date_utc"])),
            "summary": str(data.get("summary", _DEFAULT["summary"])).strip()
        }
    except Exception:
        return _DEFAULT
