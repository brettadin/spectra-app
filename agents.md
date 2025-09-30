# AGENTS.md — Spectra App v1.2+

This repository uses a **docs-first, citation-required** workflow. If you are an AI or human agent making changes, you must follow this contract.

## 1) Before you touch code
- Read `docs/runtime.json` to know installed versions.
- Query the local docs index (RAG):
  - HTTP: `GET http://127.0.0.1:8765/search?q=<query>&k=8&lib=<lib>`
  - Index lives at `docs/.index/`. Prefer chunks whose metadata matches `runtime.json`.
- Respect the **UI Contract** in `docs/ui_contract.json`. A patch that violates the contract is rejected.

## 2) When you add or change behavior
- Update **brains**: append to `atlas/brains.md` (decision, rationale, alternatives).
- Update **patch notes**: create `docs/patch_notes/v<next>.md` and increment `version.json`.
- Update **tests or contract** if behavior changed:
  - `docs/ui_contract.json` and `docs/tests/` (smoke list exists in v1.1.x notes; preserve rules).
- Log your work: append a new section to `docs/ai_log/YYYY-MM-DD.md` with:
  - Summary (what/why), referenced doc URLs, affected files, verification steps.

## 3) Provenance and exports
- Ensure the export manifest continues to include: provenance, unit logs, derived trace lineage, and app version. If you touch exports, reflect the change in `atlas/brains.md` and the manifest schema docs.

## 4) Safety rules you must preserve
- **Unit toggles** are idempotent (always derive from canonical nm baseline).
- **Duplicate guard** behavior consistent with ledger scope (session/global).
- **Differential** ops:
  - A − B and A / B with epsilon guard when B≈0.
  - Suppress trivial zero-result traces by default; provide “Add anyway.”
- **Legend hygiene**: no empty/duplicate labels; truncate with tooltip; group derived traces.
- **Selections persist**: Trace A/B widgets maintain independent state; include “Lock” and “Swap A↔B.”

## 5) Commit checklist (blockers)
A change is **invalid** unless all are true:
- [ ] Code compiles and runs.
- [ ] `version.json` bumped and `docs/patch_notes/v*.md` added.
- [ ] `docs/ai_log/YYYY-MM-DD.md` contains your summary and citations.
- [ ] UI Contract validated (no removed required controls or tabs).
- [ ] If docs were used, you cited at least one chunk’s `url` from `docs/mirrored/**.meta.json` in your ai_log entry.

## 6) Where to read docs (local mirror)
- Mirror configuration: `docs/sources.yaml`
- Mirrored pages: `docs/mirrored/**`
- Search API: `tools/search_server.py` (serves `GET /search`)
- If a doc is missing, update `sources.yaml`, re-run `tools/mirror_docs.py`, and re-index.

## 7) Forbidden moves
- Do not remove required sidebar controls or tabs.
- Do not change export schemas without updating docs and tests.
- Do not bypass the duplicate ledger without an explicit user-facing control.

## 8) Handoffs
If you stop mid-change, leave a `# Handoff` section in `docs/ai_log/YYYY-MM-DD.md` with:
- Next steps checklist
- Open questions
- Known risks
