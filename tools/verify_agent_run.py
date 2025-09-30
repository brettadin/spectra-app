# tools/verify_agent_run.py
import json, sys, pathlib, re, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
errors, notes = [], []

# , 1 version bump & patch notes 
v_candidates = [ROOT / "app" / "version.json", ROOT / "version.json"]
vfile = next((p for p in v_candidates if p.exists()), None)

raw_v = None
if not vfile:
    errors.append(f"version.json missing (checked: {', '.join(map(str, v_candidates))})")
else:
    try:
        raw_v = json.loads(vfile.read_text(encoding="utf-8"))["version"]
        notes.append(f"Using version from {vfile}: {raw_v}")
    except Exception as e:
        errors.append(f"version.json invalid at {vfile}: {e}")

# normalize: strip all leading v/V, e.g., vv1.2.0a -> 1.2.0a
def normalize(v: str) -> str:
    return re.sub(r'^[vV]+', '', v.strip())

core_v = normalize(raw_v) if raw_v else None

# find patch notes
if core_v:
    pn_dirs = [ROOT / "docs" / "patch_notes", ROOT / "docs" / "PATCH_NOTES"]
    pn_found = []
    patterns = [
        f"PATCH_NOTES_v{core_v}.md",
        f"PATCH_NOTES_{core_v}.md",
        f"v{core_v}.md",
        f"{core_v}.md",
    ]
    for d in pn_dirs:
        if not d.exists():
            continue
        for pat in patterns:
            pn_found.extend(d.glob(pat))
    if not pn_found:
        looked = "; ".join(f"{d}:[{', '.join(patterns)}]" for d in pn_dirs if d.exists())
        errors.append(f"patch notes missing for v{core_v} ({looked or 'no patch_notes dirs present'})")
    else:
        notes.append("Found patch notes: " + ", ".join(map(str, pn_found)))

# ,  2 ai_log for today 
today = dt.date.today().isoformat()
logfile = ROOT / "docs" / "ai_log" / f"{today}.md"
if not logfile.exists():
    errors.append(f"docs/ai_log/{today}.md is missing")
else:
    notes.append(f"Found ai_log: {logfile}")

# ,  3 UI contract present 
uicontract = ROOT / "docs" / "ui_contract.json"
if not uicontract.exists():
    errors.append("docs/ui_contract.json missing")
else:
    notes.append("ui_contract.json present")

# ,  4 ai_log must include at least one citation 
if logfile.exists():
    text = logfile.read_text(encoding="utf-8")
    has_http = re.search(r"https?://", text) is not None
    has_meta = re.search(r"docs/mirrored/.+?\.meta\.json", text) is not None
    if not (has_http or has_meta):
        snippet = text[:240].replace("\n", " ")
        errors.append(
            "ai_log has no citations to mirrored docs. Include at least one URL "
            "(https://...) OR a path to a mirrored .meta.json."
        )
        notes.append(f"ai_log snippet (first 240 chars): {snippet!r}")

# ,  Exit 
if errors:
    print("VERIFIER FAIL:")
    for e in errors:
        print(" -", e)
    if notes:
        print("\nINFO:")
        for n in notes:
            print(" -", n)
    sys.exit(1)

print("Verifier OK")
for n in notes:
    print(" -", n)
