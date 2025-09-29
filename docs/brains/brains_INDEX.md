# MAKE NEW BRAINS EACH TIME YOU MAKE A CHANGE. DO NOT OVER WRITE PREVIOUS BRAINS * unless needed
# Spectra App — Brains Index
_Last updated: 2025-09-28T23:00:00Z_

This index is the mandated entry point before touching the codebase.
It tracks the latest continuity documents and the required cross-links between them.

## Required Reading Order
1. Start with the **current brains log** for context.
2. Read the **AI handoff brief** to understand the live guardrails.
3. Review the **paired patch notes** to learn what shipped and what still needs follow-up.
4. Skim provider directories under `data/providers/` if you are touching fetchers or caches.

## Continuity Table
| Version | Brains Log | Patch Notes | AI Handoff |
| --- | --- | --- | --- |
| v1.1.9 | [docs/brains/brains_v1.1.9.md](brains_v1.1.9.md) | [docs/patch_notes/PATCH_NOTES_v1.1.9.md](../patch_notes/PATCH_NOTES_v1.1.9.md) | — |
| v1.1.8 | [docs/brains/brains_v1.1.8.md](brains_v1.1.8.md) | [docs/patch_notes/PATCH_NOTES_v1.1.8.md](../patch_notes/PATCH_NOTES_v1.1.8.md) | [docs/ai_handoff/AI Handoff Prompt — v1.1.8.txt](../ai_handoff/AI%20Handoff%20Prompt%20—%20v1.1.8.txt) |
| v1.1.7 | [docs/brains/brains_v1.1.7.md](brains_v1.1.7.md) | [docs/patch_notes/PATCH_NOTES_v1.1.7.md](../patch_notes/PATCH_NOTES_v1.1.7.md) | [docs/ai_handoff/AI Handoff Prompt — v1.1.7.txt](../ai_handoff/AI%20Handoff%20Prompt%20—%20v1.1.7.txt) |
| v1.1.6b | [docs/brains/brains_v1.1.6b.md](brains_v1.1.6b.md) | [docs/patch_notes/PATCH_NOTES_v1.1.6b.md](../patch_notes/PATCH_NOTES_v1.1.6b.md) | [docs/ai_handoff/AI_HANDOFF_PROMPT_v1.1.6b.md](../ai_handoff/AI_HANDOFF_PROMPT_v1.1.6b.md) |
| v1.1.6 | [docs/brains/brains_v1.1.6.md](brains_v1.1.6.md) | [docs/patch_notes/PATCH_NOTES_v1.1.6.md](../patch_notes/PATCH_NOTES_v1.1.6.md) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5a | [docs/brains/brains_v1.1.5a.md](brains_v1.1.5a.md) | [docs/PATCH_NOTES/v1.1.5a.txt](../PATCH_NOTES/v1.1.5a.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |

Older releases remain in `docs/brains/` and `docs/patches/` for archeology, but the table above is the active continuity contract.

- Patch notes (md) for v1.1.9: docs/patch_notes/PATCH_NOTES_v1.1.9.md
- Patch notes (txt) for v1.1.9: docs/PATCH_NOTES/v1.1.9.txt
- Patch notes (txt) for v1.1.8: docs/PATCH_NOTES/v1.1.8.txt
- Patch notes (txt) for v1.1.7: docs/PATCH_NOTES/v1.1.7.txt
- Patch notes (txt) for v1.1.6b: docs/PATCH_NOTES/v1.1.6b.txt
- Patch notes (txt) for v1.1.6: docs/PATCH_NOTES/v1.1.6.txt

## Provider Directories
Continuity-critical fetchers cache artifacts in these directories. The `Verify-Project` script fails if any are missing.
- `data/providers/mast/`
- `data/providers/eso/`
- `data/providers/sdss/`
- `data/providers/doi/`
- `data/providers/simbad/`
- `data/providers/nist/`

Always commit new provider caches or metadata with a README explaining provenance.
