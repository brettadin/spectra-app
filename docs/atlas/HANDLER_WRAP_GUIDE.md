# HANDLER_WRAP_GUIDE (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:48:19Z  
**Author:** v1.1.4

Short recipes for robust handlers.

## File load
```python
def try_load_csv(path: str):
    import pandas as pd
    try:
        return pd.read_csv(path)
    except pd.errors.ParserError as e:
        return None, f"CSV parse error: {e}"
    except Exception as e:
        return None, str(e)
```

## Unit toggle
```python
def apply_units(df, target):
    try:
        # convert between nm / Å / µm / cm⁻¹
        return convert_df(df, target)
    except Exception as e:
        st.warning(f"Unit conversion failed: {e}")
        return df
```
