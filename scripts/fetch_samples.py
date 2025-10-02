from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server.fetch_archives import materialise_curated_mast_library

if __name__ == '__main__':
    base = Path.cwd()
    path = materialise_curated_mast_library(base)
    print('Saved curated CALSPEC manifest to', path)
