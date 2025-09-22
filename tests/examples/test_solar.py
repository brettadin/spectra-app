import pandas as pd
import pytest

from app.examples import solar


@pytest.fixture()
def raw_frame() -> pd.DataFrame:
    return solar.load_frame(kind="raw")


@pytest.fixture()
def smoothed_frame() -> pd.DataFrame:
    return solar.load_frame(kind="smoothed")


def test_available_bands_includes_full():
    bands = solar.available_bands()
    assert bands[0] == "full"
    assert set(bands[1:]) == {"uv", "uv-vis", "vis", "nir", "ir"}


def test_raw_frame_includes_hover(raw_frame: pd.DataFrame) -> None:
    assert "hover" in raw_frame.columns
    assert any(isinstance(text, str) and text for text in raw_frame["hover"])


def test_smoothed_frame_suppresses_hover(smoothed_frame: pd.DataFrame) -> None:
    assert "hover" not in smoothed_frame.columns


@pytest.mark.parametrize("band", ["uv", "uv-vis", "vis", "nir", "ir"])
def test_band_filtering_matches_band_labels(raw_frame: pd.DataFrame, band: str) -> None:
    filtered = solar.load_frame(kind="raw", band=band)
    assert not filtered.empty
    assert set(filtered["band"]) == {band}
    # every filtered wavelength should also appear in the full dataset with the same band
    merged = pd.merge(
        filtered[["wavelength_nm", "band"]],
        raw_frame[["wavelength_nm", "band"]],
        on="wavelength_nm",
        suffixes=("_filtered", "_full"),
    )
    assert (merged["band_filtered"] == merged["band_full"]).all()


def test_load_payload_respects_hover_suppression() -> None:
    raw_payload = solar.load_payload(kind="raw", band="vis")
    assert isinstance(raw_payload["hover"], list)
    assert len(raw_payload["hover"]) == len(raw_payload["wavelength_nm"])
    smoothed_payload = solar.load_payload(kind="smoothed", band="vis")
    assert smoothed_payload["hover"] is None


def test_load_payload_metadata_fields() -> None:
    payload = solar.load_payload(kind="raw", band="uv")
    metadata = payload["metadata"]
    assert metadata["example_slug"] == "solar-irradiance"
    assert metadata["example_kind"] == "raw"
    assert metadata["solar_band"] == "uv"
    assert metadata["data_points"] == len(payload["wavelength_nm"])
    provenance = payload["provenance"]
    assert provenance["source"].startswith("ASTM G173")
    assert provenance["url"].startswith("https://")
