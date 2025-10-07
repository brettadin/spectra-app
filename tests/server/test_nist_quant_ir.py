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


def test_finalise_payload_preserves_samples_and_tags_units():
    wavelengths = [500.0, 510.0, 520.0]
    flux = [0.1, 0.2, 0.3]
    payload = {
        "wavelength_nm": list(wavelengths),
        "flux": list(flux),
        "metadata": {"reported_flux_unit": "Transmittance"},
        "provenance": {},
        "axis": "transmission",
    }

    nist_quant_ir._finalise_payload(payload)

    assert payload["flux"] == flux
    metadata = payload["metadata"]
    provenance = payload["provenance"]
    assert metadata["axis"] == "transmission"
    assert metadata["axis_kind"] == "wavelength"
    assert metadata["wavelength_unit"] == "cm^-1"
    assert metadata["preferred_wavelength_unit"] == "cm^-1"
    assert metadata["wavelength_display_unit"] == "cm^-1"
    assert provenance["axis"] == "transmission"
    units_meta = provenance.get("units")
    assert units_meta["preferred_wavelength"] == "cm^-1"
    assert "wavenumber_cm_1" in payload
