from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server.fetch_archives import fetch_sample_mast

if __name__ == '__main__':
    base = Path.cwd()
    path = fetch_sample_mast(base)
    print('Saved provenance to', path)
