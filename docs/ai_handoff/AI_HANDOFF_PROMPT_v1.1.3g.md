# AI Handoff Prompt — v1.1.3g
_Last updated: 2025-09-19T23:29:54.799027Z_

## Context
You are taking over development of the **Spectra App**, a Streamlit-based tool for ingesting, comparing, and exporting spectral data.  
The app is already stable in its **Overlay** and **Differential** modes, with robust unit conversions, duplicate handling, and export features.

This is a **patch-only project**: you must never overwrite or rebuild from scratch. All updates must extend functionality while preserving existing features.

---

## Continuity Rules
1. **Read Before Acting**  
   - Load the most recent Brains file: `docs/Brains_v1.1.3g.md`  
   - Load the most recent AI_HANDOFF file: `docs/AI_HANDOFF_PROMPT_v1.1.3g.md`  
   These are the single sources of truth for continuity.

2. **Patch Discipline**  
   - Always bump patch version numbers (e.g., v1.1.3h).  
   - All files must be UTF-8, structured, with no placeholders or ellipses.  
   - Maintain patch notes under `docs/patches/`.  
   - Maintain checksums and version.json.  
   - Update the Brains file with every patch.

3. **Do Not Break**  
   - Overlay, Differential, Export, unit conversions, and duplicate guard must remain intact.  
   - Any new functionality must be modular — added alongside, not replacing existing code.

---

## Current State (from Brains v1.1.3g)
- **Overlay:** Stable with examples, CSV/TXT ingestion, large dataset handling, dedupe guard, export with manifest.  
- **Differential:** Stable math for A−B and A/B; issues remain with dropdown resets, legend clutter, and division spikes near zero.  
- **Unit Conversions:** Idempotent across nm, Å, µm, cm⁻¹.  
- **Duplicate Guard:** Functional with Global/Session/Off scope + override and purge options.  
- **Provenance:** Export manifest includes unit logs and lineage.  
- **Outstanding Issues:** Dropdown reset, trace list clutter, legend duplication in trivial results, division instability near zero denominators.

---

## Next Objectives
**Introduce Data Fetching** without breaking existing build:  
- Implement modular data fetchers (e.g., Astroquery, MAST, SIMBAD, ESO).  
- Ensure fetched datasets include **full provenance**: DOI, URL, instrument, citation.  
- Integrate fetched data into overlays as if they were uploaded files.  
- Preserve canonical nm baseline and provenance logs.  
- Update Brains with lessons from data fetching integration.

---

## Deliverables for Each Patch
- Updated `app/` code (modular additions, not rewrites).  
- Updated `app/version.json` with new patch version + timestamp.  
- New patch notes in `docs/patches/`.  
- Updated `CHECKSUMS.txt`.  
- Updated Brains file (e.g., `docs/Brains_v1.1.3h.md`).  
- Updated AI_HANDOFF prompt for next handoff.

---

## Summary
You are not starting fresh — you are continuing a carefully versioned, patch-only project.  
Your first task in this build cycle is to add **modular data fetching** while keeping Overlay/Differential intact.  
Every change must be documented in Brains and AI_HANDOFF to maintain project continuity.
