"""Phase 2 card P2-72 gate for Linux CI workflow Linux validation terminal dispatch completion await.

This script consumes the P2-71 Linux validation terminal dispatch trace artifact and converges to
one completion contract:
1) validate dispatch trace contract and poll command,
2) optionally poll workflow run status until terminal/timeout,
3) emit completion JSON/Markdown + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TRACE_STATUSES: set[str] = {
    "blocked",
    "ready_dry_run",
    "ready_with_follow_up_dry_run",
    "dispatch_failed",
    "contract_failed",
    "run_tracking_missing",
    "run_tracking_ready",
    "run_in_progress",
    "run_completed_success",
    "run_completed_failure",
    "run_poll_failed",
}


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


def load_linux_validation_terminal_dispatch_trace_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: Linux validation terminal dispatch trace report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"{path}: Linux validation terminal dispatch trace payload must be object"
        )

    required_fields = (
        "source_linux_validation_terminal_dispatch_execution_report",
        "source_linux_validation_terminal_dispatch_report",
        "linux_validation_terminal_dispatch_execution_status",
        "linux_validation_terminal_dispatch_execution_decision",
        "linux_validation_terminal_dispatch_execution_exit_code",
        "linux_validation_terminal_should_dispatch",
        "linux_validation_terminal_dispatch_attempted",
        "linux_validation_terminal_dispatch_trace_status",
        "linux_validation_terminal_dispatch_trace_exit_code",
        "linux_validation_terminal_should_poll_workflow_run",
        "linux_validation_terminal_run_id",
        "linux_validation_terminal_run_url",
        "linux_validation_terminal_repo_owner",
        "linux_validation_terminal_repo_name",
        "linux_validation_terminal_poll_command",
        "linux_validation_terminal_poll_command_parts",
        "linux_validation_terminal_poll_attempted",
        "linux_validation_terminal_poll_returncode",
        "linux_validation_terminal_poll_status",
        "linux_validation_terminal_poll_conclusion",
        "linux_validation_terminal_poll_url",
        "linux_validation_terminal_poll_error_type",
        "linux_validation_terminal_poll_error_message",
        "linux_validation_terminal_poll_stdout_tail",
        "linux_validation_terminal_poll_stderr_tail",
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

    trace_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_trace_status"],
        field="linux_validation_terminal_dispatch_trace_status",
        path=path,
    )
    if trace_status not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TRACE_STATUSES:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_trace_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TRACE_STATUSES)}"
        )

    trace_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_trace_exit_code"],
        field="linux_validation_terminal_dispatch_trace_exit_code",
        path=path,
    )
    if trace_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_trace_exit_code' must be >= 0"
        )

    should_poll_workflow_run = _coerce_bool(
        payload["linux_validation_terminal_should_poll_workflow_run"],
        field="linux_validation_terminal_should_poll_workflow_run",
        path=path,
    )

    run_id_raw = payload["linux_validation_terminal_run_id"]
    if run_id_raw is None:
        run_id = None
    else:
        run_id = _coerce_int(run_id_raw, field="linux_validation_terminal_run_id", path=path)
        if run_id < 1:
            raise ValueError(
                f"{path}: field 'linux_validation_terminal_run_id' must be >= 1 when present"
            )

    run_url = _coerce_str(
        payload["linux_validation_terminal_run_url"],
        field="linux_validation_terminal_run_url",
        path=path,
    )
    repo_owner = _coerce_str(
        payload["linux_validation_terminal_repo_owner"],
        field="linux_validation_terminal_repo_owner",
        path=path,
    )
    repo_name = _coerce_str(
        payload["linux_validation_terminal_repo_name"],
        field="linux_validation_terminal_repo_name",
        path=path,
    )
    poll_command = _coerce_str(
        payload["linux_validation_terminal_poll_command"],
        field="linux_validation_terminal_poll_command",
        path=path,
    )
    poll_command_parts = _coerce_str_list(
        payload["linux_validation_terminal_poll_command_parts"],
        field="linux_validation_terminal_poll_command_parts",
        path=path,
    )
    poll_attempted = _coerce_bool(
        payload["linux_validation_terminal_poll_attempted"],
        field="linux_validation_terminal_poll_attempted",
        path=path,
    )
    poll_returncode_raw = payload["linux_validation_terminal_poll_returncode"]
    if poll_returncode_raw is None:
        poll_returncode = None
    else:
        poll_returncode = _coerce_int(
            poll_returncode_raw,
            field="linux_validation_terminal_poll_returncode",
            path=path,
        )
    poll_status = _coerce_str(
        payload["linux_validation_terminal_poll_status"],
        field="linux_validation_terminal_poll_status",
        path=path,
    )
    poll_conclusion = _coerce_str(
        payload["linux_validation_terminal_poll_conclusion"],
        field="linux_validation_terminal_poll_conclusion",
        path=path,
    )
    poll_url = _coerce_str(
        payload["linux_validation_terminal_poll_url"],
        field="linux_validation_terminal_poll_url",
        path=path,
    )
    poll_error_type = _coerce_str(
        payload["linux_validation_terminal_poll_error_type"],
        field="linux_validation_terminal_poll_error_type",
        path=path,
    )
    poll_error_message = _coerce_str(
        payload["linux_validation_terminal_poll_error_message"],
        field="linux_validation_terminal_poll_error_message",
        path=path,
    )
    poll_stdout_tail = _coerce_str(
        payload["linux_validation_terminal_poll_stdout_tail"],
        field="linux_validation_terminal_poll_stdout_tail",
        path=path,
    )
    poll_stderr_tail = _coerce_str(
        payload["linux_validation_terminal_poll_stderr_tail"],
        field="linux_validation_terminal_poll_stderr_tail",
        path=path,
    )
    reason_codes = _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path)
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

    if should_poll_workflow_run:
        if run_id is None:
            raise ValueError(f"{path}: should_poll_workflow_run=true requires run_id")
        if not poll_command_parts:
            raise ValueError(f"{path}: should_poll_workflow_run=true requires poll_command_parts")
        if len(poll_command_parts) < 3 or poll_command_parts[1:3] != ["run", "view"]:
            raise ValueError(f"{path}: poll_command_parts must include '<gh> run view ...' contract")
        if shlex.split(poll_command) != poll_command_parts:
            raise ValueError(f"{path}: poll_command and poll_command_parts mismatch")
    else:
        if run_id is not None:
            raise ValueError(f"{path}: should_poll_workflow_run=false requires run_id=null")

    return {
        "generated_at": payload.get("generated_at"),
        "source_linux_validation_terminal_dispatch_execution_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_execution_report"],
            field="source_linux_validation_terminal_dispatch_execution_report",
            path=path,
        ),
        "source_linux_validation_terminal_dispatch_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_report"],
            field="source_linux_validation_terminal_dispatch_report",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_status": _coerce_str(
            payload["linux_validation_terminal_dispatch_execution_status"],
            field="linux_validation_terminal_dispatch_execution_status",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_decision": _coerce_str(
            payload["linux_validation_terminal_dispatch_execution_decision"],
            field="linux_validation_terminal_dispatch_execution_decision",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_exit_code": _coerce_int(
            payload["linux_validation_terminal_dispatch_execution_exit_code"],
            field="linux_validation_terminal_dispatch_execution_exit_code",
            path=path,
        ),
        "linux_validation_terminal_should_dispatch": _coerce_bool(
            payload["linux_validation_terminal_should_dispatch"],
            field="linux_validation_terminal_should_dispatch",
            path=path,
        ),
        "linux_validation_terminal_dispatch_attempted": _coerce_bool(
            payload["linux_validation_terminal_dispatch_attempted"],
            field="linux_validation_terminal_dispatch_attempted",
            path=path,
        ),
        "linux_validation_terminal_dispatch_trace_status": trace_status,
        "linux_validation_terminal_dispatch_trace_exit_code": trace_exit_code,
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
        "release_run_id": _coerce_int(payload["release_run_id"], field="release_run_id", path=path)
        if payload["release_run_id"] is not None
        else None,
        "release_run_url": _coerce_str(
            payload["release_run_url"], field="release_run_url", path=path
        ),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"], field="follow_up_queue_url", path=path
        ),
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


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
            "error_message": f"workflow run poll timeout after {timeout_seconds}s",
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


def build_linux_validation_terminal_dispatch_completion_payload(
    trace_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    poll_interval_seconds: int,
    max_polls: int,
    poll_timeout_seconds: int,
    dry_run: bool,
    allow_in_progress: bool,
    poll_executor: Callable[..., dict[str, Any]] = execute_run_poll_command,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    trace_status = str(trace_report["linux_validation_terminal_dispatch_trace_status"])
    should_poll_workflow_run = bool(
        trace_report["linux_validation_terminal_should_poll_workflow_run"]
    )

    completion_status = trace_status
    completion_exit_code = int(
        trace_report["linux_validation_terminal_dispatch_trace_exit_code"]
    )
    reason_codes = list(trace_report["reason_codes"])

    poll_iterations = 0
    poll_attempted = False
    poll_returncode = trace_report["linux_validation_terminal_poll_returncode"]
    poll_status = str(trace_report["linux_validation_terminal_poll_status"])
    poll_conclusion = str(trace_report["linux_validation_terminal_poll_conclusion"])
    poll_url = str(trace_report["linux_validation_terminal_poll_url"])
    poll_error_type = str(trace_report["linux_validation_terminal_poll_error_type"])
    poll_error_message = str(trace_report["linux_validation_terminal_poll_error_message"])
    poll_stdout_tail = str(trace_report["linux_validation_terminal_poll_stdout_tail"])
    poll_stderr_tail = str(trace_report["linux_validation_terminal_poll_stderr_tail"])

    should_await = should_poll_workflow_run and trace_status in {
        "run_tracking_ready",
        "run_in_progress",
    }

    if should_await and not dry_run:
        for attempt in range(1, max_polls + 1):
            poll_iterations = attempt
            poll_attempted = True
            poll_result = poll_executor(
                list(trace_report["linux_validation_terminal_poll_command_parts"]),
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
                completion_status = "run_poll_failed"
                completion_exit_code = 1
                if poll_error_type == "command_not_found":
                    reason_codes.append(
                        "linux_validation_terminal_dispatch_run_poll_cli_unavailable"
                    )
                elif poll_error_type == "timeout":
                    reason_codes.append("linux_validation_terminal_dispatch_run_poll_timeout")
                else:
                    reason_codes.append(
                        "linux_validation_terminal_dispatch_run_poll_command_failed"
                    )
                break

            if poll_payload is None:
                completion_status = "run_poll_failed"
                completion_exit_code = 1
                reason_codes.append(
                    "linux_validation_terminal_dispatch_run_poll_payload_invalid"
                )
                break

            poll_status_value = poll_payload.get("status")
            poll_conclusion_value = poll_payload.get("conclusion")
            poll_url_value = poll_payload.get("url")
            if isinstance(poll_status_value, str):
                poll_status = poll_status_value
            else:
                poll_status = ""
            if isinstance(poll_conclusion_value, str):
                poll_conclusion = poll_conclusion_value
            else:
                poll_conclusion = ""
            if isinstance(poll_url_value, str) and poll_url_value:
                poll_url = poll_url_value

            if poll_status == "completed":
                if poll_conclusion == "success":
                    completion_status = "run_completed_success"
                    completion_exit_code = 0
                    reason_codes = [
                        "linux_validation_terminal_dispatch_run_completed_success"
                    ]
                else:
                    completion_status = "run_completed_failure"
                    completion_exit_code = 1
                    reason_codes.append(
                        "linux_validation_terminal_dispatch_run_completed_with_failure"
                    )
                break

            completion_status = "run_in_progress"
            completion_exit_code = 0 if allow_in_progress else 1
            reason_codes.append(
                "linux_validation_terminal_dispatch_run_still_in_progress"
            )
            if attempt < max_polls:
                sleep_fn(float(poll_interval_seconds))
        else:
            completion_status = "run_await_timeout"
            completion_exit_code = 0 if allow_in_progress else 1
            reason_codes.append(
                "linux_validation_terminal_dispatch_run_await_timeout"
            )
    elif should_await and dry_run:
        completion_status = trace_status
        completion_exit_code = int(
            trace_report["linux_validation_terminal_dispatch_trace_exit_code"]
        )
        reason_codes.append(
            "linux_validation_terminal_dispatch_completion_poll_skipped_dry_run"
        )
    else:
        if trace_status == "run_completed_success":
            completion_exit_code = 0
        elif trace_status in {
            "run_tracking_missing",
            "run_completed_failure",
            "run_poll_failed",
        }:
            completion_exit_code = 1
        elif trace_status in {"blocked", "ready_dry_run", "ready_with_follow_up_dry_run"}:
            completion_exit_code = int(
                trace_report["linux_validation_terminal_dispatch_trace_exit_code"]
            )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_linux_validation_terminal_dispatch_trace_report": str(source_path),
        "project_root": str(project_root),
        "source_linux_validation_terminal_dispatch_execution_report": str(
            trace_report["source_linux_validation_terminal_dispatch_execution_report"]
        ),
        "source_linux_validation_terminal_dispatch_report": str(
            trace_report["source_linux_validation_terminal_dispatch_report"]
        ),
        "linux_validation_terminal_dispatch_execution_status": str(
            trace_report["linux_validation_terminal_dispatch_execution_status"]
        ),
        "linux_validation_terminal_dispatch_execution_decision": str(
            trace_report["linux_validation_terminal_dispatch_execution_decision"]
        ),
        "linux_validation_terminal_dispatch_execution_exit_code": int(
            trace_report["linux_validation_terminal_dispatch_execution_exit_code"]
        ),
        "linux_validation_terminal_should_dispatch": bool(
            trace_report["linux_validation_terminal_should_dispatch"]
        ),
        "linux_validation_terminal_dispatch_attempted": bool(
            trace_report["linux_validation_terminal_dispatch_attempted"]
        ),
        "linux_validation_terminal_dispatch_trace_status": trace_status,
        "linux_validation_terminal_dispatch_trace_exit_code": int(
            trace_report["linux_validation_terminal_dispatch_trace_exit_code"]
        ),
        "linux_validation_terminal_dispatch_completion_status": completion_status,
        "linux_validation_terminal_dispatch_completion_exit_code": int(completion_exit_code),
        "dry_run": dry_run,
        "allow_in_progress": allow_in_progress,
        "should_poll_workflow_run": should_poll_workflow_run,
        "linux_validation_terminal_run_id": trace_report["linux_validation_terminal_run_id"],
        "linux_validation_terminal_run_url": str(
            trace_report["linux_validation_terminal_run_url"]
        ),
        "linux_validation_terminal_repo_owner": str(
            trace_report["linux_validation_terminal_repo_owner"]
        ),
        "linux_validation_terminal_repo_name": str(
            trace_report["linux_validation_terminal_repo_name"]
        ),
        "linux_validation_terminal_poll_command": str(
            trace_report["linux_validation_terminal_poll_command"]
        ),
        "linux_validation_terminal_poll_command_parts": list(
            trace_report["linux_validation_terminal_poll_command_parts"]
        ),
        "poll_interval_seconds": poll_interval_seconds,
        "max_polls": max_polls,
        "poll_timeout_seconds": poll_timeout_seconds,
        "poll_iterations": poll_iterations,
        "poll_attempted": poll_attempted,
        "poll_returncode": poll_returncode,
        "poll_status": poll_status,
        "poll_conclusion": poll_conclusion,
        "poll_url": poll_url,
        "poll_error_type": poll_error_type,
        "poll_error_message": poll_error_message,
        "poll_stdout_tail": poll_stdout_tail,
        "poll_stderr_tail": poll_stderr_tail,
        "reason_codes": _unique(reason_codes),
        "structural_issues": list(trace_report["structural_issues"]),
        "missing_artifacts": list(trace_report["missing_artifacts"]),
        "release_run_id": trace_report["release_run_id"],
        "release_run_url": str(trace_report["release_run_url"]),
        "follow_up_queue_url": str(trace_report["follow_up_queue_url"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux Validation Terminal Dispatch Completion Report",
        "",
        (
            "- Completion Status: **"
            f"{str(payload['linux_validation_terminal_dispatch_completion_status']).upper()}**"
        ),
        (
            "- Completion Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_completion_exit_code']}`"
        ),
        f"- Should Poll Workflow Run: `{payload['should_poll_workflow_run']}`",
        f"- Poll Attempted: `{payload['poll_attempted']}`",
        f"- Poll Iterations: `{payload['poll_iterations']}`",
        f"- Run ID: `{payload['linux_validation_terminal_run_id']}`",
        f"- Run URL: `{payload['linux_validation_terminal_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Dispatch Trace Report: `{payload['source_linux_validation_terminal_dispatch_trace_report']}`",
        f"- Source Dispatch Execution Report: `{payload['source_linux_validation_terminal_dispatch_execution_report']}`",
        f"- Source Dispatch Report: `{payload['source_linux_validation_terminal_dispatch_report']}`",
        "",
        "## Poll Result",
        "",
        f"- Poll Return Code: `{payload['poll_returncode']}`",
        f"- Poll Status: `{payload['poll_status']}`",
        f"- Poll Conclusion: `{payload['poll_conclusion']}`",
        f"- Poll URL: `{payload['poll_url']}`",
        f"- Poll Error Type: `{payload['poll_error_type']}`",
    ]

    if payload["poll_stdout_tail"]:
        lines.append("- Poll stdout:")
        lines.append("```text")
        lines.append(str(payload["poll_stdout_tail"]))
        lines.append("```")
    if payload["poll_stderr_tail"]:
        lines.append("- Poll stderr:")
        lines.append("```text")
        lines.append(str(payload["poll_stderr_tail"]))
        lines.append("```")

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

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    run_id = payload["linux_validation_terminal_run_id"]
    return {
        "workflow_linux_validation_terminal_dispatch_completion_status": str(
            payload["linux_validation_terminal_dispatch_completion_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_completion_exit_code": str(
            payload["linux_validation_terminal_dispatch_completion_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_completion_should_poll": (
            "true" if payload["should_poll_workflow_run"] else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_completion_poll_attempted": (
            "true" if payload["poll_attempted"] else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_completion_poll_iterations": str(
            payload["poll_iterations"]
        ),
        "workflow_linux_validation_terminal_dispatch_completion_poll_status": str(
            payload["poll_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_completion_poll_conclusion": str(
            payload["poll_conclusion"]
        ),
        "workflow_linux_validation_terminal_dispatch_completion_run_id": (
            "" if run_id is None else str(run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_completion_run_url": str(
            payload["linux_validation_terminal_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_completion_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_completion_report_json": str(output_json),
        "workflow_linux_validation_terminal_dispatch_completion_report_markdown": str(
            output_markdown
        ),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Await Linux validation terminal dispatch completion from P2-71 trace report"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-trace-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json",
        help="P2-71 Linux validation terminal dispatch trace report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used for optional poll command execution",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=30,
        help="Sleep interval between polls when awaiting completion",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=20,
        help="Maximum poll attempts when awaiting completion",
    )
    parser.add_argument(
        "--poll-timeout-seconds",
        type=int,
        default=600,
        help="Timeout seconds for each poll command execution",
    )
    parser.add_argument(
        "--allow-in-progress",
        action="store_true",
        help="Return exit 0 when run remains in progress after max polls",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.json",
        help="Output completion JSON report path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.md",
        help="Output completion markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print completion JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    if args.poll_interval_seconds < 1:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-completion-gate] --poll-interval-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.max_polls < 1:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-completion-gate] --max-polls must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-completion-gate] --poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    trace_report_path = Path(args.linux_validation_terminal_dispatch_trace_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)
    project_root = Path(args.project_root).resolve()

    try:
        trace_report = load_linux_validation_terminal_dispatch_trace_report(trace_report_path)
        payload = build_linux_validation_terminal_dispatch_completion_payload(
            trace_report,
            source_path=trace_report_path.resolve(),
            project_root=project_root,
            poll_interval_seconds=args.poll_interval_seconds,
            max_polls=args.max_polls,
            poll_timeout_seconds=args.poll_timeout_seconds,
            dry_run=args.dry_run,
            allow_in_progress=args.allow_in_progress,
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-completion-gate] "
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
        print(f"linux validation terminal dispatch completion json: {output_json_path}")
        print(f"linux validation terminal dispatch completion markdown: {output_markdown_path}")

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
        "linux validation terminal dispatch completion summary: "
        f"linux_validation_terminal_dispatch_completion_status="
        f"{payload['linux_validation_terminal_dispatch_completion_status']} "
        f"should_poll={payload['should_poll_workflow_run']} "
        f"linux_validation_terminal_dispatch_completion_exit_code="
        f"{payload['linux_validation_terminal_dispatch_completion_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_completion_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
