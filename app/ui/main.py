from __future__ import annotations

import json
import math
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
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
from streamlit.delta_generator import DeltaGenerator

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "app.ui"

from .targets import RegistryUnavailableError, render_targets_panel

from .._version import get_version_info
from ..ingest import OverlayIngestResult
from ..export_manifest import build_manifest
from ..server.fetch_archives import FetchError, fetch_spectrum
from ..similarity_panel import render_similarity_panel
from ..providers import ProviderQuery, search as provider_search
from ..utils.duplicate_ledger import DuplicateLedger
from ..utils.local_ingest import (
    SUPPORTED_ASCII_EXTENSIONS,
    SUPPORTED_FITS_EXTENSIONS,
    LocalIngestError,
    ingest_local_file,
)
from .controller import (
    DIFFERENTIAL_OPERATIONS,
    DifferentialResult,
    OverlayTrace,
    WorkspaceController,
    axis_kind_for_trace as _axis_kind_for_trace,
    build_differential_figure as _build_differential_figure,
    build_differential_summary as _build_differential_summary,
    build_overlay_figure as _build_overlay_figure,
    compute_differential_result as _compute_differential_result,
    determine_primary_axis_kind as _determine_primary_axis_kind,
    effective_viewport as _effective_viewport,
    group_overlays_by_axis_kind as _group_overlays_by_axis_kind,
    infer_viewport_bounds as _infer_viewport_bounds,
    is_full_resolution_enabled,
    normalize_axis_kind as _normalize_axis_kind,
    normalization_display as _normalization_display,
    prepare_similarity_inputs,
    trace_label,
)

st.set_page_config(page_title="Spectra App", layout="wide")

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ExampleSpec:
    slug: str
    label: str
    description: str
    provider: str
    query: ProviderQuery


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


def _controller() -> WorkspaceController:
    return WorkspaceController(st.session_state, VIEWPORT_STATE_KEY)


def _ensure_session_state() -> WorkspaceController:
    controller = _controller()
    controller.ensure_defaults()
    return controller


def _trace_label(trace_id: Optional[str]) -> str:
    return trace_label(st.session_state, trace_id)


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
                added, message = _controller().add_overlay_payload(payload)
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

    controller = _controller()
    return controller.add_overlay(
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

    overlays = _controller().get_overlays()
    if not overlays:
        container.caption("Load an example or fetch from an archive to begin.")


def _render_line_catalog_group(container: DeltaGenerator) -> None:
    online = bool(st.session_state.get("network_available", True))
    container.markdown("#### Line catalogs")
    if not online:
        container.caption("Using local cache")
        container.info("NIST lookups are unavailable while offline.")
        return
    container.markdown("NIST ASD lines")
    _render_nist_form(container)


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
    added, message = _controller().add_overlay_payload(payload)
    (container.success if added else container.info)(message)


def _render_display_section(container: DeltaGenerator) -> None:
    container.markdown("#### Display & viewport")
    overlays = _controller().get_overlays()
    cleared = container.button(
        "Clear overlays",
        key="clear_overlays_button",
        help="Remove all overlays from the session.",
        disabled=not overlays,
    )
    if cleared:
        _clear_overlays()
        st.session_state["overlay_clear_message"] = "Cleared all overlays."

    units = container.selectbox(
        "Wavelength units",
        ["nm", "Å", "µm", "cm^-1"],
        index=["nm", "Å", "µm", "cm^-1"].index(
            st.session_state.get("display_units", "nm")
        ),
    )
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
        _controller().set_viewport_for_kind(primary_axis, (None, None))
        return

    stored_viewport = _controller().get_viewport_for_kind(primary_axis)
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
    _controller().set_viewport_for_kind(
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
            _controller().set_overlays(overlays)

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
        _controller().set_overlays(overlays)

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
        trace for trace in _controller().get_overlays() if trace.trace_id not in set(trace_ids)
    ]
    _controller().set_overlays(remaining)
    cache = st.session_state.get("similarity_cache")
    reset = getattr(cache, "reset", None)
    if callable(reset):
        reset()


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


def _resolve_image_statistics(
    trace: OverlayTrace, meta: Mapping[str, object]
) -> Optional[Mapping[str, object]]:
    stats = meta.get("image_statistics")
    if isinstance(stats, Mapping):
        return stats
    if isinstance(trace.metadata, Mapping):
        raw = trace.metadata.get("image_statistics")
        if isinstance(raw, Mapping):
            return raw
    if isinstance(trace.image, Mapping):
        image_stats = trace.image.get("statistics")
        if isinstance(image_stats, Mapping):
            return image_stats
    return None


def _format_pixel_range(trace: OverlayTrace, meta: Mapping[str, object]) -> str:
    if str(trace.axis_kind or meta.get("axis_kind") or "wavelength").lower() != "image":
        return "—"
    stats = _resolve_image_statistics(trace, meta)
    if not isinstance(stats, Mapping):
        return "—"
    minimum = stats.get("min")
    maximum = stats.get("max")
    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        return "—"
    if not math.isfinite(float(minimum)) or not math.isfinite(float(maximum)):
        return "—"
    unit_suffix = f" {trace.flux_unit}" if trace.flux_unit else ""
    return f"{float(minimum):.3g} – {float(maximum):.3g}{unit_suffix}"


def _format_pixel_spread(trace: OverlayTrace, meta: Mapping[str, object]) -> str:
    if str(trace.axis_kind or meta.get("axis_kind") or "wavelength").lower() != "image":
        return "—"
    stats = _resolve_image_statistics(trace, meta)
    if not isinstance(stats, Mapping):
        return "—"
    p16 = stats.get("p16")
    p84 = stats.get("p84")
    median = stats.get("median")
    components: List[str] = []
    if isinstance(median, (int, float)) and math.isfinite(float(median)):
        components.append(f"median {float(median):.3g}")
    if isinstance(p16, (int, float)) and isinstance(p84, (int, float)):
        if math.isfinite(float(p16)) and math.isfinite(float(p84)):
            components.append(f"16–84% {float(p16):.3g}–{float(p84):.3g}")
    if not components:
        return "—"
    unit_suffix = f" {trace.flux_unit}" if trace.flux_unit else ""
    return ", ".join(components) + unit_suffix


def _format_spatial_axes(trace: OverlayTrace) -> str:
    if str(trace.axis_kind or "wavelength").lower() != "image":
        return "—"
    provenance_units = None
    if isinstance(trace.provenance, Mapping):
        units = trace.provenance.get("units")
        if isinstance(units, Mapping):
            provenance_units = units.get("image_axes")
    axes: Sequence[str] = ()
    if isinstance(provenance_units, Sequence) and not isinstance(provenance_units, str):
        axes = [str(axis) for axis in provenance_units if axis]
    if not axes:
        if isinstance(trace.metadata, Mapping):
            ctype = trace.metadata.get("image_axis_ctype")
            if isinstance(ctype, str) and ctype.strip():
                axes = [ctype.strip()]
    return ", ".join(axes) if axes else "—"


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
                "Pixel range": _format_pixel_range(trace, meta),
                "Pixel stats": _format_pixel_spread(trace, meta),
                "Spatial axes": _format_spatial_axes(trace),
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
    supported = sorted(SUPPORTED_ASCII_EXTENSIONS | SUPPORTED_FITS_EXTENSIONS)
    accepted_types = sorted(
        {ext.lstrip(".") for ext in supported if ext.startswith(".")}
    )
    uploader = st.file_uploader(
        "Select spectral files",
        type=accepted_types,
        accept_multiple_files=True,
        key="local_upload_widget",
        help="Supports ASCII tables (CSV/TXT/TSV/ASCII), FITS spectral products, and gzip-compressed variants.",
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

        added, message = _controller().add_overlay_payload(payload)
        registry[checksum] = {"name": uploaded.name, "added": added, "message": message}
        (st.success if added else st.info)(message)


def _clear_overlays() -> None:
    st.session_state["overlay_traces"] = []
    st.session_state["reference_trace_id"] = None
    cache = st.session_state.get("similarity_cache")
    reset = getattr(cache, "reset", None)
    if callable(reset):
        reset()
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
    overlays = _controller().get_overlays()
    target_overlays = [trace for trace in overlays if trace.visible] or overlays
    axis_groups = _group_overlays_by_axis_kind(target_overlays)
    primary_axis = _determine_primary_axis_kind(target_overlays)
    selected_group = axis_groups.get(primary_axis) or target_overlays
    stored_viewport = _controller().get_viewport_for_kind(primary_axis)
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
    overlays = _controller().get_overlays()
    if not overlays:
        st.info("Upload a recorded spectrum or fetch from the archive tab to begin.")
        return
    st.divider()

    display_units = st.session_state.get("display_units", "nm")
    display_mode = st.session_state.get("display_mode", "Flux (raw)")
    normalization = st.session_state.get("normalization_mode", "unit")
    differential_mode = st.session_state.get("differential_mode", "Off")
    target_overlays = [trace for trace in overlays if trace.visible] or overlays
    axis_groups = _group_overlays_by_axis_kind(target_overlays)
    plottable_groups = {
        kind: group
        for kind, group in axis_groups.items()
        if kind not in {"image", "time"}
    }
    viewport_store = _controller().get_viewport_store()
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

    full_resolution = is_full_resolution_enabled(st.session_state)
    fig, axis_title = _build_overlay_figure(
        overlays,
        display_units,
        display_mode,
        normalization,
        filter_viewports,
        reference,
        differential_mode,
        version_info.get("version", "v?"),
        axis_viewport_by_kind=effective_viewports if single_axis else None,
        full_resolution=full_resolution,
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
    _render_line_tables(overlays)


def _add_differential_overlay(result: DifferentialResult) -> Tuple[bool, str]:
    controller = _controller()
    metadata = {
        "kind": "differential",
        "operation_code": result.operation_code,
        "operation_label": result.operation_label,
        "normalization": result.normalization,
        "sample_points": result.sample_points,
        "trace_a_id": result.trace_a_id,
        "trace_b_id": result.trace_b_id,
    }
    provenance = {
        "differential": {
            "trace_a": result.trace_a_label,
            "trace_b": result.trace_b_label,
            "computed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(result.computed_at)),
        }
    }
    summary = (
        f"{result.operation_label} of {result.trace_a_label} and {result.trace_b_label}"
    )
    return controller.add_overlay(
        result.label,
        result.grid_nm,
        result.result,
        provider="Differential",
        summary=summary,
        metadata=metadata,
        provenance=provenance,
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
    overlays = _controller().get_overlays()
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
    viewport_store = _controller().get_viewport_store()
    visible_vectors, effective_viewport, similarity_options, cache = prepare_similarity_inputs(
        st.session_state, spectral_overlays, viewport_store
    )

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
    if len(visible_vectors) >= 2:
        render_similarity_panel(
            visible_vectors,
            effective_viewport,
            similarity_options,
            cache,
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

    overlays = _controller().get_overlays()
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

    sidebar = st.sidebar
    controls_panel = sidebar.container()
    _render_settings_group(controls_panel)
    _render_ingest_queue_panel(controls_panel)

    overlay_tab, diff_tab, library_tab, docs_tab = st.tabs(
        ["Overlay", "Differential", "Library", "Docs & Provenance"]
    )
    with overlay_tab:
        _render_overlay_tab(version_info)
    with diff_tab:
        _render_differential_tab()
    with library_tab:
        _render_library_tab()
    with docs_tab:
        _render_docs_tab(version_info)

    _render_status_bar(version_info)


def main() -> None:
    render()


if __name__ == "__main__":
    main()
