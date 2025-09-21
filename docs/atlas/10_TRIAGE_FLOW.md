# 10_TRIAGE_FLOW (v1.1.4x)

**Blank page?**
→ Check `ui_debug.log` for EXPORTS and TRY_ENTRY lines.
- If no `render` exported: add it or wire to `app.ui.entry.render()`.
- If handler breaks: wrap and render error.
- If badge missing: confirm `version.json` load path.
