import pytest

from app.ui.main import _normalise_display_unit_hint, _preferred_display_unit


@pytest.mark.parametrize(
    "value, expected",
    [
        ("cm^-1", "cm^-1"),
        ("1/CM", "cm^-1"),
        ("Wavenumbers", "cm^-1"),
        ("micrometers", "µm"),
        ("μm", "µm"),
        ("µm", "µm"),
        ("angstroms", "Å"),
        ("Å", "Å"),
        ("nanometers", "nm"),
        (None, None),
        ("", None),
    ],
)
def test_normalise_display_unit_hint(value, expected):
    assert _normalise_display_unit_hint(value) == expected


def test_preferred_display_unit_prioritises_original_non_nm():
    metadata = {"original_wavelength_unit": "cm^-1"}
    assert _preferred_display_unit(metadata, {}) == "cm^-1"


def test_preferred_display_unit_falls_back_to_reported():
    metadata = {"reported_wavelength_unit": "Micrometers"}
    assert _preferred_display_unit(metadata, {}) == "µm"


def test_preferred_display_unit_uses_provenance_units():
    provenance = {"units": {"wavelength_original": "Angstroms"}}
    assert _preferred_display_unit({}, provenance) == "Å"


def test_preferred_display_unit_ignores_nm():
    metadata = {"original_wavelength_unit": "nm"}
    assert _preferred_display_unit(metadata, {}) is None
