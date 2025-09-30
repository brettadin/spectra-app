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

def load_yaml(p):
    import yaml
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def ensure_runtime():
    import importlib, platform
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "libs": {}
    }
    # Lazy: detect versions if installed
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
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    doc = Document(r.text)
    html = doc.summary(html_partial=True)
    soup = BeautifulSoup(html, "lxml")

    # strip nav/boilerplate
    for bad in soup.select("nav, header, footer, .sidebar, .sphinxsidebar, .toctree-wrapper, .related, .wy-nav-side, .wy-side-nav-search"):
        bad.decompose()

    # normalize code blocks
    for pre in soup.find_all("pre"):
        pre.attrs = {}

    md = markdownify.markdownify(str(soup), heading_style="ATX")
    meta = {
        "url": url,
        "title": doc.short_title(),
        "retrieved": int(time.time()),
        "sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()
    }
    return md, meta

def slugify(url, base_url):
    # turn /en/stable/io/fits/ into io/fits
    path = url.split(base_url.rstrip("/"))[-1]
    path = re.sub(r"^/+", "", path)
    path = re.sub(r"/index\.html?$", "", path)
    path = path.strip("/")
    # drop version prefix segments like en/stable/
    parts = [p for p in path.split("/") if p not in {"en", "stable", "latest"}]
    return "/".join(parts) or "index"

def mirror():
    runtime = ensure_runtime()
    cfg = load_yaml(SRC)
    MIR.mkdir(parents=True, exist_ok=True)
    for entry in cfg:
        base = entry["base_url"].rstrip("/") + "/"
        keep = entry.get("keep", [])
        name = entry["name"]
        for k in keep:
            url = base + k.strip("/") + "/"
            try:
                md, meta = fetch_clean(url)
                rel = pathlib.Path(name, k).with_suffix(".md")
                out_md = MIR / rel
                out_md.parent.mkdir(parents=True, exist_ok=True)
                out_md.write_text(md, encoding="utf-8")
                (MIR / rel.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2), encoding="utf-8")
                print(f"[mirrored] {url} -> {rel}")
            except Exception as e:
                print(f"[skip] {url} ({e})", file=sys.stderr)

if __name__ == "__main__":
    mirror()
