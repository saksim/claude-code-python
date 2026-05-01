"""Phase 2 card P2-24 gate for Linux CI workflow dispatch readiness.

This script converts the P2-23 execution decision payload into a dispatch
contract that can be consumed by downstream CI jobs:
1) ready/blocked dispatch status,
2) canonical dispatch command parts,
3) report artifacts + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import shlex
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
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}: field '{field}' must be non-empty string")
    return value


def _coerce_str_list(value: Any, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{path}: field '{field}' must be non-empty string list")
    return list(value)


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def load_execution_decision(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: execution decision file not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: execution decision payload must be object")

    required_fields = (
        "decision",
        "decision_status",
        "should_execute_workflow",
        "on_block_policy",
        "exit_code",
        "workflow_path",
        "workflow_plan_path",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
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

    should_execute_workflow = _coerce_bool(
        payload["should_execute_workflow"],
        field="should_execute_workflow",
        path=path,
    )
    on_block_policy = payload["on_block_policy"]
    if on_block_policy not in {"fail", "skip"}:
        raise ValueError(f"{path}: field 'on_block_policy' must be 'fail' or 'skip'")
    exit_code = _coerce_int(payload["exit_code"], field="exit_code", path=path)
    if exit_code not in {0, 1}:
        raise ValueError(f"{path}: field 'exit_code' must be 0 or 1")

    workflow_path = _coerce_str(payload["workflow_path"], field="workflow_path", path=path)
    workflow_plan_path = _coerce_str(
        payload["workflow_plan_path"],
        field="workflow_plan_path",
        path=path,
    )
    reason_codes = _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path)
    failed_checks = _coerce_str_list(payload["failed_checks"], field="failed_checks", path=path)

    structural_issues_raw = payload["structural_issues"]
    if not isinstance(structural_issues_raw, list) or not all(
        isinstance(item, str) and item for item in structural_issues_raw
    ):
        raise ValueError(f"{path}: field 'structural_issues' must be non-empty string list")
    structural_issues = list(structural_issues_raw)

    missing_artifacts_raw = payload["missing_artifacts"]
    if not isinstance(missing_artifacts_raw, list) or not all(
        isinstance(item, str) and item for item in missing_artifacts_raw
    ):
        raise ValueError(f"{path}: field 'missing_artifacts' must be non-empty string list")
    missing_artifacts = list(missing_artifacts_raw)

    if decision == "execute" and not should_execute_workflow:
        raise ValueError(f"{path}: decision/should_execute_workflow contract mismatch")
    if decision == "blocked" and should_execute_workflow:
        raise ValueError(f"{path}: decision/should_execute_workflow contract mismatch")
    if decision == "execute" and decision_status != "approved":
        raise ValueError(f"{path}: execute decision requires decision_status='approved'")
    if decision == "blocked" and decision_status != "blocked":
        raise ValueError(f"{path}: blocked decision requires decision_status='blocked'")
    if decision == "execute" and exit_code != 0:
        raise ValueError(f"{path}: execute decision requires exit_code=0")
    if decision == "blocked" and on_block_policy == "fail" and exit_code != 1:
        raise ValueError(f"{path}: blocked+fail policy requires exit_code=1")
    if decision == "blocked" and on_block_policy == "skip" and exit_code != 0:
        raise ValueError(f"{path}: blocked+skip policy requires exit_code=0")

    return {
        "generated_at": payload.get("generated_at"),
        "source_governance_publish_report": payload.get("source_governance_publish_report"),
        "decision": decision,
        "decision_status": decision_status,
        "should_execute_workflow": should_execute_workflow,
        "on_block_policy": on_block_policy,
        "exit_code": exit_code,
        "workflow_path": workflow_path,
        "workflow_plan_path": workflow_plan_path,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


def build_dispatch_payload(
    decision_report: dict[str, Any],
    *,
    source_path: Path,
    workflow_ref: str,
    gh_executable: str,
) -> dict[str, Any]:
    should_dispatch = bool(decision_report["should_execute_workflow"])
    workflow_path = str(decision_report["workflow_path"])
    workflow_plan_path = str(decision_report["workflow_plan_path"])
    decision = str(decision_report["decision"])
    decision_status = str(decision_report["decision_status"])

    command_parts: list[str]
    command: str
    dispatch_status: str
    dispatch_mode: str
    if should_dispatch:
        command_parts = [
            gh_executable,
            "workflow",
            "run",
            workflow_path,
            "--ref",
            workflow_ref,
            "--raw-field",
            f"source_decision_report={source_path}",
            "--raw-field",
            f"workflow_plan_path={workflow_plan_path}",
        ]
        command = _format_shell_command(command_parts)
        dispatch_status = "ready"
        dispatch_mode = "workflow_dispatch"
    else:
        command_parts = []
        command = ""
        dispatch_status = "blocked"
        dispatch_mode = "none"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_execution_decision_report": str(source_path),
        "source_governance_publish_report": decision_report["source_governance_publish_report"],
        "workflow_path": workflow_path,
        "workflow_plan_path": workflow_plan_path,
        "workflow_ref": workflow_ref,
        "decision": decision,
        "decision_status": decision_status,
        "dispatch_status": dispatch_status,
        "dispatch_mode": dispatch_mode,
        "should_dispatch_workflow": should_dispatch,
        "exit_code": int(decision_report["exit_code"]),
        "on_block_policy": str(decision_report["on_block_policy"]),
        "reason_codes": list(decision_report["reason_codes"]),
        "failed_checks": list(decision_report["failed_checks"]),
        "structural_issues": list(decision_report["structural_issues"]),
        "missing_artifacts": list(decision_report["missing_artifacts"]),
        "dispatch_command": command,
        "dispatch_command_parts": command_parts,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Dispatch Readiness Report",
        "",
        f"- Dispatch Status: **{str(payload['dispatch_status']).upper()}**",
        f"- Dispatch Mode: `{payload['dispatch_mode']}`",
        f"- Should Dispatch Workflow: `{payload['should_dispatch_workflow']}`",
        f"- Exit Code: `{payload['exit_code']}`",
        f"- Workflow Ref: `{payload['workflow_ref']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Execution Decision Report: `{payload['source_execution_decision_report']}`",
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

    lines.extend(["", "## Missing Artifacts"])
    missing_artifacts = payload["missing_artifacts"]
    if missing_artifacts:
        lines.extend(f"- `{item}`" for item in missing_artifacts)
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    return {
        "workflow_dispatch_status": str(payload["dispatch_status"]),
        "workflow_dispatch_mode": str(payload["dispatch_mode"]),
        "workflow_dispatch_should_dispatch": "true" if payload["should_dispatch_workflow"] else "false",
        "workflow_dispatch_exit_code": str(payload["exit_code"]),
        "workflow_dispatch_command": str(payload["dispatch_command"]),
        "workflow_dispatch_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_dispatch_report_json": str(output_json),
        "workflow_dispatch_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Linux CI workflow dispatch contract from execution decision report"
    )
    parser.add_argument(
        "--execution-decision",
        default=".claude/reports/linux_unified_gate/ci_workflow_execution_decision.json",
        help="P2-23 execution decision JSON path",
    )
    parser.add_argument(
        "--workflow-ref",
        default="main",
        help="Git ref used in workflow dispatch command",
    )
    parser.add_argument(
        "--gh-executable",
        default="gh",
        help="GitHub CLI executable used in dispatch command",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch.json",
        help="Output dispatch JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch.md",
        help="Output dispatch markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print dispatch JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output files",
    )
    args = parser.parse_args()

    execution_decision_path = Path(args.execution_decision)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        decision_report = load_execution_decision(execution_decision_path)
        payload = build_dispatch_payload(
            decision_report,
            source_path=execution_decision_path.resolve(),
            workflow_ref=args.workflow_ref,
            gh_executable=args.gh_executable,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-dispatch-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"workflow dispatch json: {output_json_path}")
        print(f"workflow dispatch markdown: {output_markdown_path}")

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
        "dispatch summary: "
        f"dispatch_status={payload['dispatch_status']} "
        f"should_dispatch_workflow={payload['should_dispatch_workflow']} "
        f"exit_code={payload['exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

