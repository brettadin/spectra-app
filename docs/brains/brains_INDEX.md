# Spectra App — Brains Index
_Last updated: 2025-09-23T12:00:00Z_

This index is the mandated entry point before touching the codebase.
It tracks the latest continuity documents and the required cross-links between them.

## Required Reading Order
1. Start with the **current brains log** for context.
2. Read the **AI handoff bridge** to understand the live guardrails.
3. Review the **paired patch notes** so you know what shipped and what still needs follow-up.
4. Skim provider directories under `data/providers/` if you are touching fetchers or caches.

## Continuity Table
| Version | Brains Log | Patch Notes | AI Handoff |
| --- | --- | --- | --- |
| v1.1.5f | [docs/brains/brains_v1.1.5f.md](brains_v1.1.5f.md) | [docs/PATCH_NOTES/v1.1.5f.txt](../PATCH_NOTES/v1.1.5f.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5e | [docs/brains/brains_v1.1.5e.md](brains_v1.1.5e.md) | [docs/PATCH_NOTES/v1.1.5e.txt](../PATCH_NOTES/v1.1.5e.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5d | [docs/brains/brains_v1.1.5d.md](brains_v1.1.5d.md) | [docs/PATCH_NOTES/v1.1.5d.txt](../PATCH_NOTES/v1.1.5d.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5c | [docs/brains/brains_v1.1.5c.md](brains_v1.1.5c.md) | [docs/PATCH_NOTES/v1.1.5c.txt](../PATCH_NOTES/v1.1.5c.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5b | [docs/brains/brains_v1.1.5b.md](brains_v1.1.5b.md) | [docs/PATCH_NOTES/v1.1.5b.txt](../PATCH_NOTES/v1.1.5b.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |
| v1.1.5a | [docs/brains/brains_v1.1.5a.md](brains_v1.1.5a.md) | [docs/PATCH_NOTES/v1.1.5a.txt](../PATCH_NOTES/v1.1.5a.txt) | [docs/brains/ai_handoff.md](ai_handoff.md) |

Older releases remain in `docs/brains/` and `docs/patches/` for archeology, but the table above is the active continuity contract.

## Provider Directories
Continuity-critical fetchers cache artifacts in these directories. The `Verify-Project` script fails if any are missing.
- `data/providers/mast/`
- `data/providers/eso/`
- `data/providers/simbad/`
- `data/providers/nist/`

Always commit new provider caches or metadata with a README explaining provenance.
