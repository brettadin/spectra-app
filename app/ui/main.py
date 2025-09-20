from __future__ import annotations

import json
import math
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app._version import get_version_info
from app.server.fetch_archives import FetchError, fetch_spectrum

st.set_page_config(page_title='Spectra App', layout='wide')

VI = get_version_info()  # version info dict

root = Path('.')
exports = root / 'exports'
exports.mkdir(exist_ok=True, parents=True)

# Header with version badge
st.markdown(
    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
    f"<h2 style='margin:0'>Spectra App</h2>"
    f"<span style='background:#111;border:1px solid #333;padding:4px 8px;border-radius:8px;'>"
    f"{VI['version']} • {VI['date_utc']}</span></div>",
    unsafe_allow_html=True
)

st.sidebar.title('Spectra Controls')
st.sidebar.caption(f"Build: {VI['version']} — {VI['summary'] or 'No summary'}")

with st.expander("What's new in this patch?"):
    st.write(f"**{VI['version']}** — {VI['summary'] or 'No summary provided.'}")
    st.caption(f"Built: {VI['date_utc']}")

if "nist_overlays" not in st.session_state:
    st.session_state["nist_overlays"] = []

st.sidebar.markdown("### NIST ASD overlays")
with st.sidebar.form("nist_overlay_form", clear_on_submit=False):
    nist_identifier = st.text_input(
        "Element or spectrum",
        key="nist_element_identifier",
        placeholder="e.g. H, Hydrogen, Fe II",
        help="Enter an element symbol or name. Add a Roman numeral or +++ to specify the ion stage.",
    )
    nist_lower = st.number_input(
        "Lower λ (nm)",
        min_value=0.0,
        value=380.0,
        step=10.0,
        key="nist_lower_bound",
        help="Minimum wavelength to request from NIST (nanometers).",
    )
    nist_upper = st.number_input(
        "Upper λ (nm)",
        min_value=0.0,
        value=750.0,
        step=10.0,
        key="nist_upper_bound",
        help="Maximum wavelength to request from NIST (nanometers).",
    )
    nist_use_ritz = st.checkbox(
        "Prefer Ritz wavelengths",
        value=True,
        key="nist_prefer_ritz",
        help="Use Ritz wavelengths when available; fall back to observed values otherwise.",
    )
    if st.form_submit_button("Add NIST overlay"):
        identifier = (st.session_state.get("nist_element_identifier") or "").strip()
        lower = float(st.session_state.get("nist_lower_bound", nist_lower))
        upper = float(st.session_state.get("nist_upper_bound", nist_upper))
        use_ritz = bool(st.session_state.get("nist_prefer_ritz", True))
        if not identifier:
            st.sidebar.warning("Enter an element symbol or spectrum label.")
        elif math.isclose(lower, upper):
            st.sidebar.warning("Lower and upper wavelength bounds must differ.")
        else:
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
                st.sidebar.error(f"Failed to fetch NIST data: {exc}")
            else:
                st.session_state["nist_overlays"].append(result)
                st.sidebar.success(f"Added {result['meta'].get('label', identifier)}")

if st.session_state["nist_overlays"]:
    if st.sidebar.button("Clear NIST overlays"):
        st.session_state["nist_overlays"] = []
        for key in list(st.session_state.keys()):
            if key.startswith("nist_visible_"):
                del st.session_state[key]
    else:
        st.sidebar.caption("Toggle overlays to display them on the charts.")
        for idx, overlay in enumerate(st.session_state["nist_overlays"]):
            label = overlay.get("meta", {}).get("label", f"NIST overlay {idx + 1}")
            visible_key = f"nist_visible_{idx}"
            visible = st.sidebar.checkbox(label, value=True, key=visible_key)
            overlay["visible"] = visible

st.sidebar.write('Examples')
ex_toggle_he = st.sidebar.checkbox('He (example)', value=False)
ex_toggle_ne = st.sidebar.checkbox('Ne (example)', value=False)
display_mode = st.sidebar.selectbox(
    'Display mode',
    ['Flux (raw)', 'Flux (normalized)'],
    index=0,
    help='Choose how traces are scaled before plotting.'
)
display_units = st.sidebar.selectbox(
    'Display units',
    ['nm', 'Å', 'µm', 'cm^-1'],
    index=0,
    help='Unit applied to the wavelength axis.'
)

tabs = st.tabs(['Overlay', 'Differential', 'Docs'])

def _convert_wavelength(series: pd.Series, unit: str) -> tuple[pd.Series, str]:
    unit = unit or 'nm'
    if unit == 'Å':
        return series * 10.0, 'Wavelength (Å)'
    if unit == 'µm':
        return series / 1000.0, 'Wavelength (µm)'
    if unit == 'cm^-1':
        # Avoid divide-by-zero; replace zeros with NaN before inversion.
        safe = series.replace(0, pd.NA)
        return 1e7 / safe, 'Wavenumber (cm⁻¹)'
    return series, 'Wavelength (nm)'


def _prepare_trace(csv_path: str, label: str, display_units: str, display_mode: str) -> tuple[pd.DataFrame, str]:
    df = pd.read_csv(csv_path)
    wavelengths, axis_title = _convert_wavelength(df['wavelength_nm'], display_units)
    intensities = pd.Series(df['intensity'], dtype=float)
    if display_mode == 'Flux (normalized)':
        max_val = float(intensities.abs().max())
        if max_val:
            intensities = intensities / max_val
    plot_df = pd.DataFrame({'wavelength': wavelengths, 'flux': intensities}).dropna()
    plot_df = plot_df.sort_values('wavelength')
    plot_df['series'] = label
    return plot_df, axis_title


def _prepare_nist_trace(data: dict, display_units: str, display_mode: str) -> tuple[pd.DataFrame, str]:
    lines = data.get('lines') or []
    if not lines:
        return pd.DataFrame(), 'Wavelength (nm)'

    base_series = pd.Series([line.get('wavelength_nm') for line in lines], dtype=float)
    converted, axis_title = _convert_wavelength(base_series, display_units)

    if display_mode == 'Flux (normalized)':
        intensities = pd.Series([line.get('relative_intensity_normalized') for line in lines], dtype=float)
    else:
        intensities = pd.Series([line.get('relative_intensity') for line in lines], dtype=float)

    if intensities.notna().any():
        intensities = intensities.fillna(0.0)
    else:
        intensities = pd.Series([1.0] * len(lines), dtype=float)

    axis_unit = axis_title.split('(')[-1].strip(')') if '(' in axis_title else axis_title
    converted_list = converted.tolist()

    hover_texts: list[str] = []
    for idx, line in enumerate(lines):
        wavelength_value = converted_list[idx]
        if isinstance(wavelength_value, (int, float)) and math.isfinite(wavelength_value):
            text_lines = [f"λ: {wavelength_value:.4f} {axis_unit}"]
        else:
            text_lines = ["λ unavailable"]

        ritz_nm = line.get('ritz_wavelength_nm')
        observed_nm = line.get('observed_wavelength_nm')
        if ritz_nm and observed_nm and not math.isclose(ritz_nm, observed_nm, rel_tol=1e-9, abs_tol=1e-9):
            text_lines.append(f"Ritz: {ritz_nm:.4f} nm")
            text_lines.append(f"Observed: {observed_nm:.4f} nm")
        elif ritz_nm:
            text_lines.append(f"Ritz: {ritz_nm:.4f} nm")
        elif observed_nm:
            text_lines.append(f"Observed: {observed_nm:.4f} nm")

        rel_int = line.get('relative_intensity')
        if rel_int is not None:
            text_lines.append(f"Rel. intensity: {rel_int:g}")
        norm_int = line.get('relative_intensity_normalized')
        if norm_int is not None:
            text_lines.append(f"Normalized: {norm_int:.3f}")

        accuracy = line.get('accuracy')
        if accuracy:
            text_lines.append(f"Accuracy: {accuracy}")

        lower = line.get('lower_level')
        upper = line.get('upper_level')
        if lower or upper:
            text_lines.append(f"{lower or '?'} → {upper or '?'}")

        hover_texts.append("<br>".join(text_lines))

    plot_df = pd.DataFrame(
        {
            'wavelength': converted,
            'flux': intensities,
            'series': data.get('meta', {}).get('label', 'NIST ASD'),
            'hover_text': hover_texts,
            'relative_intensity': [line.get('relative_intensity') for line in lines],
            'relative_intensity_normalized': [line.get('relative_intensity_normalized') for line in lines],
            'observed_wavelength_nm': [line.get('observed_wavelength_nm') for line in lines],
            'ritz_wavelength_nm': [line.get('ritz_wavelength_nm') for line in lines],
        }
    )
    return plot_df, axis_title


def _add_nist_trace(fig: go.Figure, trace_df: pd.DataFrame, label: str) -> None:
    if trace_df.empty:
        return
    xs: list[float | None] = []
    ys: list[float | None] = []
    hover: list[str | None] = []
    for _, row in trace_df.iterrows():
        wavelength = row['wavelength']
        flux_value = float(row['flux']) if row['flux'] is not None else 0.0
        text = row.get('hover_text')
        xs.extend([wavelength, wavelength, None])
        ys.extend([0.0, flux_value, None])
        hover.extend([text, text, None])

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode='lines',
            name=label,
            hoverinfo='text',
            hovertext=hover,
            line=dict(width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trace_df['wavelength'],
            y=trace_df['flux'],
            mode='markers',
            marker=dict(size=6, symbol='line-ns'),
            name=f"{label} markers",
            hoverinfo='text',
            hovertext=trace_df['hover_text'],
            showlegend=False,
        )
    )


def _build_nist_line_table(data: dict) -> pd.DataFrame:
    records = []
    for line in data.get('lines') or []:
        records.append(
            {
                'Wavelength (nm)': line.get('wavelength_nm'),
                'Observed (nm)': line.get('observed_wavelength_nm'),
                'Ritz (nm)': line.get('ritz_wavelength_nm'),
                'Relative intensity': line.get('relative_intensity'),
                'Normalized intensity': line.get('relative_intensity_normalized'),
                'Transition prob. (s⁻¹)': line.get('transition_probability_s'),
                'Oscillator strength': line.get('oscillator_strength'),
                'Accuracy': line.get('accuracy'),
                'Lower level': line.get('lower_level'),
                'Upper level': line.get('upper_level'),
                'Type': line.get('transition_type'),
                'TP reference': line.get('transition_probability_reference'),
                'Line reference': line.get('line_reference'),
            }
        )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame.from_records(records)


with tabs[0]:
    st.header('Overlays')
    fig = go.Figure()
    axis_title = 'Wavelength (nm)'
    rows = []
    active_nist_overlays: list[dict] = []

    try:
        if ex_toggle_he:
            trace_df, axis_title = _prepare_trace('app/examples/He.csv', 'He (example)', display_units, display_mode)
            fig.add_trace(go.Scatter(x=trace_df['wavelength'], y=trace_df['flux'], mode='lines+markers', name='He (example)'))
            rows.extend(
                {
                    'series': 'He (example)',
                    'wavelength': float(row['wavelength']),
                    'unit': display_units,
                    'flux': float(row['flux']),
                    'display_mode': display_mode,
                }
                for _, row in trace_df.iterrows()
            )
        if ex_toggle_ne:
            trace_df, axis_title = _prepare_trace('app/examples/Ne.csv', 'Ne (example)', display_units, display_mode)
            fig.add_trace(go.Scatter(x=trace_df['wavelength'], y=trace_df['flux'], mode='lines+markers', name='Ne (example)'))
            rows.extend(
                {
                    'series': 'Ne (example)',
                    'wavelength': float(row['wavelength']),
                    'unit': display_units,
                    'flux': float(row['flux']),
                    'display_mode': display_mode,
                }
                for _, row in trace_df.iterrows()
            )
    except Exception as e:
        st.error(f"Failed to load examples: {e}")

    for idx, overlay in enumerate(st.session_state.get("nist_overlays", [])):
        if not overlay.get('visible', True):
            continue
        trace_df, axis_override = _prepare_nist_trace(overlay, display_units, display_mode)
        if trace_df.empty:
            continue
        axis_title = axis_override
        label = overlay.get('meta', {}).get('label', f"NIST overlay {idx + 1}")
        _add_nist_trace(fig, trace_df, label)
        for _, row in trace_df.iterrows():
            wavelength_value = row['wavelength']
            flux_value = row['flux']
            try:
                wavelength_float = float(wavelength_value)
                flux_float = float(flux_value)
            except (TypeError, ValueError):
                continue
            if math.isnan(wavelength_float) or math.isnan(flux_float):
                continue
            rows.append(
                {
                    'series': label,
                    'wavelength': wavelength_float,
                    'unit': display_units,
                    'flux': flux_float,
                    'display_mode': display_mode,
                }
            )
        active_nist_overlays.append(overlay)

    fig.update_layout(
        xaxis_title=axis_title,
        yaxis_title='Normalized intensity' if display_mode == 'Flux (normalized)' else 'Flux / Intensity',
        legend=dict(itemclick='toggleothers')
    )
    # Version watermark annotation for screenshots/PNGs
    fig.update_layout(annotations=[dict(text=f"{VI['version']}", xref="paper", yref="paper", x=0.99, y=-0.20, showarrow=False, font=dict(size=12), align="right", opacity=0.7)])
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Legend must have no empty labels.')

    if active_nist_overlays:
        with st.expander('View NIST line details'):
            for overlay in active_nist_overlays:
                meta = overlay.get('meta', {})
                label = meta.get('label', 'NIST ASD')
                query = meta.get('query', {})
                count = len(overlay.get('lines') or [])
                st.markdown(
                    f"**{label}** — {count} lines from {query.get('lower_wavelength', '…')} to {query.get('upper_wavelength', '…')} {query.get('wavelength_unit', 'nm')}"
                )
                line_table = _build_nist_line_table(overlay)
                if line_table.empty:
                    st.info('No line details available for this selection.')
                else:
                    st.dataframe(line_table, use_container_width=True, hide_index=True)

    if st.button('Export what I see'):
        if not rows:
            st.warning('No traces selected for export.')
        else:
            ts = time.strftime('%Y%m%d-%H%M%S')
            png_path = exports / f'spectra_export_{ts}.png'
            csv_path = exports / f'spectra_export_{ts}.csv'
            man_path = exports / f'spectra_export_{ts}.manifest.json'
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            # Save PNG
            try:
                fig.write_image(str(png_path))
            except Exception as e:
                st.warning(f"PNG export requires kaleido. Error: {e}")
            # Manifest with version stamping
            manifest = {
                'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'viewport': None,
                'series': [],
                'global_units': {'wavelength': display_units, 'intensity_mode': display_mode},
                'software': {'name':'spectra-app', 'version': VI['version'], 'built_utc': VI['date_utc']},
                'notes': VI['summary']
            }
            for label in sorted({row['series'] for row in rows}):
                count = sum(1 for row in rows if row['series'] == label)
                manifest['series'].append({'label': label, 'points': count})
            man_path.write_text(json.dumps(manifest, indent=2))
            st.success(f'Exported: {png_path} / {csv_path} / {man_path}')

with tabs[1]:
    st.header('Differential (scaffold)')
    st.info('Wire your backlight and observed spectra here. This is a placeholder view.')

with tabs[2]:
    st.header('Docs')
    page = st.selectbox('Open doc', [
        'docs/index.md',
        'docs/ingestion.md',
        'docs/ui/displaying_data_guide.md',
        'docs/ui/ui_design_guide.md',
        'docs/ui/bad_ui_guide.md',
        'docs/sources/astro_data_docs.md',
        'docs/sources/telescopes_overview.md',
        'docs/sources/notable_sources_techniques_tools.md',
        'docs/sources/stellar_light_methods.md',
        'docs/math/spectroscopy_math_part1.md',
        'docs/math/spectroscopy_math_part2.md',
        'docs/math/instrument_accuracy_errors_interpretation.md',
        'docs/differential/part1b.md',
        'docs/differential/part1c.md',
        'docs/differential/part2.md',
        'docs/modeling/spectral_modeling_part1a.md',
    ])
    try:
        st.code(Path(page).read_text(encoding='utf-8'), language='markdown')
    except Exception as e:
        st.error(f"Failed to load doc {page}: {e}")
