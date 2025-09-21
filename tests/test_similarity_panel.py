from __future__ import annotations

import numpy as np

from app import similarity_panel
from app.similarity import SimilarityCache, SimilarityOptions, TraceVectors


class _FakeColumn:
    def markdown(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None

    def metric(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None

    def caption(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None


class _FakeTab:
    def __enter__(self):  # noqa: D401 - context manager protocol
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: D401 - context manager protocol
        return False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.stylers = []

    def info(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None

    def warning(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None

    def markdown(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None

    def columns(self, count):  # noqa: D401 - simple no-op helper
        return [_FakeColumn() for _ in range(count)]

    def tabs(self, labels):  # noqa: D401 - simple no-op helper
        return [_FakeTab() for _ in labels]

    def dataframe(self, styled, **kwargs):  # noqa: D401 - capture the rendered styler
        self.stylers.append(styled)

    def caption(self, *args, **kwargs):  # noqa: D401 - simple no-op helper
        return None


def test_render_similarity_panel_handles_duplicate_labels(monkeypatch):
    traces = [
        TraceVectors(
            trace_id="trace-1",
            label="Duplicate",
            wavelengths_nm=np.array([400.0, 500.0]),
            flux=np.array([1.0, 2.0]),
        ),
        TraceVectors(
            trace_id="trace-2",
            label="Duplicate",
            wavelengths_nm=np.array([400.0, 500.0]),
            flux=np.array([1.2, 2.2]),
        ),
    ]
    options = SimilarityOptions(metrics=("cosine",), normalization="unit", primary_metric="cosine")
    cache = SimilarityCache()
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(similarity_panel, "st", fake_st)

    frames = similarity_panel.render_similarity_panel(traces, (None, None), options, cache)

    assert "cosine" in frames
    frame = frames["cosine"]
    assert list(frame.index) == ["trace-1", "trace-2"]
    assert list(frame.columns) == ["trace-1", "trace-2"]
    assert fake_st.stylers, "Expected render to emit at least one dataframe"
    styled = fake_st.stylers[0]
    assert styled.data.columns.is_unique
    assert styled.data.index.is_unique
    assert styled.data.columns.tolist() == ["Duplicate", "Duplicate (2)"]
