from __future__ import annotations

import math

import pytest
from astropy.table import Table

from app.server.fetchers import nist


@pytest.fixture
def sample_table() -> Table:
    return Table(
        rows=[
            (
                '5000.0',
                '5002.0',
                '20',
                '1.0e+6',
                '5.0e-1',
                'AAA',
                '10.0  -  11.0',
                '1s     | 2S | 1/2 |',
                '2p     | 2P* | 3/2 |',
                'E1',
                'T1000',
                'L2000',
            ),
            (
                '',
                '6000.0',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
            ),
        ],
        names=[
            'Observed',
            'Ritz',
            'Rel.',
            'Aki',
            'fik',
            'Acc.',
            'Ei           Ek',
            'Lower level',
            'Upper level',
            'Type',
            'TP',
            'Line',
        ],
    )


def test_fetch_basic(monkeypatch: pytest.MonkeyPatch, sample_table: Table) -> None:
    captured = {}

    def fake_query(min_wav, max_wav, *, linename=None, wavelength_type=None):
        captured['min_wav'] = min_wav
        captured['max_wav'] = max_wav
        captured['linename'] = linename
        captured['wavelength_type'] = wavelength_type
        return sample_table.copy()

    monkeypatch.setattr(nist, 'Nist', type('Dummy', (), {'query': staticmethod(fake_query)}))

    result = nist.fetch(element='H', lower_wavelength=380.0, upper_wavelength=780.0)

    assert captured['linename'] == 'H I'
    assert pytest.approx(captured['min_wav'].value, rel=1e-6) == 380.0
    assert pytest.approx(captured['max_wav'].value, rel=1e-6) == 780.0
    assert result['meta']['label'] == 'H I (NIST ASD)'
    assert result['meta']['element_symbol'] == 'H'
    assert result['wavelength_nm'] == [500.2, 600.0]
    assert result['intensity'][0] == pytest.approx(20.0)
    assert result['intensity'][1] is None
    assert result['intensity_normalized'][0] == pytest.approx(1.0)
    assert result['intensity_normalized'][1] is None
    first_line = result['lines'][0]
    assert math.isclose(first_line['wavelength_nm'], 500.2)
    assert math.isclose(first_line['observed_wavelength_nm'] or 0.0, 500.0)
    assert math.isclose(first_line['ritz_wavelength_nm'] or 0.0, 500.2)
    second_line = result['lines'][1]
    assert math.isclose(second_line['wavelength_nm'], 600.0)
    assert second_line['observed_wavelength_nm'] is None
    assert math.isclose(second_line['ritz_wavelength_nm'] or 0.0, 600.0)
    assert first_line['transition_probability_s'] == pytest.approx(1.0e6)
    assert first_line['oscillator_strength'] == pytest.approx(5.0e-1)
    assert first_line['lower_level_energy_ev'] == pytest.approx(10.0)
    assert first_line['upper_level_energy_ev'] == pytest.approx(11.0)
    assert '2P*' in (first_line['upper_level'] or '')


def test_fetch_linename(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_query(min_wav, max_wav, *, linename=None, wavelength_type=None):  # noqa: D401 - simple stub
        return Table(rows=[], names=['Observed', 'Ritz', 'Rel.', 'Aki', 'fik', 'Acc.', 'Ei           Ek', 'Lower level', 'Upper level', 'Type', 'TP', 'Line'])

    monkeypatch.setattr(nist, 'Nist', type('Dummy', (), {'query': staticmethod(fake_query)}))

    result = nist.fetch(linename='Fe II')
    assert result['wavelength_nm'] == []
    assert result['meta']['element_symbol'] == 'Fe'
    assert result['meta']['ion_stage'] == 'II'
    assert 'note' in result['meta']


def test_fetch_unknown_element() -> None:
    with pytest.raises(ValueError):
        nist.fetch(element='Xx')
