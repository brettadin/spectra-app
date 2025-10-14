# Log and Patch Naming Inconsistencies

The current repository retains a wealth of historical notes scattered across `brains/`, `atlas/`, and various `PATCHLOG` files.  Unfortunately, the naming conventions for these logs are inconsistent, making it difficult to reconstruct the timeline of development or trace specific changes.  This document summarises the observed problems and proposes a normalisation strategy.

## Observed Problems

1. **Day‑only filenames** – Several patches are named after a numerical day with no month or year (e.g. `05.txt`, `17.md`).  Without context, it is impossible to know whether “05” refers to May 5th or another day.  The redesign brief notes that the AI sometimes labelled logs “as a day of the month” incorrectly【875267955107972†L63-L74】.

2. **Mixed formats** – Some logs use `.txt` while others are `.md` or `.docx`.  The choice appears arbitrary.  A consistent extension would simplify parsing and documentation generation.

3. **Misaligned dates** – In a few cases, the date mentioned inside the file (e.g. in a header) does not match the filename.  For example, a log labelled `07-12-2025_fix-units.md` contains work performed on July 11th.

4. **Scattered location** – Historical notes are stored in multiple locations (`brains/`, `atlas/`, `docs/tech_notes/`, etc.).  Some directories have been renamed, leaving dangling references.

5. **No indexing** – There is no master index listing all logs and their contents.  Consequently, important decisions are effectively hidden.

## Normalisation Plan

To address these issues and create a coherent history for future agents, we propose the following steps:

1. **Define a canonical filename scheme:** Use ISO‑8601 dates and descriptive slugs, e.g. `YYYY‑MM‑DD_short-description.md`.  This provides chronological ordering and human‑readable context.  For example, a patch applied on 2025‑10‑05 to fix unit conversions would be named `2025‑10‑05_fix-unit-conversions.md`.

2. **Consolidate locations:** Move all historical notes into a single directory (`docs/history/`).  Subdirectories can group related entries (e.g. `patches/`, `brains/`, `atlas/`).  This way, a single index can list the entire development history.

3. **Write a normalisation script:** Implement a script (e.g. `tools/normalize_logs.py`) that performs the following:
   * Parses each existing log, extracts date information from headers or content, and infers missing month/year values based on nearby commits and file timestamps.
   * Renames the file according to the canonical scheme.
   * Inserts a front‑matter block at the top of each normalised file recording the original filename, its original location, and any assumptions made during normalisation.
   * Updates references within the repository (e.g. patch logs referencing other files) to the new names.

4. **Generate a knowledge index:** After normalisation, generate `docs/history/KNOWLEDGE_LOG.md`, a chronological index of all entries.  Each entry should include:
   * Date and time of the entry.
   * Short description or title.
   * Link to the log file.
   * Tags (e.g. `bugfix`, `feature`, `refactor`, `note`).
   * Author (if known; otherwise mark as AI agent or human user).

5. **Adopt guidelines for future logs:** Document the naming convention and index procedure in `docs/knowledge_guidelines.md`.  Require future agents to append new entries using the canonical scheme and update the index accordingly.

This normalisation will improve traceability and ensure continuity of knowledge across agent sessions.