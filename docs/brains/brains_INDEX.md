# Spectra App — Brains Index
<<<<<<< HEAD
 codex/improve-unit-conversions-and-file-uploads-ussv5s
_Last updated: 2025-09-21T23:00:00Z_
=======
 codex/improve-unit-conversions-and-file-uploads-udgaxh
_Last updated: 2025-09-21T23:00:00Z_
=======
_Last updated: 2025-09-21T02:00:00Z_
 main
 main
=======
_Last updated: 2025-09-21T00:00:00Z_
>>>>>>> parent of 9fe7c940 (v1.1.5d: fix export imports and surface atlas docs)

This index is the mandated entry point before touching the codebase.
It tracks the latest continuity documents and the required cross-links between them.

## Required Reading Order
1. Start with the **current brains log** for context.
2. Read the **AI handoff brief** to understand the live guardrails.
3. Review the **paired patch notes** so you know what shipped and what still needs follow-up.
4. Skim provider directories under `data/providers/` if you are touching fetchers or caches.

## Continuity Table
| Version | Brains Log | Patch Notes | AI Handoff |
| --- | --- | --- | --- |
<<<<<<< HEAD
 codex/improve-unit-conversions-and-file-uploads-ussv5s
| v1.1.5d | [docs/brains/brains_v1.1.5d.md](brains_v1.1.5d.md) | [docs/PATCH_NOTES/v1.1.5d.txt](../PATCH_NOTES/v1.1.5d.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5c | [docs/brains/brains_v1.1.5c.md](brains_v1.1.5c.md) | [docs/PATCH_NOTES/v1.1.5c.txt](../PATCH_NOTES/v1.1.5c.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
=======
 codex/improve-unit-conversions-and-file-uploads-udgaxh
| v1.1.5c | [docs/brains/brains_v1.1.5c.md](brains_v1.1.5c.md) | [docs/PATCH_NOTES/v1.1.5c.txt](../PATCH_NOTES/v1.1.5c.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
=======
 main
 main
| v1.1.5b | [docs/brains/brains_v1.1.5b.md](brains_v1.1.5b.md) | [docs/PATCH_NOTES/v1.1.5b.txt](../PATCH_NOTES/v1.1.5b.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
=======
>>>>>>> parent of 9fe7c940 (v1.1.5d: fix export imports and surface atlas docs)
| v1.1.5a | [docs/brains/brains_v1.1.5a.md](brains_v1.1.5a.md) | [docs/PATCH_NOTES/v1.1.5a.txt](../PATCH_NOTES/v1.1.5a.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |

Older releases remain in `docs/brains/` and `docs/patches/` for archeology, but the table above is the active continuity contract.

## Provider Directories
Continuity-critical fetchers cache artifacts in these directories. The `Verify-Project` script now fails if any are missing.
- `data/providers/mast/`
- `data/providers/eso/`
- `data/providers/simbad/`
- `data/providers/nist/`

Always commit new provider caches or metadata with a README explaining provenance.
