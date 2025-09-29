from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go
import streamlit as st

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from app.ui.main import ExampleSpec


@dataclass(frozen=True)
class ExamplePreview:
    wavelengths: Tuple[float, ...]
    flux: Tuple[float, ...]


def _sparkline(preview: ExamplePreview) -> go.Figure:
    wavelengths = np.asarray(preview.wavelengths, dtype=float)
    flux = np.asarray(preview.flux, dtype=float)
    if wavelengths.size == 0 or flux.size == 0:
        wavelengths = np.array([0.0, 1.0])
        flux = np.array([0.0, 0.0])
    if flux.size == 0 or np.allclose(flux, flux[0]):
        flux = np.full_like(flux, 0.5)
    else:
        flux_min = float(np.min(flux))
        flux_max = float(np.max(flux))
        if not np.isfinite(flux_min) or not np.isfinite(flux_max):
            flux = np.clip(flux, -1.0, 1.0)
            flux_min = float(np.min(flux))
            flux_max = float(np.max(flux))
        span = flux_max - flux_min
        if span <= 0:
            flux = np.full_like(flux, 0.5)
        else:
            flux = (flux - flux_min) / span

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=wavelengths,
            y=flux,
            mode="lines",
            line={"color": "#5B8FF9", "width": 2},
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=4, b=4),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=120,
    )
    return fig


def filter_examples(
    examples: Sequence["ExampleSpec"],
    *,
    search: str = "",
    providers: Optional[Sequence[str]] = None,
    favourites_only: bool = False,
    favourites: Sequence[str] | None = None,
) -> List["ExampleSpec"]:
    favourites_set = set(favourites or [])
    provider_set = set(providers or [])
    terms = [term for term in search.lower().split() if term]
    results: List["ExampleSpec"] = []
    for spec in examples:
        if providers is not None:
            if not provider_set:
                continue
            if spec.provider not in provider_set:
                continue
        if favourites_only and spec.slug not in favourites_set:
            continue
        if not terms:
            matches_terms = True
        else:
            haystack_parts: List[str] = [
                spec.slug,
                spec.label,
                spec.description,
                spec.provider,
            ]
            query = getattr(spec, "query", None)
            if query is not None:
                try:
                    payload = query.as_dict()
                except AttributeError:
                    payload = {}
                for value in payload.values():
                    if value is None:
                        continue
                    if isinstance(value, (list, tuple)):
                        haystack_parts.extend(str(item) for item in value)
                    else:
                        haystack_parts.append(str(value))
            haystack = " ".join(part for part in haystack_parts if part).lower()
            matches_terms = all(term in haystack for term in terms)
        if matches_terms:
            results.append(spec)
    return results


def render_example_browser_sheet(
    *,
    examples: Sequence["ExampleSpec"],
    visible: bool,
    favourites: Sequence[str],
    recents: Sequence[str],
    load_callback: Callable[["ExampleSpec"], Tuple[bool, str]],
    toggle_favourite: Callable[[str, bool], None],
    preview_loader: Callable[["ExampleSpec"], Optional[ExamplePreview]],
    resolve_spec: Callable[[str], Optional["ExampleSpec"]],
    network_available: bool,
) -> None:
    if not visible:
        return

    favourites_set = set(favourites)
    recent_order: Dict[str, int] = {slug: index for index, slug in enumerate(recents)}

    sheet = st.container(border=True)
    with sheet:
        if not examples:
            st.info("Example library is empty.")
            if st.button("Close", key="example_browser_close_empty"):
                st.session_state["example_browser_visible"] = False
            return

        header_cols = st.columns([4, 1])
        header_cols[0].subheader("Example browser")
        if header_cols[1].button("Close", key="example_browser_close"):
            st.session_state["example_browser_active_detail"] = None
            st.session_state["example_browser_visible"] = False
            return

        if not network_available:
            st.caption("Using local cache")

        provider_options = sorted({spec.provider for spec in examples})
        st.session_state.setdefault("example_browser_search", "")
        stored_providers = [
            provider
            for provider in st.session_state.get(
                "example_browser_provider_filter", provider_options
            )
            if provider in provider_options
        ]
        if not stored_providers:
            stored_providers = provider_options
        st.session_state["example_browser_provider_filter"] = stored_providers
        st.session_state.setdefault("example_browser_favourites_only", False)

        search_value = st.text_input(
            "Search examples",
            value=st.session_state["example_browser_search"],
            key="example_browser_search",
            help="Filter by label, description, provider, or query metadata.",
        )
        selected_providers = st.multiselect(
            "Providers",
            provider_options,
            default=stored_providers,
            key="example_browser_provider_filter",
        )
        favourites_only = st.checkbox(
            "Show favourites only",
            value=st.session_state["example_browser_favourites_only"],
            key="example_browser_favourites_only",
        )

        filtered = filter_examples(
            examples,
            search=search_value,
            providers=selected_providers,
            favourites_only=favourites_only,
            favourites=favourites,
        )

        if recents:
            labels = []
            for slug in recents:
                spec = resolve_spec(slug)
                if spec:
                    labels.append(spec.label)
            if labels:
                st.caption("Recent: " + ", ".join(labels[:5]))

        def sort_key(spec: "ExampleSpec") -> Tuple[int, int, str]:
            favourite_rank = 0 if spec.slug in favourites_set else 1
            recent_rank = recent_order.get(spec.slug, len(recent_order))
            return (favourite_rank, recent_rank, spec.label.lower())

        filtered.sort(key=sort_key)

        if not filtered:
            st.info("No examples match the current filters.")

        detail_slug = st.session_state.get("example_browser_active_detail")

        for spec in filtered:
            card = st.container(border=True)
            with card:
                st.markdown(f"**{spec.label}**")
                st.caption(f"Provider: {spec.provider}")
                if spec.description:
                    st.caption(spec.description)
                preview = preview_loader(spec)
                if preview:
                    st.plotly_chart(
                        _sparkline(preview),
                        width="stretch",
                        config={"displayModeBar": False},
                    )
                elif not network_available:
                    st.caption(
                        "Preview unavailable offline; load to fetch cached data."
                    )
                else:
                    st.caption("Preview unavailable; load to fetch data.")

                button_cols = st.columns(3)
                if button_cols[0].button(
                    "Load example", key=f"example_browser_load_{spec.slug}"
                ):
                    added, message = load_callback(spec)
                    (st.success if added else st.info)(message)
                if button_cols[1].button(
                    "View details", key=f"example_browser_details_{spec.slug}"
                ):
                    st.session_state["example_browser_active_detail"] = spec.slug
                    detail_slug = spec.slug
                favourite_label = (
                    "★ Favourited" if spec.slug in favourites_set else "☆ Favourite"
                )
                if button_cols[2].button(
                    favourite_label, key=f"example_browser_favourite_{spec.slug}"
                ):
                    desired = spec.slug not in favourites_set
                    toggle_favourite(spec.slug, desired)
                    if desired:
                        st.success(f"Added {spec.label} to favourites.")
                        favourites_set.add(spec.slug)
                    else:
                        st.info(f"Removed {spec.label} from favourites.")
                        favourites_set.discard(spec.slug)

        if detail_slug:
            detail_spec = resolve_spec(detail_slug)
            if detail_spec:
                st.divider()
                st.markdown(f"### {detail_spec.label}")
                if detail_spec.description:
                    st.caption(detail_spec.description)
                if getattr(detail_spec, "query", None) is not None:
                    try:
                        query_payload = detail_spec.query.as_dict()
                    except AttributeError:
                        query_payload = {}
                    st.json(query_payload)
            else:
                st.session_state["example_browser_active_detail"] = None
