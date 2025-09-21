**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 08 - DEBUGGING PLAYBOOK (Server)
Concrete step-by-step when the UI goes blank or panels fail after a server change.

1. Reproduce locally using `Start-Spectra-Patched.ps1`. Check `logs/ui_debug.log` and `logs/server.log`.
2. If `ui_debug.log` shows SmartEntry import errors, inspect `app_patched.py.bak.*` and search for syntax errors or stray backslashes.
3. Run interactive Python: `python -c "import importlib; m=importlib.import_module('app.server.provenance'); print(dir(m))"` to see if import succeeds.
4. If import fails, run `python -m pyflakes app/server/*.py` or `flake8` to find syntax/indentation issues.
5. If blank screen but no exceptions: check Streamlit element tree by adding temporary `container.text('checkpoint')` statements in shell to localize where render stops.
6. Use the SmartEntry's exported `ui_debug.log` messages to narrow which module or entrypoint was tried last.
7. For regression caused by merging new files: diff `git show` the PR; revert locally and test to isolate problematic change.
8. If provenance merge corrupted manifest shape, restore `manifest` from saved export file or run `scripts/normalize_manifest.py`.

## Hotfix pattern
- Prefer small shims: replace complex function with a compatibility shim that returns a safe default and logs the error instead of raising.
