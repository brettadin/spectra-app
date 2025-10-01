# app/ui/targets.py  (new small component)
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from streamlit.delta_generator import DeltaGenerator


class RegistryUnavailableError(RuntimeError):
    """Raised when the target registry directory or catalog is missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


SUPPORTED_OVERLAY_TYPES = {
    "spectrum",
    "sed",
    "timeseries",
    "time-series",
    "time series",
}


def _extract_mast_products(
    manifest: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], int, bool]:
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


def _product_overlay_support(product: Dict[str, Any]) -> Dict[str, Any]:
    """Classify whether a MAST product should expose the Overlay action."""

    raw_type = str(product.get("dataproduct_type", "") or "").strip()
    normalized = raw_type.lower()

    if normalized in SUPPORTED_OVERLAY_TYPES:
        return {
            "supported": True,
            "normalized_type": normalized or None,
            "note": "",
        }

    if normalized in {"image", "cube"}:
        note = (
            "Images and cubes are 2-D products; overlay is limited to 1-D spectra, "
            "SEDs, or time-series."
        )
    elif normalized:
        note = (
            "Overlay is limited to 1-D spectra, SEDs, or time-series; "
            f"'{raw_type}' is not supported."
        )
    else:
        note = (
            "Overlay is limited to 1-D spectra, SEDs, or time-series; this entry "
            "does not report a dataproduct type."
        )

    return {"supported": False, "normalized_type": normalized or None, "note": note}


def render_targets_panel(
    registry_dir="data_registry",
    *,
    expanded: bool = False,
    sidebar: Optional[DeltaGenerator] = None,
):
    container = sidebar or st.sidebar
    p = Path(registry_dir)
    if not p.exists():
        raise RegistryUnavailableError(
            "No registry at data_registry/. Run build_registry.py first."
        )
    catalog_path = p / "catalog.csv"
    if not catalog_path.exists():
        raise RegistryUnavailableError(
            "No registry at data_registry/. Run build_registry.py first."
        )
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
            display_products = mast_products[:200]
            for idx, r in enumerate(display_products):
                url = r.get("productURL") or ""
                obsid = str(r.get("obsid", idx))
                fname = str(r.get("productFilename", ""))
                support = _product_overlay_support(r)
                dtype = str(r.get("dataproduct_type", "")) or "unknown"
                label = f"{fname} [{dtype}]"
                cols = expander.columns([3, 1])
                cols[0].code(label, language="text")
                btn_key = f"ov-{obsid}-{idx}"
                if support["supported"]:
                    if cols[1].button("Overlay", key=btn_key):
                        entry = {"url": url, "label": fname or f"product-{idx}"}
                        provider = str(
                            r.get("obs_collection") or r.get("provider") or ""
                        ).strip()
                        if provider:
                            entry["provider"] = provider
                        st.session_state.setdefault("ingest_queue", []).append(entry)
                else:
                    cols[1].button(
                        "Overlay",
                        key=btn_key,
                        disabled=True,
                        help=support["note"],
                    )
                    cols[1].caption(support["note"])
            if truncated or len(mast_products) > len(display_products):
                expander.caption(
                    f"Showing first {len(display_products)} of {total_count} MAST products."
                )
        else:
            expander.info("No curated MAST spectra found for this target.")


# In your existing main.py, sidebar area:
# from app.ui.targets import render_targets_panel
# render_targets_panel("data_registry")
