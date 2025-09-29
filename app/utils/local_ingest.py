from __future__ import annotations

import gzip
import io
import zipfile
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from app.server.ingest_ascii import parse_ascii, parse_ascii_segments
from app.server.ingest_fits import parse_fits
from app.utils.io_readers import read_table
from app.utils.spectrum_cache import SpectrumCache


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

_DENSE_SIZE_THRESHOLD = 12_000_000  # bytes
_DENSE_LINE_THRESHOLD = 400_000
_DENSE_CHUNK_SIZE = 500_000


class LocalIngestError(RuntimeError):
    """Raised when local spectra ingestion fails."""


def _detect_format(name: str, content: bytes) -> str:
    path = Path(name.lower())
    suffixes = path.suffixes or [path.suffix]
    if any(suffix == ".zip" for suffix in suffixes):
        return "zip"
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


def _build_summary(
    sample_count: int, metadata: Mapping[str, object], flux_unit: str
) -> str:
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


def _maybe_decompress(
    name: str, content: bytes
) -> Tuple[str, bytes, Optional[Dict[str, object]]]:
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


def _should_use_dense_parser(name: str, payload: bytes) -> bool:
    if len(payload) >= _DENSE_SIZE_THRESHOLD:
        return True
    line_count = payload.count(b"\n")
    if line_count >= _DENSE_LINE_THRESHOLD:
        return True
    sample = payload[:4096]
    if b"," not in sample and b"\t" not in sample and b";" not in sample:
        # Likely whitespace-delimited; favour the dense parser for robustness.
        return line_count > 0 and (len(sample.split()) // max(1, line_count or 1)) >= 3
    return False


def _should_fallback_to_table(error: Exception) -> bool:
    if not isinstance(error, ValueError):
        return False
    message = str(error).lower()
    return "no numeric samples" in message


def _parse_ascii_table(filename: str, payload: bytes) -> Dict[str, object]:
    table = read_table(payload, include_header=True)
    return parse_ascii(
        table.dataframe,
        content_bytes=payload,
        header_lines=table.header_lines,
        column_labels=table.column_labels,
        delimiter=table.delimiter,
        filename=filename,
        orientation=getattr(table, "orientation", None),
    )


def _read_zip_segments(name: str, content: bytes) -> List[Tuple[str, bytes]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise LocalIngestError(f"Failed to open archive {name}: {exc}") from exc

    segments: List[Tuple[str, bytes]] = []
    for info in archive.infolist():
        if info.is_dir():
            continue
        filename = info.filename
        if filename.startswith("__MACOSX"):
            continue
        suffix = Path(filename.lower()).suffix
        if suffix and suffix not in SUPPORTED_ASCII_EXTENSIONS:
            continue
        with archive.open(info) as handle:
            payload = handle.read()
        if not payload:
            continue
        segments.append((filename, payload))
    if not segments:
        raise LocalIngestError(
            f"Archive {name} did not contain supported ASCII spectra."
        )
    return segments


def _parse_ascii_with_table(name: str, payload: bytes) -> Dict[str, object]:
    table = read_table(payload, include_header=True)
    return parse_ascii(
        table.dataframe,
        content_bytes=payload,
        header_lines=table.header_lines,
        column_labels=table.column_labels,
        delimiter=table.delimiter,
        filename=name,
        orientation=getattr(table, "orientation", None),
    )


def _persist_dense_cache(
    parsed: Mapping[str, object],
    metadata: Mapping[str, object],
) -> Optional[Dict[str, object]]:
    provenance = parsed.get("provenance") or {}
    checksum = provenance.get("checksum")
    if not checksum:
        return None
    dataset_id = str(checksum)
    cache = SpectrumCache()
    wavelengths = np.asarray(parsed.get("wavelength_nm") or [], dtype=np.float64)
    flux = np.asarray(parsed.get("flux") or [], dtype=np.float64)
    auxiliary_values = parsed.get("auxiliary")
    aux = (
        np.asarray(auxiliary_values, dtype=np.float64)
        if isinstance(auxiliary_values, Sequence)
        else None
    )
    chunk_ranges = parsed.get("chunk_ranges") or []
    chunk_records = []
    chunk_size = int(metadata.get("dense_chunk_size", len(wavelengths)))
    if chunk_ranges:
        for index, chunk in enumerate(chunk_ranges):
            offset = int(chunk.get("offset", index * chunk_size))
            samples = int(chunk.get("samples", 0))
            if samples <= 0:
                continue
            end = min(offset + samples, wavelengths.size)
            if end <= offset:
                continue
            chunk_records.append(
                cache.write_chunk(
                    dataset_id,
                    index,
                    wavelengths[offset:end],
                    flux[offset:end],
                    aux[offset:end] if aux is not None else None,
                )
            )
    if not chunk_records and wavelengths.size:
        chunk_records.append(cache.write_chunk(dataset_id, 0, wavelengths, flux, aux))

    tiers = []
    for key, data in (parsed.get("downsample") or {}).items():
        try:
            tier = int(key)
        except (TypeError, ValueError):
            continue
        wavelengths_tier = np.asarray(data.get("wavelength_nm") or [], dtype=np.float64)
        flux_tier = np.asarray(data.get("flux") or [], dtype=np.float64)
        if not wavelengths_tier.size:
            continue
        cache.write_tier(dataset_id, tier, wavelengths_tier, flux_tier)
        tiers.append(tier)

    cache.write_index(dataset_id, chunks=chunk_records, metadata=metadata, tiers=tiers)
    return {
        "dataset_id": dataset_id,
        "path": str(cache.dataset_dir(dataset_id)),
        "chunks": [
            {
                "path": record.path.name,
                "start_nm": record.start_nm,
                "end_nm": record.end_nm,
                "samples": record.samples,
            }
            for record in chunk_records
        ],
        "tiers": sorted(tiers),
    }


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
        elif detected_format == "zip":
            segments = _read_zip_segments(processed_name, payload)
            try:
                parsed = parse_ascii_segments(
                    segments,
                    root_filename=processed_name,
                    chunk_size=_DENSE_CHUNK_SIZE,
                )
            except ValueError as dense_exc:
                fallback_payload: Optional[Dict[str, object]] = None
                last_error: Optional[Exception] = None
                for segment_name, segment_payload in segments:
                    try:
                        candidate = _parse_ascii_with_table(
                            segment_name, segment_payload
                        )
                    except (
                        Exception
                    ) as candidate_exc:  # pragma: no cover - fallback failure
                        last_error = candidate_exc
                        continue
                    fallback_payload = dict(candidate)
                    metadata = dict(fallback_payload.get("metadata") or {})
                    metadata.setdefault("segments", [name for name, _ in segments])
                    fallback_payload["metadata"] = metadata
                    provenance = dict(fallback_payload.get("provenance") or {})
                    provenance["dense_parser_fallback"] = {
                        "method": "read_table",
                        "error": str(dense_exc),
                        "segments": [name for name, _ in segments],
                        "selected_segment": segment_name,
                    }
                    fallback_payload["provenance"] = provenance
                    break
                if fallback_payload is None:
                    if last_error is not None:
                        raise dense_exc from last_error
                    raise dense_exc
                parsed = fallback_payload
                if not (_should_fallback_to_table(dense_exc) and len(segments) == 1):
                    raise
                segment_name, segment_payload = segments[0]
                try:
                    parsed = _parse_ascii_table(segment_name, segment_payload)
                except Exception as fallback_exc:
                    raise fallback_exc from dense_exc
        else:
            if _should_use_dense_parser(processed_name, payload):
                try:
                    parsed = parse_ascii_segments(
                        [(processed_name, payload)],
                        root_filename=processed_name,
                        chunk_size=_DENSE_CHUNK_SIZE,
                    )
                except ValueError as dense_exc:
                    try:
                        fallback_payload = _parse_ascii_with_table(
                            processed_name, payload
                        )
                    except (
                        Exception
                    ) as fallback_error:  # pragma: no cover - fallback failure
                        raise dense_exc from fallback_error
                    parsed = dict(fallback_payload)
                    provenance = dict(parsed.get("provenance") or {})
                    provenance["dense_parser_fallback"] = {
                        "method": "read_table",
                        "error": str(dense_exc),
                    }
                    parsed["provenance"] = provenance
            else:
                parsed = _parse_ascii_with_table(processed_name, payload)
                if not _should_fallback_to_table(dense_exc):
                        raise
                try:
                        parsed = _parse_ascii_table(processed_name, payload)
                except Exception as fallback_exc:
                        raise fallback_exc from dense_exc
                else:
                        parsed = _parse_ascii_table(processed_name, payload)
    except Exception as exc:
        raise LocalIngestError(f"Failed to ingest {original_name}: {exc}") from exc

    metadata = _clean_mapping(dict(parsed.get("metadata") or {}))
    provenance = dict(parsed.get("provenance") or {})

    cache_info: Optional[Dict[str, object]] = None
    if parsed.get("downsample"):
        cache_info = _persist_dense_cache(parsed, metadata)
        if cache_info:
            provenance.setdefault("cache", cache_info)
            metadata.setdefault("cache_dataset_id", cache_info.get("dataset_id"))
            metadata.setdefault("cache_path", cache_info.get("path"))

    parsed.pop("auxiliary", None)
    parsed.pop("chunk_ranges", None)

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
    if cache_info:
        ingest_info["cache_dataset_id"] = cache_info.get("dataset_id")

    label = _choose_label(original_name, parsed)
    flux_unit = str(parsed.get("flux_unit") or "arb")

    if processed_name:
        ingest_info.setdefault("filename", processed_name)
    checksum = provenance.get("checksum")
    if checksum:
        ingest_info.setdefault("checksum", checksum)

    flux_unit = str(parsed.get("flux_unit") or "arb")
    conversions: Dict[str, object] = {}
    original_unit = metadata.get("original_wavelength_unit")
    if original_unit and str(original_unit).lower() != "nm":
        conversions["wavelength_unit"] = {"from": original_unit, "to": "nm"}
    reported_flux = metadata.get("reported_flux_unit")
    if reported_flux and str(reported_flux) != flux_unit:
        conversions["flux_unit"] = {"from": reported_flux, "to": flux_unit}
    if conversions:
        ingest_info.setdefault("conversions", conversions)
    ingest_info.setdefault("samples", len(parsed.get("wavelength_nm") or []))

    label = _choose_label(original_name, parsed)
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
        "downsample": parsed.get("downsample"),
        "cache_dataset_id": metadata.get("cache_dataset_id"),
    }

    return payload
