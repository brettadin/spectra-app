"""Generate and parse provenance manifests.

The ProvenanceService is responsible for constructing JSON manifests that
capture the lineage of spectra and data transformations.  It records
metadata such as the application version, the source files and their
checksums, any transformation operations (e.g. unit conversions or math
operations), and citations for external knowledge.  See the specification
in `specs/provenance_schema.md` for details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib
import json
from pathlib import Path
import datetime


@dataclass
class ProvenanceService:
    """Service for creating provenance manifests."""

    app_name: str = "spectra-redesign"
    app_version: str = "0.1"

    def create_manifest(self, sources: List[Path], transforms: Optional[List[Dict[str, Any]]] = None,
                        citations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a provenance manifest for the given sources.

        Args:
            sources: A list of file paths to include in the manifest.  Each file
                will have its SHA‑256 hash computed.
            transforms: Optional list of transformation descriptors applied to
                the data after ingestion.  Each entry should include a name,
                parameters and a timestamp.
            citations: Optional list of citation dictionaries for external
                resources used.

        Returns:
            A manifest dictionary ready to be serialised to JSON.
        """
        src_entries = []
        for src in sources:
            hash_value = self._sha256(src)
            src_entries.append({
                "path": src.name,
                "sha256": hash_value,
                "units": {},
                "metadata": {}
            })
        manifest = {
            "app": {"name": self.app_name, "version": self.app_version},
            "timestamp": datetime.datetime.now().isoformat(),
            "sources": src_entries,
            "transforms": transforms or [],
            "citations": citations or []
        }
        return manifest

    def save_manifest(self, manifest: Dict[str, Any], path: Path) -> None:
        """Write the manifest dictionary to disk as formatted JSON."""
        with path.open('w') as f:
            json.dump(manifest, f, indent=2)

    def _sha256(self, path: Path) -> str:
        """Compute the SHA‑256 digest of a file."""
        h = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()