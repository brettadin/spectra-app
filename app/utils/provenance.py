"""
Provenance helpers: one schema for both fetched and uploaded data.

Usage:
    from app.utils.provenance import write_provenance, ProvenanceRecord

    rec = ProvenanceRecord(
        source="MAST",
        target="HD 189733",
        instrument="HST/STIS",
        doi="10.17909/t9-j0xv-9p31",
        url="https://archive.stsci.edu/...",
        fetched_utc="2025-09-19T20:00:00Z",
        transformations=[
            {"op": "unit_convert", "from": "Å", "to": "nm"},
            {"op": "resample", "method": "linear", "dw": 0.1}
        ],
        notes="Fetched via astroquery.mast",
        schema_version="1.0"
    )
    write_provenance(rec, out_dir="exports/last_fetch")
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

@dataclass
class ProvenanceRecord:
    source: str
    target: str
    instrument: str | None
    doi: str | None
    url: str | None
    fetched_utc: str
    transformations: List[Dict[str, Any]]
    notes: str | None = None
    schema_version: str = "1.0"

def write_provenance(rec: ProvenanceRecord, out_dir: str) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / "provenance.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(rec), f, indent=2, ensure_ascii=False)
    return str(path)
