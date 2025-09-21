# 03_RUNTIME_LIFECYCLE (v1.1.4x)

1) **Import runner** → log SMARTENTRY BOOT.

2) **Import UI root** (`app.app_merged`) → log IMPORT and EXPORTS.

3) **Call render()** → header + version badge + containers.

4) **User events** (docs/examples/scope/units) → handlers run inside containers.

5) **Errors** → `st.error` + log line; never blank.
