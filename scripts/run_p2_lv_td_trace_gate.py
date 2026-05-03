"""Phase 2 card P2-71 gate for Linux CI workflow Linux-validation terminal dispatch traceability.

This script consumes the P2-70 Linux-validation terminal dispatch execution artifact
and converges one trace contract:
1) validate terminal-dispatch execution contract,
2) extract workflow run reference (run_id/url) from execution output tails,
3) optionally poll workflow run status immediately,
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


def _coerce_optional_int(value: Any, *, field: str, path: Path) -> int | None:
    if value is None:
        return None
    return _coerce_int(value, field=field, path=path)


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


def load_linux_validation_terminal_dispatch_execution_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: Linux validation terminal dispatch execution report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"{path}: Linux validation terminal dispatch execution payload must be object"
        )

    required_fields = (
        "source_linux_validation_terminal_dispatch_report",
        "linux_validation_terminal_dispatch_execution_status",
        "linux_validation_terminal_dispatch_execution_decision",
        "linux_validation_terminal_dispatch_execution_exit_code",
        "linux_validation_terminal_dispatch_execution_requires_manual_action",
        "linux_validation_terminal_dispatch_execution_channel",
        "linux_validation_terminal_should_dispatch",
        "linux_validation_terminal_dispatch_attempted",
        "linux_validation_terminal_command",
        "linux_validation_terminal_command_parts",
        "linux_validation_terminal_dispatch_command_returncode",
        "linux_validation_terminal_dispatch_command_stdout_tail",
        "linux_validation_terminal_dispatch_command_stderr_tail",
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    execution_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_execution_status"],
        field="linux_validation_terminal_dispatch_execution_status",
        path=path,
    )
    allowed_execution_statuses = {
        "ready_dry_run",
        "ready_with_follow_up_dry_run",
        "dispatched",
        "dispatch_failed",
        "blocked",
        "contract_failed",
    }
    if execution_status not in allowed_execution_statuses:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_execution_status' must be one of "
            f"{sorted(allowed_execution_statuses)}"
        )

    execution_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_execution_exit_code"],
        field="linux_validation_terminal_dispatch_execution_exit_code",
        path=path,
    )
    if execution_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_execution_exit_code' must be >= 0"
        )

    should_dispatch = _coerce_bool(
        payload["linux_validation_terminal_should_dispatch"],
        field="linux_validation_terminal_should_dispatch",
        path=path,
    )
    dispatch_attempted = _coerce_bool(
        payload["linux_validation_terminal_dispatch_attempted"],
        field="linux_validation_terminal_dispatch_attempted",
        path=path,
    )
    command_returncode = _coerce_optional_int(
        payload["linux_validation_terminal_dispatch_command_returncode"],
        field="linux_validation_terminal_dispatch_command_returncode",
        path=path,
    )

    if execution_status in {"ready_dry_run", "ready_with_follow_up_dry_run"}:
        if not should_dispatch:
            raise ValueError(
                f"{path}: {execution_status} requires linux_validation_terminal_should_dispatch=true"
            )
        if dispatch_attempted:
            raise ValueError(
                f"{path}: {execution_status} requires linux_validation_terminal_dispatch_attempted=false"
            )
    elif execution_status == "dispatched":
        if not should_dispatch:
            raise ValueError(f"{path}: dispatched requires linux_validation_terminal_should_dispatch=true")
        if not dispatch_attempted:
            raise ValueError(f"{path}: dispatched requires linux_validation_terminal_dispatch_attempted=true")
        if command_returncode != 0:
            raise ValueError(
                f"{path}: dispatched requires linux_validation_terminal_dispatch_command_returncode=0"
            )
    elif execution_status == "dispatch_failed":
        if not should_dispatch:
            raise ValueError(
                f"{path}: dispatch_failed requires linux_validation_terminal_should_dispatch=true"
            )
        if not dispatch_attempted:
            raise ValueError(
                f"{path}: dispatch_failed requires linux_validation_terminal_dispatch_attempted=true"
            )
    else:
        if should_dispatch:
            raise ValueError(
                f"{path}: {execution_status} requires linux_validation_terminal_should_dispatch=false"
            )

    release_run_id = _coerce_optional_int(payload["release_run_id"], field="release_run_id", path=path)
    if release_run_id is not None and release_run_id < 1:
        raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    return {
        "generated_at": payload.get("generated_at"),
        "source_linux_validation_terminal_dispatch_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_report"],
            field="source_linux_validation_terminal_dispatch_report",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_status": execution_status,
        "linux_validation_terminal_dispatch_execution_decision": _coerce_str(
            payload["linux_validation_terminal_dispatch_execution_decision"],
            field="linux_validation_terminal_dispatch_execution_decision",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_exit_code": execution_exit_code,
        "linux_validation_terminal_dispatch_execution_requires_manual_action": _coerce_bool(
            payload["linux_validation_terminal_dispatch_execution_requires_manual_action"],
            field="linux_validation_terminal_dispatch_execution_requires_manual_action",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_channel": _coerce_str(
            payload["linux_validation_terminal_dispatch_execution_channel"],
            field="linux_validation_terminal_dispatch_execution_channel",
            path=path,
        ),
        "linux_validation_terminal_should_dispatch": should_dispatch,
        "linux_validation_terminal_dispatch_attempted": dispatch_attempted,
        "linux_validation_terminal_command": _coerce_str(
            payload["linux_validation_terminal_command"],
            field="linux_validation_terminal_command",
            path=path,
        ),
        "linux_validation_terminal_command_parts": _coerce_str_list(
            payload["linux_validation_terminal_command_parts"],
            field="linux_validation_terminal_command_parts",
            path=path,
        ),
        "linux_validation_terminal_dispatch_command_returncode": command_returncode,
        "linux_validation_terminal_dispatch_command_stdout_tail": _coerce_str(
            payload["linux_validation_terminal_dispatch_command_stdout_tail"],
            field="linux_validation_terminal_dispatch_command_stdout_tail",
            path=path,
        ),
        "linux_validation_terminal_dispatch_command_stderr_tail": _coerce_str(
            payload["linux_validation_terminal_dispatch_command_stderr_tail"],
            field="linux_validation_terminal_dispatch_command_stderr_tail",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(
            payload["release_run_url"],
            field="release_run_url",
            path=path,
        ),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "reason_codes": _coerce_str_list(
            payload["reason_codes"],
            field="reason_codes",
            path=path,
        ),
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
    *,
    gh_executable: str,
    run_id: int,
    repo_owner: str,
    repo_name: str,
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
            "error_message": f"run poll timeout after {timeout_seconds}s",
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


def build_linux_validation_terminal_dispatch_trace_payload(
    terminal_dispatch_execution_report: dict[str, Any],
    *,
    source_path: Path,
    gh_executable: str,
    poll_now: bool,
    dry_run: bool,
    project_root: Path,
    poll_timeout_seconds: int,
) -> dict[str, Any]:
    execution_status = str(
        terminal_dispatch_execution_report["linux_validation_terminal_dispatch_execution_status"]
    )
    reason_codes = list(terminal_dispatch_execution_report["reason_codes"])
    structural_issues = list(terminal_dispatch_execution_report["structural_issues"])
    missing_artifacts = list(terminal_dispatch_execution_report["missing_artifacts"])

    run_ref = extract_run_reference(
        stdout_tail=str(
            terminal_dispatch_execution_report[
                "linux_validation_terminal_dispatch_command_stdout_tail"
            ]
        ),
        stderr_tail=str(
            terminal_dispatch_execution_report[
                "linux_validation_terminal_dispatch_command_stderr_tail"
            ]
        ),
    )
    run_id = run_ref["run_id"]
    run_url = str(run_ref["run_url"])
    repo_owner = str(run_ref["repo_owner"])
    repo_name = str(run_ref["repo_name"])

    should_poll_workflow_run = execution_status == "dispatched" and run_id is not None
    trace_status = execution_status
    trace_exit_code = int(
        terminal_dispatch_execution_report["linux_validation_terminal_dispatch_execution_exit_code"]
    )
    poll_command_parts: list[str] = []
    poll_command = ""
    poll_attempted = False
    poll_returncode: int | None = None
    poll_status = ""
    poll_conclusion = ""
    poll_url = run_url
    poll_error_type = ""
    poll_error_message = ""
    poll_stdout_tail = ""
    poll_stderr_tail = ""

    if structural_issues or missing_artifacts:
        trace_status = "contract_failed"
        trace_exit_code = max(1, trace_exit_code)
        reason_codes.append("linux_validation_terminal_dispatch_trace_contract_failed")
    elif execution_status == "dispatched":
        if run_id is None:
            trace_status = "run_tracking_missing"
            trace_exit_code = 1
            reason_codes.append("linux_validation_terminal_dispatch_run_reference_missing")
        else:
            trace_status = "run_tracking_ready"
            trace_exit_code = 0
            poll_command_parts = build_run_poll_command(
                gh_executable=gh_executable,
                run_id=int(run_id),
                repo_owner=repo_owner,
                repo_name=repo_name,
            )
            poll_command = _format_shell_command(poll_command_parts)

            if poll_now and not dry_run:
                poll_attempted = True
                poll_result = execute_run_poll_command(
                    poll_command_parts,
                    cwd=project_root,
                    timeout_seconds=poll_timeout_seconds,
                )
                poll_returncode = int(poll_result["returncode"])
                poll_stdout_tail = str(poll_result["stdout_tail"])
                poll_stderr_tail = str(poll_result["stderr_tail"])
                poll_error_type = str(poll_result["error_type"])
                poll_error_message = str(poll_result["error_message"])
                poll_payload = poll_result["payload"]

                if poll_returncode != 0:
                    trace_status = "run_poll_failed"
                    trace_exit_code = 1
                    if poll_error_type == "command_not_found":
                        reason_codes.append(
                            "linux_validation_terminal_dispatch_run_poll_cli_unavailable"
                        )
                    elif poll_error_type == "timeout":
                        reason_codes.append(
                            "linux_validation_terminal_dispatch_run_poll_timeout"
                        )
                    else:
                        reason_codes.append(
                            "linux_validation_terminal_dispatch_run_poll_command_failed"
                        )
                elif poll_payload is None:
                    trace_status = "run_poll_failed"
                    trace_exit_code = 1
                    reason_codes.append(
                        "linux_validation_terminal_dispatch_run_poll_payload_invalid"
                    )
                else:
                    poll_status_value = poll_payload.get("status")
                    poll_conclusion_value = poll_payload.get("conclusion")
                    poll_url_value = poll_payload.get("url")
                    if isinstance(poll_status_value, str):
                        poll_status = poll_status_value
                    if isinstance(poll_conclusion_value, str):
                        poll_conclusion = poll_conclusion_value
                    if isinstance(poll_url_value, str) and poll_url_value:
                        poll_url = poll_url_value

                    if poll_status == "completed":
                        if poll_conclusion == "success":
                            trace_status = "run_completed_success"
                            trace_exit_code = 0
                            reason_codes = [
                                "linux_validation_terminal_dispatch_run_completed_success"
                            ]
                        else:
                            trace_status = "run_completed_failure"
                            trace_exit_code = 1
                            reason_codes.append(
                                "linux_validation_terminal_dispatch_run_completed_with_failure"
                            )
                    else:
                        trace_status = "run_in_progress"
                        trace_exit_code = 0
                        reason_codes.append(
                            "linux_validation_terminal_dispatch_run_still_in_progress"
                        )
    elif execution_status in {"dispatch_failed", "blocked", "contract_failed"}:
        trace_exit_code = max(1, trace_exit_code)
    elif execution_status in {"ready_dry_run", "ready_with_follow_up_dry_run"}:
        trace_exit_code = max(0, trace_exit_code)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_linux_validation_terminal_dispatch_execution_report": str(source_path),
        "project_root": str(project_root),
        "source_linux_validation_terminal_dispatch_report": str(
            terminal_dispatch_execution_report["source_linux_validation_terminal_dispatch_report"]
        ),
        "linux_validation_terminal_dispatch_execution_status": execution_status,
        "linux_validation_terminal_dispatch_execution_decision": str(
            terminal_dispatch_execution_report[
                "linux_validation_terminal_dispatch_execution_decision"
            ]
        ),
        "linux_validation_terminal_dispatch_execution_exit_code": int(
            terminal_dispatch_execution_report[
                "linux_validation_terminal_dispatch_execution_exit_code"
            ]
        ),
        "linux_validation_terminal_should_dispatch": bool(
            terminal_dispatch_execution_report["linux_validation_terminal_should_dispatch"]
        ),
        "linux_validation_terminal_dispatch_attempted": bool(
            terminal_dispatch_execution_report["linux_validation_terminal_dispatch_attempted"]
        ),
        "linux_validation_terminal_dispatch_trace_status": trace_status,
        "linux_validation_terminal_dispatch_trace_exit_code": int(trace_exit_code),
        "poll_now": poll_now,
        "dry_run": dry_run,
        "linux_validation_terminal_should_poll_workflow_run": should_poll_workflow_run,
        "linux_validation_terminal_run_id": run_id,
        "linux_validation_terminal_run_url": run_url,
        "linux_validation_terminal_repo_owner": repo_owner,
        "linux_validation_terminal_repo_name": repo_name,
        "linux_validation_terminal_poll_command": poll_command,
        "linux_validation_terminal_poll_command_parts": poll_command_parts,
        "linux_validation_terminal_poll_attempted": poll_attempted,
        "linux_validation_terminal_poll_returncode": poll_returncode,
        "linux_validation_terminal_poll_status": poll_status,
        "linux_validation_terminal_poll_conclusion": poll_conclusion,
        "linux_validation_terminal_poll_url": poll_url,
        "linux_validation_terminal_poll_error_type": poll_error_type,
        "linux_validation_terminal_poll_error_message": poll_error_message,
        "linux_validation_terminal_poll_stdout_tail": poll_stdout_tail,
        "linux_validation_terminal_poll_stderr_tail": poll_stderr_tail,
        "release_run_id": terminal_dispatch_execution_report["release_run_id"],
        "release_run_url": str(terminal_dispatch_execution_report["release_run_url"]),
        "follow_up_queue_url": str(terminal_dispatch_execution_report["follow_up_queue_url"]),
        "dispatch_execution_reason_codes": list(terminal_dispatch_execution_report["reason_codes"]),
        "reason_codes": _unique(reason_codes),
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Linux Validation Terminal Dispatch Trace Report",
        "",
        (
            "- Linux Validation Terminal Dispatch Trace Status: "
            f"**{str(payload['linux_validation_terminal_dispatch_trace_status']).upper()}**"
        ),
        (
            "- Linux Validation Terminal Dispatch Trace Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_trace_exit_code']}`"
        ),
        (
            "- Should Poll Workflow Run: "
            f"`{payload['linux_validation_terminal_should_poll_workflow_run']}`"
        ),
        f"- Poll Attempted: `{payload['linux_validation_terminal_poll_attempted']}`",
        f"- Run ID: `{payload['linux_validation_terminal_run_id']}`",
        f"- Run URL: `{payload['linux_validation_terminal_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Poll Command",
    ]

    if payload["linux_validation_terminal_poll_command"]:
        lines.append(f"- `{payload['linux_validation_terminal_poll_command']}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Reason Codes"])
    reason_codes = payload["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{item}`" for item in reason_codes)
    else:
        lines.append("- none")

    lines.extend(["", "## Poll Result"])
    lines.append(
        f"- Poll Return Code: `{payload['linux_validation_terminal_poll_returncode']}`"
    )
    lines.append(f"- Poll Status: `{payload['linux_validation_terminal_poll_status']}`")
    lines.append(
        f"- Poll Conclusion: `{payload['linux_validation_terminal_poll_conclusion']}`"
    )
    lines.append(f"- Poll URL: `{payload['linux_validation_terminal_poll_url']}`")
    lines.append(
        f"- Poll Error Type: `{payload['linux_validation_terminal_poll_error_type']}`"
    )

    if payload["linux_validation_terminal_poll_stdout_tail"]:
        lines.append("- Poll stdout:")
        lines.append("```text")
        lines.append(str(payload["linux_validation_terminal_poll_stdout_tail"]))
        lines.append("```")
    if payload["linux_validation_terminal_poll_stderr_tail"]:
        lines.append("- Poll stderr:")
        lines.append("```text")
        lines.append(str(payload["linux_validation_terminal_poll_stderr_tail"]))
        lines.append("```")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    run_id = payload["linux_validation_terminal_run_id"]
    return {
        "workflow_linux_validation_terminal_dispatch_trace_status": str(
            payload["linux_validation_terminal_dispatch_trace_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_trace_should_poll": (
            "true" if payload["linux_validation_terminal_should_poll_workflow_run"] else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_trace_run_id": (
            "" if run_id is None else str(run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_trace_run_url": str(
            payload["linux_validation_terminal_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_trace_poll_status": str(
            payload["linux_validation_terminal_poll_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_trace_poll_conclusion": str(
            payload["linux_validation_terminal_poll_conclusion"]
        ),
        "workflow_linux_validation_terminal_dispatch_trace_exit_code": str(
            payload["linux_validation_terminal_dispatch_trace_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_trace_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_trace_report_json": str(output_json),
        "workflow_linux_validation_terminal_dispatch_trace_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build Linux CI workflow Linux validation terminal dispatch trace report "
            "from P2-70 execution artifact"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-execution-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json",
        help="P2-70 Linux validation terminal dispatch execution report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for optional poll command execution",
    )
    parser.add_argument(
        "--gh-executable",
        default="gh",
        help="GitHub CLI executable for poll command generation/execution",
    )
    parser.add_argument(
        "--poll-timeout-seconds",
        type=int,
        default=600,
        help="Workflow run poll timeout in seconds when --poll-now is enabled",
    )
    parser.add_argument(
        "--poll-now",
        action="store_true",
        help="Execute workflow run poll command when run reference is available",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json",
        help="Output Linux validation terminal dispatch trace JSON report path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.md",
        help="Output Linux validation terminal dispatch trace markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal dispatch trace JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    if args.poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-trace-gate] "
            "--poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    report_path = Path(args.linux_validation_terminal_dispatch_execution_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)
    project_root = Path(args.project_root).resolve()

    try:
        execution_report = load_linux_validation_terminal_dispatch_execution_report(report_path)
        payload = build_linux_validation_terminal_dispatch_trace_payload(
            execution_report,
            source_path=report_path.resolve(),
            gh_executable=args.gh_executable,
            poll_now=args.poll_now,
            dry_run=args.dry_run,
            project_root=project_root,
            poll_timeout_seconds=args.poll_timeout_seconds,
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-trace-gate] "
            f"{exc}",
            file=sys.stderr,
        )
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"linux validation terminal dispatch trace json: {output_json_path}")
        print(f"linux validation terminal dispatch trace markdown: {output_markdown_path}")

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
        "linux validation terminal dispatch trace summary: "
        f"linux_validation_terminal_dispatch_trace_status="
        f"{payload['linux_validation_terminal_dispatch_trace_status']} "
        f"should_poll={payload['linux_validation_terminal_should_poll_workflow_run']} "
        f"linux_validation_terminal_dispatch_trace_exit_code="
        f"{payload['linux_validation_terminal_dispatch_trace_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_trace_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
