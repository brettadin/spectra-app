"""Shared ingest result models for overlay workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OverlayIngestResult:
    """Outcome of an asynchronous overlay ingest job."""

    status: str
    detail: str
    payload: Optional[Dict[str, Any]] = None


__all__ = ["OverlayIngestResult"]
