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

SPECTRAL_OVERLAY_TYPES = {"spectrum", "sed"}
TIME_SERIES_TYPES = {"timeseries", "time-series", "time series"}

AXIS_SPECTRAL_KEYWORDS = {
    "wave",
    "wl",
    "lambda",
    "freq",
    "frequency",
    "energy",
    "wavenumber",
}

AXIS_TIME_KEYWORDS = {
    "time",
    "mjd",
    "bjd",
    "jd",
    "timedel",
}

CUBE_KEYWORDS = {
    "calint",
    "calints",
    "cube",
}


def _normalise_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _collect_axis_hints(product: Dict[str, Any]) -> Tuple[set[str], Optional[int]]:
    """Return axis keywords and the largest dimensionality hinted by extensions."""

    axis_hints: set[str] = set()
    max_dimensionality: Optional[int] = None

    extensions = product.get("extensions")
    if isinstance(extensions, list):
        for ext in extensions:
            if isinstance(ext, dict):
                axes = ext.get("axes")
                if isinstance(axes, list):
                    for axis in axes:
                        if isinstance(axis, dict):
                            for key in ("axis", "name", "type", "kind"):
                                val = axis.get(key)
                                if isinstance(val, str):
                                    axis_hints.add(val.lower())
                        elif isinstance(axis, str):
                            axis_hints.add(axis.lower())
                else:
                    for key in ("axis", "name", "type", "kind"):
                        val = ext.get(key)
                        if isinstance(val, str):
                            axis_hints.add(val.lower())

                axis_count = _safe_int(ext.get("naxis"))
                if axis_count is None:
                    dimensions = ext.get("dimensions") or ext.get("shape")
                    if isinstance(dimensions, (list, tuple)):
                        axis_count = len(dimensions)
                if axis_count is None and isinstance(axes, list):
                    axis_count = len(axes)

                if axis_count is not None:
                    if max_dimensionality is None or axis_count > max_dimensionality:
                        max_dimensionality = axis_count
            elif isinstance(ext, str):
                axis_hints.add(ext.lower())

    return axis_hints, max_dimensionality


def _summarise_reasons(reasons: List[str]) -> str:
    if not reasons:
        return ""
    if len(reasons) == 1:
        return reasons[0]
    return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"


def _has_axis_keyword(axis_hints: set[str], keywords: set[str]) -> bool:
    if not axis_hints:
        return False
    for hint in axis_hints:
        for keyword in keywords:
            if keyword in hint:
                return True
    return False


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

    raw_type = _normalise_text(product.get("dataproduct_type", "") or "")
    normalized = raw_type.lower()

    axis_hints, max_dimensionality = _collect_axis_hints(product)

    text_fields = [
        product.get("productType"),
        product.get("productSubGroupDescription"),
        product.get("productGroupDescription"),
        product.get("productFilename"),
        product.get("description"),
    ]
    text_blob = " ".join(filter(None, (_normalise_text(value) for value in text_fields))).lower()

    if normalized in SUPPORTED_OVERLAY_TYPES:
        reasons: List[str] = []

        if normalized in TIME_SERIES_TYPES and axis_hints and not _has_axis_keyword(
            axis_hints, AXIS_TIME_KEYWORDS
        ):
            reasons.append("its manifest extensions do not advertise a time axis")

        if normalized in SPECTRAL_OVERLAY_TYPES and axis_hints and not _has_axis_keyword(
            axis_hints, AXIS_SPECTRAL_KEYWORDS
        ):
            reasons.append("its manifest extensions do not advertise a spectral axis")

        if max_dimensionality and max_dimensionality > 2:
            reasons.append(
                f"the listed HDUs are {max_dimensionality}-D and overlay expects 1-D samples"
            )

        if normalized in TIME_SERIES_TYPES and any(
            keyword in text_blob for keyword in CUBE_KEYWORDS
        ):
            reasons.append(
                "JWST CALINTS integration cubes provide multi-dimensional stacks instead of 1-D time samples"
            )

        if reasons:
            reason_text = _summarise_reasons(reasons)
            note = (
                "Cannot overlay this product: "
                f"{reason_text}. "
                "Overlay is limited to 1-D spectra, SEDs, or time-series."
            )
            return {"supported": False, "normalized_type": normalized or None, "note": note}

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
        controls = expander.container()
        search_col, filter_col = controls.columns([2, 1])

        search_query = search_col.text_input(
            "Find a target",
            key="targets_search_query",
            placeholder="Search by name, spectral type, or tags",
        ).strip()
        require_curated = filter_col.checkbox(
            "Has curated MAST data",
            value=False,
            key="targets_filter_curated",
            help="Filter to targets with curated spectra and overlay-ready manifests.",
        )
        require_planets = filter_col.checkbox(
            "Has known planets",
            value=False,
            key="targets_filter_planets",
        )

        filtered = cat.copy()
        if search_query:
            lowered = search_query.lower()
            name_mask = filtered["name"].str.contains(lowered, case=False, na=False)
            sptype_mask = filtered["sptype"].fillna("").str.contains(
                lowered, case=False, na=False
            )
            summary_mask = filtered["summary"].fillna("").str.contains(
                lowered, case=False, na=False
            )
            combined_mask = name_mask | sptype_mask | summary_mask
            filtered = filtered[combined_mask]

        if require_curated:
            filtered = filtered[filtered["has_mast"]]

        if require_planets:
            filtered = filtered[filtered["n_planets"] > 0]

        if filtered.empty:
            controls.info("No targets match the current filters.")
            return

        sorted_names = filtered["name"].sort_values().tolist()
        name = search_col.selectbox(
            "Pick a target",
            options=sorted_names,
            key="targets_catalog_select",
        )
        if not name:
            return
        man_path = p / name.replace(" ", "_") / "manifest.json"
        if not man_path.exists():
            expander.error("Manifest missing for this target.")
            return
        manifest = json.loads(man_path.read_text())
        selected_row = filtered.loc[filtered["name"] == name].iloc[0]

        summary = manifest.get("summaries", {}).get("auto", "")
        summary_container = expander.container()
        summary_container.markdown(f"### {manifest['canonical_name']}")
        if summary:
            summary_container.info(summary)

        mast_summary = manifest.get("datasets", {}).get("mast_summary", {})
        mast_products, total_count, truncated = _extract_mast_products(manifest)
        curated_count = mast_summary.get("returned_count") or len(mast_products)
        total_obs = mast_summary.get("total_count")
        planet_value = selected_row.get("n_planets", 0)
        planet_count = 0 if pd.isna(planet_value) else int(planet_value)
        status_cols = summary_container.columns(3)
        status_cols[0].metric("Curated spectra", str(curated_count))
        status_cols[1].metric(
            "Total MAST hits", str(total_obs) if total_obs else "—"
        )
        status_cols[2].metric("Known planets", str(planet_count))

        flags = []
        flags.append("MAST ✓" if bool(selected_row.get("has_mast")) else "MAST ✗")
        flags.append("ESO ✓" if bool(selected_row.get("has_eso")) else "ESO ✗")
        flags.append(
            "CARMENES ✓" if bool(selected_row.get("has_carmenes")) else "CARMENES ✗"
        )
        coords = manifest.get("coordinates", {})
        coord_caption = []
        if coords:
            ra = coords.get("ra_deg")
            dec = coords.get("dec_deg")
            if ra is not None and dec is not None:
                coord_caption.append(f"RA {ra:.3f}° | Dec {dec:.3f}°")
        summary_container.caption(
            " • ".join(flags + coord_caption)
            if flags or coord_caption
            else "Target metadata unavailable."
        )
        if (
            mast_summary.get("truncated")
            and total_obs
            and curated_count is not None
            and curated_count < total_obs
        ):
            summary_container.caption(
                f"Showing {curated_count} curated MAST observations from {total_obs} total results."
            )

        catalog_view = expander.container()
        catalog_view.dataframe(
            filtered[["name", "sptype", "n_planets", "has_mast", "has_eso", "summary"]]
        )

        product_section = expander.container()
        if mast_products:
            product_section.subheader("Curated MAST spectra")
            product_intro, product_filters = product_section.columns([3, 2])
            collection_options = sorted(
                {
                    str(
                        r.get("obs_collection")
                        or r.get("instrument_name")
                        or r.get("project")
                        or "Curated selection"
                    ).strip()
                    or "Curated selection"
                    for r in mast_products
                }
            )
            selected_collection = product_filters.selectbox(
                "Filter by collection",
                options=["All collections"] + collection_options,
                key="targets_collection_filter",
            )

            display_products = mast_products
            if selected_collection != "All collections":
                display_products = [
                    r
                    for r in mast_products
                    if (
                        str(
                            r.get("obs_collection")
                            or r.get("instrument_name")
                            or r.get("project")
                            or "Curated selection"
                        ).strip()
                        or "Curated selection"
                    )
                    == selected_collection
                ]

            display_products = display_products[:200]
            enumerated_products = list(enumerate(display_products))
            grouped: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
            for idx, product in enumerated_products:
                group_name = (
                    str(
                        product.get("obs_collection")
                        or product.get("instrument_name")
                        or product.get("project")
                        or "Curated selection"
                    ).strip()
                    or "Curated selection"
                )
                grouped.setdefault(group_name, []).append((idx, product))

            for group_name in sorted(grouped):
                group_container = product_section.container()
                group_container.markdown(f"**{group_name}**")
                for idx, r in grouped[group_name]:
                    url = r.get("productURL") or ""
                    obsid = str(r.get("obsid", idx))
                    fname = str(r.get("productFilename", ""))
                    support = _product_overlay_support(r)
                    dtype = str(r.get("dataproduct_type", "")) or "unknown"
                    label = f"{fname} [{dtype}]"
                    cols = group_container.columns([3, 1])
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
                product_intro.caption(
                    f"Showing first {len(display_products)} of {total_count} MAST products."
                )
        else:
            product_section.info("No curated MAST spectra found for this target.")


# In your existing main.py, sidebar area:
# from app.ui.targets import render_targets_panel
# render_targets_panel("data_registry")
