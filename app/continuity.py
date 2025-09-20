from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from app._version import get_version_info


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def get_continuity_links() -> Dict[str, object]:
    """Return the continuity metadata for the current version."""

    root = _repo_root()
    version = get_version_info().get("version", "unknown")

    brains_index = root / "docs" / "brains" / "brains_INDEX.md"
    ai_bridge = root / "docs" / "brains" / "ai_handoff.md"
    brains = root / "docs" / "brains" / f"brains_{version}.md"
    patch_notes = root / "docs" / "PATCH_NOTES" / f"{version}.txt"
    provider_root = root / "data" / "providers"
    provider_dirs = [
        provider_root / "mast",
        provider_root / "eso",
        provider_root / "simbad",
        provider_root / "nist",
    ]

    required_paths: Dict[str, Path] = {
        "brains_index": brains_index,
        "ai_handoff_bridge": ai_bridge,
        "brains": brains,
        "patch_notes": patch_notes,
        "provider_root": provider_root,
    }

    missing = [name for name, path in required_paths.items() if not path.exists()]
    if missing:
        joined = ", ".join(f"{name}: {required_paths[name]}" for name in missing)
        raise FileNotFoundError(f"Missing continuity asset(s): {joined}")

    missing_providers: List[Path] = [p for p in provider_dirs if not p.exists()]
    if missing_providers:
        joined = ", ".join(str(p) for p in missing_providers)
        raise FileNotFoundError(f"Missing provider directories: {joined}")

    return {
        "version": version,
        "brains": _relative_posix(brains, root),
        "patch_notes": _relative_posix(patch_notes, root),
        "ai_handoff_bridge": _relative_posix(ai_bridge, root),
        "index": _relative_posix(brains_index, root),
        "provider_directories": [
            _relative_posix(directory, root) for directory in provider_dirs
        ],
    }


__all__ = ["get_continuity_links"]
