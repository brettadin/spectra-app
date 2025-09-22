All contributors must consult the Brains before making changes.
- The canonical knowledge base is in `docs/brains/brains_<version>.md` (use the latest version); past versions are archived for reference.
- Every change or new learning must be recorded there with a new **REF code**:
  - Format: `<PATCH>-<PART><SEQ>` (e.g., 1.1.5a-A01).
  - Each REF entry documents: What, Why, Where, How, Verification, and Provenance.
- REF codes must be:
  - Cross-referenced in `PATCHLOG.txt`.
  - Included in commit messages and PR descriptions.
  - Linked inside the AI handoff prompts for continuity.

**Contract checkpoints (must remain true every patch):**
- Unit toggles are idempotent (always derive from the canonical baseline).
- Fν/Fλ are never mixed on the same axis; axes are labeled with units.
- Legends have no empty entries or duplicates; metadata is always visible.
- Exports include PNG + CSV + manifest with provenance.
- Duplicate guard and provenance logs stay intact.

➡️ **If you are coding, updating, or patching:**
1. Read the latest Brains doc in full.
2. Add your new learnings to Brains with a REF code.
3. Cite the REF in `PATCHLOG.txt`, commit messages, and future handoffs.
4. Prepare the AI handoff notes for the next iteration.

# Spectra App — AI Handoff Bridge
_Last updated: 2025-09-22T01:22:08Z_

This bridge document ties the brains log to the operative AI handoff prompt.
It is part of the mandated continuity template: Brains → AI Handoff → Patch Notes.

## Source of Truth
- Current prompt: `docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.6b.md`
- Previous prompts remain under `docs/ai_handoff/` for historical context.
- Next revisions must update both this bridge and `docs/brains/brains_INDEX.md`.
- Keep handoff prompts UTF-8, versioned, and cross-linked from the paired brains + patch notes.

## Expectations for v1.1.6b
- Execute REF **1.1.6b-A01**: collapse archive metadata/provenance behind closed expanders while keeping “Add to overlay” accessible.
- Remove the redundant `Visible` checkbox column so the overlay multiselect governs visibility without desyncs.
- Ingest a telescope-observed solar spectrum as the default example, serving smoothed data by default with raw toggles and wavelength-band filters.
- Extend overlay traces with explicit unit semantics so emission/absorption render on dedicated, correctly labeled axes.
- Cache processed solar datasets and memoize loads to protect performance while maintaining provenance for smoothed and raw variants.

## Expectations for v1.1.5a (legacy reference)
- Do **not** regenerate the entire prompt—extend it incrementally.
- Include guidance about the continuity manifest field and provider directory requirements.
- Ensure every future prompt references `docs/brains/brains_v1.1.5a.md` until superseded.

## Checklist Before Shipping Changes
1. Read the latest brains entry and confirm the scope still matches.
2. Verify `docs/patch_notes/PATCH_NOTES_v1.1.6b.md` and `docs/PATCH_NOTES/v1.1.6b.txt` list the same continuity obligations.
3. Run `RUN_CMDS/Verify-Project.ps1` to confirm reciprocal links and provider directories are intact.
4. Prepare necessary AI handoff notes for the next iteration.
