"""Solar irradiance example utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import pandas as pd

Kind = Literal["raw", "smoothed"]
Band = Literal["full", "uv", "uv-vis", "vis", "nir", "ir"]

DEFAULT_KIND: Kind = "smoothed"
DEFAULT_BAND: Band = "full"

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "examples"
_FIXTURE_PATH = _DATA_DIR / "solar_irradiance_sample.csv"
_SOURCE_URL = (
    "https://raw.githubusercontent.com/pvlib/pvlib-python/master/pvlib/data/ASTMG173.csv"
)

_SOLAR_BANDS: Dict[str, Tuple[float, Optional[float]]] = {
    "uv": (10.0, 320.0),
    "uv-vis": (320.0, 380.0),
    "vis": (380.0, 700.0),
    "nir": (700.0, 1400.0),
    "ir": (1400.0, None),
}

_FLUX_COLUMNS: Dict[Kind, str] = {
    "raw": "irradiance_w_m2_nm_raw",
    "smoothed": "irradiance_w_m2_nm_smoothed",
}

_REQUIRED_COLUMNS: Sequence[str] = (
    "wavelength_nm",
    "irradiance_w_m2_nm_raw",
    "irradiance_w_m2_nm_smoothed",
    "feature",
)


def available_bands(include_full: bool = True) -> Tuple[str, ...]:
    """Return the supported spectral bands for the solar example."""

    names: List[str] = list(_SOLAR_BANDS.keys())
    if include_full:
        names.insert(0, "full")
    return tuple(names)


@lru_cache(maxsize=1)
def _load_source() -> pd.DataFrame:
    if not _FIXTURE_PATH.exists():
        raise FileNotFoundError(
            "Solar irradiance fixture missing: run scripts/build_solar_example.py"
        )
    frame = pd.read_csv(_FIXTURE_PATH)
    missing = [column for column in _REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(
            f"Solar fixture {_FIXTURE_PATH} missing required columns: {missing}"
        )
    return frame.copy()


def _normalize_kind(kind: Kind | str) -> Kind:
    value = str(kind).strip().lower()
    if value not in _FLUX_COLUMNS:
        raise ValueError(f"Unsupported solar example kind: {kind}")
    return value  # type: ignore[return-value]


def _normalize_band(band: Optional[str]) -> Band:
    if band is None:
        return "full"
    value = str(band).strip().lower()
    if value in {"full", "all", "*", ""}:
        return "full"
    if value not in _SOLAR_BANDS:
        raise ValueError(f"Unsupported solar spectral band: {band}")
    return value  # type: ignore[return-value]


def _classify_band(wavelength_nm: float) -> str:
    for name, (lower, upper) in _SOLAR_BANDS.items():
        if wavelength_nm < lower:
            continue
        if upper is None or wavelength_nm < upper:
            return name
    # fall back to the final band
    return list(_SOLAR_BANDS.keys())[-1]


def _format_hover(label: str, wavelength_nm: float, flux: float) -> str:
    prefix = f"{wavelength_nm:.1f} nm"
    label = (label or "").strip()
    if label:
        prefix = f"{label} • {prefix}"
    return f"{prefix}<br>{flux:.3e} W/m^2/nm"


def _load_frame(kind: Kind) -> pd.DataFrame:
    flux_column = _FLUX_COLUMNS[_normalize_kind(kind)]
    source = _load_source()
    frame = pd.DataFrame(
        {
            "wavelength_nm": source["wavelength_nm"].astype(float),
            "irradiance_w_m2_nm": source[flux_column].astype(float),
        }
    )
    frame["band"] = [
        _classify_band(value) for value in frame["wavelength_nm"].tolist()
    ]
    if flux_column == _FLUX_COLUMNS["raw"]:
        features = source.get("feature", pd.Series(["" for _ in range(len(frame))]))
        frame["hover"] = [
            _format_hover(str(label), wavelength, flux)
            for label, wavelength, flux in zip(
                features.tolist(),
                frame["wavelength_nm"].tolist(),
                frame["irradiance_w_m2_nm"].tolist(),
            )
        ]
    return frame


def _apply_band_filter(frame: pd.DataFrame, band: Band) -> pd.DataFrame:
    normalized = _normalize_band(band)
    if normalized == "full":
        return frame.copy()
    lower, upper = _SOLAR_BANDS[normalized]
    mask = frame["wavelength_nm"] >= lower
    if upper is not None:
        mask &= frame["wavelength_nm"] < upper
    filtered = frame.loc[mask].reset_index(drop=True)
    return filtered


def load_frame(kind: Kind = DEFAULT_KIND, band: Band = DEFAULT_BAND) -> pd.DataFrame:
    """Return a solar irradiance frame filtered by the requested band."""

    base = _load_frame(kind)
    return _apply_band_filter(base, band)


def load_payload(kind: Kind = DEFAULT_KIND, band: Band = DEFAULT_BAND) -> Dict[str, object]:
    """Return an overlay payload compatible with the Streamlit UI."""

    normalized_kind = _normalize_kind(kind)
    normalized_band = _normalize_band(band)
    frame = load_frame(normalized_kind, normalized_band)

    hover = frame.get("hover")
    payload: Dict[str, object] = {
        "label": "Solar irradiance (smoothed)"
        if normalized_kind == "smoothed"
        else "Solar irradiance (raw)",
        "wavelength_nm": frame["wavelength_nm"].astype(float).tolist(),
        "flux": frame["irradiance_w_m2_nm"].astype(float).tolist(),
        "flux_unit": "W/m^2/nm",
        "flux_kind": "irradiance",
        "kind": "spectrum",
        "provider": "ASTM G173 / pvlib",
        "summary": "ASTM G173 solar spectral irradiance (global tilt)",
        "metadata": {
            "example_slug": "solar-irradiance",
            "example_kind": normalized_kind,
            "solar_band": normalized_band,
            "data_points": len(frame),
        },
        "provenance": {
            "source": "ASTM G173-03 Reference Spectra (SMARTS v2.9.2)",
            "url": _SOURCE_URL,
            "example_slug": "solar-irradiance",
        },
    }
    if normalized_band != "full":
        payload["summary"] += f" – {normalized_band.upper()} band"
    if hover is not None:
        payload["hover"] = hover.tolist()
    else:
        payload["hover"] = None
    return payload


__all__ = [
    "Band",
    "Kind",
    "DEFAULT_BAND",
    "DEFAULT_KIND",
    "available_bands",
    "load_frame",
    "load_payload",
]
