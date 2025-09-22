# MAKE NEW BRAINS EACH TIME YOU MAKE A CHANGE. DO NOT OVER WRITE PREVIOUS BRAINS
All contributors must consult the Brains before making changes.
- The canonical knowledge base is in `docs/brains/brains_<version>.md` or <version>_brains.md (use the latest version); past versions are archived for reference.
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
_Last updated: 2025-09-22T12:00:00Z_

This bridge document ties the brains log to the operative AI handoff prompt.
It is part of the mandated continuity template: Brains → AI Handoff → Patch Notes.

## Source of Truth
- Current prompt: `docs/ai_handoff/AI Handoff Prompt — v1.1.7.txt`
- Previous prompts remain under `docs/ai_handoff/` for historical context.
- Next revisions must update both this bridge and `docs/brains/brains_INDEX.md`.
- Keep handoff prompts UTF-8, versioned, and cross-linked from the paired brains + patch notes.

## Expectations for v1.1.7
- Execute REF **1.1.7-A01**: deliver the aggregated **All Archives** workflow without regressing overlay, differential, or export behaviour.
- Implement `app/providers/combined.py` so a single `ProviderQuery` returns concatenated hits from MAST, ESO, and SDSS even when one provider fails.
- Register the `ALL` provider in `app/providers/__init__.py` with lazy imports and expose the "All Archives" label to the UI.
- Update `ArchiveUI` to surface the new tab ahead of MAST/ESO/SDSS, reuse the standard search form, and dispatch `provider_search("ALL", query)`.
- Extend the test suite to cover combined-provider aggregation, exception handling, and the new UI tab/form behaviour.
- Refresh continuity docs: brains_v1.1.7.md, patch notes (Markdown + txt), AI handoff references, and patch log/version metadata.

## Expectations for v1.1.6b
- Execute REF **1.1.6b-A01**: collapse archive metadata/provenance behind closed expanders while keeping “Add to overlay” accessible.
- Remove the redundant `Visible` checkbox column so the overlay multiselect governs visibility without desyncs.
- Ingest a telescope-observed solar spectrum as the default example, serving smoothed data by default with raw toggles and wavelength-band filters.
- Extend overlay traces with explicit unit semantics so emission/absorption render on dedicated, correctly labeled axes.
- Cache processed solar datasets and memoize loads to protect performance while maintaining provenance for smoothed and raw variants.
## Expectations for v1.1.5a (legacy reference)
- Do **not** regenerate the entire prompt—extend it incrementally.
- Include guidance about the continuity manifest field and provider directory requirements.
- Ensure every future prompt references `docs/brains/brains_v1.1.5a.md` until superseded. ## has been superseeded

## Checklist Before Shipping Changes
1. Read the latest brains entry and confirm the scope still matches.
2. Verify `docs/patch_notes/PATCH_NOTES_v1.1.7.md` and `docs/PATCH_NOTES/v1.1.7.txt` list the same continuity obligations.
3. Run `RUN_CMDS/Verify-Project.ps1` to confirm reciprocal links and provider directories are intact.
4. Prepare necessary AI handoff notes for the next iteration.
