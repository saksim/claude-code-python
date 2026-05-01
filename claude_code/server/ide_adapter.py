"""IDE protocol adapters backed by daemon control-plane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from claude_code.server.control_plane import ControlPlaneClient


@dataclass(frozen=True, slots=True)
class IDEWorkspaceSnapshot:
    """Normalized IDE snapshot payload from daemon."""

    working_directory: str
    diff: dict[str, Any]
    changed_files: list[dict[str, str]]
    sessions: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    findings: list[dict[str, Any]]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "IDEWorkspaceSnapshot":
        workspace = payload.get("workspace", {}) if isinstance(payload, dict) else {}
        return cls(
            working_directory=str(workspace.get("working_directory", "")),
            diff=dict(workspace.get("diff", {})),
            changed_files=list(workspace.get("changed_files", [])),
            sessions=list(workspace.get("sessions", [])),
            tasks=list(workspace.get("tasks", [])),
            findings=list(workspace.get("findings", [])),
        )


def _map_inspection_highlight(severity: Any) -> str:
    normalized = str(severity or "").strip().lower()
    if normalized in {"critical", "high"}:
        return "error"
    if normalized in {"medium"}:
        return "warning"
    if normalized in {"low"}:
        return "weak_warning"
    return "warning"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class JetBrainsWorkspaceSnapshot:
    """Normalized workspace payload for JetBrains client workflows."""

    project_root: str
    vcs: dict[str, Any]
    sessions: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    inspections: list[dict[str, Any]]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "JetBrainsWorkspaceSnapshot":
        workspace = payload.get("workspace", {}) if isinstance(payload, dict) else {}
        findings = list(workspace.get("findings", []))
        inspections: list[dict[str, Any]] = []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            severity = str(finding.get("severity", ""))
            inspections.append(
                {
                    "file_path": str(finding.get("file_path", "")),
                    "line": _safe_int(finding.get("line")),
                    "severity": severity,
                    "problem": str(finding.get("issue", "")),
                    "suggestion": str(finding.get("recommendation", "")),
                    "highlight": _map_inspection_highlight(severity),
                }
            )
        return cls(
            project_root=str(workspace.get("working_directory", "")),
            vcs={
                "diff": dict(workspace.get("diff", {})),
                "changed_files": list(workspace.get("changed_files", [])),
            },
            sessions=list(workspace.get("sessions", [])),
            tasks=list(workspace.get("tasks", [])),
            inspections=inspections,
        )


class _BaseIDEClientAdapter:
    """Shared adapter behavior for IDE clients."""

    def __init__(self, daemon_client: ControlPlaneClient) -> None:
        self._daemon = daemon_client

    def _fetch_workspace_payload(
        self,
        *,
        include_diff: bool = True,
        diff_max_lines: int = 400,
        findings_limit: int = 200,
        session_limit: int = 20,
        task_limit: int = 50,
    ) -> dict[str, Any]:
        return self._daemon.get_ide_workspace(
            include_diff=include_diff,
            diff_max_lines=diff_max_lines,
            findings_limit=findings_limit,
            session_limit=session_limit,
            task_limit=task_limit,
        )


class VSCodeClientAdapter(_BaseIDEClientAdapter):
    """Thin IDE adapter for VS Code client workflows."""

    def fetch_workspace_snapshot(
        self,
        *,
        include_diff: bool = True,
        diff_max_lines: int = 400,
        findings_limit: int = 200,
        session_limit: int = 20,
        task_limit: int = 50,
    ) -> IDEWorkspaceSnapshot:
        payload = self._fetch_workspace_payload(
            include_diff=include_diff,
            diff_max_lines=diff_max_lines,
            findings_limit=findings_limit,
            session_limit=session_limit,
            task_limit=task_limit,
        )
        return IDEWorkspaceSnapshot.from_payload(payload)


class JetBrainsClientAdapter(_BaseIDEClientAdapter):
    """Thin IDE adapter for JetBrains client workflows."""

    def fetch_workspace_snapshot(
        self,
        *,
        include_diff: bool = True,
        diff_max_lines: int = 400,
        findings_limit: int = 200,
        session_limit: int = 20,
        task_limit: int = 50,
    ) -> JetBrainsWorkspaceSnapshot:
        payload = self._fetch_workspace_payload(
            include_diff=include_diff,
            diff_max_lines=diff_max_lines,
            findings_limit=findings_limit,
            session_limit=session_limit,
            task_limit=task_limit,
        )
        return JetBrainsWorkspaceSnapshot.from_payload(payload)


__all__ = [
    "IDEWorkspaceSnapshot",
    "JetBrainsClientAdapter",
    "JetBrainsWorkspaceSnapshot",
    "VSCodeClientAdapter",
]
