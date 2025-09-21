from __future__ import annotations

from pathlib import Path

from app.continuity import get_continuity_links
from app.export_manifest import build_manifest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_continuity_links_cross_reference():
    links = get_continuity_links()

    brains = _repo_root() / links['brains']
    patch_notes = _repo_root() / links['patch_notes']
    index_file = _repo_root() / links['index']
    handoff_bridge = _repo_root() / links['ai_handoff_bridge']

    assert brains.exists(), f"Brains file missing: {brains}"
    assert patch_notes.exists(), f"Patch notes missing: {patch_notes}"
    assert index_file.exists(), f"Brains index missing: {index_file}"
    assert handoff_bridge.exists(), f"AI handoff bridge missing: {handoff_bridge}"

    brains_text = brains.read_text(encoding='utf-8')
    patch_text = patch_notes.read_text(encoding='utf-8')
    index_text = index_file.read_text(encoding='utf-8')
    handoff_text = handoff_bridge.read_text(encoding='utf-8')

    assert links['patch_notes'] in brains_text
    assert links['brains'] in patch_text
    assert links['brains'] in index_text
    assert links['patch_notes'] in index_text
    assert 'docs/ai_handoff/' in handoff_text

    provider_dirs = links['provider_directories']
    assert provider_dirs, "Provider directories list must not be empty"
    for rel in provider_dirs:
        path = _repo_root() / rel
        assert path.exists() and path.is_dir(), f"Provider dir missing: {path}"


def test_build_manifest_includes_continuity():
    rows = [
        {'series': 'Alpha'},
        {'series': 'Alpha'},
        {'series': 'Beta'},
    ]
    manifest = build_manifest(
        rows,
        display_units='nm',
        display_mode='Flux (raw)',
        exported_at='2025-09-21T00:00:00Z',
        viewport=None,
    )

    links = get_continuity_links()
    assert manifest['continuity'] == links
    labels = {entry['label']: entry['points'] for entry in manifest['series']}
    assert labels == {'Alpha': 2, 'Beta': 1}
    assert manifest['global_units']['wavelength'] == 'nm'
    assert manifest['global_units']['intensity_mode'] == 'Flux (raw)'
    assert manifest['exported_at'] == '2025-09-21T00:00:00Z'
    assert manifest['transformations']['rows_exported'] == len(rows)
    assert manifest['traces'] == []
