from __future__ import annotations

from dataclasses import replace

import numpy as np
from astropy import units as u
import pytest

from app.plugins import PluginContext, plugin_registry
from app.plugins.specviz_defaults import (
    GaussianSmoothingPlugin,
    LineListManagerPlugin,
    ModelFittingPlugin,
    RedshiftSliderPlugin,
    UnitConversionPlugin,
)
from app.services.workspace import WorkspaceContext, WorkspaceService

pytest.importorskip("specutils")
pytest.importorskip("astropy")


@pytest.fixture()
def gaussian_workspace() -> WorkspaceService:
    state: dict[str, object] = {}
    context = WorkspaceContext(state, viewport_key="viewport_axes")
    service = WorkspaceService(context)
    service.ensure_defaults()
    wavelengths = np.linspace(400.0, 700.0, 256)
    centre = 550.0
    sigma = 5.0
    flux = np.exp(-0.5 * ((wavelengths - centre) / sigma) ** 2)
    added, message = service.add_overlay(
        "Gaussian profile",
        wavelengths,
        flux,
        flux_unit="Jy",
        summary="Synthetic Gaussian line profile for plugin tests.",
    )
    assert added, message
    return service


def _build_context(service: WorkspaceService) -> PluginContext:
    overlays = [replace(trace) for trace in service.get_overlays()]
    return PluginContext(workspace=service, overlays=overlays)


def _first_trace(service: WorkspaceService):
    overlays = service.get_overlays()
    assert overlays, "Expected at least one overlay"
    return overlays[0]


def test_gaussian_smoothing_plugin_generates_overlay(gaussian_workspace: WorkspaceService) -> None:
    context = _build_context(gaussian_workspace)
    trace = _first_trace(gaussian_workspace)
    plugin = GaussianSmoothingPlugin(context)
    result = plugin.execute([trace.trace_id], {"stddev": 2.0})
    assert result.overlays, "Expected smoothing plugin to publish an overlay"
    overlay = result.overlays[0]
    assert len(overlay["wavelength_nm"]) == len(trace.wavelength_nm)
    assert overlay["provenance"], "Provenance metadata should be included"


def test_registry_contains_specviz_plugins() -> None:
    plugin_ids = {plugin.plugin_id for plugin in plugin_registry.list_plugins()}
    expected = {
        "gaussian_smoothing",
        "unit_conversion",
        "line_list_manager",
        "redshift_slider",
        "model_fitting",
    }
    assert expected.issubset(plugin_ids)


def test_unit_conversion_plugin_changes_flux_unit(gaussian_workspace: WorkspaceService) -> None:
    context = _build_context(gaussian_workspace)
    trace = _first_trace(gaussian_workspace)
    plugin = UnitConversionPlugin(context)
    target_unit = "erg cm-2 s-1 AA-1"
    result = plugin.execute([trace.trace_id], {"flux_unit": target_unit})
    overlay = result.overlays[0]
    assert u.Unit(overlay["flux_unit"]) == u.Unit(target_unit)
    table_row = result.tables[0].rows[0]
    assert u.Unit(table_row["converted_flux_unit"]) == u.Unit(target_unit)


def test_line_list_manager_returns_table(gaussian_workspace: WorkspaceService) -> None:
    context = _build_context(gaussian_workspace)
    trace = _first_trace(gaussian_workspace)
    plugin = LineListManagerPlugin(context)
    result = plugin.execute([trace.trace_id], {"threshold": 5.0, "width_nm": 0.2})
    assert result.tables, "Line list plugin should provide a table of detections"
    assert result.tables[0].name == "Detected features"
    # Overlay may be empty if no strong lines are detected, but execution should succeed.


def test_redshift_slider_scales_wavelengths(gaussian_workspace: WorkspaceService) -> None:
    context = _build_context(gaussian_workspace)
    trace = _first_trace(gaussian_workspace)
    plugin = RedshiftSliderPlugin(context)
    redshift = 0.1
    result = plugin.execute([trace.trace_id], {"redshift": redshift, "rest_frame": False})
    overlay = result.overlays[0]
    assert pytest.approx(overlay["wavelength_nm"][0]) == trace.wavelength_nm[0] * (1 + redshift)


def test_model_fitting_plugin_returns_parameters(gaussian_workspace: WorkspaceService) -> None:
    context = _build_context(gaussian_workspace)
    trace = _first_trace(gaussian_workspace)
    plugin = ModelFittingPlugin(context)
    result = plugin.execute(
        [trace.trace_id],
        {"amplitude": 1.0, "mean_nm": 550.0, "stddev_nm": 5.0},
    )
    overlay = result.overlays[0]
    assert len(overlay["flux"]) == len(trace.flux)
    assert result.tables, "Model fitting should export parameter tables"
    params = result.tables[0].rows[0]
    assert pytest.approx(params["mean_nm"], rel=1e-2) == 550.0
