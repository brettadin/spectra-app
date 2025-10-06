from __future__ import annotations

"""SpecViz-compatible helper that wraps local ingest pathways."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence, Tuple, Union

from app.utils.local_ingest import BatchIngestReport, ingest_local_paths


class SpecvizCompatError(RuntimeError):
    """Raised when scripted SpecViz-style ingestion fails."""


@dataclass
class HelperResult:
    """Container returned when diagnostics are requested."""

    payloads: List[Mapping[str, object]]
    report: BatchIngestReport


def _normalise_sequence(value: Union[str, Path, Iterable[Union[str, Path]]]) -> List[Path]:
    if isinstance(value, (str, Path)):
        return [Path(value)]
    if not isinstance(value, Iterable):
        raise TypeError("SpecvizCompatHelper.load_data expects a path or iterable of paths.")
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
    """Mirror jdaviz SpecViz helper signatures for scripted ingest workflows."""

    def __init__(self, *, follow_symlinks: bool = False) -> None:
        self._follow_symlinks = follow_symlinks

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
        **kwargs,
    ) -> Union[Mapping[str, object], List[Mapping[str, object]], HelperResult, BatchIngestReport]:
        """Load spectral files via local ingest using SpecViz-style semantics."""

        if directory is not None:
            base = Path(directory).expanduser()
        else:
            base = None

        try:
            paths = _normalise_sequence(data)
        except TypeError:
            if directory is None:
                raise
            # Allow calls like helper.load_data(None, directory=...)
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
            raise SpecvizCompatError("No data paths were provided to SpecvizCompatHelper.load_data().")

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
                "SpecvizCompatHelper.load_data() did not ingest any spectra. "
                f"Diagnostics: {errors}"
            )

        helper_options = {
            "label": data_label,
            "spectral_axis_unit": spectral_axis_unit,
            "flux_unit": flux_unit,
            "recursive": recursive,
            "glob": glob,
        }

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

        if return_report:
            report.summary.setdefault("helper", helper_options)
            return report

        if diagnostics:
            return HelperResult(payloads=mutable_payloads, report=report)

        if len(mutable_payloads) == 1:
            return mutable_payloads[0]
        return mutable_payloads


def load_data(*args, **kwargs):
    """Module-level convenience wrapper mirroring SpecViz helpers."""

    helper = SpecvizCompatHelper()
    return helper.load_data(*args, **kwargs)


__all__ = ["SpecvizCompatHelper", "SpecvizCompatError", "load_data", "HelperResult"]
