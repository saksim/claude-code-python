"""Phase 2 card P2-31 gate for Linux CI workflow release trigger.

This script consumes the P2-30 release handoff artifact and converges the
final release trigger behavior:
1) validate handoff contract and trigger readiness,
2) build/execute release dispatch command when ready,
3) emit JSON/Markdown reports + optional GitHub outputs.
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


ALLOWED_HANDOFF_STATUSES: set[str] = {
    "ready_for_release",
    "awaiting_completion",
    "blocked",
    "failed",
    "contract_failed",
}
ALLOWED_HANDOFF_ACTIONS: set[str] = {"promote", "hold", "reject"}


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


def load_release_handoff_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release handoff report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release handoff payload must be object")

    required_fields = (
        "handoff_status",
        "handoff_action",
        "should_trigger_release",
        "release_exit_code",
        "target_environment",
        "release_channel",
        "publish_status",
        "completion_status",
        "run_id",
        "run_url",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
        "source_terminal_publish_report",
        "source_dispatch_completion_report",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    handoff_status = _coerce_str(payload["handoff_status"], field="handoff_status", path=path)
    if handoff_status not in ALLOWED_HANDOFF_STATUSES:
        raise ValueError(
            f"{path}: field 'handoff_status' must be one of {sorted(ALLOWED_HANDOFF_STATUSES)}"
        )

    handoff_action = _coerce_str(payload["handoff_action"], field="handoff_action", path=path)
    if handoff_action not in ALLOWED_HANDOFF_ACTIONS:
        raise ValueError(
            f"{path}: field 'handoff_action' must be one of {sorted(ALLOWED_HANDOFF_ACTIONS)}"
        )

    should_trigger_release = _coerce_bool(
        payload["should_trigger_release"],
        field="should_trigger_release",
        path=path,
    )
    release_exit_code = _coerce_int(payload["release_exit_code"], field="release_exit_code", path=path)
    if release_exit_code < 0:
        raise ValueError(f"{path}: field 'release_exit_code' must be >= 0")

    target_environment = _coerce_str(
        payload["target_environment"],
        field="target_environment",
        path=path,
    )
    release_channel = _coerce_str(payload["release_channel"], field="release_channel", path=path)
    publish_status = _coerce_str(payload["publish_status"], field="publish_status", path=path)
    completion_status = _coerce_str(payload["completion_status"], field="completion_status", path=path)
    run_url = _coerce_str(payload["run_url"], field="run_url", path=path)

    run_id_raw = payload["run_id"]
    if run_id_raw is None:
        run_id = None
    else:
        run_id = _coerce_int(run_id_raw, field="run_id", path=path)
        if run_id < 1:
            raise ValueError(f"{path}: field 'run_id' must be >= 1 when present")

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

    if handoff_status == "ready_for_release":
        if not should_trigger_release:
            raise ValueError(
                f"{path}: ready_for_release requires should_trigger_release=true"
            )
        if handoff_action != "promote":
            raise ValueError(f"{path}: ready_for_release requires handoff_action='promote'")
        if release_exit_code != 0:
            raise ValueError(f"{path}: ready_for_release requires release_exit_code=0")
    elif handoff_status in {"awaiting_completion", "blocked"}:
        if should_trigger_release:
            raise ValueError(
                f"{path}: {handoff_status} requires should_trigger_release=false"
            )
        if handoff_action != "hold":
            raise ValueError(f"{path}: {handoff_status} requires handoff_action='hold'")
        if release_exit_code != 0:
            raise ValueError(f"{path}: {handoff_status} requires release_exit_code=0")
    elif handoff_status == "failed":
        if should_trigger_release:
            raise ValueError(f"{path}: failed requires should_trigger_release=false")
        if handoff_action != "reject":
            raise ValueError(f"{path}: failed requires handoff_action='reject'")
        if release_exit_code == 0:
            raise ValueError(f"{path}: failed requires release_exit_code>0")
    else:
        if should_trigger_release:
            raise ValueError(f"{path}: contract_failed requires should_trigger_release=false")
        if handoff_action != "hold":
            raise ValueError(f"{path}: contract_failed requires handoff_action='hold'")
        if release_exit_code == 0:
            raise ValueError(f"{path}: contract_failed requires release_exit_code>0")

    return {
        "generated_at": payload.get("generated_at"),
        "handoff_status": handoff_status,
        "handoff_action": handoff_action,
        "should_trigger_release": should_trigger_release,
        "release_exit_code": release_exit_code,
        "target_environment": target_environment,
        "release_channel": release_channel,
        "publish_status": publish_status,
        "completion_status": completion_status,
        "run_id": run_id,
        "run_url": run_url,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "source_terminal_publish_report": source_terminal_publish_report,
        "source_dispatch_completion_report": source_dispatch_completion_report,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
    }


def build_release_command_parts(
    handoff_report: dict[str, Any],
    *,
    source_report_path: Path,
    gh_executable: str,
    release_workflow_path: str,
    release_workflow_ref: str,
    release_command: str,
) -> list[str]:
    if release_command.strip():
        try:
            custom_parts = shlex.split(release_command)
        except ValueError as exc:
            raise ValueError(f"invalid --release-command ({exc})") from exc
        if not custom_parts:
            raise ValueError("invalid --release-command (empty command)")
        return custom_parts

    return [
        gh_executable,
        "workflow",
        "run",
        release_workflow_path,
        "--ref",
        release_workflow_ref,
        "--raw-field",
        f"source_release_handoff_report={source_report_path}",
        "--raw-field",
        f"target_environment={handoff_report['target_environment']}",
        "--raw-field",
        f"release_channel={handoff_report['release_channel']}",
    ]


def execute_release_trigger_command(
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
            "error_message": f"release trigger command timeout after {timeout_seconds}s",
        }

    return {
        "attempted": True,
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(completed.stdout or ""),
        "stderr_tail": _tail_text(completed.stderr or ""),
        "error_type": "",
        "error_message": "",
    }


def build_release_trigger_payload(
    handoff_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    release_command_parts: list[str],
    release_workflow_path: str,
    release_workflow_ref: str,
    dry_run: bool,
    command_result: dict[str, Any] | None,
) -> dict[str, Any]:
    should_trigger_release = bool(handoff_report["should_trigger_release"])
    handoff_status = str(handoff_report["handoff_status"])
    release_exit_code = int(handoff_report["release_exit_code"])

    release_command = (
        _format_shell_command(release_command_parts) if release_command_parts else ""
    )
    reason_codes = list(handoff_report["reason_codes"])
    release_trigger_attempted = False
    command_returncode: int | None = None
    command_stdout_tail = ""
    command_stderr_tail = ""
    trigger_error_type = ""
    trigger_error_message = ""

    if should_trigger_release:
        if dry_run:
            release_trigger_status = "ready_dry_run"
            release_trigger_exit_code = 0
        else:
            release_trigger_attempted = True
            if command_result is None:
                release_trigger_status = "trigger_failed"
                release_trigger_exit_code = 1
                reason_codes.append("release_trigger_result_missing")
            else:
                command_returncode = int(command_result["returncode"])
                command_stdout_tail = str(command_result.get("stdout_tail", ""))
                command_stderr_tail = str(command_result.get("stderr_tail", ""))
                trigger_error_type = str(command_result.get("error_type", ""))
                trigger_error_message = str(command_result.get("error_message", ""))
                if command_returncode == 0:
                    release_trigger_status = "triggered"
                    release_trigger_exit_code = 0
                    reason_codes = ["release_trigger_command_succeeded"]
                else:
                    release_trigger_status = "trigger_failed"
                    release_trigger_exit_code = 1
                    if trigger_error_type == "command_not_found":
                        reason_codes.append("release_trigger_cli_unavailable")
                    elif trigger_error_type == "timeout":
                        reason_codes.append("release_trigger_timeout")
                    else:
                        reason_codes.append("release_trigger_command_failed")
    else:
        if handoff_status == "awaiting_completion":
            release_trigger_status = "awaiting_completion"
            release_trigger_exit_code = 0
        elif handoff_status == "blocked":
            release_trigger_status = "blocked"
            release_trigger_exit_code = 0
        else:
            release_trigger_status = "handoff_failed"
            release_trigger_exit_code = max(1, release_exit_code)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_handoff_report": str(source_path),
        "project_root": str(project_root),
        "source_terminal_publish_report": str(handoff_report["source_terminal_publish_report"]),
        "source_dispatch_completion_report": str(handoff_report["source_dispatch_completion_report"]),
        "source_dispatch_trace_report": str(handoff_report["source_dispatch_trace_report"]),
        "source_dispatch_execution_report": str(handoff_report["source_dispatch_execution_report"]),
        "source_dispatch_report": str(handoff_report["source_dispatch_report"]),
        "handoff_status": handoff_status,
        "handoff_action": str(handoff_report["handoff_action"]),
        "should_trigger_release": should_trigger_release,
        "release_exit_code": release_exit_code,
        "release_trigger_status": release_trigger_status,
        "release_trigger_exit_code": int(release_trigger_exit_code),
        "release_trigger_attempted": release_trigger_attempted,
        "release_command": release_command,
        "release_command_parts": list(release_command_parts),
        "release_workflow_path": release_workflow_path,
        "release_workflow_ref": release_workflow_ref,
        "target_environment": str(handoff_report["target_environment"]),
        "release_channel": str(handoff_report["release_channel"]),
        "publish_status": str(handoff_report["publish_status"]),
        "completion_status": str(handoff_report["completion_status"]),
        "run_id": handoff_report["run_id"],
        "run_url": str(handoff_report["run_url"]),
        "dry_run": dry_run,
        "command_returncode": command_returncode,
        "command_stdout_tail": command_stdout_tail,
        "command_stderr_tail": command_stderr_tail,
        "trigger_error_type": trigger_error_type,
        "trigger_error_message": trigger_error_message,
        "reason_codes": _unique(reason_codes),
        "failed_checks": list(handoff_report["failed_checks"]),
        "structural_issues": list(handoff_report["structural_issues"]),
        "missing_artifacts": list(handoff_report["missing_artifacts"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Trigger Report",
        "",
        f"- Trigger Status: **{str(payload['release_trigger_status']).upper()}**",
        f"- Should Trigger Release: `{payload['should_trigger_release']}`",
        f"- Trigger Attempted: `{payload['release_trigger_attempted']}`",
        f"- Trigger Exit Code: `{payload['release_trigger_exit_code']}`",
        f"- Target Environment: `{payload['target_environment']}`",
        f"- Release Channel: `{payload['release_channel']}`",
        f"- Handoff Status: `{payload['handoff_status']}`",
        f"- Run ID: `{payload['run_id']}`",
        f"- Run URL: `{payload['run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Release Handoff Report: `{payload['source_release_handoff_report']}`",
        f"- Source Terminal Publish Report: `{payload['source_terminal_publish_report']}`",
        f"- Source Dispatch Completion Report: `{payload['source_dispatch_completion_report']}`",
        f"- Source Dispatch Trace Report: `{payload['source_dispatch_trace_report']}`",
        f"- Source Dispatch Execution Report: `{payload['source_dispatch_execution_report']}`",
        f"- Source Dispatch Report: `{payload['source_dispatch_report']}`",
        "",
        "## Release Command",
    ]

    if payload["release_command"]:
        lines.append(f"- `{payload['release_command']}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Reason Codes"])
    reason_codes = payload["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{item}`" for item in reason_codes)
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
    payload: dict[str, Any],
    *,
    output_json: Path,
    output_markdown: Path,
) -> dict[str, str]:
    command_returncode = payload["command_returncode"]
    run_id = payload["run_id"]
    return {
        "workflow_release_trigger_status": str(payload["release_trigger_status"]),
        "workflow_release_trigger_should_trigger_release": "true"
        if payload["should_trigger_release"]
        else "false",
        "workflow_release_trigger_attempted": "true"
        if payload["release_trigger_attempted"]
        else "false",
        "workflow_release_trigger_exit_code": str(payload["release_trigger_exit_code"]),
        "workflow_release_trigger_command_returncode": (
            "" if command_returncode is None else str(command_returncode)
        ),
        "workflow_release_trigger_target_environment": str(payload["target_environment"]),
        "workflow_release_trigger_release_channel": str(payload["release_channel"]),
        "workflow_release_trigger_handoff_status": str(payload["handoff_status"]),
        "workflow_release_trigger_run_id": "" if run_id is None else str(run_id),
        "workflow_release_trigger_run_url": str(payload["run_url"]),
        "workflow_release_trigger_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_trigger_report_json": str(output_json),
        "workflow_release_trigger_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Linux CI workflow release trigger gate from P2-30 handoff artifact"
    )
    parser.add_argument(
        "--release-handoff-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_handoff.json",
        help="P2-30 release handoff report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for release trigger command execution",
    )
    parser.add_argument(
        "--release-workflow-path",
        default=".github/workflows/release.yml",
        help="Release workflow path used when auto-building release command",
    )
    parser.add_argument(
        "--release-workflow-ref",
        default="main",
        help="Release workflow ref used when auto-building release command",
    )
    parser.add_argument(
        "--gh-executable",
        default="gh",
        help="GitHub CLI executable used when auto-building release command",
    )
    parser.add_argument(
        "--release-command",
        default="",
        help="Optional explicit release trigger command string (overrides auto command)",
    )
    parser.add_argument(
        "--release-timeout-seconds",
        type=int,
        default=900,
        help="Release trigger command timeout in seconds",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trigger.json",
        help="Output release trigger JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trigger.md",
        help="Output release trigger markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release trigger JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate contract and skip release trigger execution",
    )
    args = parser.parse_args()

    if args.release_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-release-trigger-gate] --release-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    release_handoff_report_path = Path(args.release_handoff_report)
    project_root = Path(args.project_root)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        handoff_report = load_release_handoff_report(release_handoff_report_path)
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-trigger-gate] {exc}", file=sys.stderr)
        return 2

    release_command_parts: list[str] = []
    if handoff_report["should_trigger_release"]:
        try:
            release_command_parts = build_release_command_parts(
                handoff_report,
                source_report_path=release_handoff_report_path.resolve(),
                gh_executable=args.gh_executable,
                release_workflow_path=args.release_workflow_path,
                release_workflow_ref=args.release_workflow_ref,
                release_command=args.release_command,
            )
        except ValueError as exc:
            print(f"[p2-linux-ci-workflow-release-trigger-gate] {exc}", file=sys.stderr)
            return 2

    command_result: dict[str, Any] | None = None
    if handoff_report["should_trigger_release"] and not args.dry_run:
        command_result = execute_release_trigger_command(
            release_command_parts,
            cwd=project_root,
            timeout_seconds=args.release_timeout_seconds,
        )

    payload = build_release_trigger_payload(
        handoff_report,
        source_path=release_handoff_report_path.resolve(),
        project_root=project_root.resolve(),
        release_command_parts=release_command_parts,
        release_workflow_path=args.release_workflow_path,
        release_workflow_ref=args.release_workflow_ref,
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
        print(f"release trigger json: {output_json_path}")
        print(f"release trigger markdown: {output_markdown_path}")

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
        "release trigger summary: "
        f"release_trigger_status={payload['release_trigger_status']} "
        f"release_trigger_attempted={payload['release_trigger_attempted']} "
        f"release_trigger_exit_code={payload['release_trigger_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_trigger_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
