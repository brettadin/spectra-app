# UI_EVENT_MAP (v1.1.4x)

**Sidebar routes and what they call**

- Home → `app.ui.main.render()`
- Docs → `app.ui.main.render()` then `docs_panel()`
- Examples → `app.ui.main.render()` then `examples_panel()`
- Unit toggle → `widgets.units_and_dedupe.apply_units()` and re-render
- Dedupe scope → `widgets.units_and_dedupe.apply_scope()` and re-render
