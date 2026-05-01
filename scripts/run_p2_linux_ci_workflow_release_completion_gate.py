"""Phase 2 card P2-33 gate for Linux CI workflow release completion await.

This script consumes the P2-32 release trace artifact and converges to a
release completion verdict:
1) validate release trace contract and poll command,
2) optionally poll release run status until terminal/timeout,
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


ALLOWED_RELEASE_TRACKING_STATUSES: set[str] = {
    "blocked",
    "awaiting_completion",
    "handoff_failed",
    "release_trigger_failed",
    "release_ready_dry_run",
    "release_run_tracking_missing",
    "release_run_tracking_ready",
    "release_run_in_progress",
    "release_run_completed_success",
    "release_run_completed_failure",
    "release_run_poll_failed",
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


def load_release_trace_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release trace report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release trace payload must be object")

    required_fields = (
        "release_trigger_status",
        "release_tracking_status",
        "release_trace_exit_code",
        "should_poll_release_run",
        "release_run_id",
        "release_run_url",
        "repo_owner",
        "repo_name",
        "release_workflow_path",
        "release_workflow_ref",
        "release_poll_command",
        "release_poll_command_parts",
        "release_poll_attempted",
        "release_poll_returncode",
        "release_poll_status",
        "release_poll_conclusion",
        "release_poll_url",
        "release_poll_error_type",
        "release_poll_error_message",
        "release_poll_stdout_tail",
        "release_poll_stderr_tail",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
        "source_release_trigger_report",
        "source_release_handoff_report",
        "source_terminal_publish_report",
        "source_dispatch_completion_report",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    release_trigger_status = _coerce_str(
        payload["release_trigger_status"],
        field="release_trigger_status",
        path=path,
    )
    release_tracking_status = _coerce_str(
        payload["release_tracking_status"],
        field="release_tracking_status",
        path=path,
    )
    if release_tracking_status not in ALLOWED_RELEASE_TRACKING_STATUSES:
        raise ValueError(
            f"{path}: field 'release_tracking_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_TRACKING_STATUSES)}"
        )

    release_trace_exit_code = _coerce_int(
        payload["release_trace_exit_code"],
        field="release_trace_exit_code",
        path=path,
    )
    if release_trace_exit_code < 0:
        raise ValueError(f"{path}: field 'release_trace_exit_code' must be >= 0")

    should_poll_release_run = _coerce_bool(
        payload["should_poll_release_run"],
        field="should_poll_release_run",
        path=path,
    )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(
            release_run_id_raw,
            field="release_run_id",
            path=path,
        )
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    release_run_url = _coerce_str(payload["release_run_url"], field="release_run_url", path=path)
    repo_owner = _coerce_str(payload["repo_owner"], field="repo_owner", path=path)
    repo_name = _coerce_str(payload["repo_name"], field="repo_name", path=path)
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
    release_poll_command = _coerce_str(
        payload["release_poll_command"],
        field="release_poll_command",
        path=path,
    )
    release_poll_command_parts = _coerce_str_list(
        payload["release_poll_command_parts"],
        field="release_poll_command_parts",
        path=path,
    )
    release_poll_attempted = _coerce_bool(
        payload["release_poll_attempted"],
        field="release_poll_attempted",
        path=path,
    )
    release_poll_returncode_raw = payload["release_poll_returncode"]
    if release_poll_returncode_raw is None:
        release_poll_returncode = None
    else:
        release_poll_returncode = _coerce_int(
            release_poll_returncode_raw,
            field="release_poll_returncode",
            path=path,
        )
    release_poll_status = _coerce_str(
        payload["release_poll_status"],
        field="release_poll_status",
        path=path,
    )
    release_poll_conclusion = _coerce_str(
        payload["release_poll_conclusion"],
        field="release_poll_conclusion",
        path=path,
    )
    release_poll_url = _coerce_str(
        payload["release_poll_url"],
        field="release_poll_url",
        path=path,
    )
    release_poll_error_type = _coerce_str(
        payload["release_poll_error_type"],
        field="release_poll_error_type",
        path=path,
    )
    release_poll_error_message = _coerce_str(
        payload["release_poll_error_message"],
        field="release_poll_error_message",
        path=path,
    )
    release_poll_stdout_tail = _coerce_str(
        payload["release_poll_stdout_tail"],
        field="release_poll_stdout_tail",
        path=path,
    )
    release_poll_stderr_tail = _coerce_str(
        payload["release_poll_stderr_tail"],
        field="release_poll_stderr_tail",
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
    source_release_trigger_report = _coerce_str(
        payload["source_release_trigger_report"],
        field="source_release_trigger_report",
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

    if should_poll_release_run:
        if release_run_id is None:
            raise ValueError(f"{path}: should_poll_release_run=true requires release_run_id")
        if not release_poll_command_parts:
            raise ValueError(
                f"{path}: should_poll_release_run=true requires release_poll_command_parts"
            )
        if len(release_poll_command_parts) < 3 or release_poll_command_parts[1:3] != [
            "run",
            "view",
        ]:
            raise ValueError(
                f"{path}: release_poll_command_parts must include '<gh> run view ...' contract"
            )
        parsed_command = shlex.split(release_poll_command)
        if parsed_command != release_poll_command_parts:
            raise ValueError(f"{path}: release_poll_command and release_poll_command_parts mismatch")
    else:
        if release_run_id is not None:
            raise ValueError(f"{path}: should_poll_release_run=false requires release_run_id=null")

    return {
        "generated_at": payload.get("generated_at"),
        "release_trigger_status": release_trigger_status,
        "release_tracking_status": release_tracking_status,
        "release_trace_exit_code": release_trace_exit_code,
        "should_poll_release_run": should_poll_release_run,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "release_workflow_path": release_workflow_path,
        "release_workflow_ref": release_workflow_ref,
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
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "source_release_trigger_report": source_release_trigger_report,
        "source_release_handoff_report": source_release_handoff_report,
        "source_terminal_publish_report": source_terminal_publish_report,
        "source_dispatch_completion_report": source_dispatch_completion_report,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
    }


def execute_release_poll_command(
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


def build_release_completion_payload(
    release_trace_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    poll_interval_seconds: int,
    max_polls: int,
    poll_timeout_seconds: int,
    dry_run: bool,
    allow_in_progress: bool,
    poll_executor: Callable[..., dict[str, Any]] = execute_release_poll_command,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    release_tracking_status = str(release_trace_report["release_tracking_status"])
    should_poll_release_run = bool(release_trace_report["should_poll_release_run"])

    release_completion_status = release_tracking_status
    release_completion_exit_code = int(release_trace_report["release_trace_exit_code"])
    reason_codes = list(release_trace_report["reason_codes"])

    poll_iterations = 0
    poll_attempted = False
    poll_returncode = release_trace_report["release_poll_returncode"]
    poll_status = str(release_trace_report["release_poll_status"])
    poll_conclusion = str(release_trace_report["release_poll_conclusion"])
    poll_url = str(release_trace_report["release_poll_url"])
    poll_error_type = str(release_trace_report["release_poll_error_type"])
    poll_error_message = str(release_trace_report["release_poll_error_message"])
    poll_stdout_tail = str(release_trace_report["release_poll_stdout_tail"])
    poll_stderr_tail = str(release_trace_report["release_poll_stderr_tail"])

    should_await = should_poll_release_run and release_tracking_status in {
        "release_run_tracking_ready",
        "release_run_in_progress",
    }

    if should_await and not dry_run:
        for attempt in range(1, max_polls + 1):
            poll_iterations = attempt
            poll_attempted = True
            poll_result = poll_executor(
                list(release_trace_report["release_poll_command_parts"]),
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
                release_completion_status = "release_run_poll_failed"
                release_completion_exit_code = 1
                if poll_error_type == "command_not_found":
                    reason_codes.append("release_run_poll_cli_unavailable")
                elif poll_error_type == "timeout":
                    reason_codes.append("release_run_poll_timeout")
                else:
                    reason_codes.append("release_run_poll_command_failed")
                break

            if poll_payload is None:
                release_completion_status = "release_run_poll_failed"
                release_completion_exit_code = 1
                reason_codes.append("release_run_poll_payload_invalid")
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
                    release_completion_status = "release_run_completed_success"
                    release_completion_exit_code = 0
                    reason_codes = ["release_run_completed_success"]
                else:
                    release_completion_status = "release_run_completed_failure"
                    release_completion_exit_code = 1
                    reason_codes.append("release_run_completed_with_failure")
                break

            release_completion_status = "release_run_in_progress"
            release_completion_exit_code = 0 if allow_in_progress else 1
            reason_codes.append("release_run_still_in_progress")
            if attempt < max_polls:
                sleep_fn(float(poll_interval_seconds))
        else:
            release_completion_status = "release_run_await_timeout"
            release_completion_exit_code = 0 if allow_in_progress else 1
            reason_codes.append("release_run_await_timeout")

    elif should_await and dry_run:
        release_completion_status = release_tracking_status
        release_completion_exit_code = int(release_trace_report["release_trace_exit_code"])
        reason_codes.append("release_completion_poll_skipped_dry_run")
    else:
        if release_tracking_status == "release_run_completed_success":
            release_completion_exit_code = 0
        elif release_tracking_status in {
            "release_run_tracking_missing",
            "release_run_completed_failure",
            "release_run_poll_failed",
            "release_trigger_failed",
            "handoff_failed",
        }:
            release_completion_exit_code = 1
        elif release_tracking_status in {"blocked", "release_ready_dry_run", "awaiting_completion"}:
            release_completion_exit_code = int(release_trace_report["release_trace_exit_code"])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_trace_report": str(source_path),
        "project_root": str(project_root),
        "release_trigger_status": str(release_trace_report["release_trigger_status"]),
        "release_tracking_status": release_tracking_status,
        "release_completion_status": release_completion_status,
        "release_completion_exit_code": int(release_completion_exit_code),
        "dry_run": dry_run,
        "allow_in_progress": allow_in_progress,
        "should_poll_release_run": should_poll_release_run,
        "release_run_id": release_trace_report["release_run_id"],
        "release_run_url": str(release_trace_report["release_run_url"]),
        "repo_owner": str(release_trace_report["repo_owner"]),
        "repo_name": str(release_trace_report["repo_name"]),
        "release_workflow_path": str(release_trace_report["release_workflow_path"]),
        "release_workflow_ref": str(release_trace_report["release_workflow_ref"]),
        "release_poll_command": str(release_trace_report["release_poll_command"]),
        "release_poll_command_parts": list(release_trace_report["release_poll_command_parts"]),
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
        "release_trace_reason_codes": list(release_trace_report["reason_codes"]),
        "reason_codes": _unique(reason_codes),
        "failed_checks": list(release_trace_report["failed_checks"]),
        "structural_issues": list(release_trace_report["structural_issues"]),
        "missing_artifacts": list(release_trace_report["missing_artifacts"]),
        "source_release_trigger_report": str(release_trace_report["source_release_trigger_report"]),
        "source_release_handoff_report": str(release_trace_report["source_release_handoff_report"]),
        "source_terminal_publish_report": str(release_trace_report["source_terminal_publish_report"]),
        "source_dispatch_completion_report": str(
            release_trace_report["source_dispatch_completion_report"]
        ),
        "source_dispatch_trace_report": str(release_trace_report["source_dispatch_trace_report"]),
        "source_dispatch_execution_report": str(
            release_trace_report["source_dispatch_execution_report"]
        ),
        "source_dispatch_report": str(release_trace_report["source_dispatch_report"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Completion Report",
        "",
        f"- Release Completion Status: **{str(payload['release_completion_status']).upper()}**",
        f"- Release Completion Exit Code: `{payload['release_completion_exit_code']}`",
        f"- Should Poll Release Run: `{payload['should_poll_release_run']}`",
        f"- Poll Attempted: `{payload['poll_attempted']}`",
        f"- Poll Iterations: `{payload['poll_iterations']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Release Trace Report: `{payload['source_release_trace_report']}`",
        f"- Release Workflow Path: `{payload['release_workflow_path']}`",
        f"- Release Workflow Ref: `{payload['release_workflow_ref']}`",
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
    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    return {
        "workflow_release_completion_status": str(payload["release_completion_status"]),
        "workflow_release_completion_exit_code": str(payload["release_completion_exit_code"]),
        "workflow_release_completion_should_poll": (
            "true" if payload["should_poll_release_run"] else "false"
        ),
        "workflow_release_completion_poll_attempted": (
            "true" if payload["poll_attempted"] else "false"
        ),
        "workflow_release_completion_poll_iterations": str(payload["poll_iterations"]),
        "workflow_release_completion_poll_status": str(payload["poll_status"]),
        "workflow_release_completion_poll_conclusion": str(payload["poll_conclusion"]),
        "workflow_release_completion_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_completion_run_url": str(payload["release_run_url"]),
        "workflow_release_completion_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_completion_report_json": str(output_json),
        "workflow_release_completion_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Await Linux CI workflow release completion from P2-32 release trace report"
    )
    parser.add_argument(
        "--release-trace-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trace.json",
        help="P2-32 release trace report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used for optional release poll command execution",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=30,
        help="Sleep interval between polls when awaiting release completion",
    )
    parser.add_argument(
        "--max-polls",
        type=int,
        default=20,
        help="Maximum poll attempts when awaiting release completion",
    )
    parser.add_argument(
        "--poll-timeout-seconds",
        type=int,
        default=600,
        help="Timeout seconds for each release poll command execution",
    )
    parser.add_argument(
        "--allow-in-progress",
        action="store_true",
        help="Return exit 0 when release run remains in progress after max polls",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_completion.json",
        help="Output release completion JSON report path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_completion.md",
        help="Output release completion markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release completion JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    if args.poll_interval_seconds < 1:
        print(
            "[p2-linux-ci-workflow-release-completion-gate] "
            "--poll-interval-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.max_polls < 1:
        print(
            "[p2-linux-ci-workflow-release-completion-gate] --max-polls must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-release-completion-gate] "
            "--poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    release_trace_report_path = Path(args.release_trace_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)
    project_root = Path(args.project_root).resolve()

    try:
        release_trace_report = load_release_trace_report(release_trace_report_path)
        payload = build_release_completion_payload(
            release_trace_report,
            source_path=release_trace_report_path.resolve(),
            project_root=project_root,
            poll_interval_seconds=args.poll_interval_seconds,
            max_polls=args.max_polls,
            poll_timeout_seconds=args.poll_timeout_seconds,
            dry_run=args.dry_run,
            allow_in_progress=args.allow_in_progress,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-completion-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release completion json: {output_json_path}")
        print(f"release completion markdown: {output_markdown_path}")

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
        "release completion summary: "
        f"release_completion_status={payload['release_completion_status']} "
        f"poll_attempted={payload['poll_attempted']} "
        f"release_completion_exit_code={payload['release_completion_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_completion_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

