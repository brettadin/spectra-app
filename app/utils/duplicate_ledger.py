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

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        h = hashlib.sha256(); h.update(data); return h.hexdigest()

    def _read(self) -> Dict[str, Any]:
        with _LOCK:
            txt = self.path.read_text(encoding="utf-8") or "{}"
            return json.loads(txt)

    def _write(self, data: Dict[str, Any]) -> None:
        with _LOCK:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def seen(self, digest: str) -> bool:
        return digest in self._read()

    def record(self, digest: str, meta: Dict[str, Any]) -> None:
        db = self._read(); db[digest] = meta; self._write(db)

    def purge_session(self, session_id: str):
        db = self._read()
        kept = {k:v for k,v in db.items() if v.get("session_id") != session_id}
        self._write(kept)
