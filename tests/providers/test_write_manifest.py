from pathlib import Path

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
    assert mast_products["returned_count"] == 1
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
    assert mast_products["returned_count"] == total
    assert mast_products["truncated"] is True
    assert len(mast_products["items"]) == build_registry.MAX_MAST_PRODUCTS
    assert mast_products["items"][0]["obsid"] == "OBS-0"
    assert mast_products["items"][-1]["obsid"] == f"OBS-{build_registry.MAX_MAST_PRODUCTS - 1}"


def test_write_manifest_downloads_and_records_paths(tmp_path, monkeypatch):
    mast_products_tbl = Table(
        {
            "obsID": ["OBS-1"],
            "productFilename": ["spec.fits"],
            "dataproduct_type": ["spectrum"],
            "dataURI": ["https://example.com/spec.fits"],
        }
    )

    eso_tbl = Table(
        {
            "DP.ID": ["ESO-1"],
            "INSTRUME": ["UVES"],
            "TARGET": ["Target Star"],
            "DP.DATATYPE": ["SPECTRUM"],
            "DP.TYPE": ["SPECTRUM"],
            "MJD-OBS": [58000.0],
            "DP.DID": ["ESO/1"],
        }
    )

    download_dirs = []

    def fake_download_products(products, download_dir=None, **kwargs):
        download_dirs.append(download_dir)
        target_dir = Path(download_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        local_path = target_dir / "spec.fits"
        local_path.write_text("data")
        return Table(
            {
                "productFilename": ["spec.fits"],
                "obsID": ["OBS-1"],
                "Local Path": [str(local_path)],
                "URL": ["https://example.com/spec.fits"],
            }
        )

    class DummyEso:
        calls = []

        def __init__(self):
            pass

        def retrieve_data(self, dataset_ids, destination=None):
            DummyEso.calls.append((list(dataset_ids), destination))
            dest = Path(destination)
            dest.mkdir(parents=True, exist_ok=True)
            file_path = dest / "eso_file.fits"
            file_path.write_text("eso")
            return [str(file_path)]

    monkeypatch.setattr(build_registry.Observations, "download_products", fake_download_products)
    monkeypatch.setattr(build_registry, "Eso", DummyEso)

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
        eso_tbl=eso_tbl,
        carm_tbl=None,
        planets_df=pd.DataFrame(),
        tags=[],
        download=True,
    )

    expected_mast_dir = str(tmp_path / "Target_Star" / "mast")
    assert download_dirs == [expected_mast_dir]

    mast_entry = manifest["datasets"]["mast_products"]["items"][0]
    assert mast_entry["local_path"] == str(Path(expected_mast_dir) / "spec.fits")

    eso_entry = manifest["datasets"]["eso_phase3"][0]
    assert eso_entry["local_path"] == str(tmp_path / "Target_Star" / "eso" / "eso_file.fits")
    assert DummyEso.calls == [(["ESO-1"], str(tmp_path / "Target_Star" / "eso"))]


def test_write_manifest_skips_downloads_when_flag_false(tmp_path, monkeypatch):
    mast_products_tbl = Table(
        {
            "obsID": ["OBS-1"],
            "productFilename": ["spec.fits"],
            "dataproduct_type": ["spectrum"],
            "dataURI": ["https://example.com/spec.fits"],
        }
    )

    eso_tbl = Table(
        {
            "DP.ID": ["ESO-1"],
            "INSTRUME": ["UVES"],
            "TARGET": ["Target Star"],
            "DP.DATATYPE": ["SPECTRUM"],
            "DP.TYPE": ["SPECTRUM"],
            "MJD-OBS": [58000.0],
            "DP.DID": ["ESO/1"],
        }
    )

    def fail_download(*args, **kwargs):
        raise AssertionError("download should not be invoked")

    class BoomEso:
        def __init__(self):
            raise AssertionError("ESO should not be instantiated when download is False")

    monkeypatch.setattr(build_registry.Observations, "download_products", fail_download)
    monkeypatch.setattr(build_registry, "Eso", BoomEso)

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
        eso_tbl=eso_tbl,
        carm_tbl=None,
        planets_df=pd.DataFrame(),
        tags=[],
        download=False,
    )

    mast_entry = manifest["datasets"]["mast_products"]["items"][0]
    assert "local_path" not in mast_entry

    eso_entry = manifest["datasets"]["eso_phase3"][0]
    assert "local_path" not in eso_entry
