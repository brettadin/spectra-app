# 🔑 BRAINS FIRST — DO NOT SKIP

All contributors must consult the Brains before making changes.  
- The canonical knowledge base is in `docs/brains/brains_<version>.md` (use the latest version).  
- Every change/learning must be recorded there with a new **REF code**:
  - Format: `<PATCH>-<PART><SEQ>` (e.g., 1.1.5b-A01).  
  - Each REF entry includes: What, Why, Where, How, Verification, Provenance.  
- REF codes must be:
  - Cross-referenced in `PATCHLOG.txt`  
  - Included in commit messages and PR descriptions  
  - Linked in the AI handoff prompts for continuity  

**Contract checkpoints (must remain true every patch):**  
- Unit toggles are idempotent (always from canonical baseline).  
- Fν/Fλ are never mixed on the same axis; axes are labeled with units.  
- Legends have no empties or duplicates; metadata is always shown.  
- Exports include PNG + CSV + manifest with provenance.  
- Duplicate guard and provenance logs are intact.  

➡️ **If you are coding, updating, or patching:**  
1. Read the latest Brains doc in full.  
2. Add your new learnings to Brains with a REF code.  
3. Cite the REF in `PATCHLOG.txt`, commit messages, and future handoffs.  
4. Prepare necessary AI handoff notes for the next iteration.



# Spectra App — AI Handoff Bridge
 codex/improve-unit-conversions-and-file-uploads-udgaxh
_Last updated: 2025-09-21T23:00:00Z_
=======
_Last updated: 2025-09-21T02:00:00Z_
 main

This bridge document ties the brains log to the operative AI handoff prompt.
It is part of the mandated continuity template: Brains → AI Handoff → Patch Notes.

## Source of Truth
- Current prompt: `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.4.md`
- Next revision must update both this bridge and `docs/brains/brains_INDEX.md`.
- Keep handoff prompts UTF-8, versioned, and cross-linked from the paired brains + patch notes.

 codex/improve-unit-conversions-and-file-uploads-udgaxh
## Expectations for v1.1.5c
- Reflect the Streamlit width migration so future edits continue using the `width` parameter instead of `use_container_width`.
- Reference `docs/brains/brains_v1.1.5c.md`, `docs/PATCH_NOTES/v1.1.5c.txt`, and the Atlas index.
- Capture guidance about similarity label aliasing and the wavelength-metadata fallback alongside the existing ingestion rules.

## Checklist Before Shipping Changes
1. Read the latest brains entry and confirm the scope still matches.
2. Verify `docs/PATCH_NOTES/v1.1.5c.txt` lists the same continuity obligations.
=======
 codex/improve-unit-conversions-and-file-uploads-x1dj5i
## Expectations for v1.1.5b
- Extend the live handoff prompt with guidance about SI-normalised ingestion, provenance logging, and the in-app Atlas docs.
- Ensure the prompt references `docs/brains/brains_v1.1.5b.md`, `docs/PATCH_NOTES/v1.1.5b.txt`, and the Atlas index.
- Preserve instructions about provider cache directories and verification scripts.
=======
## Expectations for v1.1.5a+
- Do **not** regenerate the entire prompt—extend it incrementally.
- Include guidance about the new continuity manifest field and provider cache directories.
- Ensure every future prompt references `docs/brains/brains_v1.1.5a.md` until superseded.
 main

## Checklist Before Shipping Changes
1. Read the latest brains entry and confirm the scope still matches.
2. Verify `docs/PATCH_NOTES/v1.1.5b.txt` lists the same continuity obligations.
 main
3. Run `RUN_CMDS/Verify-Project.ps1` to confirm reciprocal links and provider directories are intact.
4. Prepare necessary AI handoff notes for the next iteration.