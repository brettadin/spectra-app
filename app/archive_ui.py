from __future__ import annotations

"""Archive tab controller that bridges provider adapters with the overlay UI."""

from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple

import plotly.graph_objects as go
import streamlit as st

from app.providers import ProviderHit, ProviderQuery, provider_labels, search as provider_search

AddOverlayFn = Callable[[Dict[str, object]], Tuple[bool, str]]


@dataclass
class ArchiveUI:
    """Render archive providers and push selections into session state."""

    add_overlay: AddOverlayFn

    def render(self) -> None:
        st.subheader("Archive lookups")
        st.caption(
            "Query public archives or DOI references and push results into the overlay "
            "workspace. Synthetic samples stand in for real responses until adapters are wired."
        )
        labels = provider_labels()
        tabs = st.tabs([labels[name] for name in ("MAST", "ESO", "SDSS", "DOI")])
        for provider_name, tab in zip(("MAST", "ESO", "SDSS", "DOI"), tabs):
            with tab:
                self._render_provider(provider_name)

    # ------------------------------------------------------------------
    def _results_key(self, provider: str) -> str:
        return f"archive_results_{provider.lower()}"

    def _render_provider(self, provider: str) -> None:
        query_key = f"archive_query_{provider.lower()}"
        default_query = st.session_state.get(query_key, {})
        with st.form(f"{provider}_search_form"):
            if provider == "DOI":
                doi_value = st.text_input("DOI", value=default_query.get("doi", ""), help="Enter a DOI or literature identifier.")
                text_value = st.text_input("Title/label", value=default_query.get("text", ""))
                limit = 1
                submit = st.form_submit_button("Resolve DOI")
                query = ProviderQuery(doi=doi_value.strip(), text=text_value.strip(), limit=limit)
            else:
                target = st.text_input("Target", value=default_query.get("target", ""))
                instrument = st.text_input("Instrument", value=default_query.get("instrument", ""))
                limit = st.slider("Max results", min_value=1, max_value=5, value=int(default_query.get("limit", 3)))
                submit = st.form_submit_button("Search")
                query = ProviderQuery(target=target.strip(), instrument=instrument.strip(), limit=limit)
            if submit:
                st.session_state[query_key] = query.as_dict()
                try:
                    hits = provider_search(provider, query)
                except Exception as exc:  # pragma: no cover - defensive UI branch
                    st.error(f"{provider} search failed: {exc}")
                    hits = []
                st.session_state[self._results_key(provider)] = hits

        hits = st.session_state.get(self._results_key(provider), [])
        if not hits:
            st.info("Run a search to see results.")
            return

        summary_df = self._build_summary(hits)
        if not summary_df.empty:
            st.dataframe(summary_df, width="stretch", hide_index=True)

        for idx, hit in enumerate(hits):
            exp_label = f"{hit.label} — {hit.summary}"
            with st.expander(exp_label, expanded=(idx == 0)):
                df = hit.to_dataframe().head(200)
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df["wavelength_nm"],
                        y=df["flux"],
                        mode="lines",
                        name=hit.label,
                    )
                )
                fig.update_layout(
                    xaxis_title="Wavelength (nm)",
                    yaxis_title="Flux",
                    height=260,
                    margin=dict(t=20, b=20, l=40, r=10),
                )
                st.plotly_chart(fig, width="stretch")
                st.caption(hit.summary)
                cols = st.columns(2)
                with cols[0]:
                    st.write("**Metadata**")
                    st.json(dict(hit.metadata))
                with cols[1]:
                    st.write("**Provenance**")
                    st.json(dict(hit.provenance))

                if st.button(f"Add to overlay", key=f"add_{provider}_{idx}"):
                    added, message = self.add_overlay(hit.to_overlay_payload())
                    if added:
                        st.success(message)
                    else:
                        st.warning(message)

    # ------------------------------------------------------------------
    @staticmethod
    def _build_summary(hits: Sequence[ProviderHit]):
        from app.providers.base import summarise_hits

        return summarise_hits(hits)
