# 02_ENTRYPOINT_CONTRACT (v1.1.4x)

**Purpose:** make launching deterministic and boring.

## The contract
- UI root module **must export** `render()` with zero import‑time layout.
- Runner calls exactly one of: `render()` or `run_module(__main__)`. Prefer the former.
- A minimal header/banner must render before deep logic to guarantee first paint.
- Every attempt writes a line to `logs/ui_debug.log` with ISO UTC timestamps.

## Pseudocode
```python
def render():
    # set page config
    # draw banner + version badge
    # layout sidebar + route containers
    # dispatch to selected panel (docs/examples/home)
```
## Anti‑patterns
- Doing Streamlit calls on import.
- Guessing entry names without logging.
- Letting exceptions propagate to a blank screen.
