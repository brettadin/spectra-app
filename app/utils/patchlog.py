from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import re

__all__ = ["PatchEntry", "read_latest_patch_entry"]

_BULLET_PREFIXES: Sequence[str] = ("-", "*", "•", "–", "—")
_VERSION_RE = re.compile(r"^(?P<version>v[0-9][\w\.\-]*)\b(?P<rest>.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class PatchEntry:
    """Structured representation of a single patch log entry."""

    version: Optional[str]
    summary: str
    raw: str


def _parse_entry(text: str) -> Optional[PatchEntry]:
    """Convert a single patch log line (without bullet) into a PatchEntry."""

    candidate = text.strip()
    if not candidate:
        return None

    raw = candidate
    version: Optional[str] = None
    summary = candidate

    match = _VERSION_RE.match(candidate)
    if match:
        version = match.group("version").strip()
        rest = match.group("rest")
        summary = rest.lstrip(" \t:-–—").strip()
    else:
        summary = candidate.strip()

    return PatchEntry(version=version or None, summary=summary, raw=raw)


def read_latest_patch_entry(path: str | Path | None = None) -> Optional[PatchEntry]:
    """Return the most recent patch entry from ``PATCHLOG.txt``.

    Parameters
    ----------
    path:
        Optional override pointing to the patch log file. Defaults to ``PATCHLOG.txt``
        located in the project root when omitted.
    """

    patch_path = Path(path) if path is not None else Path("PATCHLOG.txt")
    if not patch_path.exists():
        return None
    try:
        lines = patch_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for raw_line in reversed(lines):
        cleaned = raw_line.strip()
        if not cleaned or cleaned.startswith("="):
            continue
        body = cleaned
        if cleaned[0] in _BULLET_PREFIXES:
            body = cleaned[1:].strip()
        entry = _parse_entry(body)
        if entry:
            return entry
    return None
