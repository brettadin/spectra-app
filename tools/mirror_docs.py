# tools/mirror_docs.py
import json, hashlib, pathlib, time, sys, re
import requests
from bs4 import BeautifulSoup
from readability import Document
import markdownify

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MIR = DOCS / "mirrored"
SRC = DOCS / "sources.yaml"
RUNTIME = DOCS / "runtime.json"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "spectra-app-docbot/1.2 (+local; docs-mirror) Python-requests"
})
TIMEOUT = 30

def load_yaml(p):
    import yaml
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def ensure_runtime():
    import platform
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "libs": {}
    }
    for mod in ["astropy", "astroquery", "numpy", "scipy", "pandas"]:
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", "unknown")
            info["libs"][mod] = v
        except Exception:
            pass
    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info

def fetch_clean(url:str)->tuple[str, dict]:
    r = SESSION.get(url, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    doc = Document(r.text)
    html = doc.summary(html_partial=True)
    soup = BeautifulSoup(html, "lxml")

    for bad in soup.select("nav, header, footer, .sidebar, .sphinxsidebar, .toctree-wrapper, .related, .wy-nav-side, .wy-side-nav-search"):
        bad.decompose()
    for pre in soup.find_all("pre"):
        pre.attrs = {}

    md = markdownify.markdownify(str(soup), heading_style="ATX")
    meta = {
        "url": url,
        "title": (doc.short_title() or "").strip(),
        "retrieved": int(time.time()),
        "sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()
    }
    return md, meta

def norm_join(base, slug):
    base = base.rstrip("/")
    slug = slug.strip("/")
    return f"{base}/{slug}" if slug else f"{base}/"

def try_mirror(base_url, slug):
    # Try directory form, then .html, then raw slug (if it already endswith .html)
    candidates = []
    if slug.endswith(".html"):
        candidates = [norm_join(base_url, slug)]
    else:
        candidates = [norm_join(base_url, slug) + "/", norm_join(base_url, slug) + ".html"]

    last_err = None
    for url in candidates:
        try:
            md, meta = fetch_clean(url)
            return url, md, meta
        except Exception as e:
            last_err = e
            continue
    raise last_err

def mirror():
    ensure_runtime()
    cfg = load_yaml(SRC)
    MIR.mkdir(parents=True, exist_ok=True)

    for entry in cfg:
        base = entry["base_url"]
        name = entry["name"]
        keep = entry.get("keep", [])
        for k in keep:
            slug = k.strip("/")
            try:
                url, md, meta = try_mirror(base, slug)
                # convert slug -> file path, keep .html in name if present
                safe = slug if slug else "index"
                if safe.endswith("/"):
                    safe = safe[:-1]
                fname = safe
                if fname.endswith(".html"):
                    fname = fname[:-5]
                if not fname.endswith(".md"):
                    fname = fname + ".md"
                out_path = MIR / name / fname
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(md, encoding="utf-8")
                out_meta = out_path.with_suffix(".meta.json")
                out_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                print(f"[mirrored] {url} -> {out_path.relative_to(MIR)}")
            except Exception as e:
                print(f"[skip] {norm_join(base, slug)} ({e})", file=sys.stderr)

if __name__ == "__main__":
    mirror()
