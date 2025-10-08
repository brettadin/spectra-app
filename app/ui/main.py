from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import quote, urlparse


import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
from streamlit.delta_generator import DeltaGenerator

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "app.ui"

from .panel_registry import (
    PanelContext,
    get_panel_registry,
    register_sidebar_panel,
    register_workspace_panel,
)
from .targets import RegistryUnavailableError, render_targets_panel

from .._version import get_version_info
from ..ingest import OverlayIngestResult
from ..export_manifest import build_manifest
from ..server.differential import ratio, resample_to_common_grid, subtract
from ..server.fetch_archives import FetchError, fetch_spectrum
from ..server.fetchers import nist_quant_ir
from ..server.ir_units import IRMeta, to_A10
from ..similarity import (
    SimilarityCache,
    SimilarityOptions,
    TraceVectors,
    apply_normalization,
    viewport_alignment,
)
from ..similarity_panel import render_similarity_panel
from ..utils.downsample import build_downsample_tiers, build_lttb_downsample
from ..utils.duplicate_ledger import DuplicateLedger
from ..utils.flux import flux_percentile_range
from ..providers import ProviderQuery, search as provider_search
from ..utils.local_ingest import (
    SUPPORTED_LOCAL_UPLOAD_EXTENSIONS,
    LocalIngestError,
    ingest_local_file,
)

APP_VERSION = "v1.2.1aa"

if "health" in st.query_params or os.environ.get("SPECTRA_APP_HEALTH") == "1":
    st.write(f"SPECTRA_APP_OK {APP_VERSION}")
    st.stop()

st.set_page_config(page_title="Spectra App", layout="wide")

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


NIST_QUANT_IR_MOLECULES: Tuple[Dict[str, str], ...] = (
    {"label": "Water", "query": "Water"},
    {"label": "Methane", "query": "Methane"},
    {"label": "Carbon Dioxide", "query": "Carbon Dioxide"},
    {"label": "Benzene", "query": "Benzene"},
    {"label": "Ethylene", "query": "Ethylene"},
    {"label": "Acetone", "query": "Acetone"},
    {"label": "Ethanol", "query": "Ethanol"},
    {"label": "Methanol", "query": "Methanol"},
    {"label": "2-Propanol", "query": "2-Propanol"},
    {"label": "Ethyl Acetate", "query": "Ethyl Acetate"},
    {"label": "1-Butanol", "query": "1-Butanol"},
    {"label": "Sulfur Hexafluoride", "query": "Sulfur Hexafluoride"},
    {"label": "Acetonitrile", "query": "Acetonitrile"},
    {"label": "Acrylonitrile", "query": "Acrylonitrile"},
    {"label": "Sulfur Dioxide", "query": "Sulfur Dioxide"},
    {"label": "Carbon Tetrachloride", "query": "Carbon Tetrachloride"},
    {"label": "Butane", "query": "Butane"},
    {"label": "Ethylbenzene", "query": "Ethylbenzene"},
)

NIST_QUANT_IR_RESOLUTION = nist_quant_ir.DEFAULT_RESOLUTION_CM_1


@st.cache_data(show_spinner=False)
def _cached_quant_ir_catalog() -> Tuple[Dict[str, object], ...]:
    return nist_quant_ir.available_species()


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
    extras: Dict[str, object] = field(default_factory=dict)

    @property
    def points(self) -> int:
        if str(self.axis_kind).strip().lower() == "image":
            if isinstance(self.image, Mapping):
                data = self.image.get("data")
                try:
                    array = np.asarray(data)
                except Exception:
                    return 0
                return int(array.size)
            return 0
        return int(len(self.wavelength_nm))

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


def _get_ir_context(trace: OverlayTrace) -> Optional[Dict[str, object]]:
    extras = trace.extras if isinstance(trace.extras, Mapping) else {}
    context = extras.get("ir_context") if isinstance(extras, Mapping) else None
    if isinstance(context, Mapping):
        return dict(context)
    return None


def _set_ir_context(trace: OverlayTrace, context: Mapping[str, object]) -> None:
    if not isinstance(trace.extras, dict):
        trace.extras = {}
    trace.extras["ir_context"] = dict(context)


def _apply_ir_parameters_to_trace(
    trace: OverlayTrace, path_m: float, mole_fraction: float
) -> Tuple[bool, str]:
    context = _get_ir_context(trace)
    if context is None:
        return False, "IR conversion context unavailable."
    raw_values = context.get("raw_y")
    if raw_values is None:
        return False, "Raw IR samples unavailable for conversion."
    raw_array = np.asarray(raw_values, dtype=float)
    if raw_array.size == 0:
        return False, "Raw IR samples unavailable for conversion."

    try:
        y_factor = float(context.get("y_factor", 1.0))
    except Exception:
        y_factor = 1.0
    y_units = context.get("y_units")
    if not y_units:
        meta = trace.metadata if isinstance(trace.metadata, Mapping) else {}
        y_units = meta.get("flux_unit_input") or meta.get("reported_flux_unit")

    ir_meta = IRMeta(
        yunits=str(y_units or ""),
        yfactor=y_factor,
        path_m=float(path_m),
        mole_fraction=float(mole_fraction),
    )

    try:
        converted, provenance = to_A10(raw_array, ir_meta)
    except ValueError as exc:
        return False, str(exc)

    flux_values = tuple(float(value) for value in np.asarray(converted, dtype=float))
    trace.flux = flux_values
    trace.flux_unit = "Absorbance (A10)"
    trace.flux_kind = "relative"
    trace.axis = "absorption"

    metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
    metadata = dict(metadata)
    metadata["ir_requires_parameters"] = False
    metadata["ir_conversion_state"] = "converted"
    metadata["ir_path_m"] = float(path_m)
    metadata["ir_mole_fraction"] = float(mole_fraction)
    metadata["flux_unit"] = "Absorbance (A10)"
    metadata["flux_unit_output"] = "Absorbance (A10)"
    metadata["flux_unit_display"] = "Absorbance (A10)"
    metadata.pop("ir_conversion_error", None)
    sanity = metadata.get("ir_sanity") if isinstance(metadata.get("ir_sanity"), Mapping) else None
    if sanity is not None:
        sanity_payload = dict(sanity)
        sanity_payload["conversion_from"] = provenance.get("from")
        sanity_payload["path_m"] = float(path_m)
        sanity_payload["mole_fraction"] = float(mole_fraction)
        metadata["ir_sanity"] = sanity_payload
    trace.metadata = metadata

    provenance_map = trace.provenance if isinstance(trace.provenance, Mapping) else {}
    provenance_map = dict(provenance_map)
    units_meta = provenance_map.get("units") if isinstance(provenance_map.get("units"), Mapping) else {}
    units_meta = dict(units_meta)
    units_meta["flux_output"] = "Absorbance (A10)"
    provenance_map["units"] = units_meta
    provenance_record = {
        "status": "converted",
        "yunits_in": y_units,
        "yfactor": y_factor,
        "path_m": float(path_m),
        "mole_fraction": float(mole_fraction),
        "details": provenance,
    }
    provenance_map["ir_conversion"] = provenance_record
    trace.provenance = provenance_map

    new_context = dict(context)
    new_context.update(
        {
            "path_m": float(path_m),
            "mole_fraction": float(mole_fraction),
            "conversion_state": "converted",
            "needs_parameters": False,
            "conversion_details": provenance,
            "conversion_error": None,
        }
    )
    _set_ir_context(trace, new_context)
    trace.extras["ir_sanity"] = metadata.get("ir_sanity")

    tiers = build_downsample_tiers(
        list(trace.wavelength_nm), list(flux_values), strategy="lttb"
    )
    trace.downsample = {
        int(level): (tuple(result.wavelength_nm), tuple(result.flux))
        for level, result in tiers.items()
    }
    trace.fingerprint = _compute_fingerprint(trace.wavelength_nm, trace.flux)
    return True, "Converted to decadic absorbance (A10)."


def _render_ir_warnings(overlays: Sequence[OverlayTrace]) -> None:
    for trace in overlays:
        metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
        if metadata.get("ir_verified") is False:
            message = str(metadata.get("ir_warning") or "IR header verification failed.")
            st.warning(f"{trace.label}: {message}")


def _render_ir_parameter_prompts(overlays: Sequence[OverlayTrace]) -> None:
    pending = [
        trace
        for trace in overlays
        if isinstance(trace.metadata, Mapping)
        and bool(trace.metadata.get("ir_requires_parameters"))
    ]
    if not pending:
        return
    st.warning(
        "IR absorption coefficients detected. Provide path length and mole fraction "
        "to convert to decadic absorbance (A10)."
    )
    for trace in pending:
        context = _get_ir_context(trace) or {}
        try:
            default_path = float(context.get("path_m") or 1.0)
        except Exception:
            default_path = 1.0
        try:
            default_mole = float(context.get("mole_fraction") or 1e-6)
        except Exception:
            default_mole = 1e-6
        units_label = context.get("y_units")
        if not units_label:
            metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
            units_label = metadata.get("flux_unit_input") or metadata.get("flux_unit_display")
        panel = st.container()
        panel.caption(f"{trace.label} units: {units_label or 'unknown'}")
        form_key = f"ir_params_form_{trace.trace_id}"
        with panel.form(form_key):
            path_value = st.number_input(
                "Path length (m)",
                min_value=0.0,
                value=float(default_path),
                step=max(float(default_path) / 10.0, 0.1),
                format="%0.4f",
                key=f"{form_key}_path",
            )
            mole_value = st.number_input(
                "Mole fraction (χ)",
                min_value=0.0,
                max_value=1.0,
                value=float(default_mole),
                step=max(float(default_mole) / 10.0, 1e-6),
                format="%0.6f",
                key=f"{form_key}_mole",
                help="Enter as a fraction (e.g. 50 ppm = 5e-5).",
            )
            submitted = st.form_submit_button("Convert to A10", use_container_width=True)
        if submitted:
            success, message = _apply_ir_parameters_to_trace(
                trace, float(path_value), float(mole_value)
            )
            if success:
                _set_overlays(overlays)
                panel.success(message)
            else:
                panel.error(message)


def _render_ir_sanity_panel(overlays: Sequence[OverlayTrace]) -> None:
    entries: List[OverlayTrace] = []
    for trace in overlays:
        metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
        if metadata.get("ir_sanity"):
            entries.append(trace)
    if not entries:
        return
    st.markdown("#### IR ingest diagnostics")
    for trace in entries:
        metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
        details = metadata.get("ir_sanity")
        with st.expander(f"{trace.label} — IR ingest details", expanded=False):
            st.json(details)
            provenance = trace.provenance if isinstance(trace.provenance, Mapping) else {}
            conversion = provenance.get("ir_conversion") if isinstance(provenance, Mapping) else None
            if conversion:
                st.caption("Conversion provenance")
                st.json(conversion)
@dataclass(frozen=True)
class QuantIROption:
    label: str
    query: str
    available: bool
    relative_uncertainty: Optional[str] = None
    apodizations: Tuple[str, ...] = ()

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


@dataclass(frozen=True)
class ExampleSpec:
    slug: str
    label: str
    description: str
    provider: str
    query: ProviderQuery


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


@dataclass(frozen=True)
class DocEntry:
    title: str
    path: Path
    description: str


@dataclass(frozen=True)
class DocCategory:
    title: str
    description: str
    entries: Tuple[DocEntry, ...]


EXAMPLE_LIBRARY: Tuple[ExampleSpec, ...] = (
    ExampleSpec(
        slug="sirius-stis",
        label="Sirius A • HST/STIS (CALSPEC)",
        description="CALSPEC flux standard from Bohlin et al. 2014 (MAST).",
        provider="MAST",
        query=ProviderQuery(target="Sirius A", instrument="STIS", limit=1),
    ),
    ExampleSpec(
        slug="sz71-uvb",
        label="Sz 71 • VLT/X-Shooter UVB",
        description="PENELLOPE UVB spectrum from Manara et al. 2023 (ESO Zenodo record 10024073).",
        provider="ESO",
        query=ProviderQuery(target="Sz 71", limit=1),
    ),
    ExampleSpec(
        slug="sdss-6138-0934",
        label="SDSS J234828.73+164429.3 • BOSS",
        description="High S/N F-type spectrum from SDSS DR17 (Abdurro'uf et al. 2022).",
        provider="SDSS",
        query=ProviderQuery(target="6138-56598-0934", limit=1),
    ),
    ExampleSpec(
        slug="vhs1256b",
        label="VHS 1256-1257 b • X-Shooter",
        description="Substellar companion spectrum via DOI 10.5281/zenodo.6829330 (Petrus et al. 2022).",
        provider="DOI",
        query=ProviderQuery(doi="10.5281/zenodo.6829330", limit=1),
    ),
)

EXAMPLE_MAP: Dict[str, ExampleSpec] = {spec.slug: spec for spec in EXAMPLE_LIBRARY}


DOC_LIBRARY: Tuple[DocCategory, ...] = (
    DocCategory(
        title="Getting started",
        description="Orient yourself and load spectra into the workspace.",
        entries=(
            DocEntry(
                title="Quick start",
                path=Path("docs/app/user_guide.md"),
                description="Overview of the refreshed Spectra App experience.",
            ),
        ),
    ),
    DocCategory(
        title="Workspace reference",
        description="Deep-dives on the overlay and differential tooling.",
        entries=(
            DocEntry(
                title="Overlay workspace",
                path=Path("docs/app/overlay_workspace.md"),
                description="Manage overlays, visibility, and exports.",
            ),
            DocEntry(
                title="Differential workspace",
                path=Path("docs/app/differential_workspace.md"),
                description="Compute subtraction or ratio curves between traces.",
            ),
        ),
    ),
    DocCategory(
        title="Archives & provenance",
        description="Fetch spectra from archives and track metadata.",
        entries=(
            DocEntry(
                title="Archive & provenance",
                path=Path("docs/app/archive_and_provenance.md"),
                description="Archive lookup flow and provenance best practices.",
            ),
        ),
    ),
)


DIFFERENTIAL_OPERATIONS: Dict[str, Dict[str, object]] = {
    "Subtract (A − B)": {"code": "subtract", "symbol": "−", "func": subtract},
    "Ratio (A ÷ B)": {"code": "ratio", "symbol": "÷", "func": ratio},
}


def _format_version_timestamp(raw: object) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.strftime("%Y-%m-%d %H:%M UTC")


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------


VIEWPORT_STATE_KEY = "viewport_axes"


def _normalize_axis_kind(value: Optional[str]) -> str:
    try:
        text = str(value or "")
    except Exception:
        text = ""
    text = text.strip().lower()
    return text or "wavelength"


def _axis_kind_for_trace(trace: OverlayTrace) -> str:
    return _normalize_axis_kind(getattr(trace, "axis_kind", None))


def _group_overlays_by_axis_kind(
    overlays: Sequence[OverlayTrace],
) -> Dict[str, List[OverlayTrace]]:
    groups: Dict[str, List[OverlayTrace]] = {}
    for trace in overlays:
        kind = _axis_kind_for_trace(trace)
        if kind == "time":
            continue
        groups.setdefault(kind, []).append(trace)
    return groups


def _normalize_viewport_tuple(
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


def _get_viewport_store() -> Dict[str, Tuple[float | None, float | None]]:
    store = st.session_state.get(VIEWPORT_STATE_KEY)
    if not isinstance(store, Mapping):
        return {}
    normalized: Dict[str, Tuple[float | None, float | None]] = {}
    for kind, viewport in store.items():
        normalized[_normalize_axis_kind(kind)] = _normalize_viewport_tuple(viewport)
    return normalized


def _set_viewport_store(store: Dict[str, Tuple[float | None, float | None]]) -> None:
    st.session_state[VIEWPORT_STATE_KEY] = dict(store)


def _set_viewport_for_kind(
    axis_kind: str, viewport: Tuple[float | None, float | None]
) -> None:
    store = _get_viewport_store()
    store[_normalize_axis_kind(axis_kind)] = _normalize_viewport_tuple(viewport)
    _set_viewport_store(store)


def _get_viewport_for_kind(axis_kind: str) -> Tuple[float | None, float | None]:
    store = _get_viewport_store()
    return store.get(_normalize_axis_kind(axis_kind), (None, None))


def _determine_primary_axis_kind(
    overlays: Sequence[OverlayTrace],
) -> str:
    groups = _group_overlays_by_axis_kind(overlays)
    if groups.get("wavelength"):
        return "wavelength"
    for kind, traces in groups.items():
        if kind == "image":
            continue
        if traces:
            return kind
    return "wavelength"


def _ensure_session_state() -> None:
    st.session_state.setdefault("session_id", str(uuid.uuid4()))
    st.session_state.setdefault("overlay_traces", [])
    st.session_state.setdefault("display_units", "nm")
    st.session_state.setdefault("display_units_user_override", False)
    st.session_state.setdefault("display_mode", "Flux (raw)")
    st.session_state.setdefault("display_full_resolution", False)
    if VIEWPORT_STATE_KEY not in st.session_state:
        legacy = st.session_state.get("viewport_nm")
        if isinstance(legacy, Sequence) and len(legacy) == 2:
            _set_viewport_store({"wavelength": _normalize_viewport_tuple(legacy)})
        else:
            _set_viewport_store({"wavelength": (None, None)})
    else:
        store = _get_viewport_store()
        if "wavelength" not in store:
            store["wavelength"] = (None, None)
        _set_viewport_store(store)
    if "viewport_nm" in st.session_state:
        try:
            del st.session_state["viewport_nm"]
        except Exception:
            st.session_state["viewport_nm"] = None
    st.session_state.setdefault("auto_viewport", True)
    st.session_state.setdefault("normalization_mode", "unit")
    st.session_state.setdefault("differential_mode", "Off")
    st.session_state.setdefault("reference_trace_id", None)
    st.session_state.setdefault(
        "similarity_metrics", ["cosine", "rmse", "xcorr", "line_match"]
    )
    st.session_state.setdefault("similarity_primary_metric", "cosine")
    st.session_state.setdefault("similarity_line_peaks", 8)
    st.session_state.setdefault(
        "similarity_normalization", st.session_state.get("normalization_mode", "unit")
    )
    st.session_state.setdefault("duplicate_policy", "skip")
    st.session_state.setdefault("local_upload_registry", {})
    st.session_state.setdefault("differential_result", None)
    st.session_state.setdefault("differential_sample_points", 2000)
    st.session_state.setdefault("network_available", True)
    st.session_state.setdefault("example_recent", [])
    st.session_state.setdefault("duplicate_base_policy", "skip")
    st.session_state.setdefault("duplicate_ledger_lock", False)
    st.session_state.setdefault("duplicate_ledger_pending_action", None)
    st.session_state.setdefault("ingest_queue", [])
    if "duplicate_ledger" not in st.session_state:
        st.session_state["duplicate_ledger"] = DuplicateLedger()
    if "similarity_cache" not in st.session_state:
        st.session_state["similarity_cache"] = SimilarityCache()


def _is_full_resolution_enabled() -> bool:
    session_state = getattr(st, "session_state", None)
    if session_state is None:
        return False
    getter = getattr(session_state, "get", None)
    if callable(getter):
        return bool(getter("display_full_resolution", False))
    try:
        return bool(session_state["display_full_resolution"])
    except (KeyError, TypeError):
        return False


MAST_DOWNLOAD_ENDPOINT = "https://mast.stsci.edu/api/v0.1/Download/file"


def _resolve_overlay_url(raw_url: str) -> str:
    """Return a concrete URL for overlay ingestion."""

    url = str(raw_url or "").strip()
    if not url:
        return ""

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()

    if scheme == "mast" or (not scheme and url.startswith("mast:")):
        encoded = quote(url, safe="")
        return f"{MAST_DOWNLOAD_ENDPOINT}?uri={encoded}"

    return url


_OVERLAY_STATUS_LABELS = {
    "queued": "Queued",
    "running": "Starting",
    "downloading": "Downloading",
    "ingesting": "Ingesting",
    "success": "Completed",
    "info": "Completed",
    "error": "Failed",
}

_OVERLAY_STATUS_PROGRESS = {
    "queued": 0.0,
    "running": 0.1,
    "downloading": 0.4,
    "ingesting": 0.7,
    "success": 1.0,
    "info": 1.0,
    "error": 1.0,
}


def _ensure_ingest_runtime() -> Dict[str, Any]:
    runtime = st.session_state.get("ingest_runtime")
    if not isinstance(runtime, dict):
        runtime = {}

    executor = runtime.get("executor")
    if not isinstance(executor, ThreadPoolExecutor) or getattr(executor, "_shutdown", False):
        executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="overlay-ingest")
        runtime["executor"] = executor

    lock = runtime.get("lock")
    if lock is None or not hasattr(lock, "acquire"):
        lock = threading.Lock()
        runtime["lock"] = lock

    runtime.setdefault("jobs", {})
    runtime.setdefault("futures", {})
    st.session_state["ingest_runtime"] = runtime
    return runtime


def _normalise_ingest_item(item: Any) -> Optional[Dict[str, Any]]:
    if isinstance(item, Mapping):
        url = str(item.get("url") or "")
        label_hint = str(item.get("label") or "").strip()
        provider_hint = item.get("provider")
    else:
        url = str(item or "")
        label_hint = ""
        provider_hint = None

    if not url:
        return None

    return {"url": url, "label": label_hint, "provider": provider_hint}


def _update_ingest_job(
    runtime: Dict[str, Any],
    job_id: str,
    *,
    status: Optional[str] = None,
    detail: Optional[str] = None,
    progress: Optional[float] = None,
    finished: bool = False,
) -> None:
    lock_obj = runtime.get("lock")
    jobs = runtime.get("jobs")
    if jobs is None:
        return

    if lock_obj is None or not hasattr(lock_obj, "__enter__"):
        lock_obj = threading.Lock()
        runtime["lock"] = lock_obj

    if not isinstance(jobs, dict):
        return

    with lock_obj:
        job = jobs.get(job_id)
        if job is None:
            return

        if status:
            job["status"] = status
        if detail is not None:
            job["detail"] = detail

        if progress is None and status in _OVERLAY_STATUS_PROGRESS:
            progress = _OVERLAY_STATUS_PROGRESS[status]

        if progress is not None:
            try:
                job["progress"] = max(0.0, min(1.0, float(progress)))
            except Exception:
                job["progress"] = _OVERLAY_STATUS_PROGRESS.get(status or "queued", 0.0)

        timestamp = time.time()
        if status and job.get("started_at") is None and status not in {"queued"}:
            job["started_at"] = timestamp
        if finished or status in {"success", "info", "error"}:
            job["finished_at"] = timestamp
            if detail is not None:
                job["result"] = detail


def _submit_ingest_job(runtime: Dict[str, Any], entry: Mapping[str, Any]) -> str:
    job_id = uuid.uuid4().hex
    label_hint = str(entry.get("label") or "").strip()
    url = str(entry.get("url") or "")
    provider_hint = entry.get("provider")
    derived_name = Path(urlparse(url).path).name
    display_label = label_hint or derived_name or "remote-spectrum"

    job_record = {
        "id": job_id,
        "url": url,
        "label": display_label,
        "provider": provider_hint,
        "status": "queued",
        "detail": "Waiting to start",
        "progress": 0.0,
        "submitted_at": time.time(),
        "started_at": None,
        "finished_at": None,
    }

    lock = runtime.get("lock")
    jobs = runtime.setdefault("jobs", {})
    if lock and hasattr(lock, "acquire") and isinstance(jobs, dict):
        with lock:
            jobs[job_id] = job_record
    elif isinstance(jobs, dict):
        jobs[job_id] = job_record

    def _update(status: Optional[str] = None, detail: Optional[str] = None, progress: Optional[float] = None) -> None:
        try:
            _update_ingest_job(runtime, job_id, status=status, detail=detail, progress=progress)
        except Exception:
            pass

    executor: ThreadPoolExecutor = runtime["executor"]
    future = executor.submit(_ingest_overlay_job, entry, _update)
    runtime.setdefault("futures", {})[job_id] = future
    return job_id


def _ingest_overlay_job(
    entry: Mapping[str, Any],
    progress_callback: Callable[[Optional[str], Optional[str], Optional[float]], None],
) -> OverlayIngestResult:
    url = str(entry.get("url") or "")
    label_hint = str(entry.get("label") or "").strip()
    provider_hint = entry.get("provider")
    resolved_url = _resolve_overlay_url(url)
    derived_name = Path(urlparse(url).path).name
    label = label_hint or derived_name or "remote-spectrum"

    progress_callback("running", "Preparing download", None)

    try:
        from app.core.ingest import add_overlay_from_url as _add_overlay_from_url  # type: ignore
    except Exception:  # pragma: no cover - optional integration point
        _add_overlay_from_url = None

    try:
        if _add_overlay_from_url is not None:
            progress_callback("ingesting", "Delegating to ingest pipeline", None)
            _add_overlay_from_url(resolved_url, label=label)
            message = f"Added {label}"
            progress_callback("success", message, 1.0)
            return OverlayIngestResult(status="success", detail=message, payload=None)

        progress_callback("downloading", "Downloading overlay data", None)
        response = requests.get(resolved_url, timeout=60)
        response.raise_for_status()

        filename = derived_name or f"overlay-{uuid.uuid4().hex[:8]}"
        progress_callback("ingesting", "Ingesting overlay data", None)
        try:
            payload = ingest_local_file(filename, response.content)
        except LocalIngestError as exc:
            message = f"Unable to ingest {label}: {exc}"
            progress_callback("error", message, 1.0)
            return OverlayIngestResult(status="error", detail=message, payload=None)

        payload = dict(payload)
        payload.setdefault("label", label)
        if provider_hint and not payload.get("provider"):
            payload["provider"] = str(provider_hint)

        metadata = dict(payload.get("metadata") or {})
        metadata.setdefault("source", "Target overlay queue")
        payload["metadata"] = metadata

        provenance = dict(payload.get("provenance") or {})
        ingest_info = dict(provenance.get("ingest") or {})
        ingest_info.setdefault("method", "overlay_queue")
        ingest_info["source_url"] = url
        if resolved_url and resolved_url != url:
            ingest_info.setdefault("resolved_url", resolved_url)
        ingest_info.setdefault("label", label)
        provenance["ingest"] = ingest_info
        payload["provenance"] = provenance

        progress_callback("ingesting", "Overlay ready for addition", 0.95)
        prepared_message = f"Prepared {label}"
        return OverlayIngestResult(status="success", detail=prepared_message, payload=payload)
    except Exception as exc:  # pragma: no cover - network/runtime failure
        message = f"Failed to ingest {label}: {exc}"
        progress_callback("error", message, 1.0)
        return OverlayIngestResult(status="error", detail=message, payload=None)


def _refresh_ingest_jobs(runtime: Dict[str, Any]) -> None:
    futures = runtime.get("futures")
    if not isinstance(futures, dict):
        return

    completed: List[str] = []
    for job_id, future in list(futures.items()):
        if not isinstance(future, Future):
            completed.append(job_id)
            continue
        if not future.done():
            continue

        payload: Optional[Dict[str, Any]] = None
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover - unexpected future failure
            status, detail = "error", str(exc)
        else:
            if isinstance(result, OverlayIngestResult):
                status, detail, payload = result.status, result.detail, result.payload
            elif all(
                hasattr(result, attr) for attr in ("status", "detail")
            ):
                status = getattr(result, "status")  # type: ignore[assignment]
                detail = getattr(result, "detail")  # type: ignore[assignment]
                payload = getattr(result, "payload", None)
            elif isinstance(result, tuple):  # pragma: no cover - legacy tuple result
                if len(result) == 3:
                    status, detail, payload = result  # type: ignore[misc]
                elif len(result) == 2:
                    status, detail = result  # type: ignore[misc]
                else:
                    status, detail = "error", "Unexpected ingest result"
            else:  # pragma: no cover - unexpected result type
                status, detail = "error", "Unexpected ingest result"

        final_status = status
        final_detail = detail
        if payload is not None:
            try:
                added, message = _add_overlay_payload(payload)
            except Exception as exc:  # pragma: no cover - overlay addition failure
                final_status = "error"
                final_detail = f"Failed to add overlay: {exc}"
            else:
                final_status = "success" if added else "info"
                final_detail = message

        _update_ingest_job(
            runtime,
            job_id,
            status=final_status,
            detail=final_detail,
            progress=1.0,
            finished=True,
        )
        completed.append(job_id)

    for job_id in completed:
        futures.pop(job_id, None)


def _snapshot_ingest_jobs(runtime: Optional[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(runtime, Mapping):
        return []

    lock = runtime.get("lock")
    jobs = runtime.get("jobs")
    if lock is None or jobs is None or not hasattr(lock, "acquire"):
        return []

    with lock:
        values = list(jobs.values()) if isinstance(jobs, dict) else []
        return [dict(job) for job in values]


def _process_ingest_queue() -> None:
    runtime = _ensure_ingest_runtime()
    queue = list(st.session_state.get("ingest_queue", []))
    if queue:
        for item in queue:
            entry = _normalise_ingest_item(item)
            if entry is None:
                continue
            _submit_ingest_job(runtime, entry)
        st.session_state["ingest_queue"] = []

    _refresh_ingest_jobs(runtime)


def _render_ingest_queue_panel(container: DeltaGenerator) -> None:
    container.divider()
    container.markdown("### Overlay downloads")

    runtime = st.session_state.get("ingest_runtime")
    jobs = _snapshot_ingest_jobs(runtime)
    if not jobs:
        container.caption(
            "Queued overlays will appear here while downloads run in the background."
        )
        return

    jobs_sorted = sorted(jobs, key=lambda job: job.get("submitted_at") or 0.0)
    for job in jobs_sorted:
        label = str(job.get("label") or "").strip() or "Remote overlay"
        provider = job.get("provider")
        if provider:
            provider_str = str(provider).strip()
            if provider_str:
                label = f"{label} ({provider_str})"

        status = str(job.get("status") or "queued")
        detail = str(job.get("detail") or "").strip()
        status_title = _OVERLAY_STATUS_LABELS.get(
            status, status.replace("_", " ").title()
        )
        summary = status_title if not detail else f"{status_title}: {detail}"

        progress = job.get("progress")
        try:
            progress_value = max(0.0, min(1.0, float(progress)))
        except Exception:
            progress_value = _OVERLAY_STATUS_PROGRESS.get(status, 0.0)

        entry = container.container()
        entry.markdown(f"**{label}**")
        if status == "success":
            entry.success(summary)
        elif status == "info":
            entry.info(summary)
        elif status == "error":
            entry.error(summary)
        else:
            entry.progress(progress_value)
            entry.caption(summary)


def _get_overlays() -> List[OverlayTrace]:
    return list(st.session_state.get("overlay_traces", []))


def _set_overlays(overlays: Sequence[OverlayTrace]) -> None:
    st.session_state["overlay_traces"] = list(overlays)
    _ensure_reference_consistency()


def _get_example_spec(slug: str) -> Optional[ExampleSpec]:
    return EXAMPLE_MAP.get(slug)


def _register_example_usage(spec: ExampleSpec, *, success: bool) -> None:
    if not success:
        return
    recents = list(st.session_state.get("example_recent", []))
    if spec.slug in recents:
        recents.remove(spec.slug)
    recents.insert(0, spec.slug)
    st.session_state["example_recent"] = recents[:5]
def _ensure_reference_consistency() -> None:
    overlays = _get_overlays()
    current = st.session_state.get("reference_trace_id")
    if current and any(trace.trace_id == current for trace in overlays):
        return
    if overlays:
        st.session_state["reference_trace_id"] = overlays[0].trace_id
    else:
        st.session_state["reference_trace_id"] = None


def _trace_label(trace_id: Optional[str]) -> str:
    if trace_id is None:
        return "—"
    for trace in _get_overlays():
        if trace.trace_id == trace_id:
            suffix = f" ({trace.provider})" if trace.provider else ""
            return f"{trace.label}{suffix}"
    return trace_id


def _compute_fingerprint(wavelengths: Sequence[float], flux: Sequence[float]) -> str:
    arr_w = np.asarray([float(w) for w in wavelengths], dtype=np.float64)
    arr_f = np.asarray([float(f) for f in flux], dtype=np.float64)
    combined = np.stack((np.round(arr_w, 6), np.round(arr_f, 6)), axis=1)
    return hashlib.sha1(combined.tobytes()).hexdigest()


def _compute_image_fingerprint(image: Mapping[str, object]) -> str:
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


def _normalise_display_unit_hint(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    folded = text.casefold()
    folded = (
        folded.replace("µ", "u")
        .replace("μ", "u")
        .replace("å", "angstrom")
        .replace("Å", "angstrom")
    )
    collapsed = re.sub(r"[^a-z0-9]+", "", folded)
    if not collapsed:
        return None
    if collapsed in {"nm", "nanometer", "nanometre", "nanometers", "nanometres"}:
        return "nm"
    if collapsed in {
        "angstrom",
        "angstroem",
        "angstroms",
        "angstroems",
    }:
        return "Å"
    if collapsed in {
        "um",
        "micrometer",
        "micrometre",
        "micrometers",
        "micrometres",
        "micron",
        "microns",
        "mum",
    }:
        return "µm"
    if collapsed in {
        "cm1",
        "1cm",
        "1percm",
        "percm",
        "wavenumber",
        "wavenumbers",
        "kayser",
        "kaysers",
    }:
        return "cm^-1"
    return None


def _preferred_display_unit(
    metadata: Optional[Mapping[str, object]],
    provenance: Optional[Mapping[str, object]],
) -> Optional[str]:
    meta = metadata or {}
    prov = provenance or {}
    candidates: List[object] = []
    if isinstance(meta, Mapping):
        for key in (
            "wavelength_display_unit",
            "preferred_wavelength_unit",
            "original_wavelength_unit",
            "reported_wavelength_unit",
            "wavelength_unit",
            "axis_unit",
        ):
            candidate = meta.get(key)
            if candidate:
                candidates.append(candidate)
    units_meta = prov.get("units") if isinstance(prov, Mapping) else None
    if isinstance(units_meta, Mapping):
        for key in ("wavelength_reported", "wavelength_original", "wavelength_input"):
            candidate = units_meta.get(key)
            if candidate:
                candidates.append(candidate)
    for candidate in candidates:
        normalized = _normalise_display_unit_hint(candidate)
        if normalized and normalized != "nm":
            return normalized
    return None


def _add_overlay(
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
    extras: Optional[Mapping[str, object]] = None,
) -> Tuple[bool, str]:
    normalized_axis_kind = _normalize_axis_kind(
        axis_kind or (metadata or {}).get("axis_kind") if metadata else axis_kind
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
        overlays = _get_overlays()
        fingerprint = _compute_image_fingerprint(image)
        policy = st.session_state.get("duplicate_policy", "allow")
        if policy in {"skip", "ledger"}:
            for existing in overlays:
                if existing.fingerprint == fingerprint:
                    return False, f"Skipped duplicate trace: {label}"
            if policy == "ledger":
                ledger: DuplicateLedger = st.session_state["duplicate_ledger"]
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
        overlays = _get_overlays()
        overlays.append(trace)
        _set_overlays(overlays)

        if st.session_state.get("duplicate_policy", "allow") == "ledger":
            ledger = st.session_state["duplicate_ledger"]
            ledger.record(
                fingerprint,
                {
                    "label": label,
                    "provider": provider,
                    "session_id": st.session_state.get("session_id"),
                    "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            )

        if not st.session_state.get("reference_trace_id"):
            spectral_candidates = [
                existing
                for existing in overlays
                if _normalize_axis_kind(existing.axis_kind) not in {"image", "time"}
            ]
            if spectral_candidates:
                st.session_state["reference_trace_id"] = spectral_candidates[0].trace_id

        message = f"Added {label}"
        if provider:
            message += f" ({provider})"
        return True, message

    try:
        values_w = [float(v) for v in wavelengths]
        values_f = [float(v) for v in flux]
    except (TypeError, ValueError):
        return False, "Unable to coerce spectral data to floats."
    if not values_w or not values_f or len(values_w) != len(values_f):
        return False, "No spectral samples available."

    if hover is not None and len(hover) == len(values_w):
        paired = sorted(zip(values_w, values_f, hover), key=lambda item: float(item[0]))
        values_w = [float(item[0]) for item in paired]
        values_f = [float(item[1]) for item in paired]
        hover_sorted = [item[2] for item in paired]
    else:
        paired = sorted(zip(values_w, values_f), key=lambda item: float(item[0]))
        values_w = [float(item[0]) for item in paired]
        values_f = [float(item[1]) for item in paired]
        hover_sorted = list(hover) if hover is not None else None

    downsample_map: Dict[int, Tuple[Tuple[float, ...], Tuple[float, ...]]] = {}
    if downsample:
        for tier, payload in downsample.items():
            try:
                tier_value = int(tier)
            except (TypeError, ValueError):
                continue
            wavelengths_ds = (
                payload.get("wavelength_nm") if isinstance(payload, Mapping) else None
            )
            flux_ds = payload.get("flux") if isinstance(payload, Mapping) else None
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

    overlays = _get_overlays()
    overlays_before = len(overlays)
    fingerprint = _compute_fingerprint(values_w, values_f)
    policy = st.session_state.get("duplicate_policy", "allow")
    if policy in {"skip", "ledger"}:
        for existing in overlays:
            if existing.fingerprint == fingerprint:
                return False, f"Skipped duplicate trace: {label}"
        if policy == "ledger":
            ledger: DuplicateLedger = st.session_state["duplicate_ledger"]
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
        extras=dict(extras or {}),
    )
    overlays.append(trace)
    _set_overlays(overlays)

    if policy == "ledger":
        ledger = st.session_state["duplicate_ledger"]
        ledger.record(
            fingerprint,
            {
                "label": label,
                "provider": provider,
                "session_id": st.session_state.get("session_id"),
                "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

    if (
        overlays_before == 0
        and not st.session_state.get("display_units_user_override")
    ):
        preferred_unit = _preferred_display_unit(trace.metadata, trace.provenance)
        if (
            preferred_unit
            and preferred_unit != st.session_state.get("display_units", "nm")
        ):
            st.session_state["display_units"] = preferred_unit

    if not st.session_state.get("reference_trace_id"):
        st.session_state["reference_trace_id"] = trace.trace_id

    message = f"Added {label}"
    if provider:
        message += f" ({provider})"
    return True, message


def _add_overlay_payload(payload: Dict[str, object]) -> Tuple[bool, str]:
    base_added, base_message = _add_overlay(
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
        or ((payload.get("metadata") or {}).get("axis_kind") if isinstance(payload.get("metadata"), Mapping) else None),
        downsample=payload.get("downsample"),
        cache_dataset_id=payload.get("cache_dataset_id"),
        image=payload.get("image") if isinstance(payload.get("image"), Mapping) else None,
        extras=payload.get("extras"),
    )
    additional = payload.get("additional_traces")
    extra_success = 0
    failure_messages: List[str] = []
    if isinstance(additional, Sequence):
        for entry in additional:
            if not isinstance(entry, Mapping):
                continue
            label = entry.get("label")
            extra_label = str(label) if label is not None else f"{payload.get('label', 'Trace')} (extra)"
            success, message = _add_overlay(
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
                )
                or (
                    (payload.get("metadata") or {}).get("axis_kind")
                    if isinstance(payload.get("metadata"), Mapping)
                    else None
                ),
                downsample=entry.get("downsample"),
                cache_dataset_id=entry.get("cache_dataset_id")
                or payload.get("cache_dataset_id"),
                image=entry.get("image")
                if isinstance(entry.get("image"), Mapping)
                else (payload.get("image") if isinstance(payload.get("image"), Mapping) else None),
                extras=entry.get("extras"),
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


def _add_example_trace(spec: ExampleSpec) -> Tuple[bool, str]:
    try:
        hits = provider_search(spec.provider, spec.query)
    except Exception as exc:
        return False, f"Failed to load {spec.label}: {exc}"

    if not hits:
        return False, f"No {spec.provider} results returned for {spec.label}."

    hit = hits[0]
    metadata = dict(hit.metadata)
    metadata.setdefault("example_slug", spec.slug)
    metadata.setdefault("example_description", spec.description)

    provenance = dict(hit.provenance)
    provenance.setdefault("example_slug", spec.slug)
    provenance.setdefault("example_description", spec.description)

    summary_parts = [hit.summary]
    if spec.description and spec.description not in summary_parts:
        summary_parts.append(spec.description)
    summary = " • ".join(part for part in summary_parts if part)

    return _add_overlay(
        hit.label,
        [float(value) for value in hit.wavelengths_nm],
        [float(value) for value in hit.flux],
        provider=hit.provider,
        summary=summary or spec.description,
        metadata=metadata,
        provenance=provenance,
    )


def _load_example(spec: ExampleSpec) -> Tuple[bool, str]:
    added, message = _add_example_trace(spec)
    _register_example_usage(spec, success=added)
    return added, message


def _render_examples_group(container: DeltaGenerator) -> None:
    container.markdown("#### Examples library")
    if not EXAMPLE_LIBRARY:
        container.caption("Example library unavailable.")
        return

    quick_form = container.form("example_quick_add_form")
    quick_form.caption("Quick add")
    selection = quick_form.selectbox(
        "Quick add example",
        EXAMPLE_LIBRARY,
        format_func=lambda spec: spec.label,
        key="example_quick_add_select",
        label_visibility="collapsed",
    )
    if selection.description:
        quick_form.caption(selection.description)
    submitted = quick_form.form_submit_button("Load example", use_container_width=True)
    if submitted:
        added, message = _load_example(selection)
        (container.success if added else container.info)(message)

    overlays = _get_overlays()
    if not overlays:
        container.caption("Load an example or fetch from an archive to begin.")


def _render_line_catalog_group(container: DeltaGenerator) -> None:
    online = bool(st.session_state.get("network_available", True))
    container.markdown("#### Line catalogs")
    if not online:
        container.caption("Using local cache")
        container.info("NIST lookups are unavailable while offline.")
    container.markdown("NIST ASD lines")
    if online:
        _render_nist_form(container)
    else:
        container.caption("Connect to the network to fetch NIST ASD lines.")
    container.markdown("NIST Quantitative IR spectra")
    _render_nist_quant_ir_form(container, online=online)


def _render_nist_form(container: DeltaGenerator) -> None:
    form = container.form("nist_overlay_form", clear_on_submit=False)
    identifier = form.text_input("Element or spectrum", placeholder="e.g. Fe II")
    lower = form.number_input("Lower λ (nm)", min_value=0.0, value=380.0, step=5.0)
    upper = form.number_input("Upper λ (nm)", min_value=0.0, value=750.0, step=5.0)
    use_ritz = form.checkbox("Prefer Ritz wavelengths", value=True)
    submitted = form.form_submit_button("Fetch lines")
    if not submitted:
        return
    identifier = (identifier or "").strip()
    if not identifier:
        container.warning("Enter an element identifier.")
        return
    if math.isclose(lower, upper):
        container.warning("Lower and upper bounds must differ.")
        return
    try:
        result = fetch_spectrum(
            "nist",
            element=identifier,
            lower_wavelength=min(lower, upper),
            upper_wavelength=max(lower, upper),
            wavelength_unit="nm",
            use_ritz=use_ritz,
        )
    except (FetchError, ValueError, RuntimeError) as exc:
        container.error(f"NIST fetch failed: {exc}")
        return
    payload = _convert_nist_payload(result)
    if not payload:
        container.warning("NIST returned no lines for that query.")
        return
    added, message = _add_overlay_payload(payload)
    (container.success if added else container.info)(message)


def _normalise_quant_ir_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _build_quant_ir_options(
    catalog: Sequence[Mapping[str, object]]
) -> List[QuantIROption]:
    lookup: Dict[str, Mapping[str, object]] = {}
    for entry in catalog:
        name = str(entry.get("name") or "")
        if not name:
            continue
        lookup[_normalise_quant_ir_token(name)] = entry

    options: List[QuantIROption] = []
    for molecule in NIST_QUANT_IR_MOLECULES:
        query = molecule["query"]
        entry = lookup.get(_normalise_quant_ir_token(query))
        if entry:
            relative = entry.get("relative_uncertainty")
            relative_str = str(relative) if isinstance(relative, str) and relative else None
            apodizations_raw = entry.get("measurements") or ()
            apodizations: List[str] = []
            for candidate in apodizations_raw:
                if isinstance(candidate, Mapping):
                    label = candidate.get("apodization")
                    if label:
                        apodizations.append(str(label))
            options.append(
                QuantIROption(
                    label=molecule["label"],
                    query=query,
                    available=True,
                    relative_uncertainty=relative_str,
                    apodizations=tuple(apodizations),
                )
            )
        else:
            options.append(
                QuantIROption(
                    label=molecule["label"],
                    query=query,
                    available=False,
                    relative_uncertainty=None,
                    apodizations=(),
                )
            )
    return options


def _format_quant_ir_option(option: QuantIROption) -> str:
    label = option.label
    if not option.available:
        return f"{label} — unavailable"
    if option.relative_uncertainty:
        return f"{label} ({option.relative_uncertainty} uncertainty)"
    return label


def _render_nist_quant_ir_form(
    container: DeltaGenerator, *, online: bool
) -> None:
    if not online:
        container.caption("Connect to the network to fetch NIST Quantitative IR spectra.")
        return
    try:
        catalog = _cached_quant_ir_catalog()
    except nist_quant_ir.QuantIRFetchError as exc:
        container.error(f"NIST Quant IR catalog unavailable: {exc}")
        return
    options = _build_quant_ir_options(catalog)
    if not options:
        container.warning("No NIST Quant IR molecules configured.")
        return

    form = container.form("nist_quant_ir_form", clear_on_submit=False)
    selection = form.selectbox(
        "Molecule",
        options,
        format_func=_format_quant_ir_option,
    )
    form.caption(
        f"Resolution fixed at {NIST_QUANT_IR_RESOLUTION:.3f} cm⁻¹ using catalogued apodization windows."
    )
    manual_catalog_getter = getattr(nist_quant_ir, "manual_species_catalog", None)
    if manual_catalog_getter is None:
        try:
            manual_catalog_getter = nist_quant_ir._manual_species_catalog  # type: ignore[attr-defined]
        except AttributeError:
            manual_catalog_getter = None
    manual_names: Tuple[str, ...] = ()
    if callable(manual_catalog_getter):
        try:
            manual_names = tuple(
                sorted(
                    {
                        species.name
                        for species in manual_catalog_getter().values()
                    }
                )
            )
        except Exception:  # pragma: no cover - defensive fallback
            manual_names = ()
    if manual_names:
        form.caption(
            "Manual entries ({names}) map to the highest-resolution NIST WebBook IR spectra and are flagged in provenance.".format(
                names=", ".join(manual_names)
            )
        )
    submitted = form.form_submit_button("Fetch spectrum", use_container_width=True)
    if not submitted:
        return
    if not selection.available:
        container.info(
            f"{selection.label} is not currently available in the NIST Quantitative IR catalog."
        )
        return
    try:
        payload = fetch_spectrum(
            "nist-quant-ir",
            species=selection.query,
            resolution_cm_1=NIST_QUANT_IR_RESOLUTION,
        )
    except (FetchError, ValueError, RuntimeError) as exc:
        container.error(f"NIST Quant IR fetch failed: {exc}")
        return
    added, message = _add_overlay_payload(payload)
    (container.success if added else container.info)(message)


def _render_display_section(container: DeltaGenerator) -> None:
    container.markdown("#### Display & viewport")
    overlays = _get_overlays()
    cleared = container.button(
        "Clear overlays",
        key="clear_overlays_button",
        help="Remove all overlays from the session.",
        disabled=not overlays,
    )
    if cleared:
        _clear_overlays()
        st.session_state["overlay_clear_message"] = "Cleared all overlays."
        st.session_state["display_units_user_override"] = False

    unit_options = ["nm", "Å", "µm", "cm^-1"]
    current_units = st.session_state.get("display_units", "nm")
    if current_units not in unit_options:
        current_units = "nm"
    units = container.selectbox(
        "Wavelength units",
        unit_options,
        index=unit_options.index(current_units),
    )
    if units != current_units:
        st.session_state["display_units_user_override"] = True
    st.session_state["display_units"] = units
    display_mode_options = ["Flux (raw)", "Flux (normalized)"]
    current_mode = st.session_state.get("display_mode", "Flux (raw)")
    mode_index = (
        display_mode_options.index(current_mode)
        if current_mode in display_mode_options
        else 0
    )
    st.session_state["display_mode"] = container.selectbox(
        "Flux scaling", display_mode_options, index=mode_index
    )

    full_resolution = container.checkbox(
        "Full resolution rendering",
        value=bool(st.session_state.get("display_full_resolution", False)),
        help="Render traces using all available points in the current viewport.",
    )
    st.session_state["display_full_resolution"] = bool(full_resolution)

    target_overlays = [trace for trace in overlays if trace.visible] or overlays
    if not target_overlays:
        st.session_state["auto_viewport"] = True
        return

    axis_groups = _group_overlays_by_axis_kind(target_overlays)
    primary_axis = _determine_primary_axis_kind(target_overlays)
    selected_group = axis_groups.get(primary_axis) or target_overlays
    min_bound, max_bound = _infer_viewport_bounds(selected_group)
    if math.isclose(min_bound, max_bound):
        max_bound = min_bound + 1.0

    auto = container.checkbox(
        "Auto viewport", value=bool(st.session_state.get("auto_viewport", True))
    )
    st.session_state["auto_viewport"] = auto
    if auto:
        _set_viewport_for_kind(primary_axis, (None, None))
        return

    stored_viewport = _get_viewport_for_kind(primary_axis)
    default_low, default_high = _effective_viewport(
        selected_group, stored_viewport, axis_kind=primary_axis
    )
    if default_low is None or default_high is None:
        default_low, default_high = float(min_bound), float(max_bound)
    else:
        default_low = max(float(min_bound), float(default_low))
        default_high = min(float(max_bound), float(default_high))
        if default_low >= default_high:
            default_low, default_high = float(min_bound), float(max_bound)

    if len([kind for kind, traces in axis_groups.items() if traces]) > 1:
        label = primary_axis.replace("_", " ")
        container.warning(
            f"Mixed axis kinds detected. Viewport adjustments apply to {label} traces; "
            "other kinds will auto-scale."
        )

    slider_label = "Viewport (nm)" if primary_axis == "wavelength" else "Viewport (time)"
    span = max(float(max_bound) - float(min_bound), 1.0)
    step = 1.0 if primary_axis == "wavelength" else max(span / 200.0, 1e-6)
    selection = container.slider(
        slider_label,
        min_value=float(min_bound),
        max_value=float(max_bound),
        value=(float(default_low), float(default_high)),
        step=float(step),
    )
    _set_viewport_for_kind(
        primary_axis, (float(selection[0]), float(selection[1]))
    )


def _render_settings_group(container: DeltaGenerator) -> None:
    container.markdown("### Session controls")
    online = container.checkbox(
        "Enable archive fetchers",
        value=bool(st.session_state.get("network_available", True)),
        key="network_available_toggle",
        help="Disable to work offline using cached data only.",
    )
    st.session_state["network_available"] = bool(online)
    if not online:
        container.caption("Using local cache for remote fetches.")

    container.divider()
    _render_display_section(container)
    container.divider()
    _render_examples_group(container)
    container.divider()
    _render_line_catalog_group(container)
def _render_uploads_group(container: DeltaGenerator) -> None:
    container.markdown("#### Duplicate handling")
    base_options = {"skip": "Skip duplicates (session)", "allow": "Allow duplicates"}
    base_code = st.session_state.get("duplicate_base_policy", "skip")
    base_labels = list(base_options.values())
    try:
        base_index = [code for code in base_options.keys()].index(base_code)
    except ValueError:
        base_index = 0
    base_selection = container.radio(
        "Session policy",
        base_labels,
        index=base_index,
        key="duplicate_base_policy_radio",
    )
    resolved_base = next(
        code for code, label in base_options.items() if label == base_selection
    )
    st.session_state["duplicate_base_policy"] = resolved_base
    if not st.session_state.get("duplicate_ledger_lock", False):
        st.session_state["duplicate_policy"] = resolved_base

    lock_state = bool(st.session_state.get("duplicate_ledger_lock", False))
    pending = st.session_state.get("duplicate_ledger_pending_action")
    checkbox_default = lock_state if pending is None else (pending == "enable")
    ledger_checkbox = container.checkbox(
        "Enforce ledger lock",
        value=checkbox_default,
        key="duplicate_ledger_lock_checkbox",
        help="Persist duplicate fingerprints across sessions using the ledger.",
    )
    checkbox_value = bool(ledger_checkbox)

    if pending is None:
        if checkbox_value != lock_state:
            st.session_state["duplicate_ledger_pending_action"] = (
                "enable" if checkbox_value else "disable"
            )
            pending = st.session_state["duplicate_ledger_pending_action"]
    else:
        if checkbox_value == lock_state:
            st.session_state["duplicate_ledger_pending_action"] = None
            pending = None
        elif checkbox_value != checkbox_default:
            st.session_state["duplicate_ledger_pending_action"] = (
                "enable" if checkbox_value else "disable"
            )
            pending = st.session_state["duplicate_ledger_pending_action"]

    if pending is None:
        st.session_state["duplicate_ledger_lock"] = lock_state
    if pending == "enable":
        container.warning(
            "Enable ledger lock to enforce duplicate detection against the persistent ledger."
        )
        confirm_col, cancel_col = container.columns(2)
        if confirm_col.button("Confirm lock", key="confirm_ledger_enable"):
            st.session_state["duplicate_ledger_lock"] = True
            st.session_state["duplicate_policy"] = "ledger"
            st.session_state["duplicate_ledger_pending_action"] = None
            container.success("Ledger lock enabled.")
        if cancel_col.button("Cancel", key="cancel_ledger_enable"):
            st.session_state["duplicate_ledger_pending_action"] = None
    elif pending == "disable":
        container.warning(
            "Disable ledger lock? New duplicates will follow the session policy."
        )
        confirm_col, cancel_col = container.columns(2)
        if confirm_col.button("Disable lock", key="confirm_ledger_disable"):
            st.session_state["duplicate_ledger_lock"] = False
            st.session_state["duplicate_policy"] = st.session_state.get(
                "duplicate_base_policy", "skip"
            )
            st.session_state["duplicate_ledger_pending_action"] = None
            container.info("Ledger lock disabled.")
        if cancel_col.button("Keep lock", key="cancel_ledger_disable"):
            st.session_state["duplicate_ledger_pending_action"] = None
    else:
        if st.session_state.get("duplicate_ledger_lock", False):
            container.caption(
                "Ledger lock is active; duplicates are validated against the persistent ledger."
            )
            if container.button(
                "Undo session ledger entries", key="purge_session_ledger"
            ):
                ledger: DuplicateLedger = st.session_state["duplicate_ledger"]
                ledger.purge_session(st.session_state.get("session_id"))
                container.success("Session ledger entries cleared.")
        else:
            container.caption("Duplicates will follow the selected session policy.")


# ---------------------------------------------------------------------------
# Overlay rendering helpers


def _infer_viewport_bounds(overlays: Sequence[OverlayTrace]) -> Tuple[float, float]:
    if not overlays:
        return 350.0, 900.0

    meta_ranges: List[Tuple[float, float]] = []
    data_wavelengths: List[float] = []

    for trace in overlays:
        meta_range = _extract_metadata_range(trace.metadata)
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


def _auto_viewport_range(
    overlays: Sequence[OverlayTrace],
    *,
    coverage: float = 0.99,
    axis_kind: Optional[str] = None,
) -> Optional[Tuple[float, float]]:
    normalized_kind = _normalize_axis_kind(axis_kind) if axis_kind else None
    if normalized_kind is not None:
        overlays = [
            trace for trace in overlays if _axis_kind_for_trace(trace) == normalized_kind
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
        mask = np.isfinite(wavelengths) & np.isfinite(flux_values)
        if mask.sum() < 2:
            continue
        wavelengths = wavelengths[mask]
        flux_values = flux_values[mask]
        if wavelengths.size < 2:
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


def _effective_viewport(
    overlays: Sequence[OverlayTrace],
    viewport: Tuple[float | None, float | None],
    *,
    axis_kind: Optional[str] = None,
) -> Tuple[float | None, float | None]:
    if not overlays:
        return (None, None)

    normalized_viewport = _normalize_viewport_tuple(viewport)
    low, high = normalized_viewport
    if low is not None or high is not None:
        return (
            float(low) if low is not None else None,
            float(high) if high is not None else None,
        )

    target_kind = axis_kind or _axis_kind_for_trace(overlays[0])
    auto_range = _auto_viewport_range(overlays, axis_kind=target_kind)
    if auto_range is not None:
        return float(auto_range[0]), float(auto_range[1])

    fallback_low, fallback_high = _infer_viewport_bounds(overlays)
    return float(fallback_low), float(fallback_high)


def _extract_metadata_range(
    metadata: Dict[str, object],
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


def _filter_viewport(
    df: pd.DataFrame, viewport: Tuple[float | None, float | None]
) -> pd.DataFrame:
    low, high = viewport
    if low is not None:
        df = df[df["wavelength_nm"] >= low]
    if high is not None:
        df = df[df["wavelength_nm"] <= high]
    return df


def _convert_wavelength(series: pd.Series, unit: str) -> Tuple[pd.Series, str]:
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
        _clean(meta.get("time_original_unit"))
        or _clean(units_meta.get("time_original_unit"))
        or _clean(meta.get("reported_time_unit"))
        or _clean(units_meta.get("time_reported"))
    )

    offset_value: Optional[object] = meta.get("time_offset") if isinstance(meta, Mapping) else None
    if offset_value is None and isinstance(units_meta, Mapping):
        offset_value = units_meta.get("time_offset")

    frame_label = _clean(meta.get("time_frame")) if isinstance(meta, Mapping) else None
    if not frame_label and isinstance(units_meta, Mapping):
        frame_label = _clean(units_meta.get("time_frame"))

    if reference_label is None and offset_value is not None:
        try:
            offset_float = float(offset_value)
            offset_text = f"{offset_float:g}"
        except (TypeError, ValueError):
            offset_text = str(offset_value)
        if frame_label:
            reference_label = f"{frame_label} - {offset_text}"
        else:
            reference_label = f"offset {offset_text}"
    elif reference_label and offset_value is not None and frame_label:
        try:
            offset_float = float(offset_value)
            offset_text = f"{offset_float:g}"
        except (TypeError, ValueError):
            offset_text = str(offset_value)
        if frame_label not in reference_label:
            reference_label = f"{frame_label} - {offset_text}"

    return unit_label, reference_label


def _convert_time_axis(series: pd.Series, trace: OverlayTrace) -> Tuple[pd.Series, str]:
    values = pd.to_numeric(series, errors="coerce")
    metadata = trace.metadata or {}
    provenance = trace.provenance or {}
    unit_label, reference_label = _time_axis_labels(metadata, provenance)
    axis_title = f"Time ({unit_label})" if unit_label else "Time"
    if reference_label:
        axis_title = f"{axis_title} — ref {reference_label}"
    return values, axis_title


def _convert_axis_series(
    series: pd.Series, trace: OverlayTrace, display_units: str
) -> Tuple[pd.Series, str]:
    if getattr(trace, "axis_kind", "wavelength") == "time":
        return _convert_time_axis(series, trace)
    return _convert_wavelength(series, display_units)


def _trace_flux_unit_label(trace: OverlayTrace) -> Optional[str]:
    metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
    candidates: List[str] = []
    if isinstance(metadata, Mapping):
        for key in (
            "flux_unit_display",
            "flux_unit",
            "reported_flux_unit",
            "flux_unit_original",
        ):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value)
    if getattr(trace, "flux_unit", None):
        candidates.append(str(trace.flux_unit))

    for candidate in candidates:
        label = candidate.strip()
        if not label:
            continue
        lowered = label.lower()
        if "transmittance" in lowered and "percent" in lowered:
            return "Transmittance (%)"
        if lowered == "transmittance" or lowered == "transmission":
            return "Transmittance"
        if "absorbance" in lowered and "base" in lowered:
            return "Absorbance (base 10)"
        if "absorbance" in lowered:
            return "Absorbance"
        if lowered in {"arb", "arbitrary", "arbitrary flux"}:
            continue
        return label
    return None


def _flux_axis_category(trace: OverlayTrace) -> str:
    label = _trace_flux_unit_label(trace)
    if label:
        lowered = label.lower()
    else:
        lowered = ""
    axis = (trace.axis or "").strip().lower()
    flux_kind = (trace.flux_kind or "").strip().lower()

    if any(token in lowered for token in ("transmittance", "transmission")) or (
        "transmission" in axis or "transmittance" in axis
    ):
        return "transmittance"
    if "absorb" in lowered or "absorb" in axis or "absorb" in flux_kind:
        return "absorbance"
    return "other"


def _resolve_flux_axis_title(
    overlays: Sequence[OverlayTrace], display_mode: str
) -> str:
    if display_mode != "Flux (raw)":
        return "Normalized flux"
    labels = []
    for trace in overlays:
        label = _trace_flux_unit_label(trace)
        if label:
            labels.append(label)
    unique = {label for label in labels if label}
    if not unique:
        return "Flux"
    if len(unique) == 1:
        return unique.pop()
    return "Flux"


def _axis_title_for_kind(
    axis_kind: str,
    overlays: Sequence[OverlayTrace],
    display_units: str,
) -> Optional[str]:
    normalized = _normalize_axis_kind(axis_kind)
    for trace in overlays:
        if _axis_kind_for_trace(trace) != normalized:
            continue
        values = list(trace.wavelength_nm)
        if not values:
            continue
        sample = pd.Series(values[: min(len(values), 256)])
        _, axis_title = _convert_axis_series(sample, trace, display_units)
        if axis_title:
            return axis_title
    return None


def _normalize_hover_values(
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


def _add_line_trace(
    fig: go.Figure,
    df: pd.DataFrame,
    label: str,
    hover_values: Optional[Sequence[Optional[str]]] = None,
    *,
    secondary_y: bool = False,
) -> None:
    xs: List[float | None] = []
    ys: List[float | None] = []
    resolved_hover = (
        _normalize_hover_values(hover_values)
        if hover_values is not None
        else _normalize_hover_values(df.get("hover"))
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
        ),
        secondary_y=secondary_y,
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
        ),
        secondary_y=secondary_y,
    )


def _build_overlay_figure(
    overlays: Sequence[OverlayTrace],
    display_units: str,
    display_mode: str,
    viewport_by_kind: Mapping[str, Tuple[float | None, float | None]],
    reference: Optional[OverlayTrace],
    differential_mode: str,
    version_tag: str,
    *,
    axis_viewport_by_kind: Optional[
        Mapping[str, Tuple[float | None, float | None]]
    ] = None,
) -> Tuple[go.Figure, str]:
    category_lookup: Dict[str, str] = {}
    target_overlays = [trace for trace in overlays if trace.visible] or list(overlays)
    for trace in target_overlays:
        category_lookup[trace.trace_id] = _flux_axis_category(trace)

    should_reverse_axis = False
    if display_units == "cm^-1":
        should_reverse_axis = any(
            isinstance(trace.metadata, Mapping)
            and bool(trace.metadata.get("ir_x_descending"))
            for trace in target_overlays
        )

    has_transmittance = any(
        category == "transmittance" for category in category_lookup.values()
    )
    has_absorbance = any(
        category == "absorbance" for category in category_lookup.values()
    )
    use_secondary_y = has_transmittance and has_absorbance

    fig = make_subplots(specs=[[{"secondary_y": use_secondary_y}]])
    axis_title = "Wavelength (nm)"
    full_resolution = _is_full_resolution_enabled()
    max_points = 3000000 if full_resolution else 1500000
    viewport_lookup = {
        _normalize_axis_kind(kind): _normalize_viewport_tuple(viewport)
        for kind, viewport in (viewport_by_kind or {}).items()
    }
    viewport_kinds = set(viewport_lookup.keys())
    axis_lookup = (
        {
            _normalize_axis_kind(kind): _normalize_viewport_tuple(viewport)
            for kind, viewport in axis_viewport_by_kind.items()
        }
        if axis_viewport_by_kind
        else {}
    )
    reference_vectors: Optional[TraceVectors] = None
    if reference and _axis_kind_for_trace(reference) not in {"image", "time"}:
        ref_kind = _axis_kind_for_trace(reference)
        reference_vectors = reference.to_vectors(
            max_points=max_points,
            viewport=viewport_lookup.get(ref_kind, (None, None)),
        )

    visible_axis_kinds: List[str] = []
    axis_titles: Dict[str, str] = {}

    for trace in overlays:
        if not trace.visible:
            continue

        axis_kind = _axis_kind_for_trace(trace)
        if axis_kind == "image":
            continue
        if axis_kind == "time" and axis_kind not in viewport_kinds:
            continue
        viewport = viewport_lookup.get(axis_kind, (None, None))
        visible_axis_kinds.append(axis_kind)

        category = category_lookup.get(trace.trace_id, "other")
        secondary_axis = use_secondary_y and category == "absorbance"

        if trace.kind == "lines":
            df = trace.to_dataframe()
            df = _filter_viewport(df, viewport)
            if df.empty:
                continue
            converted, candidate_title = _convert_axis_series(
                df["wavelength_nm"], trace, display_units
            )
            df = df.assign(wavelength=converted, flux=df["flux"].astype(float))
            hover_values = _normalize_hover_values(df.get("hover"))
            _add_line_trace(
                fig,
                df,
                trace.label,
                hover_values,
                secondary_y=secondary_axis,
            )
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

        converted, candidate_title = _convert_axis_series(
            pd.Series(sample_w), trace, display_units
        )
        axis_titles.setdefault(axis_kind, candidate_title)
        flux_array = np.asarray(sample_flux, dtype=float)

        if display_mode != "Flux (raw)":
            flux_array = apply_normalization(flux_array, "max")

        hover_values = (
            _normalize_hover_values(sample_hover) if sample_hover is not None else None
        )

        fig.add_trace(
            go.Scatter(
                x=converted.tolist(),
                y=flux_array.tolist(),
                mode="lines",
                name=trace.label,
                hovertext=hover_values if hover_values is not None else None,
                hoverinfo="text" if hover_values is not None else None,
            ),
            secondary_y=secondary_axis,
        )

    if axis_titles:
        unique_kinds = sorted({kind for kind in visible_axis_kinds})
        if len(unique_kinds) == 1:
            axis_title = axis_titles.get(unique_kinds[0], axis_title)
        else:
            friendly = " + ".join(kind.replace("_", " ") for kind in unique_kinds)
            axis_title = f"Mixed axes ({friendly})"

    if use_secondary_y:
        primary_overlays = [
            trace
            for trace in target_overlays
            if category_lookup.get(trace.trace_id) != "absorbance"
        ]
        secondary_overlays = [
            trace
            for trace in target_overlays
            if category_lookup.get(trace.trace_id) == "absorbance"
        ]
        if not primary_overlays:
            primary_overlays = secondary_overlays
            secondary_overlays = []
    else:
        primary_overlays = list(target_overlays)
        secondary_overlays: List[OverlayTrace] = []

    primary_flux_title = _resolve_flux_axis_title(primary_overlays, display_mode)
    secondary_flux_title = (
        _resolve_flux_axis_title(secondary_overlays, display_mode)
        if secondary_overlays
        else None
    )

    layout_kwargs = dict(
        legend=dict(itemclick="toggleothers"),
        margin=dict(t=50, b=40, l=60, r=20),
        height=520,
    )

    fig.update_layout(**layout_kwargs)
    fig.update_yaxes(tickformat=".3e", exponentformat="power", showexponent="all")
    fig.update_xaxes(tickformat=".0f", separatethousands=False)
    fig.update_xaxes(title_text=axis_title)

    if should_reverse_axis:
        fig.update_xaxes(autorange="reversed")

    if use_secondary_y and secondary_overlays:
        fig.update_yaxes(title_text=primary_flux_title, secondary_y=False)
        fig.update_yaxes(
            title_text=secondary_flux_title or "Absorbance",
            secondary_y=True,
        )
    else:
        fig.update_yaxes(title_text=primary_flux_title, secondary_y=False)
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
                if should_reverse_axis:
                    fig.update_xaxes(
                        range=[float(axis_high), float(axis_low)],
                        autorange="reversed",
                    )
                else:
                    fig.update_xaxes(range=[float(axis_low), float(axis_high)])
    hover_unit = display_units
    if hover_unit == "cm^-1":
        hover_unit = "cm⁻¹"
    fig.update_traces(
        hovertemplate=(
            f"(%{{x:.2f}} {hover_unit}, %{{y:.3e}})<extra>%{{fullData.name}}</extra>"
        )
    )
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


def _render_overlay_table(overlays: Sequence[OverlayTrace]) -> None:
    if not overlays:
        return
    col_show, col_hide = st.columns(2)
    with col_show:
        show_all = st.button("Show all", key="overlay_show_all")
    with col_hide:
        hide_all = st.button("Hide all", key="overlay_hide_all")

    if show_all or hide_all:
        desired_state = bool(show_all)
        mutated = False
        for trace in overlays:
            if trace.visible != desired_state:
                trace.visible = desired_state
                mutated = True
        if mutated:
            _set_overlays(overlays)

    options = [trace.trace_id for trace in overlays]

    table = pd.DataFrame(
        {
            "Label": [trace.label for trace in overlays],
            "Provider": [trace.provider or "—" for trace in overlays],
            "Kind": [trace.kind for trace in overlays],
            "Points": [trace.points for trace in overlays],
            "Visible": [trace.visible for trace in overlays],
        },
        index=[trace.trace_id for trace in overlays],
    )

    editor = st.data_editor(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Visible": st.column_config.CheckboxColumn(
                "Visible", help="Toggle overlay visibility", default=True
            ),
        },
        disabled=["Label", "Provider", "Kind", "Points"],
        key="overlay_visibility_editor",
    )

    mutated = False
    desired_visibility = editor["Visible"] if isinstance(editor, pd.DataFrame) else None
    if desired_visibility is not None:
        for trace in overlays:
            desired = bool(desired_visibility.get(trace.trace_id, trace.visible))
            if trace.visible != desired:
                trace.visible = desired
                mutated = True
    if mutated:
        _set_overlays(overlays)

    selected = st.multiselect(
        "Remove overlays",
        options,
        format_func=_trace_label,
        key="overlay_remove_select",
    )
    if selected and st.button("Remove selected", key="overlay_remove_button"):
        _remove_overlays(selected)
        st.success(f"Removed {len(selected)} overlays.")


def _render_image_overlay_panels(overlays: Sequence[OverlayTrace]) -> None:
    image_traces = [
        trace
        for trace in overlays
        if trace.visible and _axis_kind_for_trace(trace) == "image"
    ]
    if not image_traces:
        return

    st.markdown("#### Image overlays")
    for trace in image_traces:
        payload = trace.image if isinstance(trace.image, Mapping) else {}
        data = payload.get("data")
        try:
            data_array = np.asarray(data, dtype=float)
        except Exception:
            st.warning(f"{trace.label}: Unable to display image data.")
            continue
        if data_array.size == 0:
            st.info(f"{trace.label}: No pixels available.")
            continue

        mask_array = None
        if isinstance(payload, Mapping) and payload.get("mask") is not None:
            try:
                mask_candidate = np.asarray(payload.get("mask"), dtype=bool)
                if mask_candidate.shape == data_array.shape:
                    mask_array = mask_candidate
            except Exception:
                mask_array = None
        if mask_array is not None:
            data_plot = np.where(mask_array, np.nan, data_array)
        else:
            data_plot = np.array(data_array, dtype=float)

        finite = data_plot[np.isfinite(data_plot)]
        try:
            default_min = float(np.nanmin(finite if finite.size else data_plot))
        except ValueError:
            default_min = 0.0
        try:
            default_max = float(np.nanmax(finite if finite.size else data_plot))
        except ValueError:
            default_max = default_min + 1.0
        if not math.isfinite(default_min):
            default_min = 0.0
        if not math.isfinite(default_max):
            default_max = default_min + 1.0

        clip = st.slider(
            f"Intensity clip (%) • {trace.label}",
            min_value=0.0,
            max_value=25.0,
            value=1.0,
            step=0.5,
            key=f"image_clip_{trace.trace_id}",
        )

        if finite.size:
            lower = float(np.percentile(finite, clip))
            upper = float(np.percentile(finite, 100 - clip))
            if not math.isfinite(lower) or not math.isfinite(upper) or math.isclose(lower, upper):
                lower = default_min
                upper = default_max
        else:
            lower = default_min
            upper = default_max
        if not math.isfinite(lower) or not math.isfinite(upper):
            lower, upper = 0.0, 1.0
        if upper <= lower:
            upper = lower + 1.0

        fig = go.Figure(
            data=go.Heatmap(
                z=data_plot,
                colorscale="Viridis",
                zmin=lower,
                zmax=upper,
                colorbar=dict(title=str(trace.flux_unit or "")),
            )
        )
        fig.update_layout(
            dragmode="zoom",
            xaxis=dict(title="X (pixel)"),
            yaxis=dict(title="Y (pixel)", autorange="reversed"),
            margin=dict(t=30, b=40, l=40, r=20),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True, key=f"image_plot_{trace.trace_id}")

        shape = payload.get("shape") if isinstance(payload, Mapping) else None
        if isinstance(shape, (list, tuple)):
            dims = " × ".join(str(int(dim)) for dim in shape)
        else:
            dims = " × ".join(str(size) for size in data_array.shape)
        wcs_info = trace.provenance.get("wcs") if isinstance(trace.provenance, Mapping) else None
        wcs_axes = None
        if isinstance(wcs_info, Mapping):
            axes = wcs_info.get("world_axis_physical_types")
            if isinstance(axes, (list, tuple)):
                wcs_axes = ", ".join(str(axis) for axis in axes if axis)
        caption_parts = [f"Shape: {dims} px"]
        if trace.flux_unit:
            caption_parts.append(f"Flux: {trace.flux_unit}")
        if wcs_axes:
            caption_parts.append(f"WCS axes: {wcs_axes}")
        st.caption(" • ".join(caption_parts))


def _remove_overlays(trace_ids: Sequence[str]) -> None:
    remaining = [
        trace for trace in _get_overlays() if trace.trace_id not in set(trace_ids)
    ]
    _set_overlays(remaining)
    cache = st.session_state.get("similarity_cache")
    if isinstance(cache, SimilarityCache):
        cache.reset()


def _normalise_wavelength_range(meta: Dict[str, object]) -> str:
    range_candidates = [
        meta.get("wavelength_effective_range_nm"),
        meta.get("wavelength_range_nm"),
    ]
    for candidate in range_candidates:
        if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
            try:
                low = float(candidate[0])
                high = float(candidate[1])
            except (TypeError, ValueError):
                continue
            return f"{low:.2f} – {high:.2f}"
    return "—"


def _format_axis_range(trace: OverlayTrace, meta: Mapping[str, object]) -> str:
    axis_kind = str(trace.axis_kind or meta.get("axis_kind") or "wavelength").lower()
    if axis_kind == "time":
        range_candidates = [meta.get("data_time_range"), meta.get("time_range")]
        metadata_original = trace.metadata or {}
        provenance = trace.provenance or {}
        unit_label, reference_label = _time_axis_labels(metadata_original, provenance)
        for candidate in range_candidates:
            if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
                try:
                    low = float(candidate[0])
                    high = float(candidate[1])
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(low) or not math.isfinite(high):
                    continue
                suffix = f" {unit_label}" if unit_label else ""
                range_text = f"{low:.4f} – {high:.4f}{suffix}"
                if reference_label:
                    range_text += f" (ref: {reference_label})"
                return range_text
        return "—"
    if axis_kind == "image":
        shape = meta.get("image_shape")
        if isinstance(shape, (list, tuple)) and shape:
            try:
                dims = " × ".join(str(int(dim)) for dim in shape)
            except Exception:
                dims = None
            if dims:
                return f"{dims} px"
        return "—"

    range_candidates = [
        meta.get("wavelength_effective_range_nm"),
        meta.get("wavelength_range_nm"),
    ]
    for candidate in range_candidates:
        if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
            try:
                low = float(candidate[0])
                high = float(candidate[1])
            except (TypeError, ValueError):
                continue
            if not math.isfinite(low) or not math.isfinite(high):
                continue
            return f"{low:.2f} – {high:.2f} nm"
    return "—"


def _build_metadata_summary_rows(
    overlays: Sequence[OverlayTrace],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for trace in overlays:
        meta = {str(k).lower(): v for k, v in (trace.metadata or {}).items()}
        axis_range = _format_axis_range(trace, meta)
        rows.append(
            {
                "Label": trace.label,
                "Axis": trace.axis,
                "Flux unit": trace.flux_unit,
                "Instrument": meta.get("instrument") or meta.get("instrume") or "—",
                "Telescope": meta.get("telescope") or meta.get("telescop") or "—",
                "Observation": meta.get("date-obs")
                or meta.get("date_obs")
                or meta.get("observation_date")
                or "—",
                "Axis range": axis_range,
                "Resolution": meta.get("resolution_native")
                or meta.get("resolution")
                or "—",
            }
        )
    return rows


def _render_metadata_summary(overlays: Sequence[OverlayTrace]) -> None:
    if not overlays:
        return
    rows = _build_metadata_summary_rows(overlays)
    if rows:
        st.markdown("#### Metadata summary")
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    with st.expander("Metadata & provenance details", expanded=False):
        for trace in overlays:
            st.markdown(f"**{trace.label}**")
            if trace.metadata:
                st.json(trace.metadata)
            else:
                st.caption("No metadata recorded.")
            if trace.provenance:
                st.json(trace.provenance)
            else:
                st.caption("No conversion provenance available.")


def _get_upload_registry() -> Dict[str, Dict[str, object]]:
    return st.session_state.setdefault("local_upload_registry", {})


def _read_uploaded_file(
    uploaded,
) -> Tuple[Optional[str], Optional[bytes], Optional[str], str]:
    """Return the checksum and payload bytes for a Streamlit upload widget."""

    try:
        payload_bytes = uploaded.getvalue()
    except Exception as exc:  # pragma: no cover - Streamlit defensive branch
        return None, None, f"Unable to read {uploaded.name}: {exc}", "warning"

    if not payload_bytes:
        return None, None, f"{uploaded.name} is empty; skipping upload.", "warning"

    checksum = hashlib.sha256(payload_bytes).hexdigest()
    return checksum, payload_bytes, None, "info"


def _render_local_upload() -> None:
    st.markdown("### Upload recorded spectra")
    supported = sorted(SUPPORTED_LOCAL_UPLOAD_EXTENSIONS)
    accepted_types = sorted(
        {ext.lstrip(".") for ext in supported if ext.startswith(".")}
    )
    uploader = st.file_uploader(
        "Select spectral files",
        type=accepted_types,
        accept_multiple_files=True,
        key="local_upload_widget",
        help="Supports ASCII tables (CSV/TXT/TSV/ASCII), JCAMP-DX spectra, FITS spectral products, and gzip-compressed variants.",
    )
    st.caption("Supported extensions: " + ", ".join(sorted(supported)))
    if st.button("Reset uploaded file tracker", key="reset_upload_registry"):
        st.session_state["local_upload_registry"] = {}
        st.success("Cleared upload tracker.")

    if not uploader:
        return

    registry = _get_upload_registry()

    for uploaded in uploader:
        try:
            payload_bytes = uploaded.getvalue()
        except Exception as exc:  # pragma: no cover - Streamlit defensive branch
            st.warning(f"Unable to read {uploaded.name}: {exc}")
            continue

        if not payload_bytes:
            st.warning(f"{uploaded.name} is empty; skipping upload.")
            continue

        checksum = hashlib.sha256(payload_bytes).hexdigest()

        checksum, payload_bytes, error_message, level = _read_uploaded_file(uploaded)
        if error_message:
            (st.error if level == "error" else st.warning)(error_message)
            if checksum:
                registry[checksum] = {
                    "name": uploaded.name,
                    "added": False,
                    "message": error_message,
                }
            continue

        if not checksum or payload_bytes is None:
            continue

        if checksum in registry:
            continue

        try:
            payload = ingest_local_file(uploaded.name, payload_bytes)
        except LocalIngestError as exc:
            st.warning(str(exc))
            registry[checksum] = {
                "name": uploaded.name,
                "added": False,
                "message": str(exc),
            }
            continue
        except Exception as exc:  # pragma: no cover - unexpected failure
            st.error(f"Unexpected error ingesting {uploaded.name}: {exc}")
            registry[checksum] = {
                "name": uploaded.name,
                "added": False,
                "message": str(exc),
            }

            message = str(exc)
            st.warning(message)
            registry[checksum] = {
                "name": uploaded.name,
                "added": False,
                "message": message,
            }
            continue
        except Exception as exc:  # pragma: no cover - unexpected failure
            message = f"Unexpected error ingesting {uploaded.name}: {exc}"
            st.error(message)
            registry[checksum] = {
                "name": uploaded.name,
                "added": False,
                "message": message,
            }
            continue

        added, message = _add_overlay_payload(payload)
        registry[checksum] = {"name": uploaded.name, "added": added, "message": message}
        (st.success if added else st.info)(message)


def _clear_overlays() -> None:
    st.session_state["overlay_traces"] = []
    st.session_state["reference_trace_id"] = None
    cache: SimilarityCache = st.session_state["similarity_cache"]
    cache.reset()
    st.session_state["local_upload_registry"] = {}
    st.session_state["differential_result"] = None


def _export_current_view(
    fig: go.Figure,
    overlays: Sequence[OverlayTrace],
    display_units: str,
    display_mode: str,
    viewport: Mapping[str, Tuple[float | None, float | None]],
) -> None:
    rows: List[Dict[str, object]] = []
    series_details: Dict[str, Dict[str, object]] = {}
    for trace in overlays:
        if not trace.visible:
            continue
        axis_kind = _axis_kind_for_trace(trace)
        axis_view = viewport.get(axis_kind, (None, None))
        df = _filter_viewport(trace.to_dataframe(), axis_view)
        if df.empty:
            continue
        converted, axis_title = _convert_axis_series(
            df["wavelength_nm"], trace, display_units
        )
        scaled = df["flux"].to_numpy(dtype=float)
        if display_mode != "Flux (raw)":
            scaled = apply_normalization(scaled, "max")
        for wavelength_value, flux_value in zip(converted, scaled):
            if not math.isfinite(float(wavelength_value)) or not math.isfinite(
                float(flux_value)
            ):
                continue
            if axis_kind == "wavelength":
                unit_label = display_units
            elif axis_title and "(" in axis_title and axis_title.rstrip().endswith(")"):
                unit_label = axis_title.rsplit("(", 1)[1].rstrip(") ")
            else:
                unit_label = axis_title or axis_kind
            rows.append(
                {
                    "series": trace.label,
                    "wavelength": float(wavelength_value),
                    "axis_kind": axis_kind,
                    "unit": unit_label,
                    "flux": float(flux_value),
                    "display_mode": display_mode,
                }
            )
        metadata = trace.metadata if isinstance(trace.metadata, Mapping) else {}
        provenance = trace.provenance if isinstance(trace.provenance, Mapping) else {}
        detail_payload: Dict[str, object] = {}
        if metadata.get("ir_sanity"):
            detail_payload["ir_sanity"] = metadata.get("ir_sanity")
        conversion = provenance.get("ir_conversion") if isinstance(provenance, Mapping) else None
        if conversion:
            detail_payload["ir_conversion"] = conversion
        if detail_payload:
            series_details.setdefault(trace.label, {}).update(detail_payload)
    if not rows:
        st.warning("Nothing to export in the current viewport.")
        return
    df_export = pd.DataFrame(rows)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    csv_path = EXPORT_DIR / f"spectra_export_{timestamp}.csv"
    png_path = EXPORT_DIR / f"spectra_export_{timestamp}.png"
    manifest_path = EXPORT_DIR / f"spectra_export_{timestamp}.manifest.json"
    df_export.to_csv(csv_path, index=False)
    try:
        fig.write_image(str(png_path))
    except Exception as exc:
        st.warning(f"PNG export requires kaleido ({exc}).")
    viewport_payload = {
        kind: {"low": vp[0], "high": vp[1]}
        for kind, vp in viewport.items()
    }
    manifest = build_manifest(
        rows,
        display_units=display_units,
        display_mode=display_mode,
        exported_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        viewport=viewport_payload,
        series_details=series_details,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    st.success(f"Exported: {csv_path.name}, {png_path.name}, {manifest_path.name}")


# ---------------------------------------------------------------------------
# Line metadata helpers


def _collect_line_overlays(overlays: Sequence[OverlayTrace]) -> List[OverlayTrace]:
    return [
        trace
        for trace in overlays
        if trace.kind == "lines" and trace.metadata.get("lines")
    ]


def _build_line_table(trace: OverlayTrace) -> pd.DataFrame:
    records: List[Dict[str, object]] = []
    for line in trace.metadata.get("lines", []) or []:
        records.append(
            {
                "Wavelength (nm)": line.get("wavelength_nm"),
                "Observed (nm)": line.get("observed_wavelength_nm"),
                "Ritz (nm)": line.get("ritz_wavelength_nm"),
                "Relative intensity": line.get("relative_intensity"),
                "Normalised": line.get("relative_intensity_normalized"),
                "Lower": line.get("lower_level"),
                "Upper": line.get("upper_level"),
                "Transition": line.get("transition_type"),
            }
        )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame.from_records(records)


def _render_line_tables(overlays: Sequence[OverlayTrace]) -> None:
    line_overlays = _collect_line_overlays(overlays)
    if not line_overlays:
        return
    with st.expander("Line metadata tables"):
        for trace in line_overlays:
            st.markdown(f"**{trace.label}**")
            table = _build_line_table(trace)
            if table.empty:
                st.info("No line metadata available.")
            else:
                st.dataframe(table, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Patch log helpers


def _resolve_patch_metadata(version_info: Mapping[str, object]) -> Tuple[str, str, str]:
    """Derive patch version and summary strings for UI presentation."""

    def _text(value: object) -> str:
        return str(value).strip() if value is not None else ""

    patch_version = _text(version_info.get("patch_version"))
    version_fallback = _text(version_info.get("version")) or "v?"
    if not patch_version:
        patch_version = version_fallback

    patch_summary = _text(version_info.get("patch_summary"))
    if not patch_summary:
        patch_summary = _text(version_info.get("summary"))
    if not patch_summary:
        patch_summary = "No summary recorded."

    patch_line = _text(version_info.get("patch_raw"))
    if patch_line:
        display_line = patch_line
    elif patch_version:
        display_line = (
            f"{patch_version}: {patch_summary}" if patch_summary else patch_version
        )
    else:
        display_line = patch_summary

    return patch_version, patch_summary, display_line


def _format_line_hover(line: Dict[str, object]) -> str:
    parts: List[str] = []
    wavelength = line.get("wavelength_nm")
    if isinstance(wavelength, (int, float)) and math.isfinite(wavelength):
        parts.append(f"λ {wavelength:.4f} nm")
    ritz = line.get("ritz_wavelength_nm")
    observed = line.get("observed_wavelength_nm")
    if isinstance(ritz, (int, float)) and math.isfinite(ritz):
        parts.append(f"Ritz {ritz:.4f} nm")
    if isinstance(observed, (int, float)) and math.isfinite(observed):
        parts.append(f"Observed {observed:.4f} nm")
    rel = line.get("relative_intensity")
    if rel is not None:
        parts.append(f"Rel {rel}")
    norm = line.get("relative_intensity_normalized")
    if norm is not None:
        parts.append(f"Norm {norm:.3f}")
    lower = line.get("lower_level")
    upper = line.get("upper_level")
    if lower or upper:
        parts.append(f"{lower or '?'} → {upper or '?'}")
    return " | ".join(parts)


def _convert_nist_payload(data: Dict[str, object]) -> Optional[Dict[str, object]]:
    lines = data.get("lines") or []
    if not lines:
        return None
    meta = data.get("meta") or {}
    wavelengths: List[float] = []
    flux: List[float] = []
    hover: List[str] = []
    for line in lines:
        wavelength = line.get("wavelength_nm")
        if wavelength is None:
            continue
        wavelengths.append(float(wavelength))
        intensity = line.get("relative_intensity_normalized")
        if intensity is None:
            intensity = line.get("relative_intensity")
        if intensity is None:
            intensity = 1.0
        flux.append(float(intensity))
        hover.append(_format_line_hover(line))
    if not wavelengths:
        return None
    provenance = dict(meta)
    provenance["archive"] = "NIST"
    payload = {
        "label": meta.get("label") or "NIST ASD",
        "wavelength_nm": wavelengths,
        "flux": flux,
        "provider": "NIST",
        "summary": f"{len(wavelengths)} NIST ASD lines",
        "kind": "lines",
        "metadata": {
            "lines": lines,
            "query": meta.get("query"),
        },
        "provenance": provenance,
        "hover": hover,
    }
    return payload


# ---------------------------------------------------------------------------
# Status bar


def _render_status_bar(version_info: Mapping[str, object]) -> None:
    overlays = _get_overlays()
    target_overlays = [trace for trace in overlays if trace.visible] or overlays
    axis_groups = _group_overlays_by_axis_kind(target_overlays)
    primary_axis = _determine_primary_axis_kind(target_overlays)
    selected_group = axis_groups.get(primary_axis) or target_overlays
    stored_viewport = _get_viewport_for_kind(primary_axis)
    effective_viewport = _effective_viewport(
        selected_group, stored_viewport, axis_kind=primary_axis
    )
    low, high = effective_viewport
    auto_enabled = bool(st.session_state.get("auto_viewport", True))
    auto_active = (
        auto_enabled
        and stored_viewport[0] is None
        and stored_viewport[1] is None
        and low is not None
        and high is not None
    )
    display_units = st.session_state.get("display_units", "nm")
    axis_title = _axis_title_for_kind(primary_axis, selected_group, display_units)
    unit_suffix: Optional[str] = None
    if axis_title and "(" in axis_title and axis_title.rstrip().endswith(")"):
        unit_suffix = axis_title.rsplit("(", 1)[1].rstrip(") ")
    elif axis_title:
        unit_suffix = axis_title
    if not unit_suffix:
        unit_suffix = "nm" if primary_axis == "wavelength" else primary_axis.replace("_", " ")
    unit_suffix = unit_suffix.strip()
    low_str = f"{low:.1f} {unit_suffix}" if low is not None else "auto"
    high_str = f"{high:.1f} {unit_suffix}" if high is not None else "auto"
    viewport_str = f"{low_str} – {high_str}"
    if auto_active:
        viewport_str += " (auto)"
    policy_map = {
        "allow": "duplicates allowed",
        "skip": "session dedupe",
        "ledger": "ledger enforced",
    }
    policy = policy_map.get(
        st.session_state.get("duplicate_policy"), "duplicates allowed"
    )
    reference = (
        _trace_label(st.session_state.get("reference_trace_id")) if overlays else "—"
    )
    st.markdown(
        (
            "<div style='margin-top:1rem;padding:0.6rem 0.8rem;border-top:1px solid #333;font-size:0.85rem;opacity:0.85;'>"
            f"<strong>{len(overlays)}</strong> overlays • viewport {viewport_str} • reference: {reference} • {policy}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main tab renderers


def _render_reference_controls(overlays: Sequence[OverlayTrace]) -> None:
    st.subheader("Reference & overlays")
    if not overlays:
        st.caption("Load an example or fetch from an archive to begin.")
        return

    options = [trace.trace_id for trace in overlays]
    current = st.session_state.get("reference_trace_id")
    default_index = 0
    if current in options:
        default_index = options.index(current)
    elif options:
        st.session_state["reference_trace_id"] = options[0]

    selection = st.selectbox(
        "Reference trace",
        options,
        index=default_index,
        format_func=_trace_label,
        key="reference_trace_select",
    )
    st.session_state["reference_trace_id"] = selection


def _render_overlay_tab(version_info: Dict[str, str]) -> None:
    st.header("Overlay workspace")
    _render_local_upload()
    cleared_message = st.session_state.pop("overlay_clear_message", None)
    if cleared_message:
        st.warning(str(cleared_message))
    overlays = _get_overlays()
    if not overlays:
        st.info("Upload a recorded spectrum or fetch from the archive tab to begin.")
        return
    st.divider()

    _render_ir_warnings(overlays)
    _render_ir_parameter_prompts(overlays)

    display_units = st.session_state.get("display_units", "nm")
    display_mode = st.session_state.get("display_mode", "Flux (raw)")
    differential_mode = st.session_state.get("differential_mode", "Off")
    target_overlays = [trace for trace in overlays if trace.visible] or overlays
    axis_groups = _group_overlays_by_axis_kind(target_overlays)
    plottable_groups = {
        kind: group
        for kind, group in axis_groups.items()
        if kind not in {"image", "time"}
    }
    viewport_store = _get_viewport_store()
    auto_enabled = bool(st.session_state.get("auto_viewport", True))
    effective_viewports: Dict[str, Tuple[float | None, float | None]] = {}
    filter_viewports: Dict[str, Tuple[float | None, float | None]] = {}
    for kind, group in plottable_groups.items():
        stored = viewport_store.get(kind, (None, None))
        effective = _effective_viewport(group, stored, axis_kind=kind)
        effective_viewports[kind] = effective
        if auto_enabled and stored[0] is None and stored[1] is None:
            filter_viewports[kind] = (None, None)
        else:
            filter_viewports[kind] = effective
    visible_axis_kinds = [kind for kind, traces in plottable_groups.items() if traces]
    single_axis = len(visible_axis_kinds) == 1

    reference = next(
        (
            trace
            for trace in overlays
            if trace.trace_id == st.session_state.get("reference_trace_id")
        ),
        None,
    )
    if reference is None or _axis_kind_for_trace(reference) in {"image", "time"}:
        reference = next(
            (
                trace
                for trace in overlays
                if _axis_kind_for_trace(trace) not in {"image", "time"}
            ),
            overlays[0] if overlays else None,
        )
    if reference is not None and _axis_kind_for_trace(reference) in {"image", "time"}:
        reference = None

    fig, axis_title = _build_overlay_figure(
        overlays,
        display_units,
        display_mode,
        filter_viewports,
        reference,
        differential_mode,
        version_info.get("version", "v?"),
        axis_viewport_by_kind=effective_viewports if single_axis else None,
    )
    st.plotly_chart(fig, use_container_width=True)
    _render_image_overlay_panels(overlays)

    if len(visible_axis_kinds) > 1:
        friendly = " + ".join(kind.replace("_", " ") for kind in sorted(visible_axis_kinds))
        st.warning(
            f"Mixed axis kinds visible ({friendly}). Viewport limits apply per axis and the plot auto-scales the combined view."
        )

    control_col, action_col = st.columns([3, 1])
    with control_col:
        _render_overlay_table(overlays)
    with action_col:
        if st.button("Export view", key="export_view"):
            _export_current_view(
                fig,
                overlays,
                display_units,
                display_mode,
                effective_viewports,
            )
        st.caption(f"Axis: {axis_title}")

    _render_metadata_summary(overlays)
    _render_ir_sanity_panel(overlays)
    _render_line_tables(overlays)


def _normalization_display(mode: str) -> str:
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


def _compute_differential_result(
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


def _build_differential_figure(result: DifferentialResult) -> go.Figure:
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
            name=f"Result ({result.operation_label})",
            mode="lines",
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        height=520,
        margin=dict(t=30, b=36, l=32, r=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    fig.update_xaxes(title_text="Wavelength (nm)", row=2, col=1)
    fig.update_yaxes(
        title_text=f"Flux ({_normalization_display(result.normalization)})",
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text=result.operation_label, row=2, col=1)
    return fig


def _build_differential_summary(result: DifferentialResult) -> pd.DataFrame:
    grid = np.asarray(result.grid_nm, dtype=float)
    if grid.size:
        range_text = f"{grid.min():.2f} – {grid.max():.2f}"
    else:
        range_text = "—"

    def _series_stats(label: str, values: Sequence[float]) -> Dict[str, object]:
        arr = np.asarray(values, dtype=float)
        finite = arr[np.isfinite(arr)]
        if finite.size:
            min_val = float(finite.min())
            max_val = float(finite.max())
            mean_val = float(finite.mean())
            std_val = float(finite.std())
        else:
            min_val = max_val = mean_val = std_val = float("nan")
        return {
            "Series": label,
            "Min": min_val,
            "Max": max_val,
            "Mean": mean_val,
            "Std": std_val,
            "Samples": int(arr.size),
            "Range (nm)": range_text,
        }

    rows = [
        _series_stats(f"A • {result.trace_a_label}", result.values_a),
        _series_stats(f"B • {result.trace_b_label}", result.values_b),
        _series_stats(f"Result ({result.operation_label})", result.result),
    ]
    return pd.DataFrame(rows)


def _add_differential_overlay(result: DifferentialResult) -> Tuple[bool, str]:
    timestamp = (
        datetime.fromtimestamp(result.computed_at, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    metadata = {
        "source": "differential",
        "operation": result.operation_code,
        "operation_label": result.operation_label,
        "trace_a": {"id": result.trace_a_id, "label": result.trace_a_label},
        "trace_b": {"id": result.trace_b_id, "label": result.trace_b_label},
        "sample_points": result.sample_points,
        "normalization": result.normalization,
        "computed_at": timestamp,
    }
    if result.grid_nm:
        metadata["wavelength_range_nm"] = [
            float(min(result.grid_nm)),
            float(max(result.grid_nm)),
        ]
    summary = f"{result.operation_label} on {result.sample_points} samples"
    return _add_overlay(
        result.label,
        result.grid_nm,
        result.result,
        provider="DIFF",
        summary=summary,
        metadata=metadata,
        provenance=dict(metadata),
        flux_kind="derived",
    )


def _render_differential_result(result: Optional[DifferentialResult]) -> None:
    if result is None:
        return
    fig = _build_differential_figure(result)
    st.plotly_chart(fig, use_container_width=True)
    grid = np.asarray(result.grid_nm, dtype=float)
    if grid.size:
        st.caption(
            f"Overlap {grid.min():.2f} – {grid.max():.2f} nm • "
            f"{result.sample_points} samples • Normalization: {_normalization_display(result.normalization)}"
        )
    summary = _build_differential_summary(result)
    st.dataframe(summary, hide_index=True, width="stretch")
    if st.button("Add result to overlays", key="add_differential_overlay"):
        added, message = _add_differential_overlay(result)
        (st.success if added else st.info)(message)


def _render_differential_tab() -> None:
    st.header("Differential analysis")
    overlays = _get_overlays()
    _render_reference_controls(overlays)
    spectral_overlays = [
        trace
        for trace in overlays
        if trace.kind != "lines" and _axis_kind_for_trace(trace) not in {"image", "time"}
    ]
    if len(spectral_overlays) < 2:
        st.info("Add at least two spectra to compare differentially.")
        return

    norm_map = {
        "Unit vector (L2)": "unit",
        "Peak normalised": "max",
        "Z-score": "zscore",
        "None": "none",
    }
    norm_labels = list(norm_map.keys())
    current_norm = st.session_state.get("normalization_mode", "unit")
    try:
        norm_index = norm_labels.index(
            next(label for label, code in norm_map.items() if code == current_norm)
        )
    except StopIteration:
        norm_index = 0

    diff_options = ["Off", "Relative to reference"]
    diff_mode = st.session_state.get("differential_mode", "Off")
    diff_index = diff_options.index(diff_mode) if diff_mode in diff_options else 0

    norm_col, diff_col = st.columns(2)
    norm_selection = norm_col.selectbox(
        "Normalization",
        norm_labels,
        index=norm_index,
    )
    st.session_state["normalization_mode"] = norm_map[norm_selection]
    diff_selection = diff_col.selectbox(
        "Differential mode",
        diff_options,
        index=diff_index,
    )
    st.session_state["differential_mode"] = diff_selection
    if diff_selection != "Off":
        diff_col.caption("Traces are regridded onto the reference before subtracting.")

    with st.expander("Similarity settings", expanded=False):
        metric_options = ["cosine", "rmse", "xcorr", "line_match"]
        current_metrics = st.session_state.get("similarity_metrics", metric_options)
        metrics = st.multiselect(
            "Metrics",
            options=metric_options,
            default=current_metrics if current_metrics else metric_options[:1],
            format_func=lambda m: m.replace("_", " ").title(),
        )
        if not metrics:
            metrics = metric_options[:1]
        st.session_state["similarity_metrics"] = metrics

        primary_metric = st.session_state.get("similarity_primary_metric", metrics[0])
        if primary_metric not in metrics:
            primary_metric = metrics[0]
        st.session_state["similarity_primary_metric"] = st.selectbox(
            "Primary metric",
            metrics,
            index=metrics.index(primary_metric),
            format_func=lambda m: m.replace("_", " ").title(),
        )

        line_peaks = st.slider(
            "Line peak count",
            min_value=3,
            max_value=20,
            value=int(st.session_state.get("similarity_line_peaks", 8)),
            help="Number of strongest samples considered for the line-match metric.",
        )
        st.session_state["similarity_line_peaks"] = int(line_peaks)

        similarity_norm_labels = ["Unit vector (L2)", "Peak normalised", "Z-score", "None"]
        similarity_norm_codes = {
            "Unit vector (L2)": "unit",
            "Peak normalised": "max",
            "Z-score": "zscore",
            "None": "none",
        }
        similarity_current_code = st.session_state.get(
            "similarity_normalization",
            st.session_state.get("normalization_mode", "unit"),
        )
        similarity_current_label = next(
            (
                label
                for label, code in similarity_norm_codes.items()
                if code == similarity_current_code
            ),
            similarity_norm_labels[0],
        )
        similarity_selection = st.selectbox(
            "Similarity normalization",
            similarity_norm_labels,
            index=similarity_norm_labels.index(similarity_current_label),
        )
        st.session_state["similarity_normalization"] = similarity_norm_codes[
            similarity_selection
        ]

    st.divider()

    trace_map = {trace.trace_id: trace for trace in spectral_overlays}
    options = list(trace_map.keys())
    default_a = st.session_state.get("differential_trace_a_id")
    if default_a not in options:
        reference = st.session_state.get("reference_trace_id")
        default_a = reference if reference in options else options[0]
    default_b = st.session_state.get("differential_trace_b_id")
    if default_b not in options or default_b == default_a:
        default_b = next((tid for tid in options if tid != default_a), options[0])

    operation_labels = list(DIFFERENTIAL_OPERATIONS.keys())
    default_operation = st.session_state.get("differential_operation_label")
    if default_operation not in operation_labels:
        default_operation = operation_labels[0]

    sample_default = int(st.session_state.get("differential_sample_points", 2000))
    normalization = st.session_state.get("normalization_mode", "unit")
    viewport_store = _get_viewport_store()
    similarity_sources = [
        trace
        for trace in spectral_overlays
        if trace.visible and _axis_kind_for_trace(trace) not in {"image", "time"}
    ]
    if len(similarity_sources) < 2:
        similarity_sources = [
            trace
            for trace in spectral_overlays
            if _axis_kind_for_trace(trace) not in {"image", "time"}
        ]
    wavelength_sources = [
        trace for trace in similarity_sources if _axis_kind_for_trace(trace) == "wavelength"
    ]
    stored_wavelength_view = viewport_store.get("wavelength", (None, None))
    if wavelength_sources:
        effective_viewport = _effective_viewport(
            wavelength_sources,
            stored_wavelength_view,
            axis_kind="wavelength",
        )
    else:
        effective_viewport = (None, None)

    with st.form(key="differential_compute_form"):
        col_a, col_b = st.columns(2)
        trace_a_id = col_a.selectbox(
            "Trace A",
            options,
            index=options.index(default_a),
            format_func=_trace_label,
        )
        trace_b_id = col_b.selectbox(
            "Trace B",
            options,
            index=options.index(default_b),
            format_func=_trace_label,
        )
        col_op, col_samples = st.columns(2)
        operation_label = col_op.selectbox(
            "Operation",
            operation_labels,
            index=operation_labels.index(default_operation),
        )
        sample_points = col_samples.slider(
            "Resample points",
            min_value=300,
            max_value=8000,
            step=100,
            value=sample_default,
        )
        submitted = st.form_submit_button(
            "Compute differential",
            key="differential_compute_submit",
            use_container_width=True,
        )


    result = st.session_state.get("differential_result")
    if submitted:
        if trace_a_id == trace_b_id:
            st.warning("Select two distinct traces to compute a differential.")
        else:
            try:
                result = _compute_differential_result(
                    trace_map[trace_a_id],
                    trace_map[trace_b_id],
                    operation_label,
                    int(sample_points),
                    normalization,
                )
            except ValueError as exc:
                st.error(str(exc))
                result = None
            else:
                st.session_state["differential_result"] = result
                st.session_state["differential_trace_a_id"] = trace_a_id
                st.session_state["differential_trace_b_id"] = trace_b_id
                st.session_state["differential_operation_label"] = operation_label
                st.session_state["differential_sample_points"] = int(sample_points)

    st.caption(
        "Differential maths uses the normalization chosen above and resamples "
        "both traces onto a shared wavelength grid."
    )
    if "similarity_cache" not in st.session_state:
        st.session_state["similarity_cache"] = SimilarityCache()
    cache: SimilarityCache = st.session_state["similarity_cache"]
    full_resolution = _is_full_resolution_enabled()
    vector_max_points = None if full_resolution else 15000
    viewport_map = {"wavelength": effective_viewport} if wavelength_sources else {}
    visible_vectors = [
        trace.to_vectors(
            max_points=vector_max_points,
            viewport=viewport_map.get(_axis_kind_for_trace(trace), (None, None)),
        )
        for trace in similarity_sources
    ]
    if len(visible_vectors) >= 2:
        options = SimilarityOptions(
            metrics=tuple(st.session_state.get("similarity_metrics", ["cosine"])),
            normalization=st.session_state.get(
                "similarity_normalization", normalization
            ),
            line_match_top_n=int(st.session_state.get("similarity_line_peaks", 8)),
            primary_metric=st.session_state.get("similarity_primary_metric", "cosine"),
            reference_id=st.session_state.get("reference_trace_id"),
        )
        render_similarity_panel(
            visible_vectors, effective_viewport, options, cache
        )
    _render_differential_result(result)


def _render_library_tab() -> None:
    st.header("Data library")
    st.caption(
        "Browse curated examples, target manifests, and upload policies "
        "from a single workspace panel."
    )

    st.info(
        "Use the **Examples library** panel in the sidebar to quick-load curated "
        "spectra or open the full browser without leaving your current tab."
    )

    st.divider()

    targets_container = st.container()
    try:
        render_targets_panel(expanded=True, sidebar=targets_container)
    except RegistryUnavailableError as exc:
        targets_container.info(str(exc))

    st.divider()

    uploads_container = st.container()
    _render_uploads_group(uploads_container)


def _render_docs_tab(version_info: Mapping[str, object]) -> None:
    st.header("Docs & provenance")
    _, patch_summary, patch_line = _resolve_patch_metadata(version_info)
    banner_text = patch_line or patch_summary or "No summary recorded."
    st.info(banner_text)
    if not DOC_LIBRARY:
        st.info("Documentation library is empty.")
        return

    category_titles = [category.title for category in DOC_LIBRARY]
    if "docs_category_select" not in st.session_state:
        st.session_state["docs_category_select"] = category_titles[0]
    selected_category_title = st.selectbox(
        "Guide category", category_titles, key="docs_category_select"
    )
    category = next(cat for cat in DOC_LIBRARY if cat.title == selected_category_title)
    if category.description:
        st.caption(category.description)

    entry_titles = [entry.title for entry in category.entries]
    if not entry_titles:
        st.warning("No documents available in this category yet.")
        entry = None
    else:
        if (
            "docs_entry_select" not in st.session_state
            or st.session_state["docs_entry_select"] not in entry_titles
        ):
            st.session_state["docs_entry_select"] = entry_titles[0]
        selected_entry_title = st.selectbox(
            "Document", entry_titles, key="docs_entry_select"
        )
        entry = next(e for e in category.entries if e.title == selected_entry_title)
        if entry.description:
            st.caption(entry.description)
    if entry:
        try:
            content = entry.path.read_text(encoding="utf-8")
        except Exception as exc:
            st.error(f"Failed to load {entry.path}: {exc}")
        else:
            st.markdown(content)
            st.download_button(
                "Download Markdown",
                content,
                file_name=entry.path.name,
                mime="text/markdown",
            )
            try:
                modified = datetime.fromtimestamp(
                    entry.path.stat().st_mtime, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M UTC")
            except OSError:
                modified = ""
            if modified:
                st.caption(f"Last updated {modified}")

    overlays = _get_overlays()
    if overlays:
        st.divider()
        st.subheader("Session provenance")
        for trace in overlays:
            with st.expander(trace.label):
                if trace.summary:
                    st.write(trace.summary)
                if trace.provenance:
                    st.json(trace.provenance)
                else:
                    st.caption("No provenance metadata recorded.")
    else:
        st.caption("Load overlays to view provenance manifests.")


# ---------------------------------------------------------------------------
# Panel registry integration
# ---------------------------------------------------------------------------


def _sidebar_settings_panel(
    container: DeltaGenerator, context: PanelContext
) -> None:  # pragma: no cover - Streamlit UI
    _render_settings_group(container)


def _sidebar_ingest_panel(
    container: DeltaGenerator, context: PanelContext
) -> None:  # pragma: no cover - Streamlit UI
    _render_ingest_queue_panel(container)


def _workspace_overlay_panel(context: PanelContext) -> None:  # pragma: no cover - Streamlit UI
    version_info = context.get("version_info", {})
    if isinstance(version_info, Mapping):
        resolved = dict(version_info)
    else:
        resolved = {}
    _render_overlay_tab(resolved)


def _workspace_differential_panel(
    context: PanelContext,
) -> None:  # pragma: no cover - Streamlit UI
    _render_differential_tab()


def _workspace_library_panel(
    context: PanelContext,
) -> None:  # pragma: no cover - Streamlit UI
    _render_library_tab()


def _workspace_docs_panel(context: PanelContext) -> None:  # pragma: no cover - Streamlit UI
    version_info = context.get("version_info", {})
    if isinstance(version_info, Mapping):
        resolved = dict(version_info)
    else:
        resolved = {}
    _render_docs_tab(resolved)


_registry = get_panel_registry()
if not any(panel.panel_id == "session_controls" for panel in _registry.iter_sidebar()):
    register_sidebar_panel(
        "session_controls",
        "Session controls",
        _sidebar_settings_panel,
        order=10,
    )
if not any(panel.panel_id == "ingest_queue" for panel in _registry.iter_sidebar()):
    register_sidebar_panel(
        "ingest_queue",
        "Overlay downloads",
        _sidebar_ingest_panel,
        order=20,
    )
if not any(panel.panel_id == "overlay" for panel in _registry.iter_workspace()):
    register_workspace_panel(
        "overlay",
        "Overlay",
        _workspace_overlay_panel,
        order=10,
    )
if not any(panel.panel_id == "differential" for panel in _registry.iter_workspace()):
    register_workspace_panel(
        "differential",
        "Differential",
        _workspace_differential_panel,
        order=20,
    )
if not any(panel.panel_id == "library" for panel in _registry.iter_workspace()):
    register_workspace_panel(
        "library",
        "Library",
        _workspace_library_panel,
        order=30,
    )
if not any(panel.panel_id == "docs" for panel in _registry.iter_workspace()):
    register_workspace_panel(
        "docs",
        "Docs & Provenance",
        _workspace_docs_panel,
        order=40,
    )


# ---------------------------------------------------------------------------
# Entry points


def _render_app_header(version_info: Mapping[str, object]) -> None:
    st.title("Spectra App")
    patch_version, patch_summary, _ = _resolve_patch_metadata(version_info)
    build_version = patch_version or str(version_info.get("version") or "v?")
    timestamp = _format_version_timestamp(version_info.get("date_utc"))
    caption_parts = [build_version]
    if timestamp:
        caption_parts.append(f"Updated {timestamp}")
    if patch_summary:
        caption_parts.append(str(patch_summary))
    st.caption(" • ".join(part for part in caption_parts if part))


def render() -> None:
    _ensure_session_state()
    _process_ingest_queue()
    version_info = get_version_info()

    _render_app_header(version_info)

    context: Dict[str, object] = {"version_info": version_info}
    panel_context: PanelContext = context
    registry = get_panel_registry()

    sidebar = st.sidebar
    for panel in registry.iter_sidebar():
        container = sidebar.container()
        panel.render(container, panel_context)

    workspace_panels = list(registry.iter_workspace())
    if workspace_panels:
        tabs = st.tabs([panel.label for panel in workspace_panels])
        for spec, tab in zip(workspace_panels, tabs):
            with tab:
                spec.render(panel_context)
    else:
        st.info("No workspace panels registered.")

    _render_status_bar(version_info)


def main() -> None:
    render()


if __name__ == "__main__":
    main()
