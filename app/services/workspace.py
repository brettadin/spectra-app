from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import pandas as pd
import plotly.graph_objects as go

from ..export_manifest import build_manifest
from ..similarity import SimilarityCache, SimilarityOptions, TraceVectors, apply_normalization
from ..ui.controller import (
    OverlayTrace,
    WorkspaceController,
    axis_kind_for_trace,
    convert_axis_series,
    filter_viewport,
    prepare_similarity_inputs,
)


Viewport = Tuple[float | None, float | None]


@dataclass
class WorkspaceContext:
    """Container describing runtime state required by workspace services."""

    state: MutableMapping[str, Any] = field(default_factory=dict)
    viewport_key: str = "viewport_axes"
    export_dir: Path = field(default_factory=lambda: Path("exports"))

    def __post_init__(self) -> None:  # pragma: no cover - simple path coercion
        if not isinstance(self.export_dir, Path):
            self.export_dir = Path(self.export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ExportResult:
    """Result returned when exporting the current workspace view."""

    success: bool
    message: str
    csv_path: Optional[Path] = None
    png_path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    warnings: Tuple[str, ...] = ()


class WorkspaceService:
    """High-level operations for managing workspace overlays and exports."""

    def __init__(self, context: WorkspaceContext) -> None:
        self._context = context

    # ------------------------------------------------------------------
    # Controller helpers
    # ------------------------------------------------------------------
    @property
    def context(self) -> WorkspaceContext:
        return self._context

    @property
    def controller(self) -> WorkspaceController:
        return WorkspaceController(self._context.state, self._context.viewport_key)

    def ensure_defaults(self) -> None:
        self.controller.ensure_defaults()

    # ------------------------------------------------------------------
    # Overlay management
    # ------------------------------------------------------------------
    def get_overlays(self) -> List[OverlayTrace]:
        return self.controller.get_overlays()

    def set_overlays(self, overlays: Sequence[OverlayTrace]) -> None:
        self.controller.set_overlays(overlays)

    def add_overlay(self, *args: Any, **kwargs: Any) -> Tuple[bool, str]:
        return self.controller.add_overlay(*args, **kwargs)

    def add_overlay_payload(self, payload: Mapping[str, object]) -> Tuple[bool, str]:
        return self.controller.add_overlay_payload(payload)

    def remove_overlays(self, trace_ids: Sequence[str]) -> None:
        remaining = [
            trace for trace in self.get_overlays() if trace.trace_id not in set(trace_ids)
        ]
        self.set_overlays(remaining)
        self.reset_similarity_cache()

    def clear_overlays(self) -> None:
        state = self._context.state
        state["overlay_traces"] = []
        state["reference_trace_id"] = None
        self.reset_similarity_cache()
        state["local_upload_registry"] = {}
        state["differential_result"] = None

    # ------------------------------------------------------------------
    # Similarity cache helpers
    # ------------------------------------------------------------------
    def get_similarity_cache(self) -> SimilarityCache:
        cache: SimilarityCache = self._context.state.setdefault(
            "similarity_cache", SimilarityCache()
        )
        return cache

    def reset_similarity_cache(self) -> None:
        cache = self._context.state.get("similarity_cache")
        reset = getattr(cache, "reset", None)
        if callable(reset):
            reset()
        else:
            self._context.state["similarity_cache"] = SimilarityCache()

    def prepare_similarity_inputs(
        self, overlays: Sequence[OverlayTrace]
    ) -> Tuple[
        List[TraceVectors], Viewport, SimilarityOptions, SimilarityCache
    ]:
        viewport_store = self.get_viewport_store()
        vectors, viewport, options, cache = prepare_similarity_inputs(
            self._context.state, overlays, viewport_store
        )
        return list(vectors), viewport, options, cache

    # ------------------------------------------------------------------
    # Viewport helpers
    # ------------------------------------------------------------------
    def get_viewport_store(self) -> Dict[str, Viewport]:
        return dict(self.controller.get_viewport_store())

    def set_viewport_store(self, store: Mapping[str, Viewport]) -> None:
        self.controller.set_viewport_store(store)

    def set_viewport_for_kind(self, axis_kind: str, viewport: Viewport) -> None:
        self.controller.set_viewport_for_kind(axis_kind, viewport)

    def get_viewport_for_kind(self, axis_kind: str) -> Viewport:
        return self.controller.get_viewport_for_kind(axis_kind)

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------
    def export_view(
        self,
        overlays: Sequence[OverlayTrace],
        display_units: str,
        display_mode: str,
        viewport: Mapping[str, Viewport],
        *,
        fig: Optional[go.Figure] = None,
        filename_prefix: Optional[str] = None,
    ) -> ExportResult:
        rows: List[Dict[str, object]] = []
        viewport_map = dict(viewport)
        for trace in overlays:
            if not trace.visible:
                continue
            axis_kind = axis_kind_for_trace(trace)
            axis_view = viewport_map.get(axis_kind, (None, None))
            df = filter_viewport(trace.to_dataframe(), axis_view)
            if df.empty:
                continue
            converted, axis_title = convert_axis_series(df["wavelength_nm"], trace, display_units)
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
            return ExportResult(
                success=False,
                message="Nothing to export in the current viewport.",
            )

        export_dir = self._context.export_dir
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base = filename_prefix or "spectra_export"
        csv_path = export_dir / f"{base}_{timestamp}.csv"
        png_path = export_dir / f"{base}_{timestamp}.png"
        manifest_path = export_dir / f"{base}_{timestamp}.manifest.json"

        df_export = pd.DataFrame(rows)
        df_export.to_csv(csv_path, index=False)

        warnings: List[str] = []
        if fig is not None:
            try:
                fig.write_image(str(png_path))
            except Exception as exc:  # pragma: no cover - depends on kaleido availability
                warnings.append(f"PNG export requires kaleido ({exc}).")
                png_path = None
        else:
            png_path = None

        viewport_payload = {
            kind: {"low": vp[0], "high": vp[1]} for kind, vp in viewport_map.items()
        }
        manifest = build_manifest(
            rows,
            display_units=display_units,
            display_mode=display_mode,
            exported_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            viewport=viewport_payload,
        )
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        message = f"Exported: {csv_path.name}"
        if png_path:
            message += f", {Path(png_path).name}"
        message += f", {manifest_path.name}"

        return ExportResult(
            success=True,
            message=message,
            csv_path=csv_path,
            png_path=png_path,
            manifest_path=manifest_path,
            warnings=tuple(warnings),
        )


__all__ = ["WorkspaceContext", "WorkspaceService", "ExportResult"]
