from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

import plotly.graph_objects as go

from app.services.workspace import ExportResult, WorkspaceContext, WorkspaceService
from app.utils.local_ingest import BatchIngestReport, ingest_local_paths


class SpecvizCompatError(RuntimeError):
    """Raised when scripted SpecViz-style automation fails."""


@dataclass(frozen=True)
class HelperResult:
    payloads: List[Mapping[str, object]]
    report: BatchIngestReport


@dataclass(frozen=True)
class ExportPayload:
    csv_path: Path
    manifest_path: Path
    png_path: Optional[Path]
    warnings: Tuple[str, ...] = ()


def _normalise_sequence(value: Union[str, Path, Iterable[Union[str, Path]]]) -> List[Path]:
    if isinstance(value, (str, Path)):
        return [Path(value)]
    if not isinstance(value, Iterable):
        raise TypeError("load_data expects a path or iterable of paths.")
    paths: List[Path] = []
    for item in value:
        paths.append(Path(item))
    return paths


def _apply_helper_provenance(
    payloads: Iterable[MutableMapping[str, object]],
    helper_options: Mapping[str, object],
) -> None:
    for payload in payloads:
        provenance = dict(payload.get("provenance") or {})
        helper_chain = list(provenance.get("helpers") or [])
        helper_chain.append({"helper": "SpecvizCompatHelper", **helper_options})
        provenance["helpers"] = helper_chain
        provenance.setdefault("helper", helper_options)
        payload["provenance"] = provenance


class SpecvizCompatHelper:
    """Mirror jdaviz SpecViz helper signatures for scripted workflows."""

    def __init__(
        self,
        *,
        context: WorkspaceContext | None = None,
        workspace: WorkspaceService | None = None,
        follow_symlinks: bool = False,
    ) -> None:
        if workspace is None:
            context = context or WorkspaceContext()
            workspace = WorkspaceService(context)
        else:
            context = workspace.context
        self._context = context
        self._workspace = workspace
        self._follow_symlinks = follow_symlinks
        self._workspace.ensure_defaults()

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------
    @property
    def workspace(self) -> WorkspaceService:
        return self._workspace

    @property
    def context(self) -> WorkspaceContext:
        return self._context

    # ------------------------------------------------------------------
    # Core helper methods
    # ------------------------------------------------------------------
    def load_data(
        self,
        data: Union[str, Path, Iterable[Union[str, Path]]],
        data_label: str | None = None,
        spectral_axis_unit: str | None = None,
        flux_unit: str | None = None,
        *,
        directory: str | Path | None = None,
        glob: Union[str, Sequence[str], None] = None,
        recursive: bool = True,
        allow_empty: bool = False,
        return_report: bool = False,
        diagnostics: bool = False,
        add_to_workspace: bool = True,
        **kwargs: object,
    ) -> Union[Mapping[str, object], List[Mapping[str, object]], HelperResult, BatchIngestReport]:
        base = Path(directory).expanduser() if directory is not None else None

        try:
            paths = _normalise_sequence(data)
        except TypeError:
            if directory is None:
                raise
            paths = []

        resolved: List[Path] = []
        for path in paths:
            if base is not None and not path.is_absolute():
                resolved.append((base / path).expanduser())
            else:
                resolved.append(path.expanduser())

        if base is not None and not resolved:
            resolved = [base]

        if not resolved and not allow_empty:
            raise SpecvizCompatError("No data paths were provided to load_data().")

        report = ingest_local_paths(
            resolved,
            recursive=recursive,
            glob_patterns=glob,
            follow_symlinks=self._follow_symlinks,
            context="specviz_helper",
        )

        payloads = report.successful_payloads()
        if not payloads and not allow_empty:
            errors = report.summary.get("errors") or []
            raise SpecvizCompatError(
                "load_data() did not ingest any spectra. " f"Diagnostics: {errors}"
            )

        helper_options = {
            "label": data_label,
            "spectral_axis_unit": spectral_axis_unit,
            "flux_unit": flux_unit,
            "recursive": recursive,
            "glob": glob,
        }
        if kwargs:
            helper_options.update({str(key): value for key, value in kwargs.items()})
        mutable_payloads: List[MutableMapping[str, object]] = [dict(payload) for payload in payloads]
        _apply_helper_provenance(mutable_payloads, helper_options)

        if data_label and len(mutable_payloads) == 1:
            mutable_payloads[0]["label"] = data_label

        if spectral_axis_unit and mutable_payloads:
            for payload in mutable_payloads:
                wavelength = dict(payload.get("wavelength") or {})
                wavelength["unit"] = spectral_axis_unit
                payload["wavelength"] = wavelength

        if flux_unit and mutable_payloads:
            for payload in mutable_payloads:
                payload["flux_unit"] = flux_unit

        if add_to_workspace and mutable_payloads:
            for payload in mutable_payloads:
                self._workspace.add_overlay_payload(payload)

        if return_report:
            report.summary.setdefault("helper", helper_options)
            return report

        if diagnostics:
            return HelperResult(payloads=mutable_payloads, report=report)

        if len(mutable_payloads) == 1:
            return mutable_payloads[0]
        return mutable_payloads

    def get_spectra(self, include_hidden: bool = False) -> Dict[str, Mapping[str, object]]:
        overlays = self._workspace.get_overlays()
        spectra: Dict[str, Mapping[str, object]] = {}
        for trace in overlays:
            if not include_hidden and not trace.visible:
                continue
            spectra[trace.trace_id] = {
                "label": trace.label,
                "wavelength_nm": tuple(trace.wavelength_nm),
                "flux": tuple(trace.flux),
                "kind": trace.kind,
                "axis_kind": trace.axis_kind,
                "metadata": dict(trace.metadata or {}),
                "provenance": dict(trace.provenance or {}),
            }
        return spectra

    def set_limits(
        self,
        lower: float | None,
        upper: float | None,
        *,
        axis_kind: str = "wavelength",
    ) -> None:
        self._workspace.set_viewport_for_kind(axis_kind, (lower, upper))
        self._context.state["auto_viewport"] = False

    def run_plugin(self, plugin_name: str, *args: object, **kwargs: object) -> ExportPayload:
        normalised = plugin_name.strip().lower()
        if normalised in {"export view", "export 1d", "export spectrum"}:
            return self.export_view(*args, **kwargs)
        raise SpecvizCompatError(f"Plugin '{plugin_name}' is not supported by this helper.")

    def export_view(
        self,
        viewer: str | None = None,
        *,
        display_units: str | None = None,
        display_mode: str | None = None,
        filename_prefix: str | None = None,
        fig: Optional[go.Figure] = None,
        viewport: Optional[Mapping[str, Tuple[float | None, float | None]]] = None,
    ) -> ExportPayload:
        overlays = self._workspace.get_overlays()
        if not overlays:
            raise SpecvizCompatError("No overlays available for export.")

        viewport_map = dict(viewport or self._workspace.get_viewport_store())
        if not viewport_map:
            primary_axis = str(overlays[0].axis_kind or "wavelength")
            viewport_map[primary_axis] = (None, None)

        chosen_units = display_units or str(self._context.state.get("display_units", "nm"))
        chosen_mode = display_mode or str(self._context.state.get("display_mode", "Flux (raw)"))

        result: ExportResult = self._workspace.export_view(
            overlays,
            chosen_units,
            chosen_mode,
            viewport_map,
            fig=fig,
            filename_prefix=filename_prefix,
        )
        if not result.success or result.csv_path is None or result.manifest_path is None:
            raise SpecvizCompatError(result.message)
        return ExportPayload(
            csv_path=result.csv_path,
            manifest_path=result.manifest_path,
            png_path=result.png_path,
            warnings=result.warnings,
        )


def load_data(*args: object, **kwargs: object):
    helper = SpecvizCompatHelper()
    return helper.load_data(*args, **kwargs)


def get_spectra(*args: object, **kwargs: object):
    helper = SpecvizCompatHelper()
    return helper.get_spectra(*args, **kwargs)


def set_limits(*args: object, **kwargs: object) -> None:
    helper = SpecvizCompatHelper()
    helper.set_limits(*args, **kwargs)


def run_plugin(*args: object, **kwargs: object) -> ExportPayload:
    helper = SpecvizCompatHelper()
    return helper.run_plugin(*args, **kwargs)


def export_view(*args: object, **kwargs: object) -> ExportPayload:
    helper = SpecvizCompatHelper()
    return helper.export_view(*args, **kwargs)


__all__ = [
    "SpecvizCompatHelper",
    "SpecvizCompatError",
    "HelperResult",
    "ExportPayload",
    "load_data",
    "get_spectra",
    "set_limits",
    "run_plugin",
    "export_view",
]
