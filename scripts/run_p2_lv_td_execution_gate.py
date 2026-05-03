"""Phase 2 card P2-70 gate for Linux CI workflow Linux-validation terminal dispatch execution.

This script executes (or dry-runs) the P2-69 Linux validation terminal dispatch contract:
1) validates terminal dispatch-ready vs blocked payload contract,
2) executes canonical Linux validation terminal command when ready,
3) emits execution JSON/Markdown + optional GitHub outputs.
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


ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_STATUSES: set[str] = {
    "ready_dry_run",
    "ready_with_follow_up_dry_run",
    "blocked",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_DECISIONS: set[str] = {
    "dispatch_linux_validation_terminal",
    "dispatch_linux_validation_terminal_with_follow_up",
    "hold_linux_validation_terminal_blocker",
    "abort_linux_validation_terminal_dispatch",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_CHANNELS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}

ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_EXECUTION_STATUSES: set[str] = {
    "ready_dry_run",
    "ready_with_follow_up_dry_run",
    "dispatched",
    "dispatch_failed",
    "blocked",
    "contract_failed",
}


def _coerce_bool(value: Any, *, field: str, path: Path) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path}: field '{field}' must be bool")
    return value


def _coerce_int(value: Any, *, field: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path}: field '{field}' must be int")
    return value


def _coerce_optional_int(value: Any, *, field: str, path: Path) -> int | None:
    if value is None:
        return None
    return _coerce_int(value, field=field, path=path)


def _coerce_str(value: Any, *, field: str, path: Path) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path}: field '{field}' must be string")
    return value


def _coerce_str_list(value: Any, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: field '{field}' must be string list")
    return list(value)


def _tail_text(text: str, *, max_lines: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _unique(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


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


def load_linux_validation_terminal_dispatch_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: Linux validation terminal dispatch report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: Linux validation terminal dispatch payload must be object")

    required_fields = (
        "source_linux_validation_terminal_verdict_publish_report",
        "source_linux_validation_terminal_verdict_report",
        "source_linux_validation_dispatch_report",
        "source_linux_validation_final_publish_archive_report",
        "project_root",
        "source_terminal_verdict_report",
        "source_release_final_publish_archive_report",
        "source_gate_manifest_drift_report",
        "release_final_publish_archive_status",
        "gate_manifest_drift_status",
        "gate_manifest_drift_missing_runtime_tests",
        "gate_manifest_drift_missing_manifest_entries",
        "gate_manifest_drift_orphan_manifest_entries",
        "terminal_verdict_status",
        "terminal_verdict_decision",
        "terminal_verdict_exit_code",
        "terminal_verdict_should_proceed",
        "terminal_verdict_requires_manual_action",
        "terminal_verdict_channel",
        "linux_validation_should_dispatch",
        "linux_validation_requires_manual_action",
        "linux_validation_channel",
        "linux_validation_dispatch_status",
        "linux_validation_dispatch_decision",
        "linux_validation_dispatch_exit_code",
        "linux_validation_dispatch_attempted",
        "linux_validation_dispatch_command_returncode",
        "linux_validation_terminal_verdict_status",
        "linux_validation_terminal_verdict_decision",
        "linux_validation_terminal_verdict_exit_code",
        "linux_validation_terminal_verdict_should_proceed",
        "linux_validation_terminal_verdict_requires_manual_action",
        "linux_validation_terminal_verdict_channel",
        "linux_validation_terminal_verdict_publish_status",
        "linux_validation_terminal_verdict_publish_decision",
        "linux_validation_terminal_verdict_publish_exit_code",
        "linux_validation_terminal_verdict_publish_should_notify",
        "linux_validation_terminal_verdict_publish_requires_manual_action",
        "linux_validation_terminal_verdict_publish_channel",
        "linux_validation_terminal_verdict_publish_summary",
        "dry_run",
        "verdict_command_returncode",
        "verdict_command_stdout_tail",
        "verdict_command_stderr_tail",
        "verdict_error_type",
        "verdict_error_message",
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "linux_validation_dispatch_summary",
        "linux_validation_terminal_verdict_summary",
        "linux_validation_terminal_dispatch_status",
        "linux_validation_terminal_dispatch_decision",
        "linux_validation_terminal_dispatch_exit_code",
        "linux_validation_terminal_should_dispatch",
        "linux_validation_terminal_dispatch_requires_manual_action",
        "linux_validation_terminal_dispatch_channel",
        "linux_validation_terminal_dispatch_summary",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        "evidence_manifest",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    dispatch_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_status"],
        field="linux_validation_terminal_dispatch_status",
        path=path,
    )
    if dispatch_status not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_STATUSES:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_STATUSES)}"
        )

    dispatch_decision = _coerce_str(
        payload["linux_validation_terminal_dispatch_decision"],
        field="linux_validation_terminal_dispatch_decision",
        path=path,
    )
    if dispatch_decision not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_DECISIONS:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_decision' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_DECISIONS)}"
        )

    dispatch_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_exit_code"],
        field="linux_validation_terminal_dispatch_exit_code",
        path=path,
    )
    if dispatch_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_exit_code' must be >= 0"
        )

    dispatch_channel = _coerce_str(
        payload["linux_validation_terminal_dispatch_channel"],
        field="linux_validation_terminal_dispatch_channel",
        path=path,
    )
    if dispatch_channel not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_CHANNELS:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_channel' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_CHANNELS)}"
        )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    expected_dispatch = {
        "ready_dry_run": (
            "dispatch_linux_validation_terminal",
            True,
            False,
            "release",
            0,
        ),
        "ready_with_follow_up_dry_run": (
            "dispatch_linux_validation_terminal_with_follow_up",
            True,
            False,
            "follow_up",
            None,
        ),
        "blocked": (
            "hold_linux_validation_terminal_blocker",
            False,
            True,
            "blocker",
            None,
        ),
        "contract_failed": (
            "abort_linux_validation_terminal_dispatch",
            False,
            True,
            "blocker",
            None,
        ),
    }
    (
        expected_decision,
        expected_should_dispatch,
        expected_requires_manual_action,
        expected_channel,
        expected_exit_code,
    ) = expected_dispatch[dispatch_status]

    should_dispatch = _coerce_bool(
        payload["linux_validation_terminal_should_dispatch"],
        field="linux_validation_terminal_should_dispatch",
        path=path,
    )
    requires_manual_action = _coerce_bool(
        payload["linux_validation_terminal_dispatch_requires_manual_action"],
        field="linux_validation_terminal_dispatch_requires_manual_action",
        path=path,
    )
    if dispatch_decision != expected_decision:
        raise ValueError(
            f"{path}: dispatch decision mismatch for status={dispatch_status}; "
            f"expected {expected_decision}, got {dispatch_decision}"
        )
    if should_dispatch != expected_should_dispatch:
        raise ValueError(
            f"{path}: linux_validation_terminal_should_dispatch mismatch for status={dispatch_status}"
        )
    if requires_manual_action != expected_requires_manual_action:
        raise ValueError(
            f"{path}: linux_validation_terminal_dispatch_requires_manual_action mismatch for "
            f"status={dispatch_status}"
        )
    if dispatch_channel != expected_channel:
        raise ValueError(
            f"{path}: linux_validation_terminal_dispatch_channel mismatch for status={dispatch_status}; "
            f"expected {expected_channel}, got {dispatch_channel}"
        )
    if expected_exit_code == 0 and dispatch_exit_code != 0:
        raise ValueError(
            f"{path}: linux_validation_terminal_dispatch_exit_code must be 0 when status=ready_dry_run"
        )
    if expected_exit_code is None and dispatch_exit_code == 0 and dispatch_status != "ready_dry_run":
        raise ValueError(
            f"{path}: linux_validation_terminal_dispatch_exit_code cannot be 0 when status={dispatch_status}"
        )

    payload["release_run_id"] = release_run_id
    payload["linux_validation_dispatch_command_returncode"] = _coerce_optional_int(
        payload["linux_validation_dispatch_command_returncode"],
        field="linux_validation_dispatch_command_returncode",
        path=path,
    )
    payload["verdict_command_returncode"] = _coerce_optional_int(
        payload["verdict_command_returncode"],
        field="verdict_command_returncode",
        path=path,
    )
    payload["gate_manifest_drift_missing_runtime_tests"] = _coerce_str_list(
        payload["gate_manifest_drift_missing_runtime_tests"],
        field="gate_manifest_drift_missing_runtime_tests",
        path=path,
    )
    payload["gate_manifest_drift_missing_manifest_entries"] = _coerce_str_list(
        payload["gate_manifest_drift_missing_manifest_entries"],
        field="gate_manifest_drift_missing_manifest_entries",
        path=path,
    )
    payload["gate_manifest_drift_orphan_manifest_entries"] = _coerce_str_list(
        payload["gate_manifest_drift_orphan_manifest_entries"],
        field="gate_manifest_drift_orphan_manifest_entries",
        path=path,
    )
    payload["reason_codes"] = _coerce_str_list(
        payload["reason_codes"],
        field="reason_codes",
        path=path,
    )
    payload["structural_issues"] = _coerce_str_list(
        payload["structural_issues"],
        field="structural_issues",
        path=path,
    )
    payload["missing_artifacts"] = _coerce_str_list(
        payload["missing_artifacts"],
        field="missing_artifacts",
        path=path,
    )
    payload["evidence_manifest"] = _load_evidence_manifest(
        payload["evidence_manifest"],
        field="evidence_manifest",
        path=path,
    )
    return payload


def build_linux_validation_terminal_command_parts(
    *,
    terminal_dispatch_report: dict[str, Any],
    python_executable: str,
    linux_validation_terminal_command: str,
) -> list[str]:
    if not bool(terminal_dispatch_report["linux_validation_terminal_should_dispatch"]):
        return []
    if linux_validation_terminal_command.strip():
        try:
            parts = shlex.split(linux_validation_terminal_command)
        except ValueError as exc:
            raise ValueError(f"invalid --linux-validation-terminal-command ({exc})") from exc
        if not parts:
            raise ValueError("invalid --linux-validation-terminal-command (empty command)")
        return parts
    return [
        python_executable,
        "scripts/run_p2_linux_unified_pipeline_gate.py",
        "--continue-on-failure",
    ]


def execute_linux_validation_terminal_command(
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
            "error_message": f"linux validation terminal command timeout after {timeout_seconds}s",
        }

    return {
        "attempted": True,
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(completed.stdout or ""),
        "stderr_tail": _tail_text(completed.stderr or ""),
        "error_type": "",
        "error_message": "",
    }


def build_linux_validation_terminal_dispatch_execution_payload(
    terminal_dispatch_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    linux_validation_terminal_timeout_seconds: int,
    command_parts: list[str],
    dry_run: bool,
    command_result: dict[str, Any] | None,
) -> dict[str, Any]:
    upstream_status = str(terminal_dispatch_report["linux_validation_terminal_dispatch_status"])
    upstream_decision = str(terminal_dispatch_report["linux_validation_terminal_dispatch_decision"])
    upstream_exit_code = int(terminal_dispatch_report["linux_validation_terminal_dispatch_exit_code"])
    should_dispatch = bool(terminal_dispatch_report["linux_validation_terminal_should_dispatch"])
    requires_manual_action = bool(
        terminal_dispatch_report["linux_validation_terminal_dispatch_requires_manual_action"]
    )
    dispatch_channel = str(terminal_dispatch_report["linux_validation_terminal_dispatch_channel"])

    reason_codes = list(terminal_dispatch_report["reason_codes"])
    structural_issues = list(terminal_dispatch_report["structural_issues"])
    missing_artifacts = list(terminal_dispatch_report["missing_artifacts"])

    dispatch_attempted = False
    command_returncode: int | None = None
    command_stdout_tail = ""
    command_stderr_tail = ""
    dispatch_error_type = ""
    dispatch_error_message = ""

    execution_status: str
    execution_decision: str
    execution_exit_code: int
    execution_requires_manual_action: bool
    execution_channel: str

    if structural_issues or missing_artifacts:
        execution_status = "contract_failed"
        execution_decision = "abort_linux_validation_terminal_dispatch"
        execution_exit_code = max(1, upstream_exit_code)
        execution_requires_manual_action = True
        execution_channel = "blocker"
    elif not should_dispatch:
        if upstream_status == "contract_failed":
            execution_status = "contract_failed"
            execution_decision = "abort_linux_validation_terminal_dispatch"
        else:
            execution_status = "blocked"
            execution_decision = "hold_linux_validation_terminal_blocker"
        execution_exit_code = max(1, upstream_exit_code)
        execution_requires_manual_action = True
        execution_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_execution_blocked")
    elif dry_run:
        execution_status = upstream_status
        execution_decision = upstream_decision
        execution_exit_code = upstream_exit_code
        execution_requires_manual_action = requires_manual_action
        execution_channel = dispatch_channel
        reason_codes.append("linux_validation_terminal_dispatch_execution_dry_run")
    else:
        dispatch_attempted = True
        if command_result is None:
            execution_status = "dispatch_failed"
            execution_decision = upstream_decision
            execution_exit_code = 1
            execution_requires_manual_action = True
            execution_channel = "blocker"
            reason_codes.append("linux_validation_terminal_dispatch_execution_result_missing")
        else:
            command_returncode = int(command_result["returncode"])
            command_stdout_tail = str(command_result.get("stdout_tail", ""))
            command_stderr_tail = str(command_result.get("stderr_tail", ""))
            dispatch_error_type = str(command_result.get("error_type", ""))
            dispatch_error_message = str(command_result.get("error_message", ""))

            if command_returncode == 0:
                execution_status = "dispatched"
                execution_decision = upstream_decision
                execution_exit_code = max(1, upstream_exit_code) if dispatch_channel == "follow_up" else 0
                execution_requires_manual_action = False
                execution_channel = dispatch_channel
                reason_codes = ["linux_validation_terminal_dispatch_execution_command_succeeded"]
            else:
                execution_status = "dispatch_failed"
                execution_decision = upstream_decision
                execution_exit_code = 1
                execution_requires_manual_action = True
                execution_channel = "blocker"
                if dispatch_error_type == "command_not_found":
                    reason_codes.append("linux_validation_terminal_dispatch_execution_cli_unavailable")
                elif dispatch_error_type == "timeout":
                    reason_codes.append("linux_validation_terminal_dispatch_execution_timeout")
                else:
                    reason_codes.append("linux_validation_terminal_dispatch_execution_command_failed")

    if execution_status not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_EXECUTION_STATUSES:
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_execution_status computed"
        )
    if execution_decision not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_DECISIONS:
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_execution_decision computed"
        )
    if execution_channel not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_CHANNELS:
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_execution_channel computed"
        )

    reason_codes = _unique(reason_codes)
    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)
    summary = (
        f"linux_validation_terminal_dispatch_status={upstream_status} "
        f"linux_validation_terminal_dispatch_execution_status={execution_status} "
        f"linux_validation_terminal_dispatch_execution_decision={execution_decision}"
    )

    payload = dict(terminal_dispatch_report)
    payload.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_linux_validation_terminal_dispatch_report": str(source_path),
            "project_root": str(project_root),
            "dry_run": dry_run,
            "linux_validation_terminal_timeout_seconds": linux_validation_terminal_timeout_seconds,
            "linux_validation_terminal_command": _format_shell_command(command_parts),
            "linux_validation_terminal_command_parts": command_parts,
            "linux_validation_terminal_dispatch_attempted": dispatch_attempted,
            "linux_validation_terminal_dispatch_command_returncode": command_returncode,
            "linux_validation_terminal_dispatch_command_stdout_tail": command_stdout_tail,
            "linux_validation_terminal_dispatch_command_stderr_tail": command_stderr_tail,
            "linux_validation_terminal_dispatch_error_type": dispatch_error_type,
            "linux_validation_terminal_dispatch_error_message": dispatch_error_message,
            "linux_validation_terminal_dispatch_execution_status": execution_status,
            "linux_validation_terminal_dispatch_execution_decision": execution_decision,
            "linux_validation_terminal_dispatch_execution_exit_code": execution_exit_code,
            "linux_validation_terminal_dispatch_execution_requires_manual_action": (
                execution_requires_manual_action
            ),
            "linux_validation_terminal_dispatch_execution_channel": execution_channel,
            "linux_validation_terminal_dispatch_execution_summary": summary,
            "reason_codes": reason_codes,
            "structural_issues": structural_issues,
            "missing_artifacts": missing_artifacts,
        }
    )
    return payload


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Linux Validation Terminal Dispatch Execution Report",
        "",
        (
            "- Linux Validation Terminal Dispatch Execution Status: "
            f"**{str(payload['linux_validation_terminal_dispatch_execution_status']).upper()}**"
        ),
        (
            "- Linux Validation Terminal Dispatch Execution Decision: "
            f"`{payload['linux_validation_terminal_dispatch_execution_decision']}`"
        ),
        (
            "- Linux Validation Terminal Dispatch Execution Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_execution_exit_code']}`"
        ),
        (
            "- Linux Validation Terminal Dispatch Attempted: "
            f"`{payload['linux_validation_terminal_dispatch_attempted']}`"
        ),
        (
            "- Linux Validation Terminal Should Dispatch: "
            f"`{payload['linux_validation_terminal_should_dispatch']}`"
        ),
        f"- Dry Run: `{payload['dry_run']}`",
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Terminal Dispatch Command",
    ]

    if payload["linux_validation_terminal_command"]:
        lines.append(f"- `{payload['linux_validation_terminal_command']}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- {payload['linux_validation_terminal_dispatch_execution_summary']}",
            "",
            "## Reason Codes",
        ]
    )
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
    stdout_tail = str(payload["linux_validation_terminal_dispatch_command_stdout_tail"]).strip()
    stderr_tail = str(payload["linux_validation_terminal_dispatch_command_stderr_tail"]).strip()
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
    dispatch_command_returncode = payload["linux_validation_terminal_dispatch_command_returncode"]
    release_run_id = payload["release_run_id"]
    return {
        "workflow_linux_validation_terminal_dispatch_execution_status": str(
            payload["linux_validation_terminal_dispatch_execution_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_execution_decision": str(
            payload["linux_validation_terminal_dispatch_execution_decision"]
        ),
        "workflow_linux_validation_terminal_dispatch_execution_exit_code": str(
            payload["linux_validation_terminal_dispatch_execution_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_execution_should_dispatch": (
            "true" if payload["linux_validation_terminal_should_dispatch"] else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_execution_attempted": (
            "true" if payload["linux_validation_terminal_dispatch_attempted"] else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_execution_requires_manual_action": (
            "true"
            if payload["linux_validation_terminal_dispatch_execution_requires_manual_action"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_execution_channel": str(
            payload["linux_validation_terminal_dispatch_execution_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_execution_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_execution_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_execution_run_url": str(
            payload["release_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_execution_command_returncode": (
            "" if dispatch_command_returncode is None else str(dispatch_command_returncode)
        ),
        "workflow_linux_validation_terminal_dispatch_execution_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_execution_report_json": str(output_json),
        "workflow_linux_validation_terminal_dispatch_execution_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Execute Linux CI workflow Linux validation terminal dispatch contract "
            "from P2-69 Linux validation terminal dispatch report"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.json",
        help="P2-69 Linux validation terminal dispatch report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for Linux validation terminal command execution",
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable used by default terminal command",
    )
    parser.add_argument(
        "--linux-validation-terminal-command",
        default="",
        help="Optional explicit Linux validation terminal command string",
    )
    parser.add_argument(
        "--linux-validation-terminal-timeout-seconds",
        type=int,
        default=7200,
        help="Linux validation terminal command timeout in seconds",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json",
        help="Output Linux validation terminal dispatch execution JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.md",
        help="Output Linux validation terminal dispatch execution markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal dispatch execution JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    if args.linux_validation_terminal_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-execution-gate] "
            "--linux-validation-terminal-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    source_path = Path(args.linux_validation_terminal_dispatch_report)
    project_root = Path(args.project_root)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        terminal_dispatch_report = load_linux_validation_terminal_dispatch_report(source_path)
        command_parts = build_linux_validation_terminal_command_parts(
            terminal_dispatch_report=terminal_dispatch_report,
            python_executable=args.python_executable,
            linux_validation_terminal_command=args.linux_validation_terminal_command,
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-execution-gate] "
            f"{exc}",
            file=sys.stderr,
        )
        return 2

    command_result: dict[str, Any] | None = None
    if bool(terminal_dispatch_report["linux_validation_terminal_should_dispatch"]) and not args.dry_run:
        command_result = execute_linux_validation_terminal_command(
            command_parts,
            cwd=project_root,
            timeout_seconds=args.linux_validation_terminal_timeout_seconds,
        )

    payload = build_linux_validation_terminal_dispatch_execution_payload(
        terminal_dispatch_report,
        source_path=source_path.resolve(),
        project_root=project_root.resolve(),
        linux_validation_terminal_timeout_seconds=args.linux_validation_terminal_timeout_seconds,
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
        print(f"linux validation terminal dispatch execution json: {output_json_path}")
        print(f"linux validation terminal dispatch execution markdown: {output_markdown_path}")

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
        "linux validation terminal dispatch execution summary: "
        f"linux_validation_terminal_dispatch_execution_status="
        f"{payload['linux_validation_terminal_dispatch_execution_status']} "
        f"linux_validation_terminal_dispatch_attempted="
        f"{payload['linux_validation_terminal_dispatch_attempted']} "
        f"linux_validation_terminal_dispatch_execution_exit_code="
        f"{payload['linux_validation_terminal_dispatch_execution_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_execution_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
