"""Compatibility wrapper preserved for legacy launch scripts."""
from __future__ import annotations

from app.app_merged import main as _merged_main, render as _merged_render


def render() -> None:
    _merged_render()


def main() -> None:
    _merged_main()


if __name__ == "__main__":
    main()
