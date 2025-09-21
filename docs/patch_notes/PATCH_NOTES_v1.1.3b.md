# PATCH\_NOTES\_v1.1.3b

Date: 2025-09-19T21:52:21.104226Z

## Summary

Consolidated patch that requires no prior patches:

* Restores legacy UI (tabs/examples/version badge/expander) and integrates duplicate guard, unit logging, provenance, and differential.
* Adds UI Contract + verify script to prevent accidental UI regressions.
* Includes all utils so this patch stands alone.

## Acceptance

* Sidebar shows Examples, Display mode, Display units, Export.
* Tabs present: Overlay (default), Differential, Docs.
* Version badge visible; "What's new" expander present.
* Example traces render on first load; legend non-empty.
* Export writes CSV + manifest with unit logs and provenance entries.
