"""Phase 2 card P2-25 gate for Linux CI workflow dispatch execution.

This script executes (or dry-runs) the P2-24 dispatch contract:
1) validates dispatch-ready vs blocked payload contract,
2) executes canonical dispatch command when ready,
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
    if not isinstance(value, list):
        raise ValueError(f"{path}: field '{field}' must be string list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: field '{field}' must be string list")
    return list(value)


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _tail_text(text: str, *, max_lines: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def load_dispatch_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: dispatch report file not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: dispatch report payload must be object")

    required_fields = (
        "decision",
        "decision_status",
        "dispatch_status",
        "dispatch_mode",
        "should_dispatch_workflow",
        "exit_code",
        "on_block_policy",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
        "dispatch_command",
        "dispatch_command_parts",
        "workflow_path",
        "workflow_ref",
        "workflow_plan_path",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    decision = payload["decision"]
    if decision not in {"execute", "blocked"}:
        raise ValueError(f"{path}: field 'decision' must be 'execute' or 'blocked'")

    decision_status = payload["decision_status"]
    if decision_status not in {"approved", "blocked"}:
        raise ValueError(f"{path}: field 'decision_status' must be 'approved' or 'blocked'")

    dispatch_status = payload["dispatch_status"]
    if dispatch_status not in {"ready", "blocked"}:
        raise ValueError(f"{path}: field 'dispatch_status' must be 'ready' or 'blocked'")

    dispatch_mode = payload["dispatch_mode"]
    if dispatch_mode not in {"workflow_dispatch", "none"}:
        raise ValueError(f"{path}: field 'dispatch_mode' must be 'workflow_dispatch' or 'none'")

    should_dispatch_workflow = _coerce_bool(
        payload["should_dispatch_workflow"],
        field="should_dispatch_workflow",
        path=path,
    )
    exit_code = _coerce_int(payload["exit_code"], field="exit_code", path=path)
    if exit_code not in {0, 1}:
        raise ValueError(f"{path}: field 'exit_code' must be 0 or 1")

    on_block_policy = payload["on_block_policy"]
    if on_block_policy not in {"fail", "skip"}:
        raise ValueError(f"{path}: field 'on_block_policy' must be 'fail' or 'skip'")

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
    dispatch_command = _coerce_str(payload["dispatch_command"], field="dispatch_command", path=path)
    dispatch_command_parts = _coerce_str_list(
        payload["dispatch_command_parts"],
        field="dispatch_command_parts",
        path=path,
    )
    workflow_path = _coerce_str(payload["workflow_path"], field="workflow_path", path=path)
    workflow_ref = _coerce_str(payload["workflow_ref"], field="workflow_ref", path=path)
    workflow_plan_path = _coerce_str(
        payload["workflow_plan_path"],
        field="workflow_plan_path",
        path=path,
    )

    if dispatch_status == "ready":
        if decision != "execute" or decision_status != "approved":
            raise ValueError(f"{path}: ready dispatch requires execute/approved decision")
        if dispatch_mode != "workflow_dispatch":
            raise ValueError(f"{path}: ready dispatch requires dispatch_mode='workflow_dispatch'")
        if not should_dispatch_workflow:
            raise ValueError(f"{path}: ready dispatch requires should_dispatch_workflow=true")
        if not dispatch_command.strip():
            raise ValueError(f"{path}: ready dispatch requires non-empty dispatch_command")
        if not dispatch_command_parts:
            raise ValueError(f"{path}: ready dispatch requires non-empty dispatch_command_parts")
        if len(dispatch_command_parts) < 3:
            raise ValueError(f"{path}: ready dispatch command_parts must include gh workflow run")
        if dispatch_command_parts[1:3] != ["workflow", "run"]:
            raise ValueError(f"{path}: ready dispatch command_parts must contain 'workflow run'")
        parsed_command = shlex.split(dispatch_command)
        if parsed_command != dispatch_command_parts:
            raise ValueError(f"{path}: dispatch_command and dispatch_command_parts mismatch")
    else:
        if decision != "blocked" or decision_status != "blocked":
            raise ValueError(f"{path}: blocked dispatch requires blocked/blocked decision")
        if dispatch_mode != "none":
            raise ValueError(f"{path}: blocked dispatch requires dispatch_mode='none'")
        if should_dispatch_workflow:
            raise ValueError(f"{path}: blocked dispatch requires should_dispatch_workflow=false")
        if dispatch_command.strip():
            raise ValueError(f"{path}: blocked dispatch requires empty dispatch_command")
        if dispatch_command_parts:
            raise ValueError(f"{path}: blocked dispatch requires empty dispatch_command_parts")
        if on_block_policy == "fail" and exit_code != 1:
            raise ValueError(f"{path}: blocked+fail policy requires exit_code=1")
        if on_block_policy == "skip" and exit_code != 0:
            raise ValueError(f"{path}: blocked+skip policy requires exit_code=0")

    return {
        "generated_at": payload.get("generated_at"),
        "source_execution_decision_report": payload.get("source_execution_decision_report"),
        "source_governance_publish_report": payload.get("source_governance_publish_report"),
        "decision": decision,
        "decision_status": decision_status,
        "dispatch_status": dispatch_status,
        "dispatch_mode": dispatch_mode,
        "should_dispatch_workflow": should_dispatch_workflow,
        "exit_code": exit_code,
        "on_block_policy": on_block_policy,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "dispatch_command": dispatch_command,
        "dispatch_command_parts": dispatch_command_parts,
        "workflow_path": workflow_path,
        "workflow_ref": workflow_ref,
        "workflow_plan_path": workflow_plan_path,
    }


def execute_dispatch_command(
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
            "error_message": f"dispatch command timeout after {timeout_seconds}s",
        }

    return {
        "attempted": True,
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(completed.stdout or ""),
        "stderr_tail": _tail_text(completed.stderr or ""),
        "error_type": "",
        "error_message": "",
    }


def build_dispatch_execution_payload(
    dispatch_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    dry_run: bool,
    command_result: dict[str, Any] | None,
) -> dict[str, Any]:
    should_dispatch = bool(dispatch_report["should_dispatch_workflow"])
    base_exit_code = int(dispatch_report["exit_code"])
    command = str(dispatch_report["dispatch_command"])
    command_parts = list(dispatch_report["dispatch_command_parts"])

    execution_status: str
    dispatch_attempted = False
    command_returncode: int | None = None
    command_stdout_tail = ""
    command_stderr_tail = ""
    execution_reason_codes = list(dispatch_report["reason_codes"])
    execution_error_type = ""
    execution_error_message = ""

    if should_dispatch:
        if dry_run:
            execution_status = "ready_dry_run"
            execution_exit_code = 0
        else:
            dispatch_attempted = True
            if command_result is None:
                execution_status = "dispatch_failed"
                execution_exit_code = 1
                execution_reason_codes.append("dispatch_result_missing")
            else:
                command_returncode = int(command_result["returncode"])
                command_stdout_tail = str(command_result.get("stdout_tail", ""))
                command_stderr_tail = str(command_result.get("stderr_tail", ""))
                execution_error_type = str(command_result.get("error_type", ""))
                execution_error_message = str(command_result.get("error_message", ""))
                if command_returncode == 0:
                    execution_status = "dispatched"
                    execution_exit_code = 0
                    execution_reason_codes = ["dispatch_command_succeeded"]
                else:
                    execution_status = "dispatch_failed"
                    execution_exit_code = 1
                    if execution_error_type == "command_not_found":
                        execution_reason_codes.append("dispatch_cli_unavailable")
                    elif execution_error_type == "timeout":
                        execution_reason_codes.append("dispatch_timeout")
                    else:
                        execution_reason_codes.append("dispatch_command_failed")
    else:
        execution_status = "blocked"
        execution_exit_code = base_exit_code
        execution_reason_codes = list(dispatch_report["reason_codes"])

    deduped_reason_codes: list[str] = []
    seen: set[str] = set()
    for reason in execution_reason_codes:
        if reason in seen:
            continue
        seen.add(reason)
        deduped_reason_codes.append(reason)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dispatch_report": str(source_path),
        "project_root": str(project_root),
        "decision": str(dispatch_report["decision"]),
        "decision_status": str(dispatch_report["decision_status"]),
        "dispatch_status": str(dispatch_report["dispatch_status"]),
        "dispatch_mode": str(dispatch_report["dispatch_mode"]),
        "should_dispatch_workflow": should_dispatch,
        "dispatch_attempted": dispatch_attempted,
        "dispatch_command": command,
        "dispatch_command_parts": command_parts,
        "dry_run": dry_run,
        "execution_status": execution_status,
        "execution_exit_code": int(execution_exit_code),
        "command_returncode": command_returncode,
        "command_stdout_tail": command_stdout_tail,
        "command_stderr_tail": command_stderr_tail,
        "execution_error_type": execution_error_type,
        "execution_error_message": execution_error_message,
        "on_block_policy": str(dispatch_report["on_block_policy"]),
        "reason_codes": deduped_reason_codes,
        "failed_checks": list(dispatch_report["failed_checks"]),
        "structural_issues": list(dispatch_report["structural_issues"]),
        "missing_artifacts": list(dispatch_report["missing_artifacts"]),
        "workflow_path": str(dispatch_report["workflow_path"]),
        "workflow_ref": str(dispatch_report["workflow_ref"]),
        "workflow_plan_path": str(dispatch_report["workflow_plan_path"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Dispatch Execution Report",
        "",
        f"- Execution Status: **{str(payload['execution_status']).upper()}**",
        f"- Should Dispatch Workflow: `{payload['should_dispatch_workflow']}`",
        f"- Dispatch Attempted: `{payload['dispatch_attempted']}`",
        f"- Dry Run: `{payload['dry_run']}`",
        f"- Execution Exit Code: `{payload['execution_exit_code']}`",
        f"- Command Return Code: `{payload['command_returncode']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Dispatch Report: `{payload['source_dispatch_report']}`",
        f"- Project Root: `{payload['project_root']}`",
        f"- Workflow Plan Path: `{payload['workflow_plan_path']}`",
        f"- Workflow YAML Path: `{payload['workflow_path']}`",
        "",
        "## Dispatch Command",
    ]

    if payload["dispatch_command"]:
        lines.append(f"- `{payload['dispatch_command']}`")
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
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    command_returncode = payload["command_returncode"]
    return {
        "workflow_dispatch_execution_status": str(payload["execution_status"]),
        "workflow_dispatch_execution_should_dispatch": "true"
        if payload["should_dispatch_workflow"]
        else "false",
        "workflow_dispatch_execution_attempted": "true" if payload["dispatch_attempted"] else "false",
        "workflow_dispatch_execution_exit_code": str(payload["execution_exit_code"]),
        "workflow_dispatch_execution_command_returncode": (
            "" if command_returncode is None else str(command_returncode)
        ),
        "workflow_dispatch_execution_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_dispatch_execution_report_json": str(output_json),
        "workflow_dispatch_execution_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute Linux CI workflow dispatch contract and publish execution report"
    )
    parser.add_argument(
        "--dispatch-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch.json",
        help="P2-24 dispatch report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for dispatch command execution",
    )
    parser.add_argument(
        "--dispatch-timeout-seconds",
        type=int,
        default=300,
        help="Dispatch command timeout in seconds",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json",
        help="Output execution JSON report path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.md",
        help="Output execution markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print execution JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate dispatch report and skip command execution",
    )
    args = parser.parse_args()

    if args.dispatch_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-dispatch-execution-gate] "
            "--dispatch-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    dispatch_report_path = Path(args.dispatch_report)
    project_root = Path(args.project_root)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        dispatch_report = load_dispatch_report(dispatch_report_path)
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-dispatch-execution-gate] {exc}", file=sys.stderr)
        return 2

    command_result: dict[str, Any] | None = None
    if dispatch_report["should_dispatch_workflow"] and not args.dry_run:
        command_result = execute_dispatch_command(
            dispatch_report["dispatch_command_parts"],
            cwd=project_root,
            timeout_seconds=args.dispatch_timeout_seconds,
        )

    payload = build_dispatch_execution_payload(
        dispatch_report,
        source_path=dispatch_report_path.resolve(),
        project_root=project_root.resolve(),
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
        print(f"dispatch execution json: {output_json_path}")
        print(f"dispatch execution markdown: {output_markdown_path}")

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
        "dispatch execution summary: "
        f"execution_status={payload['execution_status']} "
        f"dispatch_attempted={payload['dispatch_attempted']} "
        f"execution_exit_code={payload['execution_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["execution_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
