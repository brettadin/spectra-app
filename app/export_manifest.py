from __future__ import annotations

import time
from typing import Iterable, List, Mapping, MutableMapping, Sequence

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
    traces: Sequence[Mapping[str, object]] | None = None,
) -> dict:
    """Build the export manifest used by the UI."""

    vi = get_version_info()
    continuity = get_continuity_links()
    timestamp = exported_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    rows_list = list(rows)

    flux_reference = 'normalized' if display_mode != 'Flux (raw)' else 'W m⁻² m⁻¹'
        <<<<<<< codex/improve-unit-conversions-and-file-uploads-4ct6vp
=======

    rows_list = list(rows)

    flux_reference = 'normalized' if display_mode != 'Flux (raw)' else 'W m⁻² m⁻¹'
        >>>>>>> main

    manifest = {
        'exported_at': timestamp,
        'viewport': viewport,
        'series': [],
        'traces': [],
        'global_units': {
            'wavelength': display_units,
            'intensity_mode': display_mode,
            'flux_reference': flux_reference,
        },
        'software': {'name': 'spectra-app', 'version': vi['version'], 'built_utc': vi['date_utc']},
        'notes': vi['summary'],
        'continuity': continuity,
        'transformations': {
            'display_mode': display_mode,
            'wavelength_units': display_units,
            'rows_exported': len(rows_list),
        },
    }

    for label in _unique_series(rows_list):
        count = sum(1 for row in rows_list if str(row.get('series', '')) == label)
        manifest['series'].append({'label': label, 'points': count})

    if traces:
        for trace in traces:
            manifest['traces'].append(
                {
                    'label': trace.get('label'),
                    'provider': trace.get('provider'),
                    'kind': trace.get('kind'),
                    'points': trace.get('points'),
                    'axis': trace.get('axis'),
                    'flux_unit': trace.get('flux_unit'),
                    'flux_kind': trace.get('flux_kind'),
                    'metadata': trace.get('metadata'),
                    'provenance': trace.get('provenance'),
                    'mirrored': trace.get('mirrored', False),
                }
            )

    return manifest


__all__ = ['build_manifest']
