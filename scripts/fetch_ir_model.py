"""Download the IR functional-group classifier assets.

Spectra ships with a lightweight linear surrogate so the UI works offline, but
fetching the published TensorFlow weights markedly improves predictions.
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
import sys

import requests

DEFAULT_MODEL_URL = "https://example.com/0_model_extended.h5"
DEFAULT_THRESHOLDS_URL = "https://example.com/optimal_thresholds.pkl"
TARGET_DIR = Path("ml_models/ir_groups")


def _download(url: str, destination: Path) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-url",
        default=DEFAULT_MODEL_URL,
        help="URL for the 0_model_extended.h5 asset",
    )
    parser.add_argument(
        "--threshold-url",
        default=DEFAULT_THRESHOLDS_URL,
        help="URL for the optimal_thresholds.pkl asset",
    )
    parser.add_argument(
        "--output-dir",
        default=str(TARGET_DIR),
        help="Directory to store the downloaded artifacts",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "0_model_extended.h5"
    thresholds_path = output_dir / "optimal_thresholds.pkl"

    print(f"Downloading model from {args.model_url} → {model_path}")
    _download(args.model_url, model_path)

    print(f"Downloading thresholds from {args.threshold_url} → {thresholds_path}")
    _download(args.threshold_url, thresholds_path)

    try:
        with thresholds_path.open("rb") as handle:
            loaded = pickle.load(handle)
        json_path = thresholds_path.with_suffix(".json")
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(loaded, handle, indent=2, sort_keys=True)
        print(f"Exported thresholds JSON → {json_path}")
    except Exception as exc:  # pragma: no cover - network or pickle failure
        print(f"Warning: unable to convert thresholds to JSON ({exc})")

    print("Download complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
