# Spectra App — AI Handoff Bridge
_Last updated: 2025-09-21T00:00:00Z_

This bridge document ties the brains log to the operative AI handoff prompt.
It is part of the mandated continuity template: Brains → AI Handoff → Patch Notes.

## Source of Truth
- Current prompt: `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.4.md`
- Next revision must update both this bridge and `docs/brains/brains_INDEX.md`.
- Keep handoff prompts UTF-8, versioned, and cross-linked from the paired brains + patch notes.

## Expectations for v1.1.5a
- Do **not** regenerate the entire prompt—extend it incrementally.
- Include guidance about the new continuity manifest field and provider cache directories.
- Ensure every future prompt references `docs/brains/brains_v1.1.5a.md` until superseded.

## Checklist Before Shipping Changes
1. Read the latest brains entry and confirm the scope still matches.
2. Verify `docs/PATCH_NOTES/v1.1.5a.txt` lists the same continuity obligations.
3. Run `RUN_CMDS/Verify-Project.ps1` to confirm reciprocal links and provider directories are intact.
