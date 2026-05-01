"""Phase 2 card P2-32 gate for Linux CI workflow release traceability.

This script consumes the P2-31 release trigger artifact and converges a
release-run trace contract:
1) validate release trigger contract and trigger status,
2) extract release run reference (run_id/url) for triggered releases,
3) optionally poll release run status immediately,
4) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_URL_PATTERN = re.compile(
    r"https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/actions/runs/(?P<run_id>\d+)"
)


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


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _tail_text(text: str, *, max_lines: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def _unique(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def load_release_trigger_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release trigger report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release trigger payload must be object")

    required_fields = (
        "source_release_handoff_report",
        "source_terminal_publish_report",
        "source_dispatch_completion_report",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
        "handoff_status",
        "should_trigger_release",
        "release_trigger_status",
        "release_trigger_exit_code",
        "release_trigger_attempted",
        "release_command",
        "release_command_parts",
        "release_workflow_path",
        "release_workflow_ref",
        "target_environment",
        "release_channel",
        "run_id",
        "run_url",
        "command_returncode",
        "command_stdout_tail",
        "command_stderr_tail",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    release_trigger_status = _coerce_str(
        payload["release_trigger_status"],
        field="release_trigger_status",
        path=path,
    )
    allowed_release_trigger_statuses = {
        "ready_dry_run",
        "awaiting_completion",
        "blocked",
        "handoff_failed",
        "triggered",
        "trigger_failed",
    }
    if release_trigger_status not in allowed_release_trigger_statuses:
        raise ValueError(
            f"{path}: field 'release_trigger_status' must be one of "
            f"{sorted(allowed_release_trigger_statuses)}"
        )

    should_trigger_release = _coerce_bool(
        payload["should_trigger_release"],
        field="should_trigger_release",
        path=path,
    )
    release_trigger_exit_code = _coerce_int(
        payload["release_trigger_exit_code"],
        field="release_trigger_exit_code",
        path=path,
    )
    if release_trigger_exit_code < 0:
        raise ValueError(f"{path}: field 'release_trigger_exit_code' must be >= 0")

    release_trigger_attempted = _coerce_bool(
        payload["release_trigger_attempted"],
        field="release_trigger_attempted",
        path=path,
    )
    release_command = _coerce_str(payload["release_command"], field="release_command", path=path)
    release_command_parts = _coerce_str_list(
        payload["release_command_parts"],
        field="release_command_parts",
        path=path,
    )
    release_workflow_path = _coerce_str(
        payload["release_workflow_path"],
        field="release_workflow_path",
        path=path,
    )
    release_workflow_ref = _coerce_str(
        payload["release_workflow_ref"],
        field="release_workflow_ref",
        path=path,
    )
    handoff_status = _coerce_str(payload["handoff_status"], field="handoff_status", path=path)
    target_environment = _coerce_str(
        payload["target_environment"],
        field="target_environment",
        path=path,
    )
    release_channel = _coerce_str(payload["release_channel"], field="release_channel", path=path)

    run_id_raw = payload["run_id"]
    if run_id_raw is None:
        run_id = None
    else:
        run_id = _coerce_int(run_id_raw, field="run_id", path=path)
        if run_id < 1:
            raise ValueError(f"{path}: field 'run_id' must be >= 1 when present")
    run_url = _coerce_str(payload["run_url"], field="run_url", path=path)

    command_returncode_raw = payload["command_returncode"]
    if command_returncode_raw is None:
        command_returncode = None
    else:
        command_returncode = _coerce_int(
            command_returncode_raw,
            field="command_returncode",
            path=path,
        )
    command_stdout_tail = _coerce_str(
        payload["command_stdout_tail"],
        field="command_stdout_tail",
        path=path,
    )
    command_stderr_tail = _coerce_str(
        payload["command_stderr_tail"],
        field="command_stderr_tail",
        path=path,
    )

    reason_codes = _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path)
    failed_checks = _coerce_str_list(payload["failed_checks"], field="failed_checks", path=path)
    structural_issues = _coerce_str_list(
        payload["structural_issues"],
        field="structural_issues",
        path=path,
    )
    missing_artifacts = _coerce_str_list(
        payload["missing_artifacts"],
        field="missing_artifacts",
        path=path,
    )
    source_release_handoff_report = _coerce_str(
        payload["source_release_handoff_report"],
        field="source_release_handoff_report",
        path=path,
    )
    source_terminal_publish_report = _coerce_str(
        payload["source_terminal_publish_report"],
        field="source_terminal_publish_report",
        path=path,
    )
    source_dispatch_completion_report = _coerce_str(
        payload["source_dispatch_completion_report"],
        field="source_dispatch_completion_report",
        path=path,
    )
    source_dispatch_trace_report = _coerce_str(
        payload["source_dispatch_trace_report"],
        field="source_dispatch_trace_report",
        path=path,
    )
    source_dispatch_execution_report = _coerce_str(
        payload["source_dispatch_execution_report"],
        field="source_dispatch_execution_report",
        path=path,
    )
    source_dispatch_report = _coerce_str(
        payload["source_dispatch_report"],
        field="source_dispatch_report",
        path=path,
    )

    if release_trigger_status == "triggered":
        if not should_trigger_release:
            raise ValueError(f"{path}: triggered requires should_trigger_release=true")
        if not release_trigger_attempted:
            raise ValueError(f"{path}: triggered requires release_trigger_attempted=true")
        if release_trigger_exit_code != 0:
            raise ValueError(f"{path}: triggered requires release_trigger_exit_code=0")
        if command_returncode != 0:
            raise ValueError(f"{path}: triggered requires command_returncode=0")
    elif release_trigger_status == "trigger_failed":
        if not should_trigger_release:
            raise ValueError(f"{path}: trigger_failed requires should_trigger_release=true")
        if not release_trigger_attempted:
            raise ValueError(f"{path}: trigger_failed requires release_trigger_attempted=true")
        if release_trigger_exit_code == 0:
            raise ValueError(f"{path}: trigger_failed requires release_trigger_exit_code>0")
    elif release_trigger_status == "ready_dry_run":
        if not should_trigger_release:
            raise ValueError(f"{path}: ready_dry_run requires should_trigger_release=true")
        if release_trigger_attempted:
            raise ValueError(f"{path}: ready_dry_run requires release_trigger_attempted=false")
        if release_trigger_exit_code != 0:
            raise ValueError(f"{path}: ready_dry_run requires release_trigger_exit_code=0")
    elif release_trigger_status in {"awaiting_completion", "blocked"}:
        if should_trigger_release:
            raise ValueError(
                f"{path}: {release_trigger_status} requires should_trigger_release=false"
            )
        if release_trigger_exit_code != 0:
            raise ValueError(
                f"{path}: {release_trigger_status} requires release_trigger_exit_code=0"
            )
    else:
        if should_trigger_release:
            raise ValueError(f"{path}: handoff_failed requires should_trigger_release=false")
        if release_trigger_exit_code == 0:
            raise ValueError(f"{path}: handoff_failed requires release_trigger_exit_code>0")

    return {
        "generated_at": payload.get("generated_at"),
        "source_release_handoff_report": source_release_handoff_report,
        "source_terminal_publish_report": source_terminal_publish_report,
        "source_dispatch_completion_report": source_dispatch_completion_report,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
        "handoff_status": handoff_status,
        "should_trigger_release": should_trigger_release,
        "release_trigger_status": release_trigger_status,
        "release_trigger_exit_code": release_trigger_exit_code,
        "release_trigger_attempted": release_trigger_attempted,
        "release_command": release_command,
        "release_command_parts": release_command_parts,
        "release_workflow_path": release_workflow_path,
        "release_workflow_ref": release_workflow_ref,
        "target_environment": target_environment,
        "release_channel": release_channel,
        "run_id": run_id,
        "run_url": run_url,
        "command_returncode": command_returncode,
        "command_stdout_tail": command_stdout_tail,
        "command_stderr_tail": command_stderr_tail,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


def extract_run_reference(*, stdout_tail: str, stderr_tail: str) -> dict[str, Any]:
    merged = "\n".join(item for item in (stdout_tail, stderr_tail) if item)
    match = RUN_URL_PATTERN.search(merged)
    if not match:
        return {
            "run_url": "",
            "run_id": None,
            "repo_owner": "",
            "repo_name": "",
        }
    run_url = match.group(0)
    return {
        "run_url": run_url,
        "run_id": int(match.group("run_id")),
        "repo_owner": match.group("owner"),
        "repo_name": match.group("repo"),
    }


def build_run_poll_command(
    *, gh_executable: str, run_id: int, repo_owner: str, repo_name: str
) -> list[str]:
    command = [
        gh_executable,
        "run",
        "view",
        str(run_id),
        "--json",
        "databaseId,status,conclusion,url,workflowName,createdAt,updatedAt",
    ]
    if repo_owner and repo_name:
        command.extend(["--repo", f"{repo_owner}/{repo_name}"])
    return command


def execute_run_poll_command(
    command_parts: list[str], *, cwd: Path, timeout_seconds: int
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
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "payload": None,
            "error_type": "command_not_found",
            "error_message": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "returncode": 124,
            "stdout_tail": _tail_text(stdout),
            "stderr_tail": _tail_text(stderr),
            "payload": None,
            "error_type": "timeout",
            "error_message": f"release run poll timeout after {timeout_seconds}s",
        }

    stdout_text = completed.stdout or ""
    stderr_text = completed.stderr or ""
    poll_payload: dict[str, Any] | None = None
    error_type = ""
    error_message = ""
    if completed.returncode == 0:
        try:
            parsed = json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            error_type = "invalid_poll_json"
            error_message = str(exc)
        else:
            if isinstance(parsed, dict):
                poll_payload = parsed
            else:
                error_type = "invalid_poll_payload"
                error_message = "poll payload must be object"

    return {
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(stdout_text),
        "stderr_tail": _tail_text(stderr_text),
        "payload": poll_payload,
        "error_type": error_type,
        "error_message": error_message,
    }


def build_release_trace_payload(
    release_trigger_report: dict[str, Any],
    *,
    source_path: Path,
    gh_executable: str,
    poll_now: bool,
    dry_run: bool,
    project_root: Path,
    poll_timeout_seconds: int,
) -> dict[str, Any]:
    release_trigger_status = str(release_trigger_report["release_trigger_status"])
    reason_codes = list(release_trigger_report["reason_codes"])

    run_ref = extract_run_reference(
        stdout_tail=str(release_trigger_report["command_stdout_tail"]),
        stderr_tail=str(release_trigger_report["command_stderr_tail"]),
    )
    release_run_id = run_ref["run_id"]
    release_run_url = str(run_ref["run_url"])
    repo_owner = str(run_ref["repo_owner"])
    repo_name = str(run_ref["repo_name"])

    should_poll_release_run = False
    release_tracking_status = release_trigger_status
    release_trace_exit_code = int(release_trigger_report["release_trigger_exit_code"])
    release_poll_command_parts: list[str] = []
    release_poll_command = ""
    release_poll_attempted = False
    release_poll_returncode: int | None = None
    release_poll_status = ""
    release_poll_conclusion = ""
    release_poll_url = release_run_url
    release_poll_error_type = ""
    release_poll_error_message = ""
    release_poll_stdout_tail = ""
    release_poll_stderr_tail = ""

    if release_trigger_status == "triggered":
        if release_run_id is None:
            release_tracking_status = "release_run_tracking_missing"
            release_trace_exit_code = 1
            reason_codes.append("release_run_reference_missing")
        else:
            should_poll_release_run = True
            release_tracking_status = "release_run_tracking_ready"
            release_poll_command_parts = build_run_poll_command(
                gh_executable=gh_executable,
                run_id=int(release_run_id),
                repo_owner=repo_owner,
                repo_name=repo_name,
            )
            release_poll_command = _format_shell_command(release_poll_command_parts)

            if poll_now and not dry_run:
                release_poll_attempted = True
                poll_result = execute_run_poll_command(
                    release_poll_command_parts,
                    cwd=project_root,
                    timeout_seconds=poll_timeout_seconds,
                )
                release_poll_returncode = int(poll_result["returncode"])
                release_poll_stdout_tail = str(poll_result["stdout_tail"])
                release_poll_stderr_tail = str(poll_result["stderr_tail"])
                release_poll_error_type = str(poll_result["error_type"])
                release_poll_error_message = str(poll_result["error_message"])
                poll_payload = poll_result["payload"]

                if release_poll_returncode != 0:
                    release_tracking_status = "release_run_poll_failed"
                    release_trace_exit_code = 1
                    if release_poll_error_type == "command_not_found":
                        reason_codes.append("release_run_poll_cli_unavailable")
                    elif release_poll_error_type == "timeout":
                        reason_codes.append("release_run_poll_timeout")
                    else:
                        reason_codes.append("release_run_poll_command_failed")
                elif poll_payload is None:
                    release_tracking_status = "release_run_poll_failed"
                    release_trace_exit_code = 1
                    reason_codes.append("release_run_poll_payload_invalid")
                else:
                    poll_status_value = poll_payload.get("status")
                    poll_conclusion_value = poll_payload.get("conclusion")
                    poll_url_value = poll_payload.get("url")
                    if isinstance(poll_status_value, str):
                        release_poll_status = poll_status_value
                    if isinstance(poll_conclusion_value, str):
                        release_poll_conclusion = poll_conclusion_value
                    if isinstance(poll_url_value, str) and poll_url_value:
                        release_poll_url = poll_url_value

                    if release_poll_status == "completed":
                        if release_poll_conclusion == "success":
                            release_tracking_status = "release_run_completed_success"
                            release_trace_exit_code = 0
                            reason_codes = ["release_run_completed_success"]
                        else:
                            release_tracking_status = "release_run_completed_failure"
                            release_trace_exit_code = 1
                            reason_codes.append("release_run_completed_with_failure")
                    else:
                        release_tracking_status = "release_run_in_progress"
                        release_trace_exit_code = 0
                        reason_codes.append("release_run_still_in_progress")
    elif release_trigger_status == "ready_dry_run":
        release_tracking_status = "release_ready_dry_run"
        release_trace_exit_code = 0
    elif release_trigger_status == "awaiting_completion":
        release_tracking_status = "awaiting_completion"
        release_trace_exit_code = 0
    elif release_trigger_status == "blocked":
        release_tracking_status = "blocked"
        release_trace_exit_code = 0
    elif release_trigger_status == "handoff_failed":
        release_tracking_status = "handoff_failed"
        release_trace_exit_code = max(1, release_trace_exit_code)
    elif release_trigger_status == "trigger_failed":
        release_tracking_status = "release_trigger_failed"
        release_trace_exit_code = max(1, release_trace_exit_code)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_trigger_report": str(source_path),
        "project_root": str(project_root),
        "source_release_handoff_report": str(release_trigger_report["source_release_handoff_report"]),
        "source_terminal_publish_report": str(release_trigger_report["source_terminal_publish_report"]),
        "source_dispatch_completion_report": str(
            release_trigger_report["source_dispatch_completion_report"]
        ),
        "source_dispatch_trace_report": str(release_trigger_report["source_dispatch_trace_report"]),
        "source_dispatch_execution_report": str(
            release_trigger_report["source_dispatch_execution_report"]
        ),
        "source_dispatch_report": str(release_trigger_report["source_dispatch_report"]),
        "handoff_status": str(release_trigger_report["handoff_status"]),
        "release_trigger_status": release_trigger_status,
        "release_trigger_exit_code": int(release_trigger_report["release_trigger_exit_code"]),
        "should_trigger_release": bool(release_trigger_report["should_trigger_release"]),
        "release_trigger_attempted": bool(release_trigger_report["release_trigger_attempted"]),
        "target_environment": str(release_trigger_report["target_environment"]),
        "release_channel": str(release_trigger_report["release_channel"]),
        "release_workflow_path": str(release_trigger_report["release_workflow_path"]),
        "release_workflow_ref": str(release_trigger_report["release_workflow_ref"]),
        "release_tracking_status": release_tracking_status,
        "release_trace_exit_code": int(release_trace_exit_code),
        "poll_now": poll_now,
        "dry_run": dry_run,
        "should_poll_release_run": should_poll_release_run,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "release_poll_command": release_poll_command,
        "release_poll_command_parts": release_poll_command_parts,
        "release_poll_attempted": release_poll_attempted,
        "release_poll_returncode": release_poll_returncode,
        "release_poll_status": release_poll_status,
        "release_poll_conclusion": release_poll_conclusion,
        "release_poll_url": release_poll_url,
        "release_poll_error_type": release_poll_error_type,
        "release_poll_error_message": release_poll_error_message,
        "release_poll_stdout_tail": release_poll_stdout_tail,
        "release_poll_stderr_tail": release_poll_stderr_tail,
        "release_trigger_reason_codes": list(release_trigger_report["reason_codes"]),
        "reason_codes": _unique(reason_codes),
        "failed_checks": list(release_trigger_report["failed_checks"]),
        "structural_issues": list(release_trigger_report["structural_issues"]),
        "missing_artifacts": list(release_trigger_report["missing_artifacts"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Trace Report",
        "",
        f"- Release Tracking Status: **{str(payload['release_tracking_status']).upper()}**",
        f"- Release Trace Exit Code: `{payload['release_trace_exit_code']}`",
        f"- Should Poll Release Run: `{payload['should_poll_release_run']}`",
        f"- Release Poll Attempted: `{payload['release_poll_attempted']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Release Trigger Report: `{payload['source_release_trigger_report']}`",
        f"- Source Release Handoff Report: `{payload['source_release_handoff_report']}`",
        f"- Source Terminal Publish Report: `{payload['source_terminal_publish_report']}`",
        f"- Source Dispatch Completion Report: `{payload['source_dispatch_completion_report']}`",
        "",
        "## Release Poll Command",
    ]

    if payload["release_poll_command"]:
        lines.append(f"- `{payload['release_poll_command']}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Reason Codes"])
    reason_codes = payload["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{item}`" for item in reason_codes)
    else:
        lines.append("- none")

    lines.extend(["", "## Release Poll Result"])
    lines.append(f"- Release Poll Return Code: `{payload['release_poll_returncode']}`")
    lines.append(f"- Release Poll Status: `{payload['release_poll_status']}`")
    lines.append(f"- Release Poll Conclusion: `{payload['release_poll_conclusion']}`")
    lines.append(f"- Release Poll URL: `{payload['release_poll_url']}`")
    lines.append(f"- Release Poll Error Type: `{payload['release_poll_error_type']}`")
    if payload["release_poll_stdout_tail"]:
        lines.append("- Release Poll stdout:")
        lines.append("```text")
        lines.append(str(payload["release_poll_stdout_tail"]))
        lines.append("```")
    if payload["release_poll_stderr_tail"]:
        lines.append("- Release Poll stderr:")
        lines.append("```text")
        lines.append(str(payload["release_poll_stderr_tail"]))
        lines.append("```")
    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    return {
        "workflow_release_trace_status": str(payload["release_tracking_status"]),
        "workflow_release_trace_should_poll": (
            "true" if payload["should_poll_release_run"] else "false"
        ),
        "workflow_release_trace_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_trace_run_url": str(payload["release_run_url"]),
        "workflow_release_trace_poll_status": str(payload["release_poll_status"]),
        "workflow_release_trace_poll_conclusion": str(payload["release_poll_conclusion"]),
        "workflow_release_trace_exit_code": str(payload["release_trace_exit_code"]),
        "workflow_release_trace_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_trace_report_json": str(output_json),
        "workflow_release_trace_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build Linux CI workflow release trace report from P2-31 release trigger artifact"
        )
    )
    parser.add_argument(
        "--release-trigger-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trigger.json",
        help="P2-31 release trigger report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for optional release run poll command execution",
    )
    parser.add_argument(
        "--gh-executable",
        default="gh",
        help="GitHub CLI executable for release run poll command",
    )
    parser.add_argument(
        "--poll-timeout-seconds",
        type=int,
        default=600,
        help="Release run poll timeout in seconds when --poll-now is enabled",
    )
    parser.add_argument(
        "--poll-now",
        action="store_true",
        help="Execute release run poll command when run reference is available",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trace.json",
        help="Output release trace JSON report path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trace.md",
        help="Output release trace markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release trace JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    if args.poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-release-trace-gate] --poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    release_trigger_report_path = Path(args.release_trigger_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)
    project_root = Path(args.project_root).resolve()

    try:
        release_trigger_report = load_release_trigger_report(release_trigger_report_path)
        payload = build_release_trace_payload(
            release_trigger_report,
            source_path=release_trigger_report_path.resolve(),
            gh_executable=args.gh_executable,
            poll_now=args.poll_now,
            dry_run=args.dry_run,
            project_root=project_root,
            poll_timeout_seconds=args.poll_timeout_seconds,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-trace-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release trace json: {output_json_path}")
        print(f"release trace markdown: {output_markdown_path}")

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
        "release trace summary: "
        f"release_tracking_status={payload['release_tracking_status']} "
        f"should_poll={payload['should_poll_release_run']} "
        f"release_trace_exit_code={payload['release_trace_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_trace_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
