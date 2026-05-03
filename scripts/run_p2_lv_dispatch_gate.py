"""Phase 2 card P2-60 gate for Linux CI workflow Linux-validation dispatch.

This script consumes the P2-59 terminal verdict artifact and converges the
Linux validation dispatch behavior:
1) validate terminal verdict + drift closure contract,
2) build/execute Linux validation command when verdict allows proceeding,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_TERMINAL_VERDICT_STATUSES: set[str] = {
    "ready_for_linux_validation",
    "ready_with_follow_up_for_linux_validation",
    "blocked",
    "contract_failed",
}
ALLOWED_TERMINAL_VERDICT_DECISIONS: set[str] = {
    "proceed_linux_validation",
    "proceed_linux_validation_with_follow_up",
    "halt_linux_validation_blocker",
    "abort_linux_validation",
}
ALLOWED_TERMINAL_VERDICT_CHANNELS: set[str] = {"release", "follow_up", "blocker"}
ALLOWED_GATE_MANIFEST_DRIFT_STATUSES: set[str] = {"passed", "failed"}

ALLOWED_LINUX_VALIDATION_DISPATCH_STATUSES: set[str] = {
    "ready_dry_run",
    "ready_with_follow_up_dry_run",
    "dispatched",
    "dispatch_failed",
    "blocked",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_DISPATCH_DECISIONS: set[str] = {
    "dispatch_linux_validation",
    "dispatch_linux_validation_with_follow_up",
    "hold_linux_validation_blocker",
    "abort_linux_validation_dispatch",
}
ALLOWED_LINUX_VALIDATION_DISPATCH_CHANNELS: set[str] = {"release", "follow_up", "blocker"}


def _coerce_bool(value: Any, *, field: str, path: Path) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path}: field '{field}' must be bool")
    return value


def _coerce_int(value: Any, *, field: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path}: field '{field}' must be int")
    return value


def _coerce_str(value: Any, *, field: str, path: Path) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path}: field '{field}' must be string")
    return value


def _coerce_str_list(value: Any, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: field '{field}' must be string list")
    return list(value)


def _unique(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _tail_text(text: str, *, max_lines: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _load_evidence_manifest(value: Any, *, field: str, path: Path) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{path}: field '{field}' must be object list")

    evidence_manifest: list[dict[str, Any]] = []
    for idx, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: {field}[{idx}] must be object")
        if "source" not in entry or "path" not in entry or "exists" not in entry:
            raise ValueError(f"{path}: {field}[{idx}] missing source/path/exists")
        evidence_manifest.append(
            {
                "source": _coerce_str(entry["source"], field=f"{field}[{idx}].source", path=path),
                "path": _coerce_str(entry["path"], field=f"{field}[{idx}].path", path=path),
                "exists": _coerce_bool(entry["exists"], field=f"{field}[{idx}].exists", path=path),
            }
        )
    return evidence_manifest


def load_terminal_verdict_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: terminal verdict report not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: terminal verdict payload must be object")

    required_fields = (
        "source_release_final_publish_archive_report",
        "source_gate_manifest_drift_report",
        "release_final_publish_archive_status",
        "gate_manifest_drift_status",
        "gate_manifest_drift_missing_runtime_tests",
        "gate_manifest_drift_missing_manifest_entries",
        "gate_manifest_drift_orphan_manifest_entries",
        "terminal_verdict_should_proceed",
        "terminal_verdict_requires_manual_action",
        "terminal_verdict_channel",
        "terminal_verdict_status",
        "terminal_verdict_decision",
        "terminal_verdict_exit_code",
        "follow_up_queue_url",
        "release_run_id",
        "release_run_url",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        "evidence_manifest",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    terminal_status = _coerce_str(
        payload["terminal_verdict_status"],
        field="terminal_verdict_status",
        path=path,
    )
    if terminal_status not in ALLOWED_TERMINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'terminal_verdict_status' must be one of "
            f"{sorted(ALLOWED_TERMINAL_VERDICT_STATUSES)}"
        )

    terminal_decision = _coerce_str(
        payload["terminal_verdict_decision"],
        field="terminal_verdict_decision",
        path=path,
    )
    if terminal_decision not in ALLOWED_TERMINAL_VERDICT_DECISIONS:
        raise ValueError(
            f"{path}: field 'terminal_verdict_decision' must be one of "
            f"{sorted(ALLOWED_TERMINAL_VERDICT_DECISIONS)}"
        )

    terminal_channel = _coerce_str(
        payload["terminal_verdict_channel"],
        field="terminal_verdict_channel",
        path=path,
    )
    if terminal_channel not in ALLOWED_TERMINAL_VERDICT_CHANNELS:
        raise ValueError(
            f"{path}: field 'terminal_verdict_channel' must be one of "
            f"{sorted(ALLOWED_TERMINAL_VERDICT_CHANNELS)}"
        )

    terminal_exit_code = _coerce_int(
        payload["terminal_verdict_exit_code"],
        field="terminal_verdict_exit_code",
        path=path,
    )
    if terminal_exit_code < 0:
        raise ValueError(f"{path}: field 'terminal_verdict_exit_code' must be >= 0")

    drift_status = _coerce_str(
        payload["gate_manifest_drift_status"],
        field="gate_manifest_drift_status",
        path=path,
    )
    if drift_status not in ALLOWED_GATE_MANIFEST_DRIFT_STATUSES:
        raise ValueError(
            f"{path}: field 'gate_manifest_drift_status' must be one of "
            f"{sorted(ALLOWED_GATE_MANIFEST_DRIFT_STATUSES)}"
        )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    return {
        "generated_at": payload.get("generated_at"),
        "source_release_final_publish_archive_report": _coerce_str(
            payload["source_release_final_publish_archive_report"],
            field="source_release_final_publish_archive_report",
            path=path,
        ),
        "source_gate_manifest_drift_report": _coerce_str(
            payload["source_gate_manifest_drift_report"],
            field="source_gate_manifest_drift_report",
            path=path,
        ),
        "release_final_publish_archive_status": _coerce_str(
            payload["release_final_publish_archive_status"],
            field="release_final_publish_archive_status",
            path=path,
        ),
        "gate_manifest_drift_status": drift_status,
        "gate_manifest_drift_missing_runtime_tests": _coerce_str_list(
            payload["gate_manifest_drift_missing_runtime_tests"],
            field="gate_manifest_drift_missing_runtime_tests",
            path=path,
        ),
        "gate_manifest_drift_missing_manifest_entries": _coerce_str_list(
            payload["gate_manifest_drift_missing_manifest_entries"],
            field="gate_manifest_drift_missing_manifest_entries",
            path=path,
        ),
        "gate_manifest_drift_orphan_manifest_entries": _coerce_str_list(
            payload["gate_manifest_drift_orphan_manifest_entries"],
            field="gate_manifest_drift_orphan_manifest_entries",
            path=path,
        ),
        "terminal_verdict_should_proceed": _coerce_bool(
            payload["terminal_verdict_should_proceed"],
            field="terminal_verdict_should_proceed",
            path=path,
        ),
        "terminal_verdict_requires_manual_action": _coerce_bool(
            payload["terminal_verdict_requires_manual_action"],
            field="terminal_verdict_requires_manual_action",
            path=path,
        ),
        "terminal_verdict_channel": terminal_channel,
        "terminal_verdict_status": terminal_status,
        "terminal_verdict_decision": terminal_decision,
        "terminal_verdict_exit_code": terminal_exit_code,
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(payload["release_run_url"], field="release_run_url", path=path),
        "reason_codes": _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path),
        "structural_issues": _coerce_str_list(
            payload["structural_issues"],
            field="structural_issues",
            path=path,
        ),
        "missing_artifacts": _coerce_str_list(
            payload["missing_artifacts"],
            field="missing_artifacts",
            path=path,
        ),
        "evidence_manifest": _load_evidence_manifest(
            payload["evidence_manifest"],
            field="evidence_manifest",
            path=path,
        ),
    }


def build_linux_validation_command_parts(
    *,
    terminal_verdict_report: dict[str, Any],
    python_executable: str,
    linux_validation_command: str,
) -> list[str]:
    if not bool(terminal_verdict_report["terminal_verdict_should_proceed"]):
        return []
    if linux_validation_command.strip():
        try:
            parts = shlex.split(linux_validation_command)
        except ValueError as exc:
            raise ValueError(f"invalid --linux-validation-command ({exc})") from exc
        if not parts:
            raise ValueError("invalid --linux-validation-command (empty command)")
        return parts
    return [
        python_executable,
        "scripts/run_p2_linux_unified_pipeline_gate.py",
        "--continue-on-failure",
    ]


def execute_linux_validation_command(
    command_parts: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command_parts,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "attempted": True,
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "error_type": "command_not_found",
            "error_message": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "attempted": True,
            "returncode": 124,
            "stdout_tail": _tail_text(stdout),
            "stderr_tail": _tail_text(stderr),
            "error_type": "timeout",
            "error_message": f"linux validation command timeout after {timeout_seconds}s",
        }

    return {
        "attempted": True,
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(completed.stdout or ""),
        "stderr_tail": _tail_text(completed.stderr or ""),
        "error_type": "",
        "error_message": "",
    }


def build_linux_validation_dispatch_payload(
    terminal_verdict_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    linux_validation_timeout_seconds: int,
    command_parts: list[str],
    dry_run: bool,
    command_result: dict[str, Any] | None,
) -> dict[str, Any]:
    terminal_status = str(terminal_verdict_report["terminal_verdict_status"])
    terminal_decision = str(terminal_verdict_report["terminal_verdict_decision"])
    terminal_exit_code = int(terminal_verdict_report["terminal_verdict_exit_code"])
    terminal_should_proceed = bool(terminal_verdict_report["terminal_verdict_should_proceed"])
    terminal_requires_manual_action = bool(
        terminal_verdict_report["terminal_verdict_requires_manual_action"]
    )
    terminal_channel = str(terminal_verdict_report["terminal_verdict_channel"])

    drift_status = str(terminal_verdict_report["gate_manifest_drift_status"])
    drift_missing_runtime_tests = list(
        terminal_verdict_report["gate_manifest_drift_missing_runtime_tests"]
    )
    drift_missing_manifest_entries = list(
        terminal_verdict_report["gate_manifest_drift_missing_manifest_entries"]
    )
    drift_orphan_manifest_entries = list(
        terminal_verdict_report["gate_manifest_drift_orphan_manifest_entries"]
    )

    reason_codes = list(terminal_verdict_report["reason_codes"])
    structural_issues = list(terminal_verdict_report["structural_issues"])
    missing_artifacts = list(terminal_verdict_report["missing_artifacts"])
    evidence_manifest = list(terminal_verdict_report["evidence_manifest"])

    expected_terminal = {
        "ready_for_linux_validation": (
            "proceed_linux_validation",
            True,
            False,
            "release",
            0,
        ),
        "ready_with_follow_up_for_linux_validation": (
            "proceed_linux_validation_with_follow_up",
            True,
            False,
            "follow_up",
            None,
        ),
        "blocked": ("halt_linux_validation_blocker", False, True, "blocker", None),
        "contract_failed": ("abort_linux_validation", False, True, "blocker", None),
    }
    (
        expected_decision,
        expected_should_proceed,
        expected_requires_manual_action,
        expected_channel,
        expected_exit_code,
    ) = expected_terminal[terminal_status]

    if terminal_decision != expected_decision:
        structural_issues.append("terminal_verdict_decision_mismatch")
    if terminal_should_proceed != expected_should_proceed:
        structural_issues.append("terminal_verdict_should_proceed_mismatch")
    if terminal_requires_manual_action != expected_requires_manual_action:
        structural_issues.append("terminal_verdict_requires_manual_action_mismatch")
    if terminal_channel != expected_channel:
        structural_issues.append("terminal_verdict_channel_mismatch")
    if expected_exit_code == 0 and terminal_exit_code != 0:
        structural_issues.append("terminal_verdict_exit_code_mismatch_ready")
    if expected_exit_code is None and terminal_exit_code == 0:
        structural_issues.append("terminal_verdict_exit_code_mismatch_non_ready")

    if drift_status != "passed":
        structural_issues.append("gate_manifest_drift_failed")
    if drift_missing_runtime_tests:
        structural_issues.append("gate_manifest_drift_missing_runtime_tests")
    if drift_missing_manifest_entries:
        structural_issues.append("gate_manifest_drift_missing_manifest_entries")
    if drift_orphan_manifest_entries:
        structural_issues.append("gate_manifest_drift_orphan_manifest_entries")

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        structural_issues.append("terminal_verdict_evidence_missing")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    linux_validation_command = _format_shell_command(command_parts) if command_parts else ""
    linux_validation_decision: str
    linux_validation_channel: str
    linux_validation_should_dispatch: bool
    linux_validation_requires_manual_action: bool

    if terminal_status == "ready_for_linux_validation":
        linux_validation_decision = "dispatch_linux_validation"
        linux_validation_channel = "release"
        linux_validation_should_dispatch = True
        linux_validation_requires_manual_action = False
    elif terminal_status == "ready_with_follow_up_for_linux_validation":
        linux_validation_decision = "dispatch_linux_validation_with_follow_up"
        linux_validation_channel = "follow_up"
        linux_validation_should_dispatch = True
        linux_validation_requires_manual_action = False
    elif terminal_status == "blocked":
        linux_validation_decision = "hold_linux_validation_blocker"
        linux_validation_channel = "blocker"
        linux_validation_should_dispatch = False
        linux_validation_requires_manual_action = True
    else:
        linux_validation_decision = "abort_linux_validation_dispatch"
        linux_validation_channel = "blocker"
        linux_validation_should_dispatch = False
        linux_validation_requires_manual_action = True

    dispatch_attempted = False
    command_returncode: int | None = None
    command_stdout_tail = ""
    command_stderr_tail = ""
    dispatch_error_type = ""
    dispatch_error_message = ""

    if structural_issues or missing_artifacts:
        dispatch_status = "contract_failed"
        dispatch_decision = "abort_linux_validation_dispatch"
        dispatch_exit_code = max(1, terminal_exit_code)
        linux_validation_should_dispatch = False
        linux_validation_requires_manual_action = True
        linux_validation_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif not linux_validation_should_dispatch:
        dispatch_status = "blocked"
        dispatch_decision = "hold_linux_validation_blocker"
        dispatch_exit_code = max(1, terminal_exit_code)
        reason_codes.append("linux_validation_dispatch_blocked")
    elif dry_run:
        if linux_validation_channel == "follow_up":
            dispatch_status = "ready_with_follow_up_dry_run"
            dispatch_exit_code = max(1, terminal_exit_code)
            reason_codes.append("linux_validation_dispatch_ready_with_follow_up_dry_run")
        else:
            dispatch_status = "ready_dry_run"
            dispatch_exit_code = 0
            reason_codes = ["linux_validation_dispatch_ready_dry_run"]
        dispatch_decision = linux_validation_decision
    else:
        dispatch_attempted = True
        if command_result is None:
            dispatch_status = "dispatch_failed"
            dispatch_decision = linux_validation_decision
            dispatch_exit_code = 1
            reason_codes.append("linux_validation_dispatch_result_missing")
        else:
            command_returncode = int(command_result["returncode"])
            command_stdout_tail = str(command_result.get("stdout_tail", ""))
            command_stderr_tail = str(command_result.get("stderr_tail", ""))
            dispatch_error_type = str(command_result.get("error_type", ""))
            dispatch_error_message = str(command_result.get("error_message", ""))
            if command_returncode == 0:
                dispatch_status = "dispatched"
                dispatch_decision = linux_validation_decision
                dispatch_exit_code = (
                    max(1, terminal_exit_code)
                    if linux_validation_channel == "follow_up"
                    else 0
                )
                reason_codes = ["linux_validation_dispatch_command_succeeded"]
            else:
                dispatch_status = "dispatch_failed"
                dispatch_decision = linux_validation_decision
                dispatch_exit_code = 1
                if dispatch_error_type == "command_not_found":
                    reason_codes.append("linux_validation_dispatch_cli_unavailable")
                elif dispatch_error_type == "timeout":
                    reason_codes.append("linux_validation_dispatch_timeout")
                else:
                    reason_codes.append("linux_validation_dispatch_command_failed")

    if dispatch_status not in ALLOWED_LINUX_VALIDATION_DISPATCH_STATUSES:
        raise ValueError("internal: unsupported linux_validation_dispatch_status computed")
    if dispatch_decision not in ALLOWED_LINUX_VALIDATION_DISPATCH_DECISIONS:
        raise ValueError("internal: unsupported linux_validation_dispatch_decision computed")
    if linux_validation_channel not in ALLOWED_LINUX_VALIDATION_DISPATCH_CHANNELS:
        raise ValueError("internal: unsupported linux_validation_channel computed")

    reason_codes = _unique(reason_codes)
    summary = (
        f"terminal_verdict_status={terminal_status} "
        f"terminal_verdict_decision={terminal_decision} "
        f"linux_validation_dispatch_status={dispatch_status} "
        f"linux_validation_dispatch_decision={dispatch_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_terminal_verdict_report": str(source_path),
        "project_root": str(project_root),
        "source_release_final_publish_archive_report": str(
            terminal_verdict_report["source_release_final_publish_archive_report"]
        ),
        "source_gate_manifest_drift_report": str(
            terminal_verdict_report["source_gate_manifest_drift_report"]
        ),
        "release_final_publish_archive_status": str(
            terminal_verdict_report["release_final_publish_archive_status"]
        ),
        "gate_manifest_drift_status": drift_status,
        "gate_manifest_drift_missing_runtime_tests": drift_missing_runtime_tests,
        "gate_manifest_drift_missing_manifest_entries": drift_missing_manifest_entries,
        "gate_manifest_drift_orphan_manifest_entries": drift_orphan_manifest_entries,
        "terminal_verdict_status": terminal_status,
        "terminal_verdict_decision": terminal_decision,
        "terminal_verdict_exit_code": terminal_exit_code,
        "terminal_verdict_should_proceed": terminal_should_proceed,
        "terminal_verdict_requires_manual_action": terminal_requires_manual_action,
        "terminal_verdict_channel": terminal_channel,
        "linux_validation_should_dispatch": linux_validation_should_dispatch,
        "linux_validation_requires_manual_action": linux_validation_requires_manual_action,
        "linux_validation_channel": linux_validation_channel,
        "linux_validation_dispatch_status": dispatch_status,
        "linux_validation_dispatch_decision": dispatch_decision,
        "linux_validation_dispatch_exit_code": int(dispatch_exit_code),
        "linux_validation_dispatch_attempted": dispatch_attempted,
        "linux_validation_timeout_seconds": linux_validation_timeout_seconds,
        "linux_validation_command": linux_validation_command,
        "linux_validation_command_parts": command_parts,
        "dry_run": dry_run,
        "command_returncode": command_returncode,
        "command_stdout_tail": command_stdout_tail,
        "command_stderr_tail": command_stderr_tail,
        "dispatch_error_type": dispatch_error_type,
        "dispatch_error_message": dispatch_error_message,
        "release_run_id": terminal_verdict_report["release_run_id"],
        "release_run_url": str(terminal_verdict_report["release_run_url"]),
        "follow_up_queue_url": str(terminal_verdict_report["follow_up_queue_url"]),
        "linux_validation_dispatch_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Linux Validation Dispatch Report",
        "",
        (
            "- Linux Validation Dispatch Status: "
            f"**{str(payload['linux_validation_dispatch_status']).upper()}**"
        ),
        (
            "- Linux Validation Dispatch Decision: "
            f"`{payload['linux_validation_dispatch_decision']}`"
        ),
        (
            "- Linux Validation Dispatch Exit Code: "
            f"`{payload['linux_validation_dispatch_exit_code']}`"
        ),
        (
            "- Linux Validation Should Dispatch: "
            f"`{payload['linux_validation_should_dispatch']}`"
        ),
        (
            "- Linux Validation Requires Manual Action: "
            f"`{payload['linux_validation_requires_manual_action']}`"
        ),
        f"- Linux Validation Channel: `{payload['linux_validation_channel']}`",
        f"- Terminal Verdict Status: `{payload['terminal_verdict_status']}`",
        f"- Gate Manifest Drift Status: `{payload['gate_manifest_drift_status']}`",
        f"- Dispatch Attempted: `{payload['linux_validation_dispatch_attempted']}`",
        f"- Dry Run: `{payload['dry_run']}`",
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['linux_validation_dispatch_summary']}",
        "",
        "## Linux Validation Command",
    ]

    if payload["linux_validation_command"]:
        lines.append(f"- `{payload['linux_validation_command']}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Reason Codes"])
    reason_codes = payload["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{item}`" for item in reason_codes)
    else:
        lines.append("- none")

    lines.extend(["", "## Structural Issues"])
    structural_issues = payload["structural_issues"]
    if structural_issues:
        lines.extend(f"- `{item}`" for item in structural_issues)
    else:
        lines.append("- none")

    lines.extend(["", "## Missing Artifacts"])
    missing_artifacts = payload["missing_artifacts"]
    if missing_artifacts:
        lines.extend(f"- `{item}`" for item in missing_artifacts)
    else:
        lines.append("- none")

    lines.extend(["", "## Command Output (tail)"])
    stdout_tail = str(payload["command_stdout_tail"]).strip()
    stderr_tail = str(payload["command_stderr_tail"]).strip()
    if stdout_tail:
        lines.append("- stdout:")
        lines.append("```text")
        lines.append(stdout_tail)
        lines.append("```")
    else:
        lines.append("- stdout: none")
    if stderr_tail:
        lines.append("- stderr:")
        lines.append("```text")
        lines.append(stderr_tail)
        lines.append("```")
    else:
        lines.append("- stderr: none")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    command_returncode = payload["command_returncode"]
    return {
        "workflow_linux_validation_dispatch_status": str(
            payload["linux_validation_dispatch_status"]
        ),
        "workflow_linux_validation_dispatch_decision": str(
            payload["linux_validation_dispatch_decision"]
        ),
        "workflow_linux_validation_dispatch_exit_code": str(
            payload["linux_validation_dispatch_exit_code"]
        ),
        "workflow_linux_validation_dispatch_should_dispatch": (
            "true" if payload["linux_validation_should_dispatch"] else "false"
        ),
        "workflow_linux_validation_dispatch_requires_manual_action": (
            "true" if payload["linux_validation_requires_manual_action"] else "false"
        ),
        "workflow_linux_validation_dispatch_channel": str(payload["linux_validation_channel"]),
        "workflow_linux_validation_dispatch_attempted": (
            "true" if payload["linux_validation_dispatch_attempted"] else "false"
        ),
        "workflow_linux_validation_dispatch_command_returncode": (
            "" if command_returncode is None else str(command_returncode)
        ),
        "workflow_linux_validation_dispatch_terminal_verdict_status": str(
            payload["terminal_verdict_status"]
        ),
        "workflow_linux_validation_dispatch_gate_manifest_drift_status": str(
            payload["gate_manifest_drift_status"]
        ),
        "workflow_linux_validation_dispatch_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_dispatch_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_dispatch_run_url": str(payload["release_run_url"]),
        "workflow_linux_validation_dispatch_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_dispatch_report_json": str(output_json),
        "workflow_linux_validation_dispatch_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dispatch Linux validation command from P2-59 terminal verdict "
            "and publish Linux validation dispatch contract"
        )
    )
    parser.add_argument(
        "--terminal-verdict-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json",
        help="P2-59 terminal verdict report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used to execute Linux validation command",
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable used by default Linux validation command",
    )
    parser.add_argument(
        "--linux-validation-command",
        default="",
        help="Optional explicit Linux validation command string",
    )
    parser.add_argument(
        "--linux-validation-timeout-seconds",
        type=int,
        default=7200,
        help="Linux validation command timeout in seconds",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json",
        help="Output Linux validation dispatch JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.md",
        help="Output Linux validation dispatch markdown path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation dispatch JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    if args.linux_validation_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-linux-validation-dispatch-gate] "
            "--linux-validation-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    source_path = Path(args.terminal_verdict_report)
    project_root = Path(args.project_root)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        terminal_verdict_report = load_terminal_verdict_report(source_path)
        command_parts = build_linux_validation_command_parts(
            terminal_verdict_report=terminal_verdict_report,
            python_executable=args.python_executable,
            linux_validation_command=args.linux_validation_command,
        )
    except ValueError as exc:
        print(
            f"[p2-linux-ci-workflow-linux-validation-dispatch-gate] {exc}",
            file=sys.stderr,
        )
        return 2

    command_result: dict[str, Any] | None = None
    should_dispatch = bool(terminal_verdict_report["terminal_verdict_should_proceed"])
    if should_dispatch and not args.dry_run:
        command_result = execute_linux_validation_command(
            command_parts,
            cwd=project_root,
            timeout_seconds=args.linux_validation_timeout_seconds,
        )

    payload = build_linux_validation_dispatch_payload(
        terminal_verdict_report,
        source_path=source_path.resolve(),
        project_root=project_root.resolve(),
        linux_validation_timeout_seconds=args.linux_validation_timeout_seconds,
        command_parts=command_parts,
        dry_run=args.dry_run,
        command_result=command_result,
    )

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"linux validation dispatch json: {output_json_path}")
        print(f"linux validation dispatch markdown: {output_markdown_path}")

    if args.github_output:
        write_github_output(
            Path(args.github_output),
            build_github_output_values(
                payload,
                output_json=output_json_path,
                output_markdown=output_markdown_path,
            ),
        )
        print(f"github output: {args.github_output}")

    print(
        "linux validation dispatch summary: "
        f"linux_validation_dispatch_status={payload['linux_validation_dispatch_status']} "
        f"linux_validation_dispatch_decision={payload['linux_validation_dispatch_decision']} "
        f"linux_validation_dispatch_exit_code={payload['linux_validation_dispatch_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_dispatch_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
