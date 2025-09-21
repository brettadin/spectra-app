from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app._version import get_version_info
from app.archive_ui import ArchiveUI
from app.export_manifest import build_manifest
from app.server.fetch_archives import FetchError, fetch_spectrum
from app.similarity import (
    SimilarityCache,
    SimilarityOptions,
    TraceVectors,
    apply_normalization,
    viewport_alignment,
)
from app.similarity_panel import render_similarity_panel
from app.utils.duplicate_ledger import DuplicateLedger

st.set_page_config(page_title="Spectra App", layout="wide")

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class OverlayTrace:
    trace_id: str
    label: str
HEAD
wavelength_m: Tuple[float, ...]
codex/improve-unit-conversions-and-file-uploads-ussv5s
 flux: Tuple[float, ...]
=======
 main
    flux_unit: str
    flux_kind: str
=======
    wavelength_nm: Tuple[float, ...]
    flux: Tuple[float, ...]
   parent of 9fe7c940 (v1.1.5d: fix export imports and surface atlas docs)
    kind: str = "spectrum"
    provider: Optional[str] = None
    summary: Optional[str] = None
    visible: bool = True
    metadata: Dict[str, object] = field(default_factory=dict)
    provenance: Dict[str, object] = field(default_factory=dict)
    fingerprint: str = ""
    hover: Optional[Tuple[str, ...]] = None

    def to_dataframe(self) -> pd.DataFrame:
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

    def to_vectors(self) -> TraceVectors:
        df = self.to_dataframe()
        return TraceVectors(
            trace_id=self.trace_id,
            label=self.label,
            wavelengths_nm=df["wavelength_nm"].to_numpy(dtype=float),
            flux=df["flux"].to_numpy(dtype=float),
            kind=self.kind,
            fingerprint=self.fingerprint,
        )

    @property
    def points(self) -> int:
        return len(self.wavelength_nm)


# ---------------------------------------------------------------------------
# Session state helpers

def _ensure_session_state() -> None:
    st.session_state.setdefault("session_id", str(uuid.uuid4()))
    st.session_state.setdefault("overlay_traces", [])
    st.session_state.setdefault("display_units", "nm")
    st.session_state.setdefault("display_mode", "Flux (raw)")
    st.session_state.setdefault("viewport_nm", (None, None))
    st.session_state.setdefault("auto_viewport", True)
    st.session_state.setdefault("normalization_mode", "unit")
    st.session_state.setdefault("differential_mode", "Off")
    st.session_state.setdefault("reference_trace_id", None)
    st.session_state.setdefault("similarity_metrics", ["cosine", "rmse", "xcorr", "line_match"])
    st.session_state.setdefault("similarity_primary_metric", "cosine")
    st.session_state.setdefault("similarity_line_peaks", 8)
    st.session_state.setdefault("similarity_normalization", st.session_state.get("normalization_mode", "unit"))
    st.session_state.setdefault("duplicate_policy", "allow")
    if "duplicate_ledger" not in st.session_state:
        st.session_state["duplicate_ledger"] = DuplicateLedger()
    if "similarity_cache" not in st.session_state:
        st.session_state["similarity_cache"] = SimilarityCache()


def _get_overlays() -> List[OverlayTrace]:
    return list(st.session_state.get("overlay_traces", []))


def _set_overlays(overlays: Sequence[OverlayTrace]) -> None:
    st.session_state["overlay_traces"] = list(overlays)
    _ensure_reference_consistency()


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
    payload = {
        "wavelength_nm": [round(float(w), 6) for w in wavelengths],
        "flux": [round(float(f), 6) for f in flux],
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()


def _add_overlay(
    label: str,
    wavelengths: Sequence[float],
    flux: Sequence[float],
    *,
    kind: str = "spectrum",
    provider: Optional[str] = None,
    summary: Optional[str] = None,
    metadata: Optional[Dict[str, object]] = None,
    provenance: Optional[Dict[str, object]] = None,
    hover: Optional[Sequence[str]] = None,
) -> Tuple[bool, str]:
    try:
        values_w = [float(v) for v in wavelengths]
        values_f = [float(v) for v in flux]
    except (TypeError, ValueError):
        return False, "Unable to coerce spectral data to floats."
    if not values_w or not values_f or len(values_w) != len(values_f):
        return False, "No spectral samples available."

    overlays = _get_overlays()
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
        hover=tuple(str(text) for text in (hover or [])) if hover else None,
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

    if not st.session_state.get("reference_trace_id"):
        st.session_state["reference_trace_id"] = trace.trace_id

    message = f"Added {label}"
    if provider:
        message += f" ({provider})"
    return True, message


def _add_overlay_payload(payload: Dict[str, object]) -> Tuple[bool, str]:
    return _add_overlay(
        str(payload.get("label") or "Trace"),
        payload.get("wavelength_nm") or [],
        payload.get("flux") or [],
        kind=str(payload.get("kind") or "spectrum"),
        provider=payload.get("provider"),
        summary=payload.get("summary"),
        metadata=payload.get("metadata"),
        provenance=payload.get("provenance"),
        hover=payload.get("hover"),
    )


def _add_example_trace(example: str, label: str) -> Tuple[bool, str]:
    csv_path = Path("app/examples") / f"{example}.csv"
    if not csv_path.exists():
        return False, f"Missing example data: {example}."
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        return False, f"Failed to load example {example}: {exc}"
    if "wavelength_nm" not in df or "intensity" not in df:
        return False, f"Example {example} missing required columns."
    metadata = {"source": "example", "path": str(csv_path)}
    provenance = {"source": "example", "file": str(csv_path)}
    return _add_overlay(
        label,
        df["wavelength_nm"].tolist(),
        df["intensity"].tolist(),
        provider="EXAMPLE",
        summary="Built-in example trace",
        metadata=metadata,
        provenance=provenance,
    )

# ---------------------------------------------------------------------------
# Sidebar rendering

def _render_reference_section() -> None:
    st.sidebar.markdown("### Reference spectra")
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Add He"):
        added, message = _add_example_trace("He", "He (example)")
        (st.sidebar.success if added else st.sidebar.info)(message)
    if col2.button("Add Ne"):
        added, message = _add_example_trace("Ne", "Ne (example)")
        (st.sidebar.success if added else st.sidebar.info)(message)
    _render_nist_form()

    overlays = _get_overlays()
    if overlays:
        options = [trace.trace_id for trace in overlays]
        current = st.session_state.get("reference_trace_id")
        try:
            index = options.index(current) if current in options else 0
        except ValueError:
            index = 0
        st.session_state["reference_trace_id"] = st.sidebar.selectbox(
            "Reference trace",
            options,
            index=index,
            format_func=_trace_label,
        )
        if st.sidebar.button("Clear overlays"):
            _clear_overlays()
            st.sidebar.warning("Cleared all overlays.")
    else:
        st.sidebar.caption("Load an example or fetch from an archive to begin.")


def _render_nist_form() -> None:
    st.sidebar.markdown("#### NIST ASD lines")
    with st.sidebar.form("nist_overlay_form", clear_on_submit=False):
        identifier = st.text_input("Element or spectrum", placeholder="e.g. Fe II")
        lower = st.number_input("Lower λ (nm)", min_value=0.0, value=380.0, step=5.0)
        upper = st.number_input("Upper λ (nm)", min_value=0.0, value=750.0, step=5.0)
        use_ritz = st.checkbox("Prefer Ritz wavelengths", value=True)
        submitted = st.form_submit_button("Fetch lines")
    if not submitted:
        return
    identifier = (identifier or "").strip()
    if not identifier:
        st.sidebar.warning("Enter an element identifier.")
        return
    if math.isclose(lower, upper):
        st.sidebar.warning("Lower and upper bounds must differ.")
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
        st.sidebar.error(f"NIST fetch failed: {exc}")
        return
    payload = _convert_nist_payload(result)
    if not payload:
        st.sidebar.warning("NIST returned no lines for that query.")
        return
    added, message = _add_overlay_payload(payload)
    (st.sidebar.success if added else st.sidebar.info)(message)


def _render_display_section() -> None:
    st.sidebar.markdown("### Display & viewport")
    units = st.sidebar.selectbox(
        "Wavelength units",
        ["nm", "Å", "µm", "cm^-1"],
        index=["nm", "Å", "µm", "cm^-1"].index(st.session_state.get("display_units", "nm")),
    )
    st.session_state["display_units"] = units
    display_mode_options = ["Flux (raw)", "Flux (normalized)"]
    current_mode = st.session_state.get("display_mode", "Flux (raw)")
    mode_index = display_mode_options.index(current_mode) if current_mode in display_mode_options else 0
    st.session_state["display_mode"] = st.sidebar.selectbox("Flux scaling", display_mode_options, index=mode_index)

    auto = st.sidebar.checkbox("Auto viewport", value=bool(st.session_state.get("auto_viewport", True)))
    st.session_state["auto_viewport"] = auto
    if auto:
        st.session_state["viewport_nm"] = (None, None)
        return

    min_bound, max_bound = _infer_viewport_bounds(_get_overlays())
    if math.isclose(min_bound, max_bound):
        max_bound = min_bound + 1.0
    low, high = st.session_state.get("viewport_nm", (min_bound, max_bound))
    if low is None or high is None:
        low, high = min_bound, max_bound
    low = max(min_bound, float(low))
    high = min(max_bound, float(high))
    selection = st.sidebar.slider(
        "Viewport (nm)",
        min_value=float(min_bound),
        max_value=float(max_bound),
        value=(low, high),
        step=1.0,
    )
    st.session_state["viewport_nm"] = (float(selection[0]), float(selection[1]))


def _render_differential_section() -> None:
    st.sidebar.markdown("### Differential & normalization")
    norm_map = {
        "Unit vector (L2)": "unit",
        "Peak normalised": "max",
        "Z-score": "zscore",
        "None": "none",
    }
    current_norm = st.session_state.get("normalization_mode", "unit")
    norm_labels = list(norm_map.keys())
    try:
        index = norm_labels.index(next(label for label, code in norm_map.items() if code == current_norm))
    except StopIteration:
        index = 0
    selection = st.sidebar.selectbox("Normalization", norm_labels, index=index)
    st.session_state["normalization_mode"] = norm_map[selection]

    diff_options = ["Off", "Relative to reference"]
    diff_mode = st.session_state.get("differential_mode", "Off")
    diff_index = diff_options.index(diff_mode) if diff_mode in diff_options else 0
    st.session_state["differential_mode"] = st.sidebar.selectbox("Differential mode", diff_options, index=diff_index)
    if st.session_state["differential_mode"] != "Off":
        st.sidebar.caption("Traces are regridded onto the reference before subtracting.")


def _render_similarity_sidebar() -> None:
    st.sidebar.markdown("### Similarity settings")
    metric_options = ["cosine", "rmse", "xcorr", "line_match"]
    current_metrics = st.session_state.get("similarity_metrics", metric_options)
    metrics = st.sidebar.multiselect(
        "Metrics",
        options=metric_options,
        default=current_metrics if current_metrics else metric_options[:1],
        format_func=lambda m: m.replace("_", " ").title(),
    )
    if not metrics:
        metrics = metric_options[:1]
    st.session_state["similarity_metrics"] = metrics

    primary = st.session_state.get("similarity_primary_metric", metrics[0])
    if primary not in metrics:
        primary = metrics[0]
    st.session_state["similarity_primary_metric"] = st.sidebar.selectbox(
        "Primary matrix",
        metrics,
        index=metrics.index(primary),
        format_func=lambda m: m.replace("_", " ").title(),
    )

    line_peaks = st.sidebar.slider(
        "Line peak count",
        min_value=3,
        max_value=20,
        value=int(st.session_state.get("similarity_line_peaks", 8)),
        help="Number of strongest samples considered for the line-match metric.",
    )
    st.session_state["similarity_line_peaks"] = int(line_peaks)

    norm_labels = ["Unit vector (L2)", "Peak normalised", "Z-score", "None"]
    norm_codes = {"Unit vector (L2)": "unit", "Peak normalised": "max", "Z-score": "zscore", "None": "none"}
    current_code = st.session_state.get("similarity_normalization", st.session_state.get("normalization_mode", "unit"))
    current_label = next((label for label, code in norm_codes.items() if code == current_code), norm_labels[0])
    selection = st.sidebar.selectbox("Similarity normalization", norm_labels, index=norm_labels.index(current_label))
    st.session_state["similarity_normalization"] = norm_codes[selection]


def _render_duplicate_sidebar() -> None:
    st.sidebar.markdown("### Duplicate handling")
    policies = [
        ("Allow duplicates", "allow"),
        ("Skip duplicates (session)", "skip"),
        ("Ledger lock (persistent)", "ledger"),
    ]
    codes = [code for _, code in policies]
    labels = [label for label, _ in policies]
    current = st.session_state.get("duplicate_policy", "allow")
    try:
        index = codes.index(current)
    except ValueError:
        index = 0
    choice = st.sidebar.radio("Policy", labels, index=index)
    st.session_state["duplicate_policy"] = dict(policies)[choice]

    if st.session_state["duplicate_policy"] == "ledger":
        if st.sidebar.button("Clear this session's ledger entries"):
            ledger: DuplicateLedger = st.session_state["duplicate_ledger"]
            ledger.purge_session(st.session_state.get("session_id"))
            st.sidebar.success("Session ledger entries cleared.")
    else:
        st.sidebar.caption("Ledger disabled for the current policy.")

# ---------------------------------------------------------------------------
# Overlay rendering helpers

def _infer_viewport_bounds(overlays: Sequence[OverlayTrace]) -> Tuple[float, float]:
    wavelengths: List[float] = []
    for trace in overlays:
        wavelengths.extend(trace.wavelength_nm)
    arr = np.array(wavelengths, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 350.0, 900.0
    return float(arr.min()), float(arr.max())


def _filter_viewport(df: pd.DataFrame, viewport: Tuple[float | None, float | None]) -> pd.DataFrame:
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


def _add_line_trace(fig: go.Figure, df: pd.DataFrame, label: str) -> None:
    xs: List[float | None] = []
    ys: List[float | None] = []
    hover: List[Optional[str]] = []
    for _, row in df.iterrows():
        x = row.get("wavelength")
        y = float(row.get("flux", 0.0))
        text = row.get("hover")
        xs.extend([x, x, None])
        ys.extend([0.0, y, None])
        hover.extend([text, text, None])
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            name=label,
            hovertext=hover if any(hover) else None,
            hoverinfo="text",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["wavelength"],
            y=df["flux"],
            mode="markers",
            marker=dict(size=6, symbol="line-ns"),
            name=f"{label} markers",
            hovertext=df.get("hover"),
            hoverinfo="text",
            showlegend=False,
        )
    )


def _build_overlay_figure(
    overlays: Sequence[OverlayTrace],
    display_units: str,
    display_mode: str,
    normalization_mode: str,
    viewport: Tuple[float | None, float | None],
    reference: Optional[OverlayTrace],
    differential_mode: str,
    version_tag: str,
) -> Tuple[go.Figure, str]:
    fig = go.Figure()
    axis_title = "Wavelength (nm)"
    reference_vectors = reference.to_vectors() if reference else None

    for trace in overlays:
        if not trace.visible:
            continue
        df = trace.to_dataframe()
        df = _filter_viewport(df, viewport)
        if df.empty:
            continue

        if (
            differential_mode == "Relative to reference"
            and reference_vectors is not None
            and trace.trace_id != reference_vectors.trace_id
            and trace.kind != "lines"
        ):
            axis, values_trace, values_ref = viewport_alignment(trace.to_vectors(), reference_vectors, viewport)
            if axis is None or values_trace is None or values_ref is None:
                continue
            df = pd.DataFrame({"wavelength_nm": axis, "flux": values_trace - values_ref})

HEAD
 codex/improve-unit-conversions-and-file-uploads-ussv5s
=======
 codex/improve-unit-conversions-and-file-uploads-udgaxh
 main
        if "wavelength_m" not in df.columns:
            if "wavelength_nm" in df.columns:
                converted_m = wavelength_to_m(df["wavelength_nm"].to_numpy(dtype=float), "nm")
                df = df.assign(wavelength_m=converted_m)
            else:
                st.warning(f"{trace.label}: missing wavelength data; trace skipped.")
                continue

 codex/improve-unit-conversions-and-file-uploads-ussv5s
=======
=======

 main
  main
        converted, axis_title = _convert_wavelength(df["wavelength_m"], display_units)
=======
        converted, axis_title = _convert_wavelength(df["wavelength_nm"], display_units)
>>>>>>> parent of 9fe7c940 (v1.1.5d: fix export imports and surface atlas docs)
        df = df.assign(wavelength=converted, flux=df["flux"].astype(float))
        if "hover" in df:
            df["hover"] = df["hover"].astype(str)
        df = df.dropna(subset=["wavelength", "flux"])
        if df.empty:
            continue

        if display_mode != "Flux (raw)":
            df["flux"] = apply_normalization(df["flux"].to_numpy(dtype=float), "max")
        elif normalization_mode and normalization_mode != "none" and trace.kind != "lines":
            df["flux"] = apply_normalization(df["flux"].to_numpy(dtype=float), normalization_mode)

        if trace.kind == "lines":
            _add_line_trace(fig, df, trace.label)
        else:
            fig.add_trace(
                go.Scatter(
                    x=df["wavelength"],
                    y=df["flux"],
                    mode="lines",
                    name=trace.label,
                    hovertext=df.get("hover"),
                    hoverinfo="text",
                )
            )

    fig.update_layout(
        xaxis_title=axis_title,
        yaxis_title="Normalized flux" if display_mode != "Flux (raw)" else "Flux",
        legend=dict(itemclick="toggleothers"),
        margin=dict(t=50, b=40, l=60, r=20),
        height=520,
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
    table = pd.DataFrame(
        {
            "Label": [trace.label for trace in overlays],
            "Provider": [trace.provider or "—" for trace in overlays],
            "Kind": [trace.kind for trace in overlays],
            "Points": [trace.points for trace in overlays],
            "Visible": [trace.visible for trace in overlays],
        }
    )
    edited = st.data_editor(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Label": st.column_config.TextColumn("Label", disabled=True),
            "Provider": st.column_config.TextColumn("Provider", disabled=True),
            "Kind": st.column_config.TextColumn("Kind", disabled=True),
            "Points": st.column_config.NumberColumn("Points", disabled=True),
            "Visible": st.column_config.CheckboxColumn("Visible"),
        },
        key="overlay_table_editor",
    )
    for trace, visible in zip(overlays, edited["Visible"].tolist()):
        trace.visible = bool(visible)
    _set_overlays(overlays)

    options = [trace.trace_id for trace in overlays]
    selected = st.multiselect(
        "Remove overlays",
        options,
        format_func=_trace_label,
        key="overlay_remove_select",
    )
    if selected and st.button("Remove selected", key="overlay_remove_button"):
        _remove_overlays(selected)
        st.success(f"Removed {len(selected)} overlays.")


def _remove_overlays(trace_ids: Sequence[str]) -> None:
    remaining = [trace for trace in _get_overlays() if trace.trace_id not in set(trace_ids)]
    _set_overlays(remaining)
    cache: SimilarityCache = st.session_state["similarity_cache"]
    cache.reset()


<<<<<<< HEAD
def _render_metadata_summary(overlays: Sequence[OverlayTrace]) -> None:
    if not overlays:
        return
    rows: List[Dict[str, object]] = []
    for trace in overlays:
        meta = {str(k).lower(): v for k, v in (trace.metadata or {}).items()}
        wavelength_range = meta.get("wavelength_range_nm")
        if isinstance(wavelength_range, (list, tuple)) and len(wavelength_range) == 2:
            wavelength_range = f"{wavelength_range[0]:.2f} – {wavelength_range[1]:.2f}"
        elif wavelength_range is None:
            wavelength_range = "—"
        rows.append(
            {
                "Label": trace.label,
                "Axis": trace.axis,
                "Flux unit": trace.flux_unit,
                "Instrument": meta.get("instrument") or meta.get("instrume") or "—",
                "Telescope": meta.get("telescope") or meta.get("telescop") or "—",
                "Observation": meta.get("date-obs") or meta.get("date_obs") or meta.get("observation_date") or "—",
                "Range (nm)": wavelength_range,
                "Resolution": meta.get("resolution_native") or meta.get("resolution") or "—",
            }
        )
    if rows:
        st.markdown("#### Metadata summary")
 codex/improve-unit-conversions-and-file-uploads-ussv5s
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
=======
 codex/improve-unit-conversions-and-file-uploads-udgaxh
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
=======
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
 main
  main
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


=======
>>>>>>> parent of 9fe7c940 (v1.1.5d: fix export imports and surface atlas docs)
def _clear_overlays() -> None:
    st.session_state["overlay_traces"] = []
    st.session_state["reference_trace_id"] = None
    cache: SimilarityCache = st.session_state["similarity_cache"]
    cache.reset()


def _export_current_view(
    fig: go.Figure,
    overlays: Sequence[OverlayTrace],
    display_units: str,
    display_mode: str,
    viewport: Tuple[float | None, float | None],
) -> None:
    rows: List[Dict[str, object]] = []
    for trace in overlays:
        if not trace.visible:
            continue
        df = _filter_viewport(trace.to_dataframe(), viewport)
        if df.empty:
            continue
        converted, _ = _convert_wavelength(df["wavelength_nm"], display_units)
        scaled = df["flux"].to_numpy(dtype=float)
        if display_mode != "Flux (raw)":
            scaled = apply_normalization(scaled, "max")
        for wavelength_value, flux_value in zip(converted, scaled):
            if not math.isfinite(float(wavelength_value)) or not math.isfinite(float(flux_value)):
                continue
            rows.append(
                {
                    "series": trace.label,
                    "wavelength": float(wavelength_value),
                    "unit": display_units,
                    "flux": float(flux_value),
                    "display_mode": display_mode,
                }
            )
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
    manifest = build_manifest(
        rows,
        display_units=display_units,
        display_mode=display_mode,
        exported_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        viewport={"low_nm": viewport[0], "high_nm": viewport[1]},
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    st.success(f"Exported: {csv_path.name}, {png_path.name}, {manifest_path.name}")

# ---------------------------------------------------------------------------
# Line metadata helpers

def _collect_line_overlays(overlays: Sequence[OverlayTrace]) -> List[OverlayTrace]:
    return [trace for trace in overlays if trace.kind == "lines" and trace.metadata.get("lines")]


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
                st.dataframe(table, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Patch log helpers

def _load_patch_note() -> str:
    path = Path("PATCHLOG.txt")
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return ""
    cleaned = [line.strip() for line in lines if line.strip() and not line.startswith("=")]
    for line in reversed(cleaned):
        if line.startswith("-"):
            return line.lstrip("- ")
    return ""


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

def _render_status_bar(version_info: Dict[str, str], patch_note: str) -> None:
    overlays = _get_overlays()
    viewport = st.session_state.get("viewport_nm", (None, None))
    low, high = viewport
    low_str = f"{low:.1f} nm" if low is not None else "auto"
    high_str = f"{high:.1f} nm" if high is not None else "auto"
    policy_map = {
        "allow": "duplicates allowed",
        "skip": "session dedupe",
        "ledger": "ledger enforced",
    }
    policy = policy_map.get(st.session_state.get("duplicate_policy"), "duplicates allowed")
    reference = _trace_label(st.session_state.get("reference_trace_id")) if overlays else "—"
    st.markdown(
        (
            "<div style='margin-top:1rem;padding:0.6rem 0.8rem;border-top:1px solid #333;font-size:0.85rem;opacity:0.85;'>"
            f"<strong>{len(overlays)}</strong> overlays • viewport {low_str} – {high_str} • reference: {reference} • {policy}<br/>"
            f"{version_info.get('version', 'v?')} • {version_info.get('date_utc', '')}<br/>"
            f"<em>{patch_note}</em>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main tab renderers

def _render_overlay_tab(version_info: Dict[str, str]) -> None:
    overlays = _get_overlays()
    st.header("Overlay workspace")
    if not overlays:
        st.info("Load a reference spectrum or fetch from the archive tab to begin.")
        return

    display_units = st.session_state.get("display_units", "nm")
    display_mode = st.session_state.get("display_mode", "Flux (raw)")
    normalization = st.session_state.get("normalization_mode", "unit")
    differential_mode = st.session_state.get("differential_mode", "Off")
    viewport = st.session_state.get("viewport_nm", (None, None))
    reference = next((trace for trace in overlays if trace.trace_id == st.session_state.get("reference_trace_id")), overlays[0])

    fig, axis_title = _build_overlay_figure(
        overlays,
        display_units,
        display_mode,
        normalization,
        viewport,
        reference,
        differential_mode,
        version_info.get("version", "v?"),
    )
    st.plotly_chart(fig, use_container_width=True)

    control_col, action_col = st.columns([3, 1])
    with control_col:
        _render_overlay_table(overlays)
    with action_col:
        if st.button("Export view", key="export_view"):
            _export_current_view(fig, overlays, display_units, display_mode, viewport)
        st.caption(f"Axis: {axis_title}")

    cache: SimilarityCache = st.session_state["similarity_cache"]
    visible_vectors = [trace.to_vectors() for trace in overlays if trace.visible]
    options = SimilarityOptions(
        metrics=tuple(st.session_state.get("similarity_metrics", ["cosine"])),
        normalization=st.session_state.get("similarity_normalization", normalization),
        line_match_top_n=int(st.session_state.get("similarity_line_peaks", 8)),
        primary_metric=st.session_state.get("similarity_primary_metric", "cosine"),
        reference_id=st.session_state.get("reference_trace_id"),
    )
    render_similarity_panel(visible_vectors, viewport, options, cache)
    _render_line_tables(overlays)


def _render_differential_tab() -> None:
    st.header("Differential analysis")
    overlays = _get_overlays()
    if len(overlays) < 2:
        st.info("Add at least two traces to explore differential workflows.")
    norm = st.session_state.get("normalization_mode", "unit")
    diff = st.session_state.get("differential_mode", "Off")
    st.write(f"Normalization mode: **{norm}**")
    st.write(f"Differential mode: **{diff}**")
    st.caption("Differential tooling shares normalization controls with the overlay tab.")


def _render_archive_tab() -> None:
    controller = ArchiveUI(add_overlay=_add_overlay_payload)
    controller.render()


def _render_docs_tab() -> None:
    st.header("Docs & provenance")
    documents = [
        "docs/index.md",
        "docs/ingestion.md",
        "docs/ui/displaying_data_guide.md",
        "docs/ui/ui_design_guide.md",
        "docs/ui/bad_ui_guide.md",
        "docs/sources/astro_data_docs.md",
        "docs/sources/telescopes_overview.md",
        "docs/sources/notable_sources_techniques_tools.md",
        "docs/sources/stellar_light_methods.md",
        "docs/math/spectroscopy_math_part1.md",
        "docs/math/spectroscopy_math_part2.md",
        "docs/math/instrument_accuracy_errors_interpretation.md",
        "docs/differential/part1b.md",
        "docs/differential/part1c.md",
        "docs/differential/part2.md",
        "docs/modeling/spectral_modeling_part1a.md",
    ]
    selection = st.selectbox("Open doc", documents)
    try:
        content = Path(selection).read_text(encoding="utf-8")
    except Exception as exc:
        st.error(f"Failed to load doc {selection}: {exc}")
    else:
        st.code(content, language="markdown")

    overlays = _get_overlays()
    if overlays:
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
# Entry points

def render() -> None:
    _ensure_session_state()
    version_info = get_version_info()
    patch_note = _load_patch_note() or version_info.get("summary") or "No summary recorded."

    st.title("Spectra App")
    st.caption(f"Build {version_info.get('version', 'v?')} • {version_info.get('date_utc', '')}")
    st.info(f"Patch: {patch_note}")

    _render_reference_section()
    st.sidebar.divider()
    _render_display_section()
    st.sidebar.divider()
    _render_differential_section()
    st.sidebar.divider()
    _render_similarity_sidebar()
    st.sidebar.divider()
    _render_duplicate_sidebar()

    overlay_tab, diff_tab, archive_tab, docs_tab = st.tabs(["Overlay", "Differential", "Archive", "Docs & Provenance"])
    with overlay_tab:
        _render_overlay_tab(version_info)
    with diff_tab:
        _render_differential_tab()
    with archive_tab:
        _render_archive_tab()
    with docs_tab:
        _render_docs_tab()

    _render_status_bar(version_info, patch_note)


def main() -> None:
    render()


if __name__ == "__main__":
    main()
