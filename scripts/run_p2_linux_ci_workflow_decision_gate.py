"""Phase 2 card P2-23 gate for Linux CI workflow execution decision.

This script turns the P2-22 governance publish payload into a single
execution decision contract for CI:
1) executable/blocked decision,
2) policy-aware exit code (fail/skip),
3) decision report artifacts + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coerce_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"field '{field}' must be bool")
    return value


def _coerce_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"field '{field}' must be int")
    return value


def _coerce_str_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"field '{field}' must be non-empty string list")
    return list(value)


def load_governance_publish_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: governance publish report file not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: governance publish payload must be object")

    for required in ("overall_status", "should_execute_workflow", "failed_checks", "failed_check_count"):
        if required not in payload:
            raise ValueError(f"{path}: missing field '{required}'")

    overall_status = payload["overall_status"]
    if overall_status not in {"passed", "failed"}:
        raise ValueError(f"{path}: field 'overall_status' must be 'passed' or 'failed'")

    should_execute_workflow = _coerce_bool(
        payload["should_execute_workflow"],
        field="should_execute_workflow",
    )
    failed_checks = _coerce_str_list(payload["failed_checks"], field="failed_checks")
    failed_check_count = _coerce_int(payload["failed_check_count"], field="failed_check_count")
    if failed_check_count != len(failed_checks):
        raise ValueError(
            f"{path}: failed_check_count ({failed_check_count}) "
            f"!= len(failed_checks) ({len(failed_checks)})"
        )

    structural_issues_raw = payload.get("structural_issues", [])
    if not isinstance(structural_issues_raw, list) or not all(
        isinstance(item, str) and item for item in structural_issues_raw
    ):
        raise ValueError(f"{path}: field 'structural_issues' must be non-empty string list")

    return {
        "generated_at": payload.get("generated_at"),
        "source_governance_report": payload.get("source_governance_report"),
        "overall_status": overall_status,
        "should_execute_workflow": should_execute_workflow,
        "failed_checks": failed_checks,
        "failed_check_count": failed_check_count,
        "structural_issues": list(structural_issues_raw),
    }


def _unique(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def build_execution_decision_payload(
    governance_publish_report: dict[str, Any],
    *,
    source_path: Path,
    workflow_plan_path: Path,
    workflow_path: Path,
    on_block_policy: str,
) -> dict[str, Any]:
    structural_issues = list(governance_publish_report["structural_issues"])

    expected_should_execute = governance_publish_report["overall_status"] == "passed"
    if expected_should_execute != bool(governance_publish_report["should_execute_workflow"]):
        structural_issues.append("status_contract_mismatch")

    should_execute_workflow = bool(governance_publish_report["should_execute_workflow"]) and not structural_issues
    missing_artifacts: list[str] = []
    if should_execute_workflow:
        if not workflow_plan_path.is_file():
            missing_artifacts.append("workflow_plan_missing")
        if not workflow_path.is_file():
            missing_artifacts.append("workflow_yaml_missing")
        if missing_artifacts:
            structural_issues.append("missing_execution_artifacts")
            should_execute_workflow = False

    structural_issues = _unique(structural_issues)
    failed_checks = list(governance_publish_report["failed_checks"])
    reason_codes = _unique(failed_checks + structural_issues)

    if should_execute_workflow:
        decision = "execute"
        decision_status = "approved"
        reason_codes = ["governance_passed"]
    else:
        decision = "blocked"
        decision_status = "blocked"
        if not reason_codes:
            reason_codes = ["governance_failed"]

    exit_code = 0 if (should_execute_workflow or on_block_policy == "skip") else 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_governance_publish_report": str(source_path),
        "workflow_plan_path": str(workflow_plan_path),
        "workflow_path": str(workflow_path),
        "governance_overall_status": str(governance_publish_report["overall_status"]),
        "decision": decision,
        "decision_status": decision_status,
        "should_execute_workflow": should_execute_workflow,
        "on_block_policy": on_block_policy,
        "exit_code": exit_code,
        "failed_checks": failed_checks,
        "failed_check_count": len(failed_checks),
        "structural_issues": structural_issues,
        "structural_issue_count": len(structural_issues),
        "missing_artifacts": missing_artifacts,
        "reason_codes": reason_codes,
        "primary_reason": reason_codes[0],
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Execution Decision Report",
        "",
        f"- Decision: **{str(payload['decision']).upper()}**",
        f"- Decision Status: `{payload['decision_status']}`",
        f"- Should Execute Workflow: `{payload['should_execute_workflow']}`",
        f"- Exit Code: `{payload['exit_code']}`",
        f"- On Block Policy: `{payload['on_block_policy']}`",
        f"- Primary Reason: `{payload['primary_reason']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Governance Publish Report: `{payload['source_governance_publish_report']}`",
        f"- Workflow Plan Path: `{payload['workflow_plan_path']}`",
        f"- Workflow YAML Path: `{payload['workflow_path']}`",
        "",
        "## Reason Codes",
    ]

    reason_codes = payload["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{item}`" for item in reason_codes)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Failed Checks",
        ]
    )
    failed_checks = payload["failed_checks"]
    if failed_checks:
        lines.extend(f"- `{item}`" for item in failed_checks)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Structural Issues",
        ]
    )
    structural_issues = payload["structural_issues"]
    if structural_issues:
        lines.extend(f"- `{item}`" for item in structural_issues)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Missing Artifacts",
        ]
    )
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
        "workflow_execution_decision": str(payload["decision"]),
        "workflow_execution_status": str(payload["decision_status"]),
        "workflow_execution_should_execute": "true" if payload["should_execute_workflow"] else "false",
        "workflow_execution_exit_code": str(payload["exit_code"]),
        "workflow_execution_on_block_policy": str(payload["on_block_policy"]),
        "workflow_execution_failed_checks": json.dumps(
            payload["failed_checks"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_execution_structural_issues": json.dumps(
            payload["structural_issues"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_execution_report_json": str(output_json),
        "workflow_execution_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Linux CI workflow execution decision from governance publish payload"
    )
    parser.add_argument(
        "--governance-publish",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance_publish.json",
        help="P2-22 governance publish JSON path",
    )
    parser.add_argument(
        "--workflow-plan",
        default=".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        help="P2-17 workflow plan JSON path",
    )
    parser.add_argument(
        "--workflow-path",
        default=".github/workflows/linux_unified_gate.yml",
        help="Rendered workflow YAML path",
    )
    parser.add_argument(
        "--on-block",
        choices=("fail", "skip"),
        default="fail",
        help="Exit policy when decision is blocked",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_execution_decision.json",
        help="Output decision JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_execution_decision.md",
        help="Output decision markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print decision JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output files",
    )
    args = parser.parse_args()

    governance_publish_path = Path(args.governance_publish)
    workflow_plan_path = Path(args.workflow_plan)
    workflow_path = Path(args.workflow_path)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        governance_report = load_governance_publish_report(governance_publish_path)
        payload = build_execution_decision_payload(
            governance_report,
            source_path=governance_publish_path.resolve(),
            workflow_plan_path=workflow_plan_path,
            workflow_path=workflow_path,
            on_block_policy=args.on_block,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-decision-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"execution decision json: {output_json_path}")
        print(f"execution decision markdown: {output_markdown_path}")

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
        "execution decision summary: "
        f"decision={payload['decision']} "
        f"should_execute_workflow={payload['should_execute_workflow']} "
        f"exit_code={payload['exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

