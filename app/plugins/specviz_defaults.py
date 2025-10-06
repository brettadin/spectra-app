from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np
from astropy import units as u
from astropy.convolution import Gaussian1DKernel, convolve
from astropy.modeling import fitting, models

from . import (
    PluginBase,
    PluginError,
    PluginField,
    PluginResult,
    PluginTable,
    plugin_registry,
)


try:  # pragma: no cover - optional dependency guard
    from specutils import Spectrum1D
except Exception as exc:  # pragma: no cover - handled at runtime
    Spectrum1D = None  # type: ignore[assignment]
    _SPECTRUM1D_ERROR = exc
else:  # pragma: no cover - import executed in tests
    _SPECTRUM1D_ERROR = None

try:  # pragma: no cover - optional dependency guard
    from specutils.analysis import find_lines_derivative as _find_lines_derivative
except Exception:  # pragma: no cover - handled when unavailable
    _find_lines_derivative = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency guard
    from specutils.fitting import fit_lines as _fit_lines
except Exception:  # pragma: no cover - handled when unavailable
    _fit_lines = None  # type: ignore[assignment]


def _require_specutils() -> None:
    if Spectrum1D is None or _SPECTRUM1D_ERROR is not None:
        raise PluginError(
            "specutils is required for this plugin but is not available."
        )


def _to_spectrum(trace) -> Spectrum1D:
    _require_specutils()
    wavelengths = np.asarray(trace.wavelength_nm, dtype=float) * u.nm
    if wavelengths.size == 0:
        raise PluginError("Spectrum does not contain wavelength samples.")
    try:
        flux_unit = u.Unit(str(trace.flux_unit or ""))
    except Exception:
        flux_unit = u.dimensionless_unscaled
    try:
        flux_values = np.asarray(trace.flux, dtype=float) * flux_unit
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise PluginError(f"Unable to interpret flux values: {exc}") from exc
    return Spectrum1D(flux=flux_values, spectral_axis=wavelengths)


def _clone_metadata(trace) -> Dict[str, Any]:
    metadata = dict(trace.metadata or {})
    metadata.setdefault("source_trace_id", trace.trace_id)
    metadata.setdefault("axis_kind", trace.axis_kind)
    return metadata


def _apply_provenance(
    plugin: PluginBase,
    *,
    selection: Sequence[str],
    parameters: Mapping[str, Any],
    extras: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    provenance = plugin.build_provenance(
        selection=selection,
        parameters=parameters,
        extras=extras,
    )
    provenance.setdefault(
        "generated_at",
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    return provenance


def _detect_lines_numpy(spectrum: Spectrum1D, sigma_threshold: float) -> List[Dict[str, Any]]:
    wavelengths = spectrum.spectral_axis.to(u.nm).value
    flux = spectrum.flux.value
    if wavelengths.size < 3:
        return []
    baseline = flux - np.median(flux)
    std = np.std(baseline)
    if not math.isfinite(std) or std <= 0:
        return []
    detections: List[Dict[str, Any]] = []
    for index in range(1, len(baseline) - 1):
        left, centre, right = baseline[index - 1], baseline[index], baseline[index + 1]
        if centre > left and centre > right and centre > sigma_threshold * std:
            detections.append({"line_center": wavelengths[index], "line_type": "emission"})
        elif centre < left and centre < right and abs(centre) > sigma_threshold * std:
            detections.append({"line_center": wavelengths[index], "line_type": "absorption"})
    return detections


def _parameter_to_value(parameter: Any, target_unit: u.Unit | None) -> float:
    convert = getattr(parameter, "to", None)
    if callable(convert) and target_unit is not None:
        try:
            return float(convert(target_unit).value)  # type: ignore[arg-type]
        except Exception:
            pass
    unit_attr = getattr(parameter, "unit", None)
    value_attr = getattr(parameter, "value", parameter)
    if target_unit is not None and unit_attr is not None:
        try:
            quantity = float(value_attr) * unit_attr
            return float(quantity.to(target_unit).value)
        except Exception:
            pass
    try:
        return float(value_attr)
    except Exception:
        return float(value_attr if isinstance(value_attr, (int, float)) else 0.0)


@plugin_registry.register
class GaussianSmoothingPlugin(PluginBase):
    plugin_id = "gaussian_smoothing"
    label = "Gaussian smoothing"
    description = "Apply Gaussian convolution to one or more spectra."
    selection_mode = "multiple"

    def config_fields(self) -> Sequence[PluginField]:
        return (
            PluginField(
                name="stddev",
                label="Kernel σ (pixels)",
                kind="slider",
                default=2.0,
                min_value=0.1,
                max_value=15.0,
                step=0.1,
                help="Standard deviation of the Gaussian kernel expressed in spectral pixels.",
            ),
        )

    def execute(
        self,
        selection: Sequence[str],
        config: Mapping[str, Any],
    ) -> PluginResult:
        if not selection:
            raise PluginError("Select at least one spectrum to smooth.")
        stddev = float(config.get("stddev") or 0.0)
        if not math.isfinite(stddev) or stddev <= 0:
            raise PluginError("Kernel σ must be greater than zero.")

        overlays: List[Mapping[str, Any]] = []
        rows: List[Mapping[str, Any]] = []
        parameters = {"stddev_pixels": stddev}
        provenance = _apply_provenance(self, selection=selection, parameters=parameters)

        for trace_id in selection:
            trace = self.context.get_overlay(trace_id)
            if trace is None:
                continue
            spectrum = _to_spectrum(trace)
            kernel = Gaussian1DKernel(stddev)
            smoothed = convolve(spectrum.flux, kernel, boundary="extend")
            overlays.append(
                {
                    "label": f"{trace.label} • Gaussian σ={stddev:g}",
                    "wavelength_nm": list(map(float, trace.wavelength_nm)),
                    "flux": [float(value) for value in smoothed.value],
                    "flux_unit": str(smoothed.unit),
                    "kind": trace.kind,
                    "metadata": _clone_metadata(trace),
                    "provenance": provenance,
                }
            )
            rows.append(
                {
                    "trace_id": trace.trace_id,
                    "label": trace.label,
                    "kernel_sigma": stddev,
                }
            )

        table = PluginTable(
            name="Gaussian smoothing", rows=rows, description="Gaussian kernel parameters applied to each spectrum."
        )
        return PluginResult(
            overlays=overlays,
            tables=(table,),
            messages=(f"Applied Gaussian smoothing (σ={stddev:g})",),
            provenance=provenance,
        )


@plugin_registry.register
class UnitConversionPlugin(PluginBase):
    plugin_id = "unit_conversion"
    label = "Unit conversion"
    description = "Convert flux units for one or more spectra."
    selection_mode = "multiple"

    def config_fields(self) -> Sequence[PluginField]:
        return (
            PluginField(
                name="flux_unit",
                label="Target flux unit",
                kind="select",
                options=(
                    "Jy",
                    "erg cm-2 s-1 AA-1",
                    "erg cm-2 s-1 nm-1",
                    "W m-2 um-1",
                ),
                default="Jy",
                help="Astropy-recognised unit for the flux axis.",
            ),
        )

    def execute(
        self,
        selection: Sequence[str],
        config: Mapping[str, Any],
    ) -> PluginResult:
        if not selection:
            raise PluginError("Select at least one spectrum to convert.")
        target = str(config.get("flux_unit") or "").strip() or "Jy"
        try:
            target_unit = u.Unit(target)
        except Exception as exc:
            raise PluginError(f"Unrecognised flux unit '{target}'.") from exc

        overlays: List[Mapping[str, Any]] = []
        rows: List[Mapping[str, Any]] = []
        parameters = {"flux_unit": target}
        provenance = _apply_provenance(self, selection=selection, parameters=parameters)

        for trace_id in selection:
            trace = self.context.get_overlay(trace_id)
            if trace is None:
                continue
            spectrum = _to_spectrum(trace)
            try:
                converted_flux = spectrum.flux.to(
                    target_unit,
                    equivalencies=u.spectral_density(spectrum.spectral_axis),
                )
            except Exception as exc:
                raise PluginError(f"Unable to convert flux for {trace.label}: {exc}") from exc
            overlays.append(
                {
                    "label": f"{trace.label} [{target_unit}]",
                    "wavelength_nm": list(map(float, trace.wavelength_nm)),
                    "flux": [float(value) for value in converted_flux.value],
                    "flux_unit": str(target_unit),
                    "kind": trace.kind,
                    "metadata": {
                        **_clone_metadata(trace),
                        "previous_flux_unit": trace.flux_unit,
                    },
                    "provenance": provenance,
                }
            )
            rows.append(
                {
                    "trace_id": trace.trace_id,
                    "label": trace.label,
                    "original_flux_unit": trace.flux_unit,
                    "converted_flux_unit": str(target_unit),
                }
            )

        table = PluginTable(
            name="Unit conversion", rows=rows, description="Flux unit conversions applied to each spectrum."
        )
        return PluginResult(
            overlays=overlays,
            tables=(table,),
            messages=(f"Converted flux to {target_unit}",),
            provenance=provenance,
        )


@plugin_registry.register
class LineListManagerPlugin(PluginBase):
    plugin_id = "line_list_manager"
    label = "Line list manager"
    description = "Detect spectral features using the derivative method and publish diagnostic markers."

    def config_fields(self) -> Sequence[PluginField]:
        return (
            PluginField(
                name="threshold",
                label="Flux threshold (σ)",
                kind="slider",
                default=5.0,
                min_value=1.0,
                max_value=15.0,
                step=0.5,
                help="Detection threshold supplied to specutils.find_lines_derivative().",
            ),
            PluginField(
                name="width_nm",
                label="Marker width (nm)",
                kind="slider",
                default=0.25,
                min_value=0.01,
                max_value=2.0,
                step=0.01,
                help="Half-width of the triangular marker drawn around each detected feature.",
            ),
        )

    def execute(
        self,
        selection: Sequence[str],
        config: Mapping[str, Any],
    ) -> PluginResult:
        if not selection:
            raise PluginError("Select a spectrum to analyse.")
        trace = self.context.get_overlay(selection[0])
        if trace is None:
            raise PluginError("Selected spectrum is no longer available.")
        spectrum = _to_spectrum(trace)
        threshold = float(config.get("threshold") or 0.0)
        width_nm = float(config.get("width_nm") or 0.0)
        if threshold <= 0:
            raise PluginError("Detection threshold must be positive.")
        if width_nm <= 0:
            raise PluginError("Marker width must be positive.")

        rows: List[Mapping[str, Any]] = []
        wavelengths: List[float] = []
        flux: List[float] = []
        hover: List[str] = []

        if _find_lines_derivative is not None:
            detected = list(_find_lines_derivative(spectrum, flux_threshold=threshold))
            colnames = set(getattr(detected, "colnames", ()))  # type: ignore[arg-type]

            def _extract(row: Any) -> tuple[float, str]:
                centre_value = row["line_center"].to(u.nm).value
                line_type = str(row["line_type"]) if "line_type" in colnames else "unknown"
                return float(centre_value), line_type

        else:
            detected = _detect_lines_numpy(spectrum, threshold)

            def _extract(row: Mapping[str, Any]) -> tuple[float, str]:
                return float(row.get("line_center", 0.0)), str(row.get("line_type", "unknown"))

        if not detected:
            message = "No significant features detected."
        else:
            for entry in detected:
                centre, line_type = _extract(entry)
                rows.append(
                    {
                        "wavelength_nm": float(centre),
                        "line_type": line_type,
                    }
                )
                wavelengths.extend(
                    [
                        float(centre - width_nm),
                        float(centre),
                        float(centre + width_nm),
                    ]
                )
                amplitude = 1.0 if line_type.lower() == "emission" else -1.0
                flux.extend([0.0, amplitude, 0.0])
                hover.extend(
                    [
                        f"{line_type.title()} line @ {centre:.3f} nm",
                        f"{line_type.title()} line @ {centre:.3f} nm",
                        f"{line_type.title()} line @ {centre:.3f} nm",
                    ]
                )
            message = f"Detected {len(rows)} features."

        provenance = _apply_provenance(
            self,
            selection=selection,
            parameters={"threshold": threshold, "width_nm": width_nm},
            extras={"source_trace": trace.trace_id},
        )
        overlays: Sequence[Mapping[str, Any]] = ()
        if rows:
            overlays = (
                {
                    "label": f"{trace.label} • Detected lines",
                    "wavelength_nm": wavelengths,
                    "flux": flux,
                    "flux_unit": "relative",
                    "kind": "lines",
                    "hover": hover,
                    "metadata": {
                        **_clone_metadata(trace),
                        "line_count": len(rows),
                        "line_detection_threshold": threshold,
                    },
                    "provenance": provenance,
                },
            )

        table = PluginTable(
            name="Detected features",
            rows=rows,
            description="Spectral features identified by specutils.find_lines_derivative().",
        )
        return PluginResult(
            overlays=overlays,
            tables=(table,),
            messages=(message,),
            provenance=provenance,
        )


@plugin_registry.register
class RedshiftSliderPlugin(PluginBase):
    plugin_id = "redshift_slider"
    label = "Redshift slider"
    description = "Apply a redshift offset to a spectrum."

    def config_fields(self) -> Sequence[PluginField]:
        return (
            PluginField(
                name="redshift",
                label="Redshift z",
                kind="slider",
                default=0.0,
                min_value=-0.1,
                max_value=5.0,
                step=0.001,
                help="Positive values shift to longer wavelengths; negative values approximate blueshift.",
            ),
            PluginField(
                name="rest_frame",
                label="Shift to rest frame",
                kind="checkbox",
                default=False,
                help="If selected, interpret z as bringing the spectrum back to rest (divide by 1+z).",
            ),
        )

    def execute(
        self,
        selection: Sequence[str],
        config: Mapping[str, Any],
    ) -> PluginResult:
        if not selection:
            raise PluginError("Select a spectrum to shift.")
        trace = self.context.get_overlay(selection[0])
        if trace is None:
            raise PluginError("Selected spectrum is no longer available.")
        z = float(config.get("redshift") or 0.0)
        rest_frame = bool(config.get("rest_frame"))
        factor = (1.0 / (1.0 + z)) if rest_frame else (1.0 + z)
        if factor <= 0:
            raise PluginError("Redshift factor must be positive.")
        shifted = [float(value) * factor for value in trace.wavelength_nm]
        provenance = _apply_provenance(
            self,
            selection=selection,
            parameters={"redshift": z, "rest_frame": rest_frame},
            extras={"source_trace": trace.trace_id},
        )
        label_suffix = f"z={z:+.3f}{' (rest)' if rest_frame else ''}"
        overlay = {
            "label": f"{trace.label} • {label_suffix}",
            "wavelength_nm": shifted,
            "flux": list(map(float, trace.flux)),
            "flux_unit": trace.flux_unit,
            "kind": trace.kind,
            "metadata": {
                **_clone_metadata(trace),
                "redshift": z,
                "rest_frame": rest_frame,
            },
            "provenance": provenance,
        }
        return PluginResult(
            overlays=(overlay,),
            tables=(
                PluginTable(
                    name="Redshift parameters",
                    rows=(
                        {
                            "trace_id": trace.trace_id,
                            "label": trace.label,
                            "redshift": z,
                            "rest_frame": rest_frame,
                        },
                    ),
                    description="Parameters applied during the redshift transformation.",
                ),
            ),
            messages=(f"Applied redshift z={z:+.3f}",),
            provenance=provenance,
        )


@plugin_registry.register
class ModelFittingPlugin(PluginBase):
    plugin_id = "model_fitting"
    label = "Model fitting"
    description = "Fit a single-component Gaussian model to a spectrum."

    def config_fields(self) -> Sequence[PluginField]:
        return (
            PluginField(
                name="amplitude",
                label="Initial amplitude",
                kind="float",
                default=1.0,
                help="Initial guess for the Gaussian amplitude in flux units.",
            ),
            PluginField(
                name="mean_nm",
                label="Initial centre (nm)",
                kind="float",
                default=500.0,
                help="Initial guess for the Gaussian centre in nanometres.",
            ),
            PluginField(
                name="stddev_nm",
                label="Initial σ (nm)",
                kind="float",
                default=1.0,
                min_value=0.01,
                step=0.01,
                help="Initial guess for the Gaussian width in nanometres.",
            ),
        )

    def execute(
        self,
        selection: Sequence[str],
        config: Mapping[str, Any],
    ) -> PluginResult:
        if not selection:
            raise PluginError("Select a spectrum to fit.")
        trace = self.context.get_overlay(selection[0])
        if trace is None:
            raise PluginError("Selected spectrum is no longer available.")
        spectrum = _to_spectrum(trace)
        amplitude_guess = float(config.get("amplitude") or 1.0)
        mean_guess = float(config.get("mean_nm") or np.median(spectrum.spectral_axis.to(u.nm).value))
        stddev_guess = float(config.get("stddev_nm") or 1.0)
        if stddev_guess <= 0:
            raise PluginError("Initial σ must be positive.")

        gaussian = models.Gaussian1D(
            amplitude=amplitude_guess * spectrum.flux.unit,
            mean=mean_guess * u.nm,
            stddev=stddev_guess * u.nm,
        )
        fitter = fitting.LevMarLSQFitter()
        try:
            if _fit_lines is not None:
                fitted = _fit_lines(spectrum, gaussian, fitter=fitter)
            else:
                fitted = fitter(gaussian, spectrum.spectral_axis, spectrum.flux)
        except Exception as exc:
            raise PluginError(f"Model fitting failed: {exc}") from exc

        model_flux = fitted(spectrum.spectral_axis)
        fitted_parameters = {
            "amplitude": _parameter_to_value(fitted.amplitude, getattr(spectrum.flux, "unit", None)),
            "mean_nm": _parameter_to_value(fitted.mean, u.nm),
            "stddev_nm": _parameter_to_value(fitted.stddev, u.nm),
        }
        provenance = _apply_provenance(
            self,
            selection=selection,
            parameters=fitted_parameters,
            extras={"source_trace": trace.trace_id},
        )

        overlays = (
            {
                "label": f"{trace.label} • Gaussian fit",
                "wavelength_nm": list(map(float, trace.wavelength_nm)),
                "flux": [float(value) for value in model_flux.value],
                "flux_unit": str(model_flux.unit),
                "kind": trace.kind,
                "metadata": {
                    **_clone_metadata(trace),
                    "model": "Gaussian1D",
                },
                "provenance": provenance,
            },
        )
        table = PluginTable(
            name="Gaussian fit",
            rows=(
                {
                    "trace_id": trace.trace_id,
                    "label": trace.label,
                    **fitted_parameters,
                },
            ),
            description="Best-fit parameters returned by specutils.fit_lines().",
        )
        messages = (
            "Gaussian model fitted",
            f"Amplitude {fitted_parameters['amplitude']:.3g}",
            f"Centre {fitted_parameters['mean_nm']:.3f} nm",
            f"Sigma {fitted_parameters['stddev_nm']:.3f} nm",
        )
        return PluginResult(
            overlays=overlays,
            tables=(table,),
            messages=messages,
            provenance=provenance,
        )
