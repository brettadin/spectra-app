from __future__ import annotations

"""Base dataclasses and helpers for archive provider adapters."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

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
    programs: Tuple[str, ...] = field(default_factory=tuple)
    catalog: str = ""
    concatenate: bool = False
    use_cached_only: bool = False
    diagnostics: bool = False
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        programs = tuple(
            str(program).strip()
            for program in self.programs
            if isinstance(program, str) and str(program).strip()
        )
        object.__setattr__(self, "programs", programs)
        object.__setattr__(self, "options", dict(self.options or {}))

    def as_dict(self) -> Dict[str, object]:
        return {
            "target": self.target,
            "text": self.text,
            "instrument": self.instrument,
            "doi": self.doi,
            "limit": self.limit,
            "wavelength_range": self.wavelength_range,
            "programs": list(self.programs),
            "catalog": self.catalog,
            "concatenate": self.concatenate,
            "use_cached_only": self.use_cached_only,
            "diagnostics": self.diagnostics,
            "options": dict(self.options),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ProviderQuery":
        programs_raw = payload.get("programs", ())
        if isinstance(programs_raw, (str, bytes)):
            programs: Tuple[str, ...] = (str(programs_raw),)
        elif isinstance(programs_raw, Iterable):
            programs = tuple(str(value) for value in programs_raw)
        else:
            programs = ()

        options_raw = payload.get("options") or {}
        if isinstance(options_raw, Mapping):
            options = dict(options_raw)
        else:
            options = {}

        return cls(
            target=str(payload.get("target") or ""),
            text=str(payload.get("text") or ""),
            instrument=str(payload.get("instrument") or ""),
            doi=str(payload.get("doi") or ""),
            limit=int(payload.get("limit") or 5),
            wavelength_range=tuple(payload.get("wavelength_range") or (None, None)),
            programs=programs,
            catalog=str(payload.get("catalog") or ""),
            concatenate=bool(payload.get("concatenate")),
            use_cached_only=bool(payload.get("use_cached_only")),
            diagnostics=bool(payload.get("diagnostics")),
            options=options,
        )


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
