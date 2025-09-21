# UI_DEBUGGING_PLAYBOOK (v1.1.4x)

1) Confirm first paint. If blank, inject a minimal header in the entry callable and try again.
2) Click Docs/Examples. If blank, handler threw. Wrap with try/except; render error block with context.
3) Toggle dedupe scope. If blank, state reset path isn’t re-rendering. Force a re-render at the end of the handler.
4) Read `ui_debug.log`. Expect lines for ENTRY, EXPORTS, TRY_ENTRY, and any handler failures.
