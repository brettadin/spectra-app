import json, datetime as dt, pathlib, textwrap, requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RUNTIME = json.loads((DOCS / "runtime.json").read_text(encoding="utf-8"))

SEARCH_URL = "http://127.0.0.1:8765/search"

AGENT_SYSTEM = """\
You must consult the local documentation index before proposing code changes.
Use GET http://127.0.0.1:8765/search?q=<query>&k=8&lib=<lib>.
Prefer chunks matching docs/runtime.json versions: {versions}.
Update docs/ai_log/<today>.md with citations and bump version.json + docs/patch_notes.
Respect docs/ui_contract.json. Violations invalidate your patch.
"""

def rag_fetch(query: str, lib: str | None = None, k: int = 8):
    params = {"q": query, "k": k}
    if lib:
        params["lib"] = lib
    r = requests.get(SEARCH_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def build_context(user_task: str):
    """Make a compact RAG bundle: top chunks for astropy/astroquery/NIST/JWST/MAST."""
    libs = ["astropy", "astroquery", "nist_asd_help", "nist_dimspec", "jwst_docs", "mast_api", "stsci_archive"]
    results = []
    for lib in libs:
        try:
            hits = rag_fetch(user_task, lib=lib, k=3)
            for h in hits:
                txt = h.get("excerpt") or h.get("text") or ""
                # Trim huge chunks
                txt = txt.strip()
                if len(txt) > 2500:
                    txt = txt[:2400] + " …"
                results.append({
                    "lib": lib,
                    "url": h.get("url") or h.get("path"),
                    "title": h.get("title") or h.get("path"),
                    "text": txt
                })
        except Exception:
            # If a lib isn’t mirrored, skip quietly
            continue
    return results

def format_context(rag_chunks):
    lines = []
    for i, ch in enumerate(rag_chunks, 1):
        lines.append(f"[{i}] lib={ch['lib']} | {ch['title']} | {ch['url']}\n{ch['text']}\n")
    return "\n".join(lines[:12])  # keep it tight

def run_agent(user_task: str):
    # 1) Build RAG bundle
    rag_chunks = build_context(user_task)
    ctx = format_context(rag_chunks)

    # 2) Build system + messages for your model
    sys_msg = AGENT_SYSTEM.format(versions=json.dumps(RUNTIME.get("libs", {}), sort_keys=True))
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "system", "content": "Use the cited context below. Prefer exact API names and parameters found there."},
        {"role": "system", "content": "CONTEXT START\n" + ctx + "\nCONTEXT END"},
        {"role": "user", "content": user_task},
    ]

    # 3) Call your LLM here. Replace with your actual client.
    # Example with a placeholder function:
    reply = call_your_llm(messages)  # <-- implement this for your stack

    # 4) Write ai_log with citations you just used
    today = dt.date.today().isoformat()
    log_dir = DOCS / "ai_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    logf = log_dir / f"{today}.md"
    header = f"## {dt.datetime.now().isoformat(timespec='seconds')} — Task\n\n{user_task}\n\n### Citations\n"
    cites = "\n".join(f"- [{c['lib']}] {c['title']} — {c['url']}" for c in rag_chunks[:12])
    body = f"\n### Output\n\n{reply}\n"
    with open(logf, "a", encoding="utf-8") as f:
        f.write(header + cites + body + "\n")

    return reply

# Dummy for illustration only
def call_your_llm(messages):
    # Integrate your model here (OpenAI client, local model, whatever).
    # Must return plain text.
    return "…model reply using the provided CONTEXT with citations…"

if __name__ == "__main__":
    import sys
    task = "Implement MAST observations query with positional cone search and write tests"
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    print(run_agent(task))
