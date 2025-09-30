import json, sys, pathlib, re, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
errors = []

# 1) version bump and patch notes
vfile = ROOT / "version.json"
try:
    v = json.loads(vfile.read_text(encoding="utf-8"))["version"]
except Exception:
    errors.append("version.json missing or invalid")
else:
    major_minor = ".".join(v.split(".")[:2])
    pn = list((ROOT / "docs" / "patch_notes").glob(f"v{v}.md"))
    if not pn:
        errors.append(f"patch notes missing for v{v} in docs/patch_notes/")

# 2) ai_log for today
today = dt.date.today().isoformat()
logfile = ROOT / "docs" / "ai_log" / f"{today}.md"
if not logfile.exists():
    errors.append(f"docs/ai_log/{today}.md is missing")

# 3) UI contract present
uicontract = ROOT / "docs" / "ui_contract.json"
if not uicontract.exists():
    errors.append("docs/ui_contract.json missing")

# 4) ai_log contains at least one mirrored-doc citation (url in meta.json)
if logfile.exists():
    text = logfile.read_text(encoding="utf-8")
    if "http" not in text:
        errors.append("ai_log has no citations to mirrored docs (expected at least one URL)")

if errors:
    print("VERIFIER FAIL:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("Verifier OK")
