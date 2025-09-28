from __future__ import annotations

from astropy.table import Table

from tools import build_registry


def test_resolve_target_vega_has_astrometry(monkeypatch):
    def fake_query_object(name: str):
        if name != "Vega":
            return None
        return Table(
            names=(
                "MAIN_ID",
                "RA",
                "DEC",
                "OTYPES",
                "SP_TYPE",
                "RVZ_RADVEL",
                "PLX_VALUE",
            ),
            rows=[
                (
                    "Vega",
                    "18 36 56.33635",
                    "+38 47 01.2802",
                    "Star",
                    "A0V",
                    -13.5,
                    130.23,
                )
            ],
        )

    monkeypatch.setattr(build_registry.SIMBAD, "query_object", fake_query_object)

    meta = build_registry.resolve_target("Vega")

    assert meta["parallax_mas"] == 130.23
    assert meta["rv_kms"] == -13.5
