# UI_FIRST_PAINT_CONTRACT (v1.1.4x)

Non-negotiables:
1. A visible frame must render on every route and at launch.
2. All panel handlers render inside an existing container; they never own the full-page lifecycle.
3. Any exception becomes an inline error block plus a log line.
4. Version badge is always visible; it never depends on data load.
