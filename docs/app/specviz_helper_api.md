# SpecViz-compatible helper API

> **Credit:** The helper interface mirrors the SpecViz helper API from the jdaviz project maintained by the Astropy collaboration.

The Spectra helper API follows the same ergonomics documented in the SpecViz helper guide so that scripted workflows can be ported without modification. Each function accepts keyword arguments compatible with the upstream helper and delegates to the new workspace service layer. This ensures that helper calls function even when Streamlit is not present.

## `load_data`

```python
load_data(
    data,
    data_label=None,
    spectral_axis_unit=None,
    flux_unit=None,
    *,
    directory=None,
    glob=None,
    recursive=True,
    allow_empty=False,
    return_report=False,
    diagnostics=False,
    add_to_workspace=True,
    **kwargs,
)
```

- Ingests local files or directories using the same semantics as SpecViz.  
- Returns a payload, list of payloads, a diagnostics container, or a batch report.  
- Automatically adds successful payloads to the workspace when `add_to_workspace=True`.  
- Records helper provenance so manifest exports capture the scripted context.

## `get_spectra`

```python
get_spectra(include_hidden=False)
```

- Returns a mapping of trace IDs to dictionaries describing each overlay (label, axis kind, metadata, provenance).  
- Set `include_hidden=True` to include overlays that are currently hidden in the viewer.

## `set_limits`

```python
set_limits(lower, upper, *, axis_kind="wavelength")
```

- Applies explicit viewport limits for the requested axis kind.  
- Disables auto-viewport so manual ranges persist across subsequent helper calls.

## `run_plugin`

```python
run_plugin(name, /, **kwargs)
```

- Supports the SpecViz export helper plugins (e.g. `"Export View"`).  
- Returns an export payload identical to calling `export_view` with the same keyword arguments.  
- Raises `SpecvizCompatError` if a requested plugin is not available in Spectra.

## `export_view`

```python
export_view(
    viewer=None,
    *,
    display_units=None,
    display_mode=None,
    filename_prefix=None,
    fig=None,
    viewport=None,
)
```

- Exports the current overlays to CSV and manifest files using the workspace service layer.  
- Returns an `ExportPayload` dataclass containing file paths and any warnings (PNG export is skipped unless a Plotly figure is provided).  
- Defaults to the workspace display units and scaling mode when values are not supplied.

## Batch scripting notes

- The helper uses `WorkspaceService` so scripted automation can run in environments without Streamlit.  
- All helper calls share the same `WorkspaceContext`, ensuring overlay state, viewports, and similarity caches stay in sync with UI sessions.  
- When running long-lived scripts, reuse a `SpecvizCompatHelper` instance to avoid reloading ingest state for each call.
