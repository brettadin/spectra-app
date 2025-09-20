from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app._version import get_version_info

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


with tabs[0]:
    st.header('Overlays')
    fig = go.Figure()
    axis_title = 'Wavelength (nm)'
    rows = []

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

    fig.update_layout(
        xaxis_title=axis_title,
        yaxis_title='Normalized intensity' if display_mode == 'Flux (normalized)' else 'Flux / Intensity',
        legend=dict(itemclick='toggleothers')
    )
    # Version watermark annotation for screenshots/PNGs
    fig.update_layout(annotations=[dict(text=f"{VI['version']}", xref="paper", yref="paper", x=0.99, y=-0.20, showarrow=False, font=dict(size=12), align="right", opacity=0.7)])
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Legend must have no empty labels.')

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
