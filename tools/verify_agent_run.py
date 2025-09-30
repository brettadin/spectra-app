import json, sys, pathlib, re, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
errors = []
notes = []

# ---------- 1) version bump & patch notes ----------
# Try both common locations for version.json
v_candidates = [ROOT / "version.json", ROOT / "app" / "version.json"]
vfile = next((p for p in v_candidates if p.exists()), None)

if not vfile:
    errors.append(f"version.json missing (checked: {', '.join(str(p) for p in v_candidates)})")
    v = None
else:
    try:
        v = json.loads(vfile.read_text(encoding="utf-8"))["version"]
        notes.append(f"Using version from {vfile}: v{v}")
    except Exception as e:
        errors.append(f"version.json invalid at {vfile}: {e}")
        v = None

# Patch notes: support both 'PATCH_NOTES_vX.Y.Z.md' and 'vX.Y.Z.md'
if v:
    pn_dir = ROOT / "docs" / "patch_notes"
    patterns = [f"PATCH_NOTES_v{v}.md", f"v{v}.md"]
    pn = [p for pat in patterns for p in pn_dir.glob(pat)]
    if not pn:
        errors.append(f"patch notes missing for v{v} in {pn_dir} (looked for: {', '.join(patterns)})")
    else:
        notes.append(f"Found patch notes: {', '.join(str(p) for p in pn)}")

# ---------- 2) ai_log for today ----------
today = dt.date.today().isoformat()
logfile = ROOT / "docs" / "ai_log" / f"{today}.md"
if not logfile.exists():
    errors.append(f"docs/ai_log/{today}.md is missing")
else:
    notes.append(f"Found ai_log: {logfile}")

# ---------- 3) UI contract present ----------
uicontract = ROOT / "docs" / "ui_contract.json"
if not uicontract.exists():
    errors.append("docs/ui_contract.json missing")
else:
    notes.append("ui_contract.json present")

# ---------- 4) ai_log must include at least one citation ----------
# Accept either: a full URL (http/https) OR a mirrored meta reference line like:
# 'docs/mirrored/<lib>/<page>.meta.json' or a URL shown in search_server results
if logfile.exists():
    text = logfile.read_text(encoding="utf-8")
    has_http = re.search(r"https?://", text) is not None
    has_meta = re.search(r"docs/mirrored/.+\.meta\.json", text) is not None
    if not (has_http or has_meta):
        errors.append(
            "ai_log has no citations to mirrored docs. "
            "Include at least one URL (https://...) OR a path to a mirrored .meta.json."
        )

# ---------- Exit ----------
if errors:
    print("VERIFIER FAIL:")
    for e in errors:
        print(" -", e)
    # also print helpful notes so the human knows what *did* work
    if notes:
        print("\nINFO:")
        for n in notes:
            print(" -", n)
    sys.exit(1)

print("Verifier OK")
for n in notes:
    print(" -", n)