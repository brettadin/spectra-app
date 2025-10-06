from __future__ import annotations

"""Base dataclasses and helpers for archive provider adapters."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import pandas as pd


@dataclass(frozen=True)
class ProviderQuery:
    """Normalised query payload passed to provider adapters."""

    target: str = ""
    text: str = ""
    instrument: str = ""
    doi: str = ""
    limit: int = 5
    wavelength_range: Tuple[Optional[float], Optional[float]] = (None, None)

    def as_dict(self) -> Dict[str, object]:
        return {
            "target": self.target,
            "text": self.text,
            "instrument": self.instrument,
            "doi": self.doi,
            "limit": self.limit,
            "wavelength_range": self.wavelength_range,
        }


@dataclass
class ProviderHit:
    """Lightweight record describing a search hit with inline spectral data."""

    provider: str
    identifier: str
    label: str
    summary: str
    wavelengths_nm: Sequence[float]
    flux: Sequence[float]
    metadata: Mapping[str, object]
    provenance: MutableMapping[str, object]
    kind: str = "spectrum"

    def __post_init__(self) -> None:
        # Normalise provider case and ensure provenance metadata exists.
        self.provider = (self.provider or "").upper()
        self.provenance.setdefault("provider", self.provider)
        self.provenance.setdefault("retrieved_utc", datetime.utcnow().isoformat() + "Z")

    def to_dataframe(self) -> pd.DataFrame:
        """Return a tabular preview of the hit's spectral data."""

        data = {
            "wavelength_nm": list(self.wavelengths_nm),
            "flux": list(self.flux),
        }
        return pd.DataFrame(data)

    def to_overlay_payload(self) -> Dict[str, object]:
        """Return a serialisable payload for the overlay session state."""

        return {
            "label": self.label,
            "wavelength_nm": list(self.wavelengths_nm),
            "flux": list(self.flux),
            "provider": self.provider,
            "summary": self.summary,
            "kind": self.kind,
            "metadata": dict(self.metadata),
            "provenance": dict(self.provenance),
        }


def summarise_hits(hits: Iterable[ProviderHit]) -> pd.DataFrame:
    """Aggregate provider hits into a summary dataframe for display."""

    records: List[Dict[str, object]] = []
    for hit in hits:
        records.append(
            {
                "Provider": hit.provider,
                "Identifier": hit.identifier,
                "Label": hit.label,
                "Points": len(hit.wavelengths_nm),
                "Summary": hit.summary,
            }
        )
    if not records:
        return pd.DataFrame(columns=["Provider", "Identifier", "Label", "Points", "Summary"])
    return pd.DataFrame.from_records(records)
