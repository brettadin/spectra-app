from __future__ import annotations

import gzip
import io
import warnings
import zipfile
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
from astropy import units as u
from astropy.units import UnitConversionError, UnitsError, UnitsWarning
from specutils import Spectrum1D

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


def _resolve_wavelength_quantity(
    values: Sequence[float],
    *,
    quantity: Optional[object],
    payload: Optional[Mapping[str, object]],
    metadata: Mapping[str, object],
) -> u.Quantity:
    if quantity is not None:
        try:
            spectral_axis = u.Quantity(quantity)
        except Exception as exc:  # pragma: no cover - defensive
            raise LocalIngestError(
                "Unable to interpret wavelength quantity from ingest payload."
            ) from exc
        if spectral_axis.shape and spectral_axis.size != len(values):
            raise LocalIngestError(
                "Wavelength quantity length does not match flux samples."
            )
        return spectral_axis

    unit_label = "nm"
    if isinstance(payload, Mapping):
        candidate = payload.get("unit")
        if isinstance(candidate, str) and candidate.strip():
            unit_label = candidate.strip()
    elif isinstance(metadata, Mapping):
        candidate = metadata.get("reported_wavelength_unit")
        if isinstance(candidate, str) and candidate.strip():
            unit_label = str(candidate).strip()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnitsWarning)
        try:
            unit = u.Unit(unit_label)
        except (ValueError, UnitsError) as exc:
            raise LocalIngestError(
                f"Unrecognised wavelength unit '{unit_label}' — update the file header to include a valid unit label."
            ) from exc

    return u.Quantity(values, unit=unit)


def _resolve_flux_quantity(values: Sequence[float], unit_label: str) -> u.Quantity:
    label = str(unit_label or "").strip()
    if not label:
        label = "arb"

    normalized = label.lower()
    custom_units = {
        "arb": u.dimensionless_unscaled,
        "arbitrary": u.dimensionless_unscaled,
        "relative": u.dimensionless_unscaled,
        "counts": u.ct,
        "count": u.ct,
        "adu": getattr(u, "adu", u.ct),
    }

    unit: u.Unit
    if normalized in custom_units:
        unit = custom_units[normalized]
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UnitsWarning)
            try:
                unit = u.Unit(label)
            except (ValueError, UnitsError) as exc:
                raise LocalIngestError(
                    f"Unrecognised flux unit '{label}' — rename the column to include a valid Astropy unit."
                ) from exc

    try:
        return u.Quantity(values, unit=unit)
    except (ValueError, TypeError, UnitConversionError) as exc:
        raise LocalIngestError(
            "Flux samples could not be converted into a physical quantity."
        ) from exc


def _build_spectrum1d(
    *,
    label: str,
    wavelengths: Sequence[float],
    flux: Sequence[float],
    flux_unit: str,
    wavelength_quantity: Optional[object],
    wavelength_payload: Optional[Mapping[str, object]],
    metadata: Mapping[str, object],
    axis_kind: Optional[str],
) -> Optional[Spectrum1D]:
    if str(axis_kind or "").lower() == "image":
        return None

    if len(wavelengths) != len(flux):
        raise LocalIngestError(
            f"{label or 'Spectrum'} contains mismatched wavelength and flux sample counts."
        )

    if not wavelengths or not flux:
        raise LocalIngestError(
            f"{label or 'Spectrum'} does not contain enough samples to build a Spectrum1D."
        )

    spectral_axis = _resolve_wavelength_quantity(
        wavelengths,
        quantity=wavelength_quantity,
        payload=wavelength_payload,
        metadata=metadata,
    )
    flux_quantity = _resolve_flux_quantity(flux, flux_unit)

    try:
        return Spectrum1D(flux=flux_quantity, spectral_axis=spectral_axis)
    except Exception as exc:  # pragma: no cover - Spectrum1D construction failure
        raise LocalIngestError(
            f"Failed to normalise {label or 'spectrum'} into a Spectrum1D object."
        ) from exc


def _attach_spectrum1d(
    payload: Mapping[str, object],
    *,
    default_label: str,
    flux_unit: str,
    metadata: Mapping[str, object],
) -> Optional[Spectrum1D]:
    wavelengths = payload.get("wavelength_nm") or []
    flux = payload.get("flux") or []
    label = str(payload.get("label") or default_label)
    axis_kind = payload.get("axis_kind") or (
        (payload.get("metadata") or {}).get("axis_kind")
        if isinstance(payload.get("metadata"), Mapping)
        else None
    )

    spectrum = _build_spectrum1d(
        label=label,
        wavelengths=wavelengths,
        flux=flux,
        flux_unit=str(payload.get("flux_unit") or flux_unit),
        wavelength_quantity=payload.get("wavelength_quantity"),
        wavelength_payload=payload.get("wavelength"),
        metadata=payload.get("metadata") or metadata,
        axis_kind=axis_kind,
    )

    return spectrum


def _summarize_image_statistics(
    image_payload: Mapping[str, object]
) -> Optional[Dict[str, float]]:
    data = image_payload.get("data")
    if data is None:
        return None
    try:
        array = np.asarray(data, dtype=float)
    except Exception:  # pragma: no cover - defensive conversion
        return None
    if array.size == 0:
        return None
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return None
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    median = float(np.median(finite))
    mean = float(np.mean(finite))
    p16, p84 = np.percentile(finite, [16, 84])
    return {
        "min": minimum,
        "max": maximum,
        "median": float(median),
        "mean": float(mean),
        "p16": float(p16),
        "p84": float(p84),
    }


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
                fallback_info: Optional[Dict[str, object]] = None
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
                    fallback_info = {
                        "method": "read_table",
                        "error": str(dense_exc),
                        "segments": [name for name, _ in segments],
                        "selected_segment": segment_name,
                    }
                    provenance = dict(fallback_payload.get("provenance") or {})
                    provenance["dense_parser_fallback"] = fallback_info
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
                if fallback_info is not None:
                    fallback_info = dict(fallback_info)
                    fallback_info["selected_segment"] = segment_name
                try:
                    parsed = _parse_ascii_table(segment_name, segment_payload)
                except Exception as fallback_exc:
                    raise fallback_exc from dense_exc
                else:
                    metadata = dict(parsed.get("metadata") or {})
                    metadata.setdefault("segments", [name for name, _ in segments])
                    parsed["metadata"] = metadata
                    provenance = dict(parsed.get("provenance") or {})
                    if fallback_info is None:
                        fallback_info = {
                            "method": "read_table",
                            "error": str(dense_exc),
                            "segments": [name for name, _ in segments],
                            "selected_segment": segment_name,
                        }
                    provenance["dense_parser_fallback"] = fallback_info
                    parsed["provenance"] = provenance
 
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
                try:
                    parsed = _parse_ascii_with_table(processed_name, payload)
                except ValueError as dense_exc:
                    if not _should_fallback_to_table(dense_exc):
                        raise
                    try:
                        parsed = _parse_ascii_table(processed_name, payload)
                    except Exception as fallback_exc:
                        raise fallback_exc from dense_exc

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
    axis_kind = parsed.get("axis_kind")
    normalized_axis_kind = str(axis_kind).lower() if axis_kind else None

    if normalized_axis_kind == "time":
        time_meta = metadata if isinstance(metadata, Mapping) else {}
        time_payload = parsed.get("time") if isinstance(parsed.get("time"), Mapping) else {}
        unit_label = (
            time_meta.get("time_unit")
            or time_meta.get("reported_time_unit")
            or time_payload.get("unit")
        )
        frame_label = time_meta.get("time_frame") or time_payload.get("frame")
        offset_value = time_meta.get("time_offset") or time_payload.get("offset")
        detail_parts: List[str] = []
        if unit_label:
            detail_parts.append(f"unit {unit_label}")
        if frame_label:
            detail_parts.append(str(frame_label))
        if offset_value is not None:
            detail_parts.append(f"offset {offset_value}")
        detail_hint = f" ({', '.join(detail_parts)})" if detail_parts else ""
        raise LocalIngestError(
            "Time-series products are not supported for overlays."
            f" Detected a time axis{detail_hint}."
        )

    image_statistics: Optional[Dict[str, float]] = None
    if normalized_axis_kind == "image":
        image_payload = parsed.get("image") if isinstance(parsed.get("image"), Mapping) else {}
        shape = image_payload.get("shape") if isinstance(image_payload, Mapping) else None
        if isinstance(shape, (list, tuple)):
            try:
                ingest_info.setdefault("samples", int(np.prod([int(dim) for dim in shape])))
            except Exception:
                ingest_info.setdefault("samples", 0)
        else:
            ingest_info.setdefault("samples", 0)
        if isinstance(image_payload, Mapping):
            existing_stats = metadata.get("image_statistics")
            if isinstance(existing_stats, Mapping):
                image_statistics = {
                    key: float(value)
                    for key, value in existing_stats.items()
                    if isinstance(value, (int, float))
                }
            else:
                image_statistics = _summarize_image_statistics(image_payload)
                if image_statistics:
                    metadata["image_statistics"] = dict(image_statistics)
    else:
        ingest_info.setdefault("samples", len(parsed.get("wavelength_nm") or []))

    label = _choose_label(original_name, parsed)
    if parsed.get("summary"):
        summary = parsed["summary"]
    elif normalized_axis_kind == "image":
        image_payload = parsed.get("image") if isinstance(parsed.get("image"), Mapping) else {}
        shape = image_payload.get("shape") if isinstance(image_payload, Mapping) else None
        if image_statistics is None and isinstance(image_payload, Mapping):
            image_statistics = _summarize_image_statistics(image_payload)
            if image_statistics:
                metadata.setdefault("image_statistics", dict(image_statistics))
        if isinstance(shape, (list, tuple)) and shape:
            dims = " × ".join(str(int(dim)) for dim in shape)
            if image_statistics and all(
                isinstance(image_statistics.get(key), (int, float))
                for key in ("min", "max")
            ):
                minimum = float(image_statistics["min"])
                maximum = float(image_statistics["max"])
                unit_suffix = f" {flux_unit}" if flux_unit else ""
                summary = (
                    f"{dims} image • Pixel range {minimum:.3g} – {maximum:.3g}{unit_suffix}"
                )
            else:
                summary = f"{dims} image"
        else:
            summary = "Image overlay"
    else:
        summary = _build_summary(
            len(parsed.get("wavelength_nm") or []), metadata, flux_unit
        )

    wavelengths = list(parsed.get("wavelength_nm") or [])
    flux_values = list(parsed.get("flux") or [])

    fallback_info = (parsed.get("provenance") or {}).get("dense_parser_fallback")
    min_samples = 2 if fallback_info else 3
    if normalized_axis_kind != "image":
        if len(wavelengths) < min_samples or len(flux_values) < min_samples:
            raise LocalIngestError(
                f"{original_name} contains only {min(len(wavelengths), len(flux_values))} samples; "
                "expected a spectral table rather than metadata."
            )

    wavelength_axis = parsed.get("wavelength")
    if isinstance(wavelength_axis, Mapping):
        wavelength_payload: Dict[str, object] = dict(wavelength_axis)
        wavelength_payload.setdefault("values", wavelengths)
    elif wavelength_axis is not None:
        wavelength_payload = {"values": wavelengths, "unit": str(wavelength_axis)}
    else:
        wavelength_payload = {"values": wavelengths, "unit": "nm"}

    payload = {
        "label": label,
        "provider": "LOCAL",
        "summary": summary,
        "wavelength_nm": wavelengths,
        "wavelength": wavelength_payload,
        "wavelength_quantity": parsed.get("wavelength_quantity"),
        "flux": flux_values,
        "flux_unit": flux_unit,
        "flux_kind": parsed.get("flux_kind") or "relative",
        "metadata": metadata,
        "provenance": provenance,
        "kind": parsed.get("kind", "spectrum"),
        "axis": parsed.get("axis", "emission"),
        "downsample": parsed.get("downsample"),
        "cache_dataset_id": metadata.get("cache_dataset_id"),
    }

    if axis_kind is not None:
        payload["axis_kind"] = axis_kind

    if normalized_axis_kind == "image" and isinstance(parsed.get("image"), Mapping):
        image_payload = dict(parsed.get("image"))
        if image_statistics:
            image_payload.setdefault("statistics", dict(image_statistics))
        payload["image"] = image_payload

    time_payload = parsed.get("time")
    if isinstance(time_payload, Mapping):
        payload["time"] = dict(time_payload)
    elif time_payload is not None:
        payload["time"] = time_payload

    additional = parsed.get("additional_traces")
    if isinstance(additional, list) and additional:
        enhanced_traces = []
        for entry in additional:
            if not isinstance(entry, Mapping):
                continue
            entry_payload = dict(entry)
            entry_metadata = entry_payload.get("metadata")
            if not isinstance(entry_metadata, Mapping):
                entry_metadata = metadata
                entry_payload["metadata"] = metadata
            flux_unit_entry = str(entry_payload.get("flux_unit") or flux_unit)
            try:
                spectrum_extra = _attach_spectrum1d(
                    entry_payload,
                    default_label=label,
                    flux_unit=flux_unit_entry,
                    metadata=entry_metadata,
                )
            except LocalIngestError as exc:
                trace_label = entry_payload.get("label") or label
                raise LocalIngestError(
                    f"Additional trace '{trace_label}' could not be normalised: {exc}"
                ) from exc
            if spectrum_extra is not None:
                entry_payload["spectrum1d"] = spectrum_extra
            enhanced_traces.append(entry_payload)
        payload["additional_traces"] = enhanced_traces

    try:
        base_spectrum = _attach_spectrum1d(
            payload,
            default_label=label,
            flux_unit=flux_unit,
            metadata=metadata,
        )
    except LocalIngestError as exc:
        raise LocalIngestError(f"{label} could not be normalised: {exc}") from exc
    if base_spectrum is not None:
        payload["spectrum1d"] = base_spectrum

    return payload
