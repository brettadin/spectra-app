from app.ui.main import OverlayTrace, _build_overlay_figure


def test_overlay_without_hover_uses_default_hover_fields():
    overlay = OverlayTrace(
        trace_id="test",
        label="Spectrum",
        wavelength_nm=(500.0, 600.0),
        flux=(1.0, 2.0),
    )

    fig, _ = _build_overlay_figure(
        overlays=[overlay],
        display_units="nm",
        display_mode="Flux (raw)",
        normalization_mode="none",
        viewport=(None, None),
        reference=None,
        differential_mode="Off",
        version_tag="vtest",
    )

    assert len(fig.data) == 1
    trace = fig.data[0]

    assert trace.hoverinfo is None
    assert trace.hovertext is None

    assert list(trace.x) == [500.0, 600.0]
    assert list(trace.y) == [1.0, 2.0]
