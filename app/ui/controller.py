from __future__ import annotations

import hashlib
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..server.differential import ratio, resample_to_common_grid, subtract
from ..similarity import (
    SimilarityCache,
    SimilarityOptions,
    TraceVectors,
    apply_normalization,
    viewport_alignment,
)
from ..utils.downsample import build_downsample_tiers, build_lttb_downsample
from ..utils.duplicate_ledger import DuplicateLedger
from ..utils.flux import flux_percentile_range


@dataclass
class OverlayTrace:
    trace_id: str
    label: str
    wavelength_nm: Tuple[float, ...]
    flux: Tuple[float, ...]
    kind: str = "spectrum"
    provider: Optional[str] = None
    summary: Optional[str] = None
    visible: bool = True
    metadata: Dict[str, object] = field(default_factory=dict)
    provenance: Dict[str, object] = field(default_factory=dict)
    fingerprint: str = ""
    hover: Optional[Tuple[str, ...]] = None
    flux_unit: str = "arb"
    flux_kind: str = "relative"
    axis: str = "emission"
    axis_kind: str = "wavelength"
    image: Optional[Dict[str, object]] = None
    downsample: Dict[int, Tuple[Tuple[float, ...], Tuple[float, ...]]] = field(
        default_factory=dict
    )
    cache_dataset_id: Optional[str] = None

    def to_dataframe(self) -> pd.DataFrame:
        if str(self.axis_kind).strip().lower() == "image":
            return pd.DataFrame(columns=["wavelength_nm", "flux"])

        data: Dict[str, Iterable[object]] = {
            "wavelength_nm": self.wavelength_nm,
            "flux": self.flux,
        }
        if self.hover:
            data["hover"] = list(self.hover)
        df = pd.DataFrame(data)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=["wavelength_nm", "flux"])
        return df.sort_values("wavelength_nm")

    def sample(
        self,
        viewport: Tuple[float | None, float | None],
        *,
        max_points: Optional[int] = 8000,
        include_hover: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[List[str]], bool]:
        if str(self.axis_kind).strip().lower() == "image":
            return np.array([], dtype=float), np.array([], dtype=float), None, True

        wavelengths = np.asarray(self.wavelength_nm, dtype=float)
        flux_values = np.asarray(self.flux, dtype=float)
        hover_values = list(self.hover) if include_hover and self.hover else None

        low, high = viewport
        if low is not None or high is not None:
            mask = np.ones_like(wavelengths, dtype=bool)
            if low is not None:
                mask &= wavelengths >= float(low)
            if high is not None:
                mask &= wavelengths <= float(high)
            wavelengths = wavelengths[mask]
            flux_values = flux_values[mask]
            if hover_values is not None:
                hover_values = [
                    hover for hover, keep in zip(hover_values, mask.tolist()) if keep
                ]

        if max_points is None:
            return wavelengths, flux_values, hover_values, True

        if wavelengths.size <= max_points:
            return wavelengths, flux_values, hover_values, True

        try:
            max_points_int = int(max_points)
        except (TypeError, ValueError):
            max_points_int = 0

        if max_points_int <= 0:
            return wavelengths, flux_values, hover_values, True

        if wavelengths.size <= max_points_int:
            return wavelengths, flux_values, hover_values, True

        min_points = max(64, max_points_int // 2)
        for tier in sorted(self.downsample.keys()):
            tier_data = self.downsample[tier]
            tier_w = np.asarray(tier_data[0], dtype=float)
            tier_f = np.asarray(tier_data[1], dtype=float)
            if low is not None:
                tier_w_mask = tier_w >= float(low)
            else:
                tier_w_mask = np.ones_like(tier_w, dtype=bool)
            if high is not None:
                tier_w_mask &= tier_w <= float(high)
            tier_w = tier_w[tier_w_mask]
            tier_f = tier_f[tier_w_mask]
            if tier_w.size == 0:
                continue
            if tier_w.size >= max_points_int:
                return tier_w[:max_points_int], tier_f[:max_points_int], None, False
            if tier_w.size >= min_points:
                return tier_w, tier_f, None, False

        target_points = min(max_points_int, int(wavelengths.size))
        downsampled = build_lttb_downsample(wavelengths, flux_values, target_points)
        sampled_w = np.asarray(downsampled.wavelength_nm, dtype=float)
        sampled_f = np.asarray(downsampled.flux, dtype=float)
        return sampled_w, sampled_f, None, False

    def to_vectors(
        self,
        *,
        max_points: Optional[int] = None,
        viewport: Tuple[float | None, float | None] | None = None,
    ) -> TraceVectors:
        if str(self.axis_kind).strip().lower() == "image":
            raise ValueError("Image overlays cannot be vectorised.")
        if max_points is None and viewport is None:
            df = self.to_dataframe()
            return TraceVectors(
                trace_id=self.trace_id,
                label=self.label,
                wavelengths_nm=df["wavelength_nm"].to_numpy(dtype=float),
                flux=df["flux"].to_numpy(dtype=float),
                kind=self.kind,
                fingerprint=self.fingerprint,
            )
        selected_w, selected_f, _, _ = self.sample(
            viewport or (None, None),
            max_points=max_points,
            include_hover=False,
        )
        return TraceVectors(
            trace_id=self.trace_id,
            label=self.label,
            wavelengths_nm=selected_w,
            flux=selected_f,
            kind=self.kind,
            fingerprint=self.fingerprint,
        )

    @property
    def points(self) -> int:
        if str(self.axis_kind).strip().lower() == "image":
            shape = self.image.get("shape") if isinstance(self.image, Mapping) else None
            if isinstance(shape, (list, tuple)):
                try:
                    return int(np.prod([int(dim) for dim in shape]))
                except Exception:
                    return 0
            return 0
        return len(self.wavelength_nm)


@dataclass
class DifferentialResult:
    grid_nm: Tuple[float, ...]
    values_a: Tuple[float, ...]
    values_b: Tuple[float, ...]
    result: Tuple[float, ...]
    trace_a_id: str
    trace_b_id: str
    trace_a_label: str
    trace_b_label: str
    operation_code: str
    operation_label: str
    normalization: str
    sample_points: int
    computed_at: float
    label: str


DIFFERENTIAL_OPERATIONS: Dict[str, Dict[str, object]] = {
    "Subtract (A − B)": {"code": "subtract", "symbol": "−", "func": subtract},
    "Ratio (A ÷ B)": {"code": "ratio", "symbol": "÷", "func": ratio},
}


def normalize_axis_kind(value: Optional[str]) -> str:
    try:
        text = str(value or "")
    except Exception:
        text = ""
    text = text.strip().lower()
    return text or "wavelength"


def axis_kind_for_trace(trace: OverlayTrace) -> str:
    return normalize_axis_kind(getattr(trace, "axis_kind", None))


def group_overlays_by_axis_kind(
    overlays: Sequence[OverlayTrace],
) -> Dict[str, List[OverlayTrace]]:
    groups: Dict[str, List[OverlayTrace]] = {}
    for trace in overlays:
        kind = axis_kind_for_trace(trace)
        if kind == "time":
            continue
        groups.setdefault(kind, []).append(trace)
    return groups


def normalize_viewport_tuple(
    viewport: Tuple[float | None, float | None] | Sequence[float | None] | None,
) -> Tuple[float | None, float | None]:
    if not isinstance(viewport, Sequence) or len(viewport) != 2:
        return (None, None)

    def _coerce(value: object) -> float | None:
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    low = _coerce(viewport[0])
    high = _coerce(viewport[1])
    return (low, high)


def get_viewport_store(
    state: MutableMapping[str, Any],
    key: str,
) -> Dict[str, Tuple[float | None, float | None]]:
    store = state.get(key)
    if not isinstance(store, Mapping):
        return {}
    normalized: Dict[str, Tuple[float | None, float | None]] = {}
    for kind, viewport in store.items():
        normalized[normalize_axis_kind(kind)] = normalize_viewport_tuple(viewport)
    return normalized


def set_viewport_store(
    state: MutableMapping[str, Any],
    key: str,
    store: Mapping[str, Tuple[float | None, float | None]],
) -> None:
    state[key] = dict(store)


def set_viewport_for_kind(
    state: MutableMapping[str, Any],
    key: str,
    axis_kind: str,
    viewport: Tuple[float | None, float | None],
) -> None:
    store = get_viewport_store(state, key)
    store[normalize_axis_kind(axis_kind)] = normalize_viewport_tuple(viewport)
    set_viewport_store(state, key, store)


def get_viewport_for_kind(
    state: MutableMapping[str, Any],
    key: str,
    axis_kind: str,
) -> Tuple[float | None, float | None]:
    store = get_viewport_store(state, key)
    return store.get(normalize_axis_kind(axis_kind), (None, None))


def determine_primary_axis_kind(
    overlays: Sequence[OverlayTrace],
) -> str:
    groups = group_overlays_by_axis_kind(overlays)
    if groups.get("wavelength"):
        return "wavelength"
    for kind, traces in groups.items():
        if kind == "image":
            continue
        if traces:
            return kind
    return "wavelength"


def ensure_session_defaults(state: MutableMapping[str, Any], viewport_key: str) -> None:
    state.setdefault("session_id", str(uuid.uuid4()))
    state.setdefault("overlay_traces", [])
    state.setdefault("display_units", "nm")
    state.setdefault("display_mode", "Flux (raw)")
    state.setdefault("display_full_resolution", False)
    if viewport_key not in state:
        legacy = state.get("viewport_nm")
        if isinstance(legacy, Sequence) and len(legacy) == 2:
            set_viewport_store(
                state,
                viewport_key,
                {"wavelength": normalize_viewport_tuple(legacy)},
            )
        else:
            set_viewport_store(state, viewport_key, {"wavelength": (None, None)})
    else:
        store = get_viewport_store(state, viewport_key)
        if "wavelength" not in store:
            store["wavelength"] = (None, None)
        set_viewport_store(state, viewport_key, store)
    if "viewport_nm" in state:
        try:
            del state["viewport_nm"]
        except Exception:
            state["viewport_nm"] = None
    state.setdefault("auto_viewport", True)
    state.setdefault("normalization_mode", "unit")
    state.setdefault("differential_mode", "Off")
    state.setdefault("reference_trace_id", None)
    state.setdefault("similarity_metrics", ["cosine", "rmse", "xcorr", "line_match"])
    state.setdefault("similarity_primary_metric", "cosine")
    state.setdefault("similarity_line_peaks", 8)
    state.setdefault(
        "similarity_normalization", state.get("normalization_mode", "unit")
    )
    state.setdefault("duplicate_policy", "skip")
    state.setdefault("local_upload_registry", {})
    state.setdefault("differential_result", None)
    state.setdefault("differential_sample_points", 2000)
    state.setdefault("network_available", True)
    state.setdefault("example_recent", [])
    state.setdefault("duplicate_base_policy", "skip")
    state.setdefault("duplicate_ledger_lock", False)
    state.setdefault("duplicate_ledger_pending_action", None)
    state.setdefault("ingest_queue", [])
    if "duplicate_ledger" not in state:
        state["duplicate_ledger"] = DuplicateLedger()
    if "similarity_cache" not in state:
        state["similarity_cache"] = SimilarityCache()


def get_overlays(state: MutableMapping[str, Any]) -> List[OverlayTrace]:
    return list(state.get("overlay_traces", []))


def set_overlays(state: MutableMapping[str, Any], overlays: Sequence[OverlayTrace]) -> None:
    state["overlay_traces"] = list(overlays)
    ensure_reference_consistency(state)


def ensure_reference_consistency(state: MutableMapping[str, Any]) -> None:
    overlays = get_overlays(state)
    current = state.get("reference_trace_id")
    if current and any(trace.trace_id == current for trace in overlays):
        return
    if overlays:
        state["reference_trace_id"] = overlays[0].trace_id
    else:
        state["reference_trace_id"] = None


def trace_label(state: MutableMapping[str, Any], trace_id: Optional[str]) -> str:
    if trace_id is None:
        return "—"
    for trace in get_overlays(state):
        if trace.trace_id == trace_id:
            suffix = f" ({trace.provider})" if trace.provider else ""
            return f"{trace.label}{suffix}"
    return trace_id


def compute_fingerprint(
    wavelengths: Sequence[float], flux: Sequence[float]
) -> str:
    arr_w = np.asarray([float(w) for w in wavelengths], dtype=np.float64)
    arr_f = np.asarray([float(f) for f in flux], dtype=np.float64)
    combined = np.stack((np.round(arr_w, 6), np.round(arr_f, 6)), axis=1)
    return hashlib.sha1(combined.tobytes()).hexdigest()


def compute_image_fingerprint(image: Mapping[str, object]) -> str:
    data = image.get("data")
    arr = np.asarray(data, dtype=np.float64)
    flattened = np.round(arr.reshape(-1), 6)
    payload_parts = [flattened.tobytes()]
    mask = image.get("mask")
    if mask is not None:
        mask_arr = np.asarray(mask, dtype=np.bool_).reshape(-1)
        payload_parts.append(mask_arr.tobytes())
    shape = image.get("shape")
    if isinstance(shape, (list, tuple)):
        shape_tuple = tuple(int(dim) for dim in shape)
    else:
        shape_tuple = tuple(int(dim) for dim in arr.shape)
    payload_parts.append(repr(shape_tuple).encode("utf-8"))
    dtype_label = str(image.get("dtype") or arr.dtype)
    payload_parts.append(dtype_label.encode("utf-8"))
    return hashlib.sha1(b"".join(payload_parts)).hexdigest()


def _build_downsample_map(
    payload: Mapping[str, object],
    values_w: Sequence[float],
    values_f: Sequence[float],
) -> Dict[int, Tuple[Tuple[float, ...], Tuple[float, ...]]]:
    downsample_map: Dict[int, Tuple[Tuple[float, ...], Tuple[float, ...]]] = {}
    source = payload.get("downsample")
    if isinstance(source, Mapping):
        for tier, tier_payload in source.items():
            try:
                tier_value = int(tier)
            except (TypeError, ValueError):
                continue
            if tier_value <= 0:
                continue
            if not isinstance(tier_payload, Mapping):
                continue
            wavelengths_ds = tier_payload.get("wavelength_nm")
            flux_ds = tier_payload.get("flux")
            if not wavelengths_ds or not flux_ds:
                continue
            if len(wavelengths_ds) != len(flux_ds):
                continue
            downsample_map[tier_value] = (
                tuple(float(value) for value in wavelengths_ds),
                tuple(float(value) for value in flux_ds),
            )
    if not downsample_map:
        generated = build_downsample_tiers(values_w, values_f, strategy="lttb")
        downsample_map = {
            tier: (tuple(result.wavelength_nm), tuple(result.flux))
            for tier, result in generated.items()
        }
    return downsample_map


def add_overlay(
    state: MutableMapping[str, Any],
    label: str,
    wavelengths: Sequence[float],
    flux: Sequence[float],
    *,
    flux_unit: Optional[str] = None,
    flux_kind: Optional[str] = None,
    kind: str = "spectrum",
    provider: Optional[str] = None,
    summary: Optional[str] = None,
    metadata: Optional[Dict[str, object]] = None,
    provenance: Optional[Dict[str, object]] = None,
    hover: Optional[Sequence[str]] = None,
    axis: Optional[str] = None,
    axis_kind: Optional[str] = None,
    downsample: Optional[Mapping[int, Mapping[str, Sequence[float]]]] = None,
    cache_dataset_id: Optional[str] = None,
    image: Optional[Mapping[str, object]] = None,
) -> Tuple[bool, str]:
    normalized_axis_kind = normalize_axis_kind(
        axis_kind
        or (metadata or {}).get("axis_kind")
        if isinstance(metadata, Mapping)
        else axis_kind
    )

    if normalized_axis_kind == "time":
        return (
            False,
            "Time-series overlays are not supported. Provide a spectral product instead.",
        )

    if normalized_axis_kind == "image":
        if not isinstance(image, Mapping):
            return False, "No image payload provided."
        data = image.get("data")
        try:
            data_array = np.asarray(data, dtype=float)
        except Exception as exc:
            return False, f"Unable to interpret image pixels: {exc}"
        if data_array.size == 0:
            return False, "Image payload contains no pixels."
        overlays = get_overlays(state)
        fingerprint = compute_image_fingerprint(image)
        policy = state.get("duplicate_policy", "allow")
        if policy in {"skip", "ledger"}:
            for existing in overlays:
                if existing.fingerprint == fingerprint:
                    return False, f"Skipped duplicate trace: {label}"
            if policy == "ledger":
                ledger: DuplicateLedger = state["duplicate_ledger"]
                if ledger.seen(fingerprint):
                    return False, f"Trace already recorded in ledger: {label}"

        trace = OverlayTrace(
            trace_id=str(uuid.uuid4()),
            label=label,
            wavelength_nm=tuple(),
            flux=tuple(),
            kind=kind,
            provider=provider,
            summary=summary,
            metadata=dict(metadata or {}),
            provenance=dict(provenance or {}),
            fingerprint=fingerprint,
            hover=None,
            flux_unit=str(flux_unit or "arb"),
            flux_kind=str(flux_kind or "relative"),
            axis=str(axis or "image"),
            axis_kind="image",
            image=dict(image),
            downsample={},
            cache_dataset_id=cache_dataset_id,
        )
        overlays = get_overlays(state)
        overlays.append(trace)
        set_overlays(state, overlays)

        if policy == "ledger":
            ledger = state["duplicate_ledger"]
            ledger.record(
                fingerprint,
                {
                    "label": label,
                    "provider": provider,
                    "session_id": state.get("session_id"),
                    "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            )

        if not state.get("reference_trace_id"):
            state["reference_trace_id"] = trace.trace_id

        message = f"Added {label}"
        if provider:
            message += f" ({provider})"
        return True, message

    values_w = [float(value) for value in wavelengths]
    values_f = [float(value) for value in flux]
    if len(values_w) != len(values_f):
        return False, "Wavelength and flux arrays must have equal length."

    if not values_w or not values_f:
        return False, "No samples provided."

    hover_sorted: Optional[List[str]] = None
    if hover:
        hover_sorted = [str(text) for text in hover]

    payload = {"downsample": downsample} if downsample is not None else {}
    downsample_map = _build_downsample_map(payload, values_w, values_f)

    overlays = get_overlays(state)
    fingerprint = compute_fingerprint(values_w, values_f)
    policy = state.get("duplicate_policy", "allow")
    if policy in {"skip", "ledger"}:
        for existing in overlays:
            if existing.fingerprint == fingerprint:
                return False, f"Skipped duplicate trace: {label}"
        if policy == "ledger":
            ledger: DuplicateLedger = state["duplicate_ledger"]
            if ledger.seen(fingerprint):
                return False, f"Trace already recorded in ledger: {label}"

    resolved_axis_kind = normalized_axis_kind or "wavelength"

    trace = OverlayTrace(
        trace_id=str(uuid.uuid4()),
        label=label,
        wavelength_nm=tuple(values_w),
        flux=tuple(values_f),
        kind=kind,
        provider=provider,
        summary=summary,
        metadata=dict(metadata or {}),
        provenance=dict(provenance or {}),
        fingerprint=fingerprint,
        hover=(
            tuple(str(text) for text in (hover_sorted or [])) if hover_sorted else None
        ),
        flux_unit=str(flux_unit or "arb"),
        flux_kind=str(flux_kind or "relative"),
        axis=str(axis or "emission"),
        axis_kind=resolved_axis_kind,
        image=None,
        downsample=downsample_map,
        cache_dataset_id=cache_dataset_id,
    )
    overlays.append(trace)
    set_overlays(state, overlays)

    if policy == "ledger":
        ledger = state["duplicate_ledger"]
        ledger.record(
            fingerprint,
            {
                "label": label,
                "provider": provider,
                "session_id": state.get("session_id"),
                "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

    if not state.get("reference_trace_id"):
        state["reference_trace_id"] = trace.trace_id

    message = f"Added {label}"
    if provider:
        message += f" ({provider})"
    return True, message


def add_overlay_payload(
    state: MutableMapping[str, Any], payload: Mapping[str, object]
) -> Tuple[bool, str]:
    base_added, base_message = add_overlay(
        state,
        str(payload.get("label") or "Trace"),
        payload.get("wavelength_nm") or [],
        payload.get("flux") or [],
        flux_unit=payload.get("flux_unit"),
        flux_kind=payload.get("flux_kind"),
        kind=str(payload.get("kind") or "spectrum"),
        provider=payload.get("provider"),
        summary=payload.get("summary"),
        metadata=payload.get("metadata"),
        provenance=payload.get("provenance"),
        hover=payload.get("hover"),
        axis=payload.get("axis"),
        axis_kind=payload.get("axis_kind")
        or (
            (payload.get("metadata") or {}).get("axis_kind")
            if isinstance(payload.get("metadata"), Mapping)
            else None
        ),
        downsample=payload.get("downsample"),
        cache_dataset_id=payload.get("cache_dataset_id"),
        image=payload.get("image") if isinstance(payload.get("image"), Mapping) else None,
    )
    additional = payload.get("additional_traces")
    extra_success = 0
    failure_messages: List[str] = []
    if isinstance(additional, Sequence):
        for entry in additional:
            if not isinstance(entry, Mapping):
                continue
            label = entry.get("label")
            extra_label = (
                str(label)
                if label is not None
                else f"{payload.get('label', 'Trace')} (extra)"
            )
            success, message = add_overlay(
                state,
                extra_label,
                entry.get("wavelength_nm") or [],
                entry.get("flux") or [],
                flux_unit=entry.get("flux_unit") or payload.get("flux_unit"),
                flux_kind=entry.get("flux_kind") or payload.get("flux_kind"),
                kind=str(entry.get("kind") or payload.get("kind") or "spectrum"),
                provider=entry.get("provider") or payload.get("provider"),
                summary=entry.get("summary") or payload.get("summary"),
                metadata=entry.get("metadata") or payload.get("metadata"),
                provenance=entry.get("provenance") or payload.get("provenance"),
                hover=entry.get("hover"),
                axis=entry.get("axis") or payload.get("axis"),
                axis_kind=entry.get("axis_kind")
                or (
                    (entry.get("metadata") or {}).get("axis_kind")
                    if isinstance(entry.get("metadata"), Mapping)
                    else None
                ),
                downsample=entry.get("downsample"),
                cache_dataset_id=entry.get("cache_dataset_id")
                or payload.get("cache_dataset_id"),
                image=entry.get("image")
                if isinstance(entry.get("image"), Mapping)
                else (
                    payload.get("image")
                    if isinstance(payload.get("image"), Mapping)
                    else None
                ),
            )
            if success:
                extra_success += 1
            else:
                failure_messages.append(message)

    combined_message = base_message
    if extra_success:
        combined_message += f"; added {extra_success} additional series"
    if failure_messages:
        combined_message += "; " + "; ".join(failure_messages)

    return base_added or extra_success > 0, combined_message


def infer_viewport_bounds(overlays: Sequence[OverlayTrace]) -> Tuple[float, float]:
    if not overlays:
        return 350.0, 900.0

    meta_ranges: List[Tuple[float, float]] = []
    data_wavelengths: List[float] = []

    for trace in overlays:
        meta_range = extract_metadata_range(trace.metadata)
        if meta_range is not None:
            meta_ranges.append(meta_range)
        data_wavelengths.extend(trace.wavelength_nm)

    if meta_ranges:
        lows, highs = zip(*meta_ranges)
        low = float(min(lows))
        high = float(max(highs))
        if math.isfinite(low) and math.isfinite(high) and low < high:
            return low, high

    arr = np.array(data_wavelengths, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 350.0, 900.0
    return float(arr.min()), float(arr.max())


def auto_viewport_range(
    overlays: Sequence[OverlayTrace],
    *,
    coverage: float = 0.99,
    axis_kind: Optional[str] = None,
) -> Optional[Tuple[float, float]]:
    normalized_kind = normalize_axis_kind(axis_kind) if axis_kind else None
    if normalized_kind is not None:
        overlays = [
            trace for trace in overlays if axis_kind_for_trace(trace) == normalized_kind
        ]
    visible = [trace for trace in overlays if trace.visible]
    target = visible if visible else list(overlays)
    if not target:
        return None

    ranges: List[Tuple[float, float]] = []
    data_low = math.inf
    data_high = -math.inf
    for trace in target:
        wavelengths = np.asarray(trace.wavelength_nm, dtype=float)
        flux_values = np.asarray(trace.flux, dtype=float)
        if wavelengths.size == 0 or flux_values.size == 0:
            continue

        data_low = min(data_low, float(np.min(wavelengths)))
        data_high = max(data_high, float(np.max(wavelengths)))

        interval = flux_percentile_range(wavelengths, flux_values, coverage=coverage)
        if interval is not None:
            ranges.append((float(interval[0]), float(interval[1])))

    if not ranges:
        return None

    low = min(low for low, _ in ranges)
    high = max(high for _, high in ranges)
    if not (math.isfinite(low) and math.isfinite(high)) or low >= high:
        return None

    if math.isfinite(data_low) and math.isfinite(data_high) and data_high > data_low:
        pad = 0.01 * (data_high - data_low)
        if pad > 0.0:
            low = max(low - pad, data_low)
            high = min(high + pad, data_high)

    return float(low), float(high)


def effective_viewport(
    overlays: Sequence[OverlayTrace],
    viewport: Tuple[float | None, float | None],
    *,
    axis_kind: Optional[str] = None,
) -> Tuple[float | None, float | None]:
    if not overlays:
        return (None, None)

    normalized_viewport = normalize_viewport_tuple(viewport)
    low, high = normalized_viewport
    if low is not None or high is not None:
        return (
            float(low) if low is not None else None,
            float(high) if high is not None else None,
        )

    target_kind = axis_kind or axis_kind_for_trace(overlays[0])
    auto_range = auto_viewport_range(overlays, axis_kind=target_kind)
    if auto_range is not None:
        return float(auto_range[0]), float(auto_range[1])

    fallback_low, fallback_high = infer_viewport_bounds(overlays)
    return float(fallback_low), float(fallback_high)


def extract_metadata_range(
    metadata: Mapping[str, object],
) -> Optional[Tuple[float, float]]:
    axis_kind = None
    if isinstance(metadata, Mapping):
        axis_kind = metadata.get("axis_kind")
    if axis_kind == "time":
        keys = ("data_time_range", "time_range")
    else:
        keys = ("wavelength_effective_range_nm", "wavelength_range_nm")
    for key in keys:
        value = metadata.get(key) if metadata else None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            try:
                low = float(value[0])
                high = float(value[1])
            except (TypeError, ValueError):
                continue
            if math.isfinite(low) and math.isfinite(high) and low < high:
                return min(low, high), max(low, high)
    return None


def filter_viewport(
    df: pd.DataFrame, viewport: Tuple[float | None, float | None]
) -> pd.DataFrame:
    low, high = viewport
    if low is not None:
        df = df[df["wavelength_nm"] >= low]
    if high is not None:
        df = df[df["wavelength_nm"] <= high]
    return df


def convert_wavelength(series: pd.Series, unit: str) -> Tuple[pd.Series, str]:
    unit = unit or "nm"
    values = pd.to_numeric(series, errors="coerce")
    if unit == "Å":
        return values * 10.0, "Wavelength (Å)"
    if unit == "µm":
        return values / 1000.0, "Wavelength (µm)"
    if unit == "cm^-1":
        safe = values.replace(0, np.nan)
        return 1e7 / safe, "Wavenumber (cm⁻¹)"
    return values, "Wavelength (nm)"


def _time_axis_labels(
    metadata: Mapping[str, object], provenance: Mapping[str, object]
) -> Tuple[Optional[str], Optional[str]]:
    def _clean(value: object) -> Optional[str]:
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text
        return None

    meta = metadata if isinstance(metadata, Mapping) else {}
    provenance_map = provenance if isinstance(provenance, Mapping) else {}
    units_meta = provenance_map.get("units") if isinstance(provenance_map, Mapping) else {}
    if not isinstance(units_meta, Mapping):
        units_meta = {}

    unit_label = (
        _clean(meta.get("time_unit"))
        or _clean(meta.get("reported_time_unit"))
        or _clean(meta.get("time_original_unit"))
        or _clean(meta.get("axis_unit"))
        or _clean(units_meta.get("time_converted_to"))
        or _clean(units_meta.get("time_reported"))
        or _clean(units_meta.get("time_original_unit"))
    )

    reference_label = (
        _clean(meta.get("time_reference"))
        or _clean(meta.get("time_reference_label"))
        or _clean(meta.get("time_reference_frame"))
        or _clean(units_meta.get("time_reference"))
    )

    offset_value = meta.get("time_offset")
    frame_label = _clean(meta.get("time_frame")) or _clean(
        units_meta.get("time_frame")
    )
    if reference_label and offset_value is not None and frame_label:
        try:
            offset_float = float(offset_value)
            offset_text = f"{offset_float:g}"
        except (TypeError, ValueError):
            offset_text = str(offset_value)
        if frame_label not in reference_label:
            reference_label = f"{frame_label} - {offset_text}"

    return unit_label, reference_label


def convert_time_axis(series: pd.Series, trace: OverlayTrace) -> Tuple[pd.Series, str]:
    values = pd.to_numeric(series, errors="coerce")
    metadata = trace.metadata or {}
    provenance = trace.provenance or {}
    unit_label, reference_label = _time_axis_labels(metadata, provenance)
    axis_title = f"Time ({unit_label})" if unit_label else "Time"
    if reference_label:
        axis_title = f"{axis_title} — ref {reference_label}"
    return values, axis_title


def convert_axis_series(
    series: pd.Series, trace: OverlayTrace, display_units: str
) -> Tuple[pd.Series, str]:
    if getattr(trace, "axis_kind", "wavelength") == "time":
        return convert_time_axis(series, trace)
    return convert_wavelength(series, display_units)


def axis_title_for_kind(
    axis_kind: str,
    overlays: Sequence[OverlayTrace],
    display_units: str,
) -> Optional[str]:
    normalized = normalize_axis_kind(axis_kind)
    for trace in overlays:
        if axis_kind_for_trace(trace) != normalized:
            continue
        values = list(trace.wavelength_nm)
        if not values:
            continue
        sample = pd.Series(values[: min(len(values), 256)])
        _, axis_title = convert_axis_series(sample, trace, display_units)
        if axis_title:
            return axis_title
    return None


def normalize_hover_values(
    values: Optional[Sequence[object]],
) -> Optional[List[Optional[str]]]:
    if values is None:
        return None
    normalized: List[Optional[str]] = []
    has_text = False
    for value in values:
        if pd.isna(value):
            normalized.append(None)
            continue
        text = str(value)
        normalized.append(text)
        if text:
            has_text = True
    return normalized if has_text else None


def add_line_trace(
    fig: go.Figure,
    df: pd.DataFrame,
    label: str,
    hover_values: Optional[Sequence[Optional[str]]] = None,
) -> None:
    xs: List[float | None] = []
    ys: List[float | None] = []
    resolved_hover = (
        normalize_hover_values(hover_values)
        if hover_values is not None
        else normalize_hover_values(df.get("hover"))
    )
    hover: Optional[List[Optional[str]]] = [] if resolved_hover is not None else None
    for idx, (_, row) in enumerate(df.iterrows()):
        x = row.get("wavelength")
        y = float(row.get("flux", 0.0))
        text = resolved_hover[idx] if resolved_hover is not None else None
        xs.extend([x, x, None])
        ys.extend([0.0, y, None])
        if hover is not None:
            hover.extend([text, text, None])
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            name=label,
            hovertext=hover if hover is not None else None,
            hoverinfo="text" if hover is not None else None,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["wavelength"],
            y=df["flux"],
            mode="markers",
            marker=dict(size=6, symbol="line-ns"),
            name=f"{label} markers",
            hovertext=resolved_hover,
            hoverinfo="text" if resolved_hover is not None else None,
            showlegend=False,
        )
    )


def build_overlay_figure(
    overlays: Sequence[OverlayTrace],
    display_units: str,
    display_mode: str,
    normalization_mode: str,
    viewport_by_kind: Mapping[str, Tuple[float | None, float | None]],
    reference: Optional[OverlayTrace],
    differential_mode: str,
    version_tag: str,
    *,
    axis_viewport_by_kind: Optional[
        Mapping[str, Tuple[float | None, float | None]]
    ] = None,
    full_resolution: bool = False,
) -> Tuple[go.Figure, str]:
    fig = go.Figure()
    axis_title = "Wavelength (nm)"
    max_points = 3000000 if full_resolution else 1500000
    viewport_lookup = {
        normalize_axis_kind(kind): normalize_viewport_tuple(viewport)
        for kind, viewport in (viewport_by_kind or {}).items()
    }
    axis_lookup = (
        {
            normalize_axis_kind(kind): normalize_viewport_tuple(viewport)
            for kind, viewport in axis_viewport_by_kind.items()
        }
        if axis_viewport_by_kind
        else {}
    )
    reference_vectors: Optional[TraceVectors] = None
    if reference and axis_kind_for_trace(reference) not in {"image", "time"}:
        ref_kind = axis_kind_for_trace(reference)
        reference_vectors = reference.to_vectors(
            max_points=max_points,
            viewport=viewport_lookup.get(ref_kind, (None, None)),
        )

    visible_axis_kinds: List[str] = []
    axis_titles: Dict[str, str] = {}

    for trace in overlays:
        if not trace.visible:
            continue

        axis_kind = axis_kind_for_trace(trace)
        if axis_kind in {"image", "time"}:
            continue
        viewport = viewport_lookup.get(axis_kind, (None, None))
        visible_axis_kinds.append(axis_kind)

        if trace.kind == "lines":
            df = trace.to_dataframe()
            df = filter_viewport(df, viewport)
            if df.empty:
                continue
            converted, candidate_title = convert_axis_series(
                df["wavelength_nm"], trace, display_units
            )
            df = df.assign(wavelength=converted, flux=df["flux"].astype(float))
            hover_values = normalize_hover_values(df.get("hover"))
            add_line_trace(fig, df, trace.label, hover_values)
            axis_titles.setdefault(axis_kind, candidate_title)
            continue

        sample_w, sample_flux, sample_hover, _ = trace.sample(
            viewport,
            max_points=max_points,
            include_hover=True,
        )
        if sample_w.size == 0:
            continue

        if (
            differential_mode == "Relative to reference"
            and reference_vectors is not None
            and trace.trace_id != reference_vectors.trace_id
        ):
            trace_vectors = TraceVectors(
                trace_id=trace.trace_id,
                label=trace.label,
                wavelengths_nm=sample_w,
                flux=sample_flux,
                kind=trace.kind,
                fingerprint=trace.fingerprint,
            )
            axis, values_trace, values_ref = viewport_alignment(
                trace_vectors,
                reference_vectors,
                viewport,
            )
            if axis is None or values_trace is None or values_ref is None:
                continue
            sample_w = np.asarray(axis, dtype=float)
            sample_flux = np.asarray(values_trace - values_ref, dtype=float)
            sample_hover = None

        converted, candidate_title = convert_axis_series(
            pd.Series(sample_w), trace, display_units
        )
        axis_titles.setdefault(axis_kind, candidate_title)
        flux_array = np.asarray(sample_flux, dtype=float)

        if display_mode != "Flux (raw)":
            flux_array = apply_normalization(flux_array, "max")
        elif normalization_mode and normalization_mode != "none":
            flux_array = apply_normalization(flux_array, normalization_mode)

        hover_values = (
            normalize_hover_values(sample_hover) if sample_hover is not None else None
        )

        fig.add_trace(
            go.Scatter(
                x=converted.tolist(),
                y=flux_array.tolist(),
                mode="lines",
                name=trace.label,
                hovertext=hover_values if hover_values is not None else None,
                hoverinfo="text" if hover_values is not None else None,
            )
        )

    if axis_titles:
        unique_kinds = sorted({kind for kind in visible_axis_kinds})
        if len(unique_kinds) == 1:
            axis_title = axis_titles.get(unique_kinds[0], axis_title)
        else:
            friendly = " + ".join(kind.replace("_", " ") for kind in unique_kinds)
            axis_title = f"Mixed axes ({friendly})"

    fig.update_layout(
        xaxis_title=axis_title,
        yaxis_title="Normalized flux" if display_mode != "Flux (raw)" else "Flux",
        legend=dict(itemclick="toggleothers"),
        margin=dict(t=50, b=40, l=60, r=20),
        height=520,
    )
    unique_kinds = sorted({kind for kind in visible_axis_kinds})
    if len(unique_kinds) == 1 and axis_lookup:
        axis_range = axis_lookup.get(unique_kinds[0])
        if axis_range is not None:
            axis_low, axis_high = axis_range
            if (
                axis_low is not None
                and axis_high is not None
                and math.isfinite(axis_low)
                and math.isfinite(axis_high)
                and axis_high > axis_low
            ):
                fig.update_xaxes(range=[float(axis_low), float(axis_high)])
    fig.update_layout(
        annotations=[
            dict(
                text=version_tag,
                xref="paper",
                yref="paper",
                x=0.99,
                y=-0.22,
                showarrow=False,
                font=dict(size=12),
                align="right",
                opacity=0.7,
            )
        ]
    )
    return fig, axis_title


def normalization_display(mode: str) -> str:
    mapping = {
        "unit": "Unit vector (L2)",
        "l2": "Unit vector (L2)",
        "max": "Peak normalised",
        "peak": "Peak normalised",
        "zscore": "Z-score",
        "z": "Z-score",
        "standard": "Z-score",
        "none": "Raw",
    }
    key = (mode or "raw").lower()
    return mapping.get(key, mode or "Raw")


def compute_differential_result(
    trace_a: OverlayTrace,
    trace_b: OverlayTrace,
    operation_label: str,
    sample_points: int,
    normalization: str,
) -> DifferentialResult:
    meta = DIFFERENTIAL_OPERATIONS[operation_label]
    grid, values_a, values_b = resample_to_common_grid(
        trace_a.wavelength_nm,
        trace_a.flux,
        trace_b.wavelength_nm,
        trace_b.flux,
        n=int(sample_points),
    )
    arr_a = np.asarray(values_a, dtype=float)
    arr_b = np.asarray(values_b, dtype=float)
    norm_a = apply_normalization(arr_a, normalization)
    norm_b = apply_normalization(arr_b, normalization)
    func = meta["func"]
    result_values = func(norm_a, norm_b)
    symbol = meta["symbol"]
    label = f"{trace_a.label} {symbol} {trace_b.label}"
    return DifferentialResult(
        grid_nm=tuple(float(v) for v in grid),
        values_a=tuple(float(v) for v in norm_a),
        values_b=tuple(float(v) for v in norm_b),
        result=tuple(float(v) for v in result_values),
        trace_a_id=trace_a.trace_id,
        trace_b_id=trace_b.trace_id,
        trace_a_label=trace_a.label,
        trace_b_label=trace_b.label,
        operation_code=str(meta["code"]),
        operation_label=operation_label,
        normalization=normalization,
        sample_points=int(sample_points),
        computed_at=time.time(),
        label=label,
    )


def build_differential_figure(result: DifferentialResult) -> go.Figure:
    grid = np.asarray(result.grid_nm, dtype=float)
    values_a = np.asarray(result.values_a, dtype=float)
    values_b = np.asarray(result.values_b, dtype=float)
    result_values = np.asarray(result.result, dtype=float)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
    )
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=values_a,
            name=f"A • {result.trace_a_label}",
            mode="lines",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=values_b,
            name=f"B • {result.trace_b_label}",
            mode="lines",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=result_values,
            name=result.operation_label,
            mode="lines",
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        height=580,
        margin=dict(t=40, b=40, l=60, r=20),
        xaxis=dict(title="Wavelength (nm)"),
        xaxis2=dict(title="Wavelength (nm)"),
        yaxis=dict(title="Normalized flux"),
        yaxis2=dict(title=result.operation_label),
    )
    return fig


def build_differential_summary(result: DifferentialResult) -> pd.DataFrame:
    rows = [
        ("Trace A", result.trace_a_label),
        ("Trace B", result.trace_b_label),
        ("Operation", result.operation_label),
        ("Normalization", normalization_display(result.normalization)),
        ("Resample points", result.sample_points),
        ("Computed", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(result.computed_at))),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def is_full_resolution_enabled(state: Mapping[str, Any]) -> bool:
    try:
        return bool(state.get("display_full_resolution", False))
    except Exception:
        return False


def prepare_similarity_inputs(
    state: MutableMapping[str, Any],
    overlays: Sequence[OverlayTrace],
    viewport_store: Mapping[str, Tuple[float | None, float | None]],
) -> Tuple[List[TraceVectors], Tuple[float | None, float | None], SimilarityOptions, SimilarityCache]:
    similarity_sources = [
        trace
        for trace in overlays
        if trace.visible and axis_kind_for_trace(trace) not in {"image", "time"}
    ]
    if len(similarity_sources) < 2:
        similarity_sources = [
            trace
            for trace in overlays
            if axis_kind_for_trace(trace) not in {"image", "time"}
        ]
    wavelength_sources = [
        trace for trace in similarity_sources if axis_kind_for_trace(trace) == "wavelength"
    ]
    stored_wavelength_view = viewport_store.get("wavelength", (None, None))
    if wavelength_sources:
        effective = effective_viewport(
            wavelength_sources,
            stored_wavelength_view,
            axis_kind="wavelength",
        )
    else:
        effective = (None, None)

    cache: SimilarityCache = state.setdefault("similarity_cache", SimilarityCache())
    full_resolution = is_full_resolution_enabled(state)
    vector_max_points = None if full_resolution else 15000
    viewport_map = {"wavelength": effective} if wavelength_sources else {}
    visible_vectors = [
        trace.to_vectors(
            max_points=vector_max_points,
            viewport=viewport_map.get(axis_kind_for_trace(trace), (None, None)),
        )
        for trace in similarity_sources
    ]
    options = SimilarityOptions(
        metrics=tuple(state.get("similarity_metrics", ["cosine"])),
        normalization=state.get("similarity_normalization", state.get("normalization_mode", "unit")),
        line_match_top_n=int(state.get("similarity_line_peaks", 8)),
        primary_metric=state.get("similarity_primary_metric", "cosine"),
        reference_id=state.get("reference_trace_id"),
    )
    return visible_vectors, effective, options, cache


class WorkspaceController:
    def __init__(self, state: MutableMapping[str, Any], viewport_key: str):
        self.state = state
        self.viewport_key = viewport_key

    def ensure_defaults(self) -> None:
        ensure_session_defaults(self.state, self.viewport_key)

    def get_overlays(self) -> List[OverlayTrace]:
        return get_overlays(self.state)

    def set_overlays(self, overlays: Sequence[OverlayTrace]) -> None:
        set_overlays(self.state, overlays)

    def add_overlay(self, *args: Any, **kwargs: Any) -> Tuple[bool, str]:
        return add_overlay(self.state, *args, **kwargs)

    def add_overlay_payload(self, payload: Mapping[str, object]) -> Tuple[bool, str]:
        return add_overlay_payload(self.state, payload)

    def get_viewport_store(self) -> Dict[str, Tuple[float | None, float | None]]:
        return get_viewport_store(self.state, self.viewport_key)

    def set_viewport_store(
        self, store: Mapping[str, Tuple[float | None, float | None]]
    ) -> None:
        set_viewport_store(self.state, self.viewport_key, store)

    def set_viewport_for_kind(
        self, axis_kind: str, viewport: Tuple[float | None, float | None]
    ) -> None:
        set_viewport_for_kind(self.state, self.viewport_key, axis_kind, viewport)

    def get_viewport_for_kind(self, axis_kind: str) -> Tuple[float | None, float | None]:
        return get_viewport_for_kind(self.state, self.viewport_key, axis_kind)

    def ensure_reference_consistency(self) -> None:
        ensure_reference_consistency(self.state)

    def trace_label(self, trace_id: Optional[str]) -> str:
        return trace_label(self.state, trace_id)

    def is_full_resolution_enabled(self) -> bool:
        return is_full_resolution_enabled(self.state)

    def prepare_similarity_inputs(
        self, overlays: Sequence[OverlayTrace]
    ) -> Tuple[
        List[TraceVectors], Tuple[float | None, float | None], SimilarityOptions, SimilarityCache
    ]:
        viewport_store = self.get_viewport_store()
        return prepare_similarity_inputs(self.state, overlays, viewport_store)


__all__ = [
    "OverlayTrace",
    "DifferentialResult",
    "WorkspaceController",
    "normalize_axis_kind",
    "axis_kind_for_trace",
    "group_overlays_by_axis_kind",
    "normalize_viewport_tuple",
    "determine_primary_axis_kind",
    "ensure_session_defaults",
    "get_overlays",
    "set_overlays",
    "add_overlay",
    "add_overlay_payload",
    "build_overlay_figure",
    "compute_differential_result",
    "build_differential_figure",
    "build_differential_summary",
    "trace_label",
    "prepare_similarity_inputs",
    "is_full_resolution_enabled",
    "auto_viewport_range",
    "effective_viewport",
    "infer_viewport_bounds",
]
