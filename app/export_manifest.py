from __future__ import annotations

import time
from typing import Iterable, List, Mapping, MutableMapping

from app._version import get_version_info
from app.continuity import get_continuity_links

Row = Mapping[str, object]


def _unique_series(rows: Iterable[Row]) -> List[str]:
    names = []
    seen = set()
    for row in rows:
        label = str(row.get("series", ""))
        if label and label not in seen:
            names.append(label)
            seen.add(label)
    return sorted(names)


def build_manifest(
    rows: Iterable[Row],
    display_units: str,
    display_mode: str,
    exported_at: str | None = None,
    viewport: MutableMapping[str, object] | None = None,
) -> dict:
    """Build the export manifest used by the UI."""

    vi = get_version_info()
    continuity = get_continuity_links()
    timestamp = exported_at or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    manifest = {
        'exported_at': timestamp,
        'viewport': viewport,
        'series': [],
        'global_units': {'wavelength': display_units, 'intensity_mode': display_mode},
        'software': {'name': 'spectra-app', 'version': vi['version'], 'built_utc': vi['date_utc']},
        'notes': vi['summary'],
        'continuity': continuity,
    }

    rows_list = list(rows)
    for label in _unique_series(rows_list):
        count = sum(1 for row in rows_list if str(row.get('series', '')) == label)
        manifest['series'].append({'label': label, 'points': count})

    return manifest


__all__ = ['build_manifest']
