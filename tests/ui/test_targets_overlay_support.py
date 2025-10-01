"""Tests for overlay eligibility in the targets panel."""

from app.ui.targets import _product_overlay_support


def test_spectrum_product_allows_overlay():
    product = {"dataproduct_type": "spectrum"}

    result = _product_overlay_support(product)

    assert result["supported"] is True
    assert result["note"] == ""


def test_timeseries_with_whitespace_allows_overlay():
    product = {"dataproduct_type": "  TimeSeries  "}

    result = _product_overlay_support(product)

    assert result["supported"] is True
    assert result["note"] == ""


def test_timeseries_with_time_axis_hints_allows_overlay():
    product = {
        "dataproduct_type": "timeseries",
        "extensions": [
            {
                "name": "LIGHTCURVE",
                "axes": [
                    {"name": "time"},
                    {"name": "flux"},
                ],
            }
        ],
    }

    result = _product_overlay_support(product)

    assert result["supported"] is True
    assert result["note"] == ""


def test_image_product_displays_annotation():
    product = {"dataproduct_type": "image"}

    result = _product_overlay_support(product)

    assert result["supported"] is False
    assert "Images" in result["note"]
    assert "1-D" in result["note"]


def test_missing_dataproduct_type_is_blocked():
    product = {}

    result = _product_overlay_support(product)

    assert result["supported"] is False
    assert "does not report" in result["note"]


def test_timeseries_without_time_axis_is_blocked():
    product = {
        "dataproduct_type": "timeseries",
        "extensions": [
            {
                "name": "SCI",
                "axes": [
                    {"name": "wavelength"},
                    {"name": "flux"},
                ],
            }
        ],
    }

    result = _product_overlay_support(product)

    assert result["supported"] is False
    assert "time axis" in result["note"]
    assert result["note"].startswith("Cannot overlay this product")


def test_jwst_calints_cube_is_blocked():
    product = {
        "dataproduct_type": "timeseries",
        "productFilename": "jw01234-o001_t001_miri_f1130w_calints.fits",
        "productSubGroupDescription": "CALINTS",
        "extensions": [
            {"naxis": 4, "axes": ["integration", "detector", "y", "x"]},
        ],
    }

    result = _product_overlay_support(product)

    assert result["supported"] is False
    assert "CALINTS" in result["note"]
    assert "1-D" in result["note"]
