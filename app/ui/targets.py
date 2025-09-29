# app/ui/targets.py  (new small component)
import json, pandas as pd, streamlit as st
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from streamlit.delta_generator import DeltaGenerator


def _extract_mast_products(manifest: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int, bool]:
    datasets = manifest.get("datasets", {}) if isinstance(manifest, dict) else {}
    mast_products = datasets.get("mast_products", [])

    if isinstance(mast_products, dict):
        items = list(mast_products.get("items", []))
        total = int(mast_products.get("total_count", len(items) or 0))
        truncated = bool(mast_products.get("truncated", total > len(items)))
        return items, total, truncated

    items = list(mast_products)
    total = len(items)
    return items, total, False


def render_targets_panel(
    registry_dir="data_registry",
    *,
    expanded: bool = False,
    sidebar: Optional[DeltaGenerator] = None,
):
    container = sidebar or st.sidebar
    p = Path(registry_dir)
    if not p.exists():
        container.warning("No registry at data_registry/. Run build_registry.py first.")
        return
    catalog_path = p / "catalog.csv"
    if not catalog_path.exists():
        container.warning("No registry at data_registry/. Run build_registry.py first.")
        return
    cat = pd.read_csv(catalog_path)
    expander = container.expander("Target catalog", expanded=expanded)
    with expander:
        expander.dataframe(
            cat[["name", "sptype", "n_planets", "has_mast", "has_eso", "summary"]]
        )

        name = expander.selectbox("Pick a target", sorted(cat["name"].tolist()))
        if not name:
            return
        man_path = p / name.replace(" ", "_") / "manifest.json"
        if not man_path.exists():
            expander.error("Manifest missing for this target.")
            return
        manifest = json.loads(man_path.read_text())
        summary = manifest.get("summaries", {}).get("auto", "")
        expander.markdown(f"**{manifest['canonical_name']}** — {summary}")
        mast_summary = manifest.get("datasets", {}).get("mast_summary", {})
        if mast_summary:
            total_obs = mast_summary.get("total_count")
            returned_obs = mast_summary.get("returned_count")
            if mast_summary.get("truncated") and total_obs and returned_obs is not None:
                expander.caption(
                    f"Showing {returned_obs} curated MAST observations from {total_obs} total results."
                )
        # Show MAST products with quick-add buttons
        mast_products, total_count, truncated = _extract_mast_products(manifest)
        if mast_products:
            expander.subheader("MAST spectra")
            for r in mast_products:
                url = r.get("productURL") or ""
                label = (
                    f"{r.get('productFilename','')} [{r.get('dataproduct_type','')}]"
                )
                cols = expander.columns([3, 1])
                cols[0].code(label, language="text")
                if cols[1].button("Overlay", key=f"ov-{label}"):
                    # your app’s existing overlay fetcher likely accepts URLs/paths;
                    # dispatch an event or stash URL in session to be ingested
                    st.session_state.setdefault("ingest_queue", []).append(url)
            if truncated:
                expander.caption(
                    f"Showing first {len(mast_products)} of {total_count} MAST products."
                )
        else:
            expander.info("No curated MAST spectra found for this target.")

# In your existing main.py, sidebar area:
# from app.ui.targets import render_targets_panel
# render_targets_panel("data_registry")
