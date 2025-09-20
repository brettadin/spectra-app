# app/ui/safe.py â€” v1.1.4
from pathlib import Path
import streamlit as st

def safe_ingest(func, *args, **kwargs):
    """Run an ingest call and surface any error instead of letting the page blank."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error("Example ingest failed.")
        st.exception(e)
        st.stop()

def safe_read_text(p: Path):
    """Read text safely; try utf-8, then latin-1. Raise FileNotFoundError for clear messaging."""
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1")

def read_version_caption(version_json_path: Path):
    """Read version.json and return a one-line caption string."""
    import json
    try:
        v = json.loads(version_json_path.read_text(encoding="utf-8")).get("version", "v?")
    except Exception:
        v = "v?"
    return f"Build: {v} â€” Idempotent unit toggling; CSV ingest hardening; duplicate scope+override; version badge; provenance drawer."
