from __future__ import annotations

import gzip
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

from app.server.ingest_ascii import parse_ascii
from app.server.ingest_fits import parse_fits
from app.utils.io_readers import read_table


SUPPORTED_ASCII_EXTENSIONS = {
    ".txt",
    ".text",
    ".csv",
    ".tsv",
    ".ssv",
    ".dat",
    ".data",
    ".tbl",
    ".tab",
    ".table",
    ".ascii",
    ".rdb",
    ".ecsv",
    ".log",
    ".out",
    ".spe",
    ".spec",
    ".spectrum",
}

SUPPORTED_FITS_EXTENSIONS = {".fits", ".fit", ".fts"}


class LocalIngestError(RuntimeError):
    """Raised when local spectra ingestion fails."""


def _detect_format(name: str, content: bytes) -> str:
    path = Path(name.lower())
    suffixes = path.suffixes or [path.suffix]
    if any(suffix in SUPPORTED_FITS_EXTENSIONS for suffix in suffixes):
        return "fits"
    signature = content[:6].upper()
    if signature.startswith(b"SIMPLE"):
        return "fits"
    if any(suffix in SUPPORTED_ASCII_EXTENSIONS for suffix in suffixes if suffix):
        return "ascii"
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - defensive path
        if signature.startswith(b"SIMPLE"):
            return "fits"
        raise LocalIngestError(f"Unable to determine file format for {name}.") from exc
    return "ascii"


def _clean_mapping(mapping: Mapping[str, object]) -> Dict[str, object]:
    cleaned: Dict[str, object] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        if isinstance(value, list):
            filtered = [item for item in value if item is not None]
            if filtered:
                cleaned[key] = filtered
            continue
        cleaned[key] = value
    return cleaned


def _choose_label(name: str, parsed: Mapping[str, object]) -> str:
    metadata = parsed.get("metadata") or {}
    candidates = [
        parsed.get("label_hint"),
        metadata.get("target"),
        metadata.get("source"),
        metadata.get("title"),
        Path(name).stem,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return Path(name).stem or "Spectrum"


def _build_summary(sample_count: int, metadata: Mapping[str, object], flux_unit: str) -> str:
    parts = [f"{sample_count} samples"]
    wavelength_range = metadata.get("wavelength_range_nm")
    if isinstance(wavelength_range, (list, tuple)) and len(wavelength_range) == 2:
        try:
            low, high = float(wavelength_range[0]), float(wavelength_range[1])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            pass
        else:
            parts.append(f"{low:.2f}–{high:.2f} nm")
    if flux_unit:
        parts.append(f"Flux: {flux_unit}")
    instrument = metadata.get("instrument")
    if isinstance(instrument, str) and instrument.strip():
        parts.append(instrument.strip())
    observation = metadata.get("observation_date")
    if isinstance(observation, str) and observation.strip():
        parts.append(observation.strip())
    return " • ".join(parts)


def _maybe_decompress(name: str, content: bytes) -> Tuple[str, bytes, Optional[Dict[str, object]]]:
    path = Path(name)
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes and suffixes[-1] in {".gz", ".gzip"}:
        try:
            decompressed = gzip.decompress(content)
        except OSError as exc:
            raise LocalIngestError(f"Failed to decompress {name}: {exc}") from exc
        inner_name = path.with_suffix("").name or name
        info: Dict[str, object] = {
            "original_size": len(content),
            "decompressed_size": len(decompressed),
        }
        info.setdefault("algorithm", "gzip")
        return inner_name, decompressed, info
    return name, content, None


def ingest_local_file(name: str, content: bytes) -> Dict[str, object]:
    """Parse a user-provided spectrum into an overlay payload."""

    if not content:
        raise LocalIngestError(f"{name} is empty; nothing to ingest.")

    original_name = name
    processed_name, payload, compression = _maybe_decompress(name, content)

    detected_format = _detect_format(processed_name, payload)

    try:
        if detected_format == "fits":
            parsed = parse_fits(payload, filename=processed_name)
        else:
            table = read_table(payload, include_header=True)
            parsed = parse_ascii(
                table.dataframe,
                content_bytes=payload,
                header_lines=table.header_lines,
                column_labels=table.column_labels,
                delimiter=table.delimiter,
                filename=processed_name,
                orientation=getattr(table, "orientation", None),
            )
    except Exception as exc:
        raise LocalIngestError(f"Failed to ingest {original_name}: {exc}") from exc

    metadata = _clean_mapping(dict(parsed.get("metadata") or {}))
    provenance = dict(parsed.get("provenance") or {})
    metadata.setdefault("source", "local upload")
    metadata.setdefault("filename", original_name)
    provenance.setdefault("filename", processed_name)
    if processed_name != original_name:
        provenance.setdefault("source_filename", original_name)
    if compression:
        metadata.setdefault("compression", compression)
        provenance.setdefault("compression", compression)
    ingest_info = provenance.setdefault(
        "ingest",
        {"method": "local_upload", "format": detected_format},
    )
    if compression:
        ingest_info["compression"] = compression

    label = _choose_label(original_name, parsed)
    flux_unit = str(parsed.get("flux_unit") or "arb")
    summary = parsed.get("summary") or _build_summary(
        len(parsed.get("wavelength_nm") or []), metadata, flux_unit
    )

    payload = {
        "label": label,
        "provider": "LOCAL",
        "summary": summary,
        "wavelength_nm": parsed.get("wavelength_nm") or [],
        "flux": parsed.get("flux") or [],
        "flux_unit": flux_unit,
        "flux_kind": parsed.get("flux_kind") or "relative",
        "metadata": metadata,
        "provenance": provenance,
        "kind": parsed.get("kind", "spectrum"),
        "axis": parsed.get("axis", "emission"),
    }

    return payload
