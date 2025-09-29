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
    assert mast_products["total_count"] == 1
    assert mast_products["truncated"] is False
    assert len(mast_products["items"]) == 1
    entry = mast_products["items"][0]

    assert entry["obsid"] == "OBS-1"
    assert entry["productURL"] == "https://example.com/spec.fits"
    assert entry["productFilename"] == "spec.fits"
    assert entry["productType"] == ""
    assert entry["description"] == ""


def test_write_manifest_caps_mast_products(tmp_path):
    total = build_registry.MAX_MAST_PRODUCTS + 5
    mast_products_tbl = Table(
        {
            "obsID": [f"OBS-{i}" for i in range(total)],
            "productFilename": [f"spec-{i}.fits" for i in range(total)],
            "dataproduct_type": ["spectrum"] * total,
            "dataURI": [f"https://example.com/spec-{i}.fits" for i in range(total)],
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
    assert mast_products["total_count"] == total
    assert mast_products["truncated"] is True
    assert len(mast_products["items"]) == build_registry.MAX_MAST_PRODUCTS
    assert mast_products["items"][0]["obsid"] == "OBS-0"
    assert mast_products["items"][-1]["obsid"] == f"OBS-{build_registry.MAX_MAST_PRODUCTS - 1}"
