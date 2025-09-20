"""Lightweight static checks to ensure the UI contract has not regressed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUES: list[str] = []


def expect_file(rel_path: str) -> Path:
    path = ROOT / rel_path
    if not path.exists():
        ISSUES.append(f"Missing required file: {rel_path}")
    return path


def load_contract() -> dict:
    contract_path = expect_file("docs/ui_contract.json")
    if not contract_path.exists():
        return {}
    try:
        return json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive branch
        ISSUES.append(f"Failed to parse docs/ui_contract.json: {exc}")
        return {}


def collect_ui_source() -> str:
    buffers = []
    for rel in ("app/ui/main.py", "app/ui/entry.py", "app/app_merged.py"):
        path = expect_file(rel)
        if path.exists():
            buffers.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(buffers)


def main() -> None:
    contract = load_contract()
    source_blob = collect_ui_source()

    for token in contract.get("tabs", []):
        if token not in source_blob:
            ISSUES.append(f"Tab label not found in code: {token}")

    for token in contract.get("sidebar", []):
        if token not in source_blob:
            ISSUES.append(f"Sidebar label not found in code: {token}")

    if ISSUES:
        print("UI CONTRACT VIOLATIONS:")
        for issue in ISSUES:
            print(" -", issue)
        sys.exit(2)

    print("UI contract static checks passed.")
    print("Smoke run:")
    print("  PowerShell> cd C:\\Code\\spectra-app")
    print("  PowerShell> .\\RUN_CMDS\\Start-Spectra-Merged.ps1")


if __name__ == "__main__":
    main()
