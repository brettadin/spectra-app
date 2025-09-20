
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
issues = []

def expect_file(rel):
    p = ROOT / rel
    if not p.exists():
        issues.append(f"Missing required file: {rel}")

def main():
    expect_file("app/app_merged.py")
    expect_file("docs/ui_contract.json")
    expect_file("app/version.json")
    merged = (ROOT / "app/app_merged.py").read_text(encoding="utf-8", errors="ignore")
    for token in ["Overlay", "Differential", "Docs"]:
        if token not in merged: issues.append(f"Tab label not found in code: {token}")
    for token in ["Examples", "Display units", "Display mode"]:
        if token not in merged: issues.append(f"Sidebar label not found in code: {token}")
    if issues:
        print("UI CONTRACT VIOLATIONS:")
        for i in issues: print(" -", i)
        sys.exit(2)
    print("UI contract static checks passed.")
    print("Smoke run:")
    print("  PowerShell> cd C:\\Code\\spectra-app")
    print("  PowerShell> .\\RUN_CMDS\\Start-Spectra-Merged.ps1")

if __name__ == "__main__":
    main()
