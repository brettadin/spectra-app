"""Persistent storage for dense spectral datasets and downsample tiers."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

import numpy as np


@dataclass(frozen=True)
class ChunkRecord:
    """Metadata describing a stored spectral chunk."""

    path: Path
    start_nm: float
    end_nm: float
    samples: int


class SpectrumCache:
    """Persist and retrieve dense spectra in chunked storage."""

    def __init__(self, base_dir: Path | None = None) -> None:
        env_dir = os.getenv("SPECTRA_CACHE_DIR")
        if base_dir is None and env_dir:
            base_dir = Path(env_dir)
        self.base_dir = base_dir or Path("data/cache/spectra")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def dataset_dir(self, dataset_id: str) -> Path:
        path = self.base_dir / dataset_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_chunk(
        self,
        dataset_id: str,
        chunk_index: int,
        wavelength_nm: Sequence[float],
        flux: Sequence[float],
        auxiliary: Optional[Sequence[float]] = None,
    ) -> ChunkRecord:
        data_dir = self.dataset_dir(dataset_id)
        path = data_dir / f"chunk_{chunk_index:05d}.npz"
        payload = {
            "wavelength_nm": np.asarray(wavelength_nm, dtype=np.float64),
            "flux": np.asarray(flux, dtype=np.float64),
        }
        if auxiliary is not None:
            payload["auxiliary"] = np.asarray(auxiliary, dtype=np.float64)
        np.savez_compressed(path, **payload)
        arr = payload["wavelength_nm"]
        if arr.size == 0:
            raise ValueError("Cannot store an empty spectral chunk")
        start_nm = float(np.nanmin(arr))
        end_nm = float(np.nanmax(arr))
        samples = int(arr.size)
        return ChunkRecord(path=path, start_nm=min(start_nm, end_nm), end_nm=max(start_nm, end_nm), samples=samples)

    def write_tier(
        self,
        dataset_id: str,
        tier_samples: int,
        wavelength_nm: Sequence[float],
        flux: Sequence[float],
    ) -> Path:
        data_dir = self.dataset_dir(dataset_id)
        path = data_dir / f"tier_{tier_samples:06d}.npz"
        np.savez_compressed(
            path,
            wavelength_nm=np.asarray(wavelength_nm, dtype=np.float64),
            flux=np.asarray(flux, dtype=np.float64),
        )
        return path

    def write_index(
        self,
        dataset_id: str,
        *,
        chunks: Sequence[ChunkRecord],
        metadata: Mapping[str, object],
        tiers: Sequence[int],
    ) -> Path:
        data_dir = self.dataset_dir(dataset_id)
        index_path = data_dir / "index.json"
        serialisable_chunks = [
            {
                "path": record.path.name,
                "start_nm": record.start_nm,
                "end_nm": record.end_nm,
                "samples": record.samples,
            }
            for record in chunks
        ]
        payload = {
            "dataset_id": dataset_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "chunks": serialisable_chunks,
            "metadata": dict(metadata),
            "tiers": sorted(int(value) for value in tiers),
        }
        index_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return index_path

