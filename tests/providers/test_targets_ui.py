from app.ui.targets import _extract_mast_products


def test_extract_mast_products_handles_summary_dict():
    manifest = {
        "datasets": {
            "mast_products": {
                "items": [{"productFilename": "a"}, {"productFilename": "b"}],
                "total_count": 5,
                "truncated": True,
            }
        }
    }

    items, total, truncated = _extract_mast_products(manifest)
    assert len(items) == 2
    assert total == 5
    assert truncated is True


def test_extract_mast_products_handles_legacy_list():
    manifest = {
        "datasets": {
            "mast_products": [
                {"productFilename": "legacy-1"},
                {"productFilename": "legacy-2"},
            ]
        }
    }

    items, total, truncated = _extract_mast_products(manifest)
    assert len(items) == 2
    assert total == 2
    assert truncated is False
