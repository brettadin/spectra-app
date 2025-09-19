from pathlib import Path
from app.server.fetch_archives import fetch_sample_mast

if __name__ == '__main__':
    base = Path('.')
    p = fetch_sample_mast(base)
    print('Saved provenance to', p)
