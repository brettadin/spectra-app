"""Panel registry for Spectra App UI components.

This module provides a lightweight plugin-style registry inspired by
SpecViz/Jdaviz where sidebar panels and workspace tabs register render
callables with identifiers and ordering metadata. Streamlit callers can
then request the registered panels to build the layout dynamically
without hard-coding module level imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping

try:  # Optional typing dependency; Streamlit is available at runtime.
    from streamlit.delta_generator import DeltaGenerator
except Exception:  # pragma: no cover - typing fallback when Streamlit missing.
    DeltaGenerator = Any  # type: ignore

PanelContext = Mapping[str, Any]
SidebarRenderFn = Callable[[DeltaGenerator, PanelContext], None]
WorkspaceRenderFn = Callable[[PanelContext], None]


@dataclass(frozen=True)
class SidebarPanel:
    """Sidebar panel registration metadata."""

    panel_id: str
    label: str
    render: SidebarRenderFn
    order: float = 0.0


@dataclass(frozen=True)
class WorkspacePanel:
    """Workspace tab registration metadata."""

    panel_id: str
    label: str
    render: WorkspaceRenderFn
    order: float = 0.0


class PanelRegistry:
    """Registry storing sidebar and workspace panels."""

    def __init__(self) -> None:
        self._sidebar: Dict[str, SidebarPanel] = {}
        self._workspace: Dict[str, WorkspacePanel] = {}

    # ------------------------------------------------------------------
    # Sidebar panels
    # ------------------------------------------------------------------
    def register_sidebar(self, panel: SidebarPanel) -> SidebarPanel:
        if panel.panel_id in self._sidebar:
            raise ValueError(f"Sidebar panel '{panel.panel_id}' already registered")
        self._sidebar[panel.panel_id] = panel
        return panel

    def iter_sidebar(self) -> Iterable[SidebarPanel]:
        return sorted(
            self._sidebar.values(),
            key=lambda item: (item.order, item.label.lower(), item.panel_id),
        )

    # ------------------------------------------------------------------
    # Workspace panels
    # ------------------------------------------------------------------
    def register_workspace(self, panel: WorkspacePanel) -> WorkspacePanel:
        if panel.panel_id in self._workspace:
            raise ValueError(f"Workspace panel '{panel.panel_id}' already registered")
        self._workspace[panel.panel_id] = panel
        return panel

    def iter_workspace(self) -> Iterable[WorkspacePanel]:
        return sorted(
            self._workspace.values(),
            key=lambda item: (item.order, item.label.lower(), item.panel_id),
        )


_registry = PanelRegistry()


def get_panel_registry() -> PanelRegistry:
    return _registry


def register_sidebar_panel(
    panel_id: str,
    label: str,
    render: SidebarRenderFn,
    *,
    order: float = 0.0,
) -> SidebarPanel:
    """Register a sidebar panel on the global registry."""

    panel = SidebarPanel(panel_id=panel_id, label=label, render=render, order=order)
    return _registry.register_sidebar(panel)


def register_workspace_panel(
    panel_id: str,
    label: str,
    render: WorkspaceRenderFn,
    *,
    order: float = 0.0,
) -> WorkspacePanel:
    """Register a workspace tab on the global registry."""

    panel = WorkspacePanel(panel_id=panel_id, label=label, render=render, order=order)
    return _registry.register_workspace(panel)


__all__ = [
    "PanelContext",
    "PanelRegistry",
    "SidebarPanel",
    "WorkspacePanel",
    "get_panel_registry",
    "register_sidebar_panel",
    "register_workspace_panel",
]
