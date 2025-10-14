# Consolidated Knowledge Log

This file serves as the single entry point for all historical notes, patches,
"brains" and "atlas" logs.  Previous iterations of Spectra‑App stored
information in many places (e.g. `brains`, `atlas`, `PATCHLOG.txt`) and often
used confusing naming schemes (sometimes based on the day of the month)【875267955107972†L63-L74】.
To avoid further fragmentation, every meaningful change or insight should be
recorded here with a timestamp and a clear description.

## Log Format

Each entry in this document should follow this structure:

```markdown
## YYYY‑MM‑DD HH:MM – [Component]

**Author**: human or agent name

**Context**: Short description of what part of the system this log refers to
  (e.g. Unit conversion, UI logic, Importer plugin).

**Summary**: Concise explanation of what was done, why it was necessary, and
  any immediate outcomes or open questions.

**References**: Links to relevant files, commits or external sources (use
  citation markers like 【875267955107972†L29-L41】 for primary documentation where
  applicable).

---
```

Entries should be appended chronologically.  Older logs imported from the
original repository can be summarised and linked at the end of this file.
When summarising legacy content, include a note indicating that the details
come from a previous format (e.g. “Imported from brains/2023‑04‑10.md”).

## Example Entry

```markdown
## 2025‑10‑14 15:23 – Units Service

**Author**: agent

**Context**: Implementation of the new UnitsService for the PySide6 rewrite.

**Summary**: Added support for converting wavelength between nm, μm and
  wavenumber, as well as intensity between absorbance and transmittance.  The
  service ensures idempotent conversions and records conversion metadata.
  Tested round‑trip conversions manually.【328409478188748†L22-L59】

**References**: `app/services/units_service.py`, design spec in
  `specs/units_and_conversions.md`, and original conversion formulas from
  `server/ir_units.py` in the legacy code【328409478188748†L22-L59】.

---
```

## Migration of Legacy Logs

To migrate existing `brains` and `atlas` logs, follow these steps:

1. Identify all existing log files in the old repository.  Normalize their
   names to the `YYYY‑MM‑DD_description.md` format.  If a file name refers
   to the day of the month rather than the actual date, determine the
   correct date by examining commit history or file metadata【875267955107972†L63-L74】.
2. Summarise the content of each file into a single entry in this log.  Use
   bullet points to capture key decisions, problems solved, and lessons
   learned.  Reference the original file location for traceability.
3. After migration, store the original files in an archive folder so that
   nothing is lost.

## Policy

* **Honesty**: Be transparent about decisions and mistakes.  If an entry
  describes an incorrect approach, annotate the outcome and how it was
  resolved.
* **Completeness**: Include enough information for future developers or
  agents to understand the context without having to search through commit
  history.  When in doubt, write more rather than less.
* **Citation**: Use tether IDs to cite official documents, academic papers or
  authoritative resources.  This ensures that claims can be verified.
