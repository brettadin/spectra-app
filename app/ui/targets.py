# app/ui/targets.py  (new small component)
import json, pandas as pd, streamlit as st
from pathlib import Path

def render_targets_panel(registry_dir="data_registry"):
    p = Path(registry_dir)
    if not p.exists():
        st.warning("No registry at data_registry/. Run build_registry.py first.")
        return
    catalog_path = p / "catalog.csv"
    if not catalog_path.exists():
        st.warning("No registry at data_registry/. Run build_registry.py first.")
        return
    cat = pd.read_csv(catalog_path)
    with st.expander("Target catalog", expanded=True):
        st.dataframe(cat[["name","sptype","n_planets","has_mast","has_eso","summary"]])

    name = st.selectbox("Pick a target", sorted(cat["name"].tolist()))
    if not name:
        return
    man_path = p / name.replace(" ","_") / "manifest.json"
    if not man_path.exists():
        st.error("Manifest missing for this target.")
        return
    manifest = json.loads(man_path.read_text())
    st.markdown(f"**{manifest['canonical_name']}** — {manifest['summaries']['auto']}")
    # Show MAST products with quick-add buttons
    mast_products = manifest.get("datasets",{}).get("mast_products", [])
    if mast_products:
        st.subheader("MAST spectra")
        for r in mast_products[:200]:  # don’t explode UI
            url = r.get("productURL") or ""
            label = f"{r.get('productFilename','')} [{r.get('dataproduct_type','')}]"
            cols = st.columns([3,1])
            cols[0].code(label, language="text")
            if cols[1].button("Overlay", key=f"ov-{label}"):
                # your app’s existing overlay fetcher likely accepts URLs/paths;
                # dispatch an event or stash URL in session to be ingested
                st.session_state.setdefault("ingest_queue", []).append(url)
    else:
        st.info("No curated MAST spectra found for this target.")

# In your existing main.py, sidebar area:
# from app.ui.targets import render_targets_panel
# render_targets_panel("data_registry")
