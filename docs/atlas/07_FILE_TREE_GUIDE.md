# 07_FILE_TREE_GUIDE (v1.1.4x)

**Goal:** help humans not get lost.

```
app/
  app_patched.py        # runner (tiny, logs, delegates)
  app_merged.py         # UI root; must export render()
  ui/                   # UI modules (entry, main, panels, widgets)
  utils/provenance.py   # tiny shim only
  server/               # provenance merger, models, fetchers
RUN_CMDS/               # idempotent launch/patch scripts
docs/                   # brains + atlas + patch notes
logs/ui_debug.log       # runtime breadcrumbs
```
