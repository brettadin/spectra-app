import numpy as np
import pytest
from astropy import units as u

from app.server.fetchers import nist_quant_ir


def test_parse_catalog_extracts_species_and_resolutions():
    html = """
    <table class="list">
      <tr>
        <th>Species</th><th>Relative</th><th>Apodization</th><th>Resolution</th>
      </tr>
      <tr>
        <td rowspan="2">Benzene</td>
        <td rowspan="2">2.1 %</td>
        <td>Boxcar</td>
        <td>
          <a href="../../cgi/cbook.cgi?ID=71-43-2&amp;Type=IR-SPEC&amp;Index=QUANT-IR,4#IR-SPEC">0.125</a>
          <a href="../../cgi/cbook.cgi?ID=71-43-2&amp;Type=IR-SPEC&amp;Index=QUANT-IR,3#IR-SPEC">0.25</a>
        </td>
      </tr>
      <tr>
        <td>Triangular</td>
        <td>
          <a href="../../cgi/cbook.cgi?ID=71-43-2&amp;Type=IR-SPEC&amp;Index=QUANT-IR,9#IR-SPEC">0.125</a>
        </td>
      </tr>
      <tr>
        <td rowspan="1">Toluene</td>
        <td rowspan="1">2.0 %</td>
        <td>Boxcar</td>
        <td>
          <a href="../../cgi/cbook.cgi?ID=108-88-3&amp;Type=IR-SPEC&amp;Index=QUANT-IR,4#IR-SPEC">0.125</a>
        </td>
      </tr>
    </table>
    """
    catalog = nist_quant_ir._parse_catalog(html)
    assert "benzene" in catalog
    benzene = catalog["benzene"]
    assert benzene.name == "Benzene"
    assert benzene.relative_uncertainty == "2.1 %"
    assert len(benzene.measurements) == 2
    first_measurement = benzene.measurements[0]
    assert first_measurement.apodization == "Boxcar"
    assert 0.125 in first_measurement.resolution_links
    assert first_measurement.resolution_links[0.125].startswith(
        "https://webbook.nist.gov/cgi/cbook.cgi?ID=71-43-2"
    )
    assert "toluene" in catalog


def test_extract_jcamp_url_returns_absolute_path():
    page_html = """
    <html>
      <body>
        <script>
          display_jcamp('/cgi/cbook.cgi?JCAMP=C71432&amp;Index=7&amp;Type=IR', null, 'jcamp-plot', 400, function () {});
        </script>
      </body>
    </html>
    """
    page_url = "https://webbook.nist.gov/cgi/cbook.cgi?ID=71-43-2&Type=IR-SPEC&Index=QUANT-IR,4#IR-SPEC"
    result = nist_quant_ir._extract_jcamp_url(page_html, page_url)
    assert (
        result
        == "https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C71432&Index=7&Type=IR"
    )


def test_choose_measurement_prefers_priority_apodization():
    species = nist_quant_ir.QuantIRSpecies(
        name="Benzene",
        relative_uncertainty="2.1 %",
        measurements=(
            nist_quant_ir.QuantIRMeasurement(
                apodization="Triangular",
                resolution_links={0.125: "https://example.invalid/tri"},
            ),
            nist_quant_ir.QuantIRMeasurement(
                apodization="Boxcar",
                resolution_links={0.125: "https://example.invalid/box"},
            ),
        ),
    )
    measurement, resolution, href = nist_quant_ir._choose_measurement(
        species,
        resolution_cm_1=0.125,
        priority=("Boxcar", "Triangular"),
    )
    assert resolution == pytest.approx(0.125)
    assert measurement.apodization == "Boxcar"
    assert href == "https://example.invalid/box"


def test_manual_species_catalog_includes_requested_entries():
    manual_catalog = nist_quant_ir.manual_species_catalog()
    expected_names = [
        "Water",
        "Methane",
        "Carbon Dioxide",
        "Benzene",
        "Ethylene",
        "Acetone",
        "Ethanol",
        "Methanol",
        "2-Propanol",
        "Ethyl Acetate",
        "1-Butanol",
        "Sulfur Hexafluoride",
        "Acetonitrile",
        "Acrylonitrile",
        "Sulfur Dioxide",
        "Carbon Tetrachloride",
        "Butane",
        "Ethylbenzene",
    ]
    for name in expected_names:
        token = nist_quant_ir._normalise_token(name)
        assert token in manual_catalog, f"missing manual record for {name}"

    water = manual_catalog[nist_quant_ir._normalise_token("Water")]
    measurement = water.measurements[0]
    link = measurement.resolution_links[nist_quant_ir.DEFAULT_RESOLUTION_CM_1]
    assert link.startswith("https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C7732185")


def test_extract_delta_x_parses_numeric_value():
    assert nist_quant_ir._extract_delta_x(b"##DELTAX=0.125\n") == pytest.approx(0.125)
    assert nist_quant_ir._extract_delta_x(b"##TITLE=Test") is None


def test_resample_manual_payload_interpolates_to_target_resolution():
    wavenumbers = np.arange(450.0, 462.0, 4.0)
    wavelengths_nm = (1e7 / wavenumbers).tolist()
    flux = np.linspace(0.0, 1.0, len(wavelengths_nm)).tolist()

    class DummyQuantity:
        def __init__(self, unit: float):
            self.unit = unit

    payload = {
        "wavelength_nm": list(wavelengths_nm),
        "flux": list(flux),
        "wavelength": {"values": list(wavelengths_nm)},
        "wavelength_quantity": DummyQuantity(1.0),
    }

    original_step = nist_quant_ir._resample_manual_payload(
        payload, target_resolution=0.5
    )
    assert original_step == pytest.approx(4.0)
    resampled_wavenumbers = np.sort(1e7 / np.asarray(payload["wavelength_nm"]))
    diffs = np.diff(resampled_wavenumbers)
    assert np.allclose(diffs, 0.5, rtol=1e-3, atol=1e-6)


def test_prepare_flux_converts_coefficients_to_percent_transmittance():
    payload = {
        "flux": [0.0, 0.5, 1.0],
        "downsample": {
            64: {"wavelength_nm": [1.0, 2.0, 3.0], "flux": [0.0, 0.5, 1.0]}
        },
        "metadata": {
            "reported_flux_unit": "(micromol/mol)-1m-1 (base 10)",
            "pressure": "101.3 Pa",
        },
        "provenance": {},
        "axis": "emission",
        "flux_unit": "(micromol/mol)-1m-1 (base 10)",
    }

    nist_quant_ir._prepare_flux(payload, manual_entry=False)

    mixing_ratio = nist_quant_ir._infer_mixing_ratio({"pressure": "101.3 Pa"})
    expected_fraction = (
        np.power(
            10.0,
            -np.array([0.0, 0.5, 1.0]) * mixing_ratio.to_value(u.umol / u.mol),
        )
        * 100.0
    )
    assert payload["flux"] == pytest.approx(expected_fraction.tolist())
    assert payload["downsample"][64]["flux"] == pytest.approx(
        expected_fraction.tolist()
    )
    assert payload["axis"] == "transmission"
    assert payload["flux_unit"] == "percent transmittance"
    assert payload["flux_kind"] == "transmission"
    metadata = payload["metadata"]
    assert metadata["axis"] == "transmission"
    assert metadata["axis_kind"] == "wavelength"
    assert metadata["flux_unit"] == "percent transmittance"
    assert metadata["flux_unit_original"] == "(micromol/mol)-1m-1 (base 10)"
    assert metadata["flux_unit_display"] == "Transmittance (%)"
    assert metadata["wavelength_unit"] == "cm^-1"
    assert metadata["preferred_wavelength_unit"] == "cm^-1"
    assert metadata["wavelength_display_unit"] == "cm^-1"
    calibration = metadata["quant_ir_calibration"]
    assert calibration["mixing_ratio_umol_per_mol"] == pytest.approx(
        mixing_ratio.to_value(u.umol / u.mol)
    )
    assert calibration["path_length_m"] == pytest.approx(1.0)
    provenance = payload["provenance"]
    assert provenance["axis"] == "transmission"
    assert provenance["flux_unit"] == "percent transmittance"
    assert (
        provenance["flux_unit_original"]
        == "(micromol/mol)-1m-1 (base 10)"
    )
    assert provenance["flux_unit_display"] == "Transmittance (%)"
    assert "χ derived from sample pressure" in provenance["transmittance_conversion"]
    units_meta = provenance.get("units", {})
    assert units_meta.get("preferred_wavelength") == "cm^-1"


def test_prepare_flux_preserves_manual_transmission_payload():
    payload = {
        "flux": [0.95, 0.75],
        "downsample": {64: {"wavelength_nm": [1.0, 2.0], "flux": [0.95, 0.75]}},
        "metadata": {"reported_flux_unit": "TRANSMITTANCE"},
        "provenance": {},
        "axis": "",
    }

    nist_quant_ir._prepare_flux(payload, manual_entry=True)

    assert payload["flux"] == pytest.approx([95.0, 75.0])
    assert payload["downsample"][64]["flux"] == pytest.approx([95.0, 75.0])
    assert payload["axis"] == "transmission"
    metadata = payload["metadata"]
    assert metadata["axis"] == "transmission"
    assert metadata["axis_kind"] == "wavelength"
    assert metadata["flux_unit"] == "percent transmittance"
    assert metadata["flux_unit_original"] == "TRANSMITTANCE"
    assert metadata["flux_unit_display"] == "Transmittance (%)"
    assert metadata["wavelength_unit"] == "cm^-1"
    assert metadata["preferred_wavelength_unit"] == "cm^-1"
    provenance = payload["provenance"]
    assert provenance["axis"] == "transmission"
    assert provenance["flux_unit"] == "percent transmittance"
    assert provenance["flux_unit_original"] == "TRANSMITTANCE"
    assert provenance["flux_unit_display"] == "Transmittance (%)"
