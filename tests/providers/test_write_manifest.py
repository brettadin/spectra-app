from astropy.table import Table

import pandas as pd

from tools import build_registry


def test_write_manifest_normalizes_mast_products(tmp_path):
    mast_products_tbl = Table(
        {
            "obsID": ["OBS-1"],
            "productFilename": ["spec.fits"],
            "dataproduct_type": ["spectrum"],
            "dataURI": ["https://example.com/spec.fits"],
        }
    )

    manifest = build_registry.write_manifest(
        tmp_path,
        "Target Star",
        {
            "canonical_name": "Target Star",
            "ra_deg": 10.0,
            "dec_deg": -5.0,
        },
        mast_meta=None,
        mast_products_tbl=mast_products_tbl,
        eso_tbl=None,
        carm_tbl=None,
        planets_df=pd.DataFrame(),
        tags=[],
    )

    mast_products = manifest["datasets"]["mast_products"]
    assert len(mast_products) == 1
    entry = mast_products[0]

    assert entry["obsid"] == "OBS-1"
    assert entry["productURL"] == "https://example.com/spec.fits"
    assert entry["productFilename"] == "spec.fits"
    assert entry["productType"] == ""
    assert entry["description"] == ""
