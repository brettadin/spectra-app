from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any, Dict

_LOCK = threading.Lock()


class DuplicateLedger:
    """Persist hashes for uploaded files across Streamlit sessions."""

    def __init__(self, cache_dir: str = ".cache", filename: str = "ledger.json") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.cache_dir / filename
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        digest = hashlib.sha256()
        digest.update(data)
        return digest.hexdigest()

    def _read(self) -> Dict[str, Any]:
        with _LOCK:
            payload = self.path.read_text(encoding="utf-8") or "{}"
            return json.loads(payload)

    def _write(self, data: Dict[str, Any]) -> None:
        with _LOCK:
            self.path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def seen(self, digest: str) -> bool:
        return digest in self._read()

    def record(self, digest: str, meta: Dict[str, Any]) -> None:
        db = self._read()
        db[digest] = meta
        self._write(db)

    def purge_session(self, session_id: str) -> None:
        db = self._read()
        kept = {key: value for key, value in db.items() if value.get("session_id") != session_id}
        self._write(kept)

