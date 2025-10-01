from __future__ import annotations

from dataclasses import dataclass

from app.providers import ProviderQuery
from app.ui import example_browser
from app.ui.main import ExampleSpec, _ensure_session_state, _load_example_preview, _register_example_usage, _toggle_example_favourite


@dataclass
class _StubHit:
    wavelengths_nm: tuple[float, float]
    flux: tuple[float, float]

    provider: str = "MAST"


def _build_example(slug: str, label: str, provider: str, description: str = "") -> ExampleSpec:
    return ExampleSpec(
        slug=slug,
        label=label,
        description=description,
        provider=provider,
        query=ProviderQuery(target=label, instrument="STIS", limit=1),
    )


def test_filter_examples_supports_search_and_favourites():
    spec_a = _build_example("vega", "Vega", "MAST", "Bright standard")
    spec_b = _build_example("betel", "Betelgeuse", "ESO", "Red supergiant")

    # Search filters down to matching term in description/label.
    results = example_browser.filter_examples(
        [spec_a, spec_b], search="bright", providers=["MAST", "ESO"], favourites_only=False, favourites=[]
    )
    assert results == [spec_a]

    # Provider filter narrows to ESO only.
    results = example_browser.filter_examples(
        [spec_a, spec_b], search="", providers=["ESO"], favourites_only=False, favourites=[]
    )
    assert results == [spec_b]

    # Favourites only restricts to starred examples regardless of provider.
    results = example_browser.filter_examples(
        [spec_a, spec_b], search="", providers=["MAST", "ESO"], favourites_only=True, favourites=["betel"]
    )
    assert results == [spec_b]


def test_normalise_provider_defaults_filters_stale_entries():
    options = ["MAST", "ESO", "NED"]
    stored = ["ESO", "HST", "ESO"]

    defaults = example_browser._normalise_provider_defaults(options, stored)

    assert defaults == ["ESO"]


def test_normalise_provider_defaults_falls_back_to_all_when_empty():
    options = ["MAST", "ESO"]

    defaults = example_browser._normalise_provider_defaults(options, [])

    assert defaults == options


def test_register_example_usage_tracks_recent(monkeypatch):
    import app.ui.main as main

    monkeypatch.setattr(main.st, "session_state", {}, raising=False)
    specs = [_build_example(f"slug-{idx}", f"Spec {idx}", "MAST") for idx in range(6)]
    for spec in specs:
        _register_example_usage(spec, success=True)

    assert main.st.session_state["example_recent"] == [
        "slug-5",
        "slug-4",
        "slug-3",
        "slug-2",
        "slug-1",
    ]

    # Loading an existing recent bumps it to the front without duplication.
    _register_example_usage(specs[3], success=True)
    assert main.st.session_state["example_recent"][0] == "slug-3"
    assert main.st.session_state["example_recent"].count("slug-3") == 1


def test_toggle_example_favourite_updates_list(monkeypatch):
    import app.ui.main as main

    monkeypatch.setattr(main.st, "session_state", {"example_favourites": []}, raising=False)

    _toggle_example_favourite("alpha", True)
    assert main.st.session_state["example_favourites"] == ["alpha"]

    _toggle_example_favourite("alpha", False)
    assert main.st.session_state["example_favourites"] == []


def test_load_example_preview_uses_cache(monkeypatch):
    import app.ui.main as main

    spec = _build_example("preview", "Preview", "MAST")
    stub_hit = _StubHit(wavelengths_nm=(400.0, 410.0), flux=(1.0, 0.5))
    calls = {"count": 0}

    def fake_search(provider, query):
        calls["count"] += 1
        return [stub_hit]

    monkeypatch.setattr(main, "provider_search", fake_search)
    monkeypatch.setattr(main.st, "session_state", {}, raising=False)

    preview = _load_example_preview(spec, allow_network=True)
    assert preview is not None
    assert calls["count"] == 1

    cached = _load_example_preview(spec, allow_network=False)
    assert cached is not None
    assert calls["count"] == 1
    assert cached.wavelengths == preview.wavelengths


def test_ensure_session_state_defaults(monkeypatch):
    import app.ui.main as main

    class _LedgerStub:
        def __init__(self):
            pass

    monkeypatch.setattr(main, "DuplicateLedger", lambda: _LedgerStub())

    class _CacheStub:
        pass

    monkeypatch.setattr(main, "SimilarityCache", lambda: _CacheStub())
    monkeypatch.setattr(main.st, "session_state", {}, raising=False)

    _ensure_session_state()

    state = main.st.session_state
    assert state["duplicate_policy"] == "skip"
    assert state["network_available"] is True
    assert state["example_recent"] == []
    assert state["example_favourites"] == []
