# app/server/provenance.py
# Spectra App v1.1.4
from typing import Dict, Any, List
import hashlib, json

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def merge_trace_provenance(manifest: Dict[str, Any], trace_id: str, prov: Dict[str, Any]) -> Dict[str, Any]:
    traces = manifest.setdefault("traces", {})
    entry = traces.setdefault(trace_id, {})
    entry.setdefault("fetch_provenance", {}).update(prov or {})
    return manifest
