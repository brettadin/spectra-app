"""Tests for the ProvenanceService."""

from pathlib import Path
import json

from app.services.provenance_service import ProvenanceService


def test_manifest_creation_and_sha256(tmp_path):
    # Create a temporary file
    file_path = tmp_path / "test.csv"
    file_path.write_text("dummy")
    service = ProvenanceService(app_version="0.1-test")
    manifest = service.create_manifest([file_path])
    # There should be one source entry
    assert len(manifest["sources"]) == 1
    src = manifest["sources"][0]
    # SHA should match
    expected_sha = service._sha256(file_path)
    assert src["sha256"] == expected_sha
    # Save the manifest and re-load to ensure valid JSON
    manifest_path = tmp_path / "manifest.json"
    service.save_manifest(manifest, manifest_path)
    with manifest_path.open() as f:
        loaded = json.load(f)
    assert loaded["app"]["version"] == "0.1-test"