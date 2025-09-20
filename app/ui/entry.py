# app/ui/entry.py — v1.1.4c9d
def render():
    import importlib
    try:
        ui_main = importlib.import_module("app.ui.main")
    except Exception:
        try:
            importlib.import_module("app.ui")
        except Exception:
            return
        else:
            return
    # Try common callables on the imported module or its 'main' attribute
    for mod in (ui_main, getattr(ui_main, "main", ui_main)):
        for name in ("render","main","app","run","entry","ui"):
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn()
    # If none found, assume top-level import already rendered
    return
