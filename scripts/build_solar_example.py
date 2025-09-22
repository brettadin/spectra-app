#!/usr/bin/env python3
"""Generate the solar irradiance example artifacts.

This script downloads the ASTM G173 reference spectrum (via the pvlib
project) and produces three artifacts inside ``data/examples``:

* ``solar_irradiance_raw.parquet`` – high resolution solar spectral irradiance
  values.
* ``solar_irradiance_smoothed.parquet`` – smoothed irradiance values using a
  rolling median filter.
* ``solar_irradiance_sample.csv`` – a down-sampled, text-friendly snapshot that
  is small enough to store in the repository. This fixture powers unit tests
  and offline documentation examples.

If ``pyarrow`` or ``fastparquet`` are unavailable, the Parquet files are
skipped with a warning; the CSV fixture is always emitted.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd

DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/pvlib/pvlib-python/master/pvlib/data/ASTMG173.csv"
)

# Spectral band boundaries (inclusive lower bound, exclusive upper bound except
# for the final band).
BAND_LIMITS: Tuple[Tuple[str, float, Optional[float]], ...] = (
    ("uv", 10.0, 320.0),
    ("uv-vis", 320.0, 380.0),
    ("vis", 380.0, 700.0),
    ("nir", 700.0, 1400.0),
    ("ir", 1400.0, None),
)

# Wavelengths (in nm) of notable Fraunhofer features for hover annotations.
FEATURE_LINES: Tuple[Tuple[float, str], ...] = (
    (393.37, "Ca II K"),
    (396.85, "Ca II H"),
    (430.79, "G-band"),
    (486.13, "Hβ"),
    (517.27, "Mg I b"),
    (589.29, "Na I D"),
    (656.28, "Hα"),
    (777.36, "O I triplet"),
    (854.21, "Ca II IR"),
)


@dataclass(frozen=True)
class SolarArtifactPaths:
    """Collection of output paths for the solar example artifacts."""

    raw_parquet: Path
    smoothed_parquet: Path
    sample_csv: Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _examples_dir(base: Optional[Path] = None) -> Path:
    base = base or _project_root()
    return base / "data" / "examples"


def _load_source(source: str) -> pd.DataFrame:
    path = Path(source)
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.read_csv(source, skiprows=1)
    if "wavelength" not in df.columns or "global" not in df.columns:
        raise ValueError("Source data must include 'wavelength' and 'global' columns")
    frame = df.rename(
        columns={
            "wavelength": "wavelength_nm",
            "global": "irradiance_w_m2_nm",
        }
    )
    frame = frame[["wavelength_nm", "irradiance_w_m2_nm"]].astype(float)
    frame = frame.sort_values("wavelength_nm").reset_index(drop=True)
    return frame


def _classify_band(value: float) -> str:
    for name, lower, upper in BAND_LIMITS:
        if value < lower:
            continue
        if upper is None or value < upper:
            return name
    return BAND_LIMITS[-1][0]


def _annotate_features(frame: pd.DataFrame) -> pd.Series:
    annotations = pd.Series(["" for _ in range(len(frame))], dtype="object")
    for target, label in FEATURE_LINES:
        idx = (frame["wavelength_nm"] - target).abs().idxmin()
        annotations.iloc[idx] = f"{label}"
    return annotations


def _rolling_median(frame: pd.DataFrame, window: int) -> pd.Series:
    return frame["irradiance_w_m2_nm"].rolling(
        window=window, center=True, min_periods=1
    ).median()


def _downsample_indices(length: int, step: int, include: Iterable[int]) -> List[int]:
    indices = set(range(0, length, step))
    indices.update(int(i) for i in include if 0 <= int(i) < length)
    return sorted(indices)


def _resolve_paths(base: Optional[Path] = None) -> SolarArtifactPaths:
    target_dir = _examples_dir(base)
    target_dir.mkdir(parents=True, exist_ok=True)
    return SolarArtifactPaths(
        raw_parquet=target_dir / "solar_irradiance_raw.parquet",
        smoothed_parquet=target_dir / "solar_irradiance_smoothed.parquet",
        sample_csv=target_dir / "solar_irradiance_sample.csv",
    )


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    try:
        frame.to_parquet(path, index=False)
    except ImportError as exc:
        logging.warning("Skipping %s (pyarrow/fastparquet unavailable): %s", path, exc)
    else:
        logging.info("Wrote %s (%d rows)", path, len(frame))


def build_solar_example(
    source: str = DEFAULT_SOURCE_URL,
    sample_step: int = 40,
    smoothing_window: int = 65,
    output_base: Optional[Path] = None,
) -> SolarArtifactPaths:
    """Build solar example artifacts from the provided data source."""

    logging.info("Loading solar spectrum from %s", source)
    frame = _load_source(source)

    logging.info("Computing rolling median with window=%d", smoothing_window)
    smoothed = _rolling_median(frame, window=smoothing_window)

    logging.info("Annotating Fraunhofer features")
    annotations = _annotate_features(frame)

    enriched = frame.copy()
    enriched["band"] = [
        _classify_band(value) for value in enriched["wavelength_nm"].values
    ]
    enriched["feature"] = annotations
    enriched["irradiance_w_m2_nm_smoothed"] = smoothed

    feature_indices = annotations[annotations.astype(bool)].index.tolist()
    sample_indices = _downsample_indices(len(enriched), sample_step, feature_indices)
    sample = enriched.iloc[sample_indices].copy().reset_index(drop=True)
    sample["feature"] = sample["feature"].fillna("")

    paths = _resolve_paths(output_base)

    logging.info("Writing CSV fixture to %s", paths.sample_csv)
    sample.rename(
        columns={
            "irradiance_w_m2_nm": "irradiance_w_m2_nm_raw",
        }
    )[[
        "wavelength_nm",
        "irradiance_w_m2_nm_raw",
        "irradiance_w_m2_nm_smoothed",
        "feature",
    ]].to_csv(paths.sample_csv, index=False, float_format="%.9g")

    raw_output = enriched[[
        "wavelength_nm",
        "irradiance_w_m2_nm",
        "band",
        "feature",
    ]].rename(columns={"irradiance_w_m2_nm": "flux"})

    smoothed_output = enriched[[
        "wavelength_nm",
        "irradiance_w_m2_nm_smoothed",
        "band",
    ]].rename(columns={"irradiance_w_m2_nm_smoothed": "flux"})

    _write_parquet(raw_output, paths.raw_parquet)
    _write_parquet(smoothed_output, paths.smoothed_parquet)

    return paths


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE_URL,
        help="Path or URL for the input solar spectrum CSV (default: ASTM G173 via pvlib)",
    )
    parser.add_argument(
        "--sample-step",
        type=int,
        default=40,
        help="Down-sampling stride for the text fixture",
    )
    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=65,
        help="Window size for the rolling median smoother",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=None,
        help="Override the project root for outputs (mainly for testing)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> SolarArtifactPaths:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    return build_solar_example(
        source=str(args.source),
        sample_step=args.sample_step,
        smoothing_window=args.smoothing_window,
        output_base=args.output_base,
    )


if __name__ == "__main__":
    main()
