# Spectra App — AI Handoff Bridge
_Last updated: 2025-09-21T23:00:00Z_

This bridge document ties the brains log to the operative AI handoff prompt.
It is part of the mandated continuity template: Brains → AI Handoff → Patch Notes.

## Source of Truth
- Current prompt: `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.4.md`
- Next revision must update both this bridge and `docs/brains/brains_INDEX.md`.
- Keep handoff prompts UTF-8, versioned, and cross-linked from the paired brains + patch notes.

## Expectations for v1.1.5c
- Reflect the Streamlit width migration so future edits continue using the `width` parameter instead of `use_container_width`.
- Reference `docs/brains/brains_v1.1.5c.md`, `docs/PATCH_NOTES/v1.1.5c.txt`, and the Atlas index.
- Capture guidance about similarity label aliasing and the wavelength-metadata fallback alongside the existing ingestion rules.

## Checklist Before Shipping Changes
1. Read the latest brains entry and confirm the scope still matches.
2. Verify `docs/PATCH_NOTES/v1.1.5c.txt` lists the same continuity obligations.
3. Run `RUN_CMDS/Verify-Project.ps1` to confirm reciprocal links and provider directories are intact.
