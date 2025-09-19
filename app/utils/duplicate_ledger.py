"""
Duplicate upload guard with SHA-256 ledger.

Usage:
    from app.utils.duplicate_ledger import DuplicateLedger
    ledger = DuplicateLedger(cache_dir=".cache")
    digest = ledger.hash_bytes(file_bytes)  # or ledger.hash_file(path)
    if ledger.seen(digest):
        st.warning("This file has already been added. Skipping duplicate.")
    else:
        ledger.record(digest, meta={"filename": name, "bytes": len(file_bytes)})
"""

from __future__ import annotations
import os, json, hashlib, threading
from pathlib import Path
from typing import Any, Dict

_LOCK = threading.Lock()

class DuplicateLedger:
    def __init__(self, cache_dir: str = ".cache", filename: str = "ledger.json"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.cache_dir / filename
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _read(self) -> Dict[str, Any]:
        with _LOCK:
            return json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def _write(self, data: Dict[str, Any]) -> None:
        with _LOCK:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def hash_file(path: str | os.PathLike) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1<<20), b""):
                h.update(chunk)
        return h.hexdigest()

    def seen(self, digest: str) -> bool:
        return digest in self._read()

    def record(self, digest: str, meta: Dict[str, Any] | None = None) -> None:
        db = self._read()
        db[digest] = meta or {}
        self._write(db)
