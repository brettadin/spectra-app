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
