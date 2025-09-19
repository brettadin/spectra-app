import streamlit as st
import plotly.graph_objects as go
import json, os, time
from pathlib import Path
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

tabs = st.tabs(['Overlay', 'Differential', 'Docs'])

with tabs[0]:
    st.header('Overlays')
    fig = go.Figure()
    traces = 0
    try:
        import pandas as pd
        if ex_toggle_he:
            df = pd.read_csv('app/examples/He.csv')
            fig.add_trace(go.Scatter(x=df['wavelength_nm'], y=df['intensity'], mode='lines+markers', name='He (example)'))
            traces += 1
        if ex_toggle_ne:
            df = pd.read_csv('app/examples/Ne.csv')
            fig.add_trace(go.Scatter(x=df['wavelength_nm'], y=df['intensity'], mode='lines+markers', name='Ne (example)'))
            traces += 1
    except Exception as e:
        st.error(f"Failed to load examples: {e}")
    fig.update_layout(xaxis_title='Wavelength (nm)', yaxis_title='Flux / Intensity', legend=dict(itemclick='toggleothers'))
    # Version watermark annotation for screenshots/PNGs
    fig.update_layout(annotations=[dict(text=f"{VI['version']}", xref="paper", yref="paper", x=0.99, y=-0.20, showarrow=False, font=dict(size=12), align="right", opacity=0.7)])
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Legend must have no empty labels.')

    if st.button('Export what I see'):
        ts = time.strftime('%Y%m%d-%H%M%S')
        png_path = exports / f'spectra_export_{ts}.png'
        csv_path = exports / f'spectra_export_{ts}.csv'
        man_path = exports / f'spectra_export_{ts}.manifest.json'
        # Save CSV of visible subset (examples only in this scaffold)
        rows = []
        import pandas as pd
        if ex_toggle_he:
            df = pd.read_csv('app/examples/He.csv')
            for w,fv in zip(df['wavelength_nm'], df['intensity']):
                rows.append({'series':'He (example)','wavelength_nm':w,'flux':fv})
        if ex_toggle_ne:
            df = pd.read_csv('app/examples/Ne.csv')
            for w,fv in zip(df['wavelength_nm'], df['intensity']):
                rows.append({'series':'Ne (example)','wavelength_nm':w,'flux':fv})
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
            'series': [{'label':'He (example)'} if ex_toggle_he else None, {'label':'Ne (example)'} if ex_toggle_ne else None],
            'global_units': {'wavelength':'nm'},
            'software': {'name':'spectra-app', 'version': VI['version'], 'built_utc': VI['date_utc']},
            'notes': VI['summary']
        }
        # Remove Nones from series
        manifest['series'] = [s for s in manifest['series'] if s]
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
