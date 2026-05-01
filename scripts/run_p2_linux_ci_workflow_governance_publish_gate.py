"""Phase 2 card P2-22 gate for Linux CI workflow governance publishing.

This script converts the P2-21 governance report into:
1) compact JSON payload for CI decisioning,
2) markdown report for quick human audit,
3) optional GitHub output key-values for downstream workflow jobs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coerce_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"field '{field}' must be int")
    return value


def _coerce_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"field '{field}' must be bool")
    return value


def _coerce_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"field '{field}' must be non-empty string")
    return value


def _coerce_str_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"field '{field}' must be non-empty string list")
    return list(value)


def load_governance_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: governance report file not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: governance report payload must be object")

    required_fields = ("overall_status", "failed_checks", "workflow_sync", "command_guard", "lineage")
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    overall_status = payload["overall_status"]
    if overall_status not in {"passed", "failed"}:
        raise ValueError(f"{path}: field 'overall_status' must be 'passed' or 'failed'")

    failed_checks = _coerce_str_list(payload["failed_checks"], field="failed_checks")

    workflow_sync = payload["workflow_sync"]
    if not isinstance(workflow_sync, dict):
        raise ValueError(f"{path}: field 'workflow_sync' must be object")
    workflow_drift = _coerce_bool(
        workflow_sync.get("workflow_drift"),
        field="workflow_sync.workflow_drift",
    )
    metadata_drift = _coerce_bool(
        workflow_sync.get("metadata_drift"),
        field="workflow_sync.metadata_drift",
    )

    command_guard = payload["command_guard"]
    if not isinstance(command_guard, dict):
        raise ValueError(f"{path}: field 'command_guard' must be object")
    command_guard_status = command_guard.get("overall_status")
    if command_guard_status not in {"passed", "failed"}:
        raise ValueError(f"{path}: field 'command_guard.overall_status' must be 'passed' or 'failed'")
    failed_commands = _coerce_int(
        command_guard.get("failed_commands"),
        field="command_guard.failed_commands",
    )
    total_commands = _coerce_int(
        command_guard.get("total_commands"),
        field="command_guard.total_commands",
    )
    issue_count = _coerce_int(command_guard.get("issue_count"), field="command_guard.issue_count")
    normalization_required = _coerce_bool(
        command_guard.get("normalization_required"),
        field="command_guard.normalization_required",
    )
    if failed_commands < 0 or total_commands < 0 or issue_count < 0:
        raise ValueError(f"{path}: command_guard counters must be >= 0")
    if failed_commands > total_commands:
        raise ValueError(f"{path}: command_guard.failed_commands exceeds total_commands")

    lineage = payload["lineage"]
    if not isinstance(lineage, dict):
        raise ValueError(f"{path}: field 'lineage' must be object")
    source_match = _coerce_bool(lineage.get("source_match"), field="lineage.source_match")
    workflow_output_match = _coerce_bool(
        lineage.get("workflow_output_match"),
        field="lineage.workflow_output_match",
    )
    lineage_issues = lineage.get("issues")
    if not isinstance(lineage_issues, list):
        raise ValueError(f"{path}: field 'lineage.issues' must be list")
    for index, item in enumerate(lineage_issues):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: lineage.issues[{index}] must be object")
        _coerce_str(item.get("code"), field=f"lineage.issues[{index}].code")
        _coerce_str(item.get("message"), field=f"lineage.issues[{index}].message")

    return {
        "generated_at": payload.get("generated_at"),
        "source_ci_workflow_plan": payload.get("source_ci_workflow_plan"),
        "workflow_path": payload.get("workflow_path"),
        "metadata_path": payload.get("metadata_path"),
        "strict_generated_at": bool(payload.get("strict_generated_at", False)),
        "overall_status": overall_status,
        "failed_checks": failed_checks,
        "workflow_sync": {
            "workflow_drift": workflow_drift,
            "metadata_drift": metadata_drift,
        },
        "command_guard": {
            "overall_status": command_guard_status,
            "failed_commands": failed_commands,
            "total_commands": total_commands,
            "issue_count": issue_count,
            "normalization_required": normalization_required,
        },
        "lineage": {
            "source_match": source_match,
            "workflow_output_match": workflow_output_match,
            "issues": list(lineage_issues),
        },
    }


def build_governance_publish_payload(
    governance_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    failed_checks = list(governance_report["failed_checks"])
    workflow_sync = governance_report["workflow_sync"]
    command_guard = governance_report["command_guard"]
    lineage = governance_report["lineage"]

    structural_issues: list[str] = []
    notes: list[str] = []

    computed_failed_checks: list[str] = []
    if workflow_sync["workflow_drift"] or workflow_sync["metadata_drift"]:
        computed_failed_checks.append("workflow_sync_drift")
    if command_guard["overall_status"] != "passed":
        computed_failed_checks.append("command_guard_failed")
    if lineage["issues"]:
        computed_failed_checks.append("lineage_mismatch")

    computed_failed_checks = sorted(set(computed_failed_checks))
    reported_failed_checks = sorted(set(failed_checks))

    if computed_failed_checks != reported_failed_checks:
        structural_issues.append("failed_checks_mismatch")
        notes.append(
            "failed_checks mismatch between reported and recomputed contracts "
            f"(reported={reported_failed_checks}, computed={computed_failed_checks})"
        )

    reported_status = str(governance_report["overall_status"])
    computed_status = "failed" if computed_failed_checks else "passed"
    if reported_status != computed_status:
        structural_issues.append("overall_status_mismatch")
        notes.append(
            "overall_status mismatch between reported and recomputed contracts "
            f"(reported={reported_status}, computed={computed_status})"
        )

    final_status = "failed" if structural_issues else reported_status
    should_execute_workflow = final_status == "passed"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_governance_report": str(source_path),
        "reported_status": reported_status,
        "computed_status": computed_status,
        "overall_status": final_status,
        "should_execute_workflow": should_execute_workflow,
        "failed_checks": reported_failed_checks,
        "failed_check_count": len(reported_failed_checks),
        "workflow_sync_summary": {
            "workflow_drift": bool(workflow_sync["workflow_drift"]),
            "metadata_drift": bool(workflow_sync["metadata_drift"]),
        },
        "command_guard_summary": {
            "overall_status": str(command_guard["overall_status"]),
            "failed_commands": int(command_guard["failed_commands"]),
            "total_commands": int(command_guard["total_commands"]),
            "issue_count": int(command_guard["issue_count"]),
            "normalization_required": bool(command_guard["normalization_required"]),
        },
        "lineage_summary": {
            "source_match": bool(lineage["source_match"]),
            "workflow_output_match": bool(lineage["workflow_output_match"]),
            "issue_count": len(lineage["issues"]),
        },
        "lineage_issues": list(lineage["issues"]),
        "structural_issues": structural_issues,
        "notes": notes,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    status = payload["overall_status"]
    lines = [
        "# Linux CI Workflow Governance Publish Report",
        "",
        f"- Status: **{status.upper()}**",
        f"- Should Execute Workflow: `{payload['should_execute_workflow']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        f"- Source Governance Report: `{payload['source_governance_report']}`",
        "",
        "## Status Contract",
        "",
        f"- Reported Status: `{payload['reported_status']}`",
        f"- Computed Status: `{payload['computed_status']}`",
        f"- Failed Check Count: `{payload['failed_check_count']}`",
        "",
        "## Failed Checks",
    ]

    failed_checks = payload["failed_checks"]
    if failed_checks:
        lines.extend(f"- `{item}`" for item in failed_checks)
    else:
        lines.append("- none")

    command_guard = payload["command_guard_summary"]
    workflow_sync = payload["workflow_sync_summary"]
    lineage = payload["lineage_summary"]

    lines.extend(
        [
            "",
            "## Contract Summaries",
            "",
            f"- Workflow Drift: `{workflow_sync['workflow_drift']}`",
            f"- Metadata Drift: `{workflow_sync['metadata_drift']}`",
            f"- Command Guard Status: `{command_guard['overall_status']}`",
            f"- Command Guard Issues: `{command_guard['issue_count']}`",
            f"- Command Guard Failed Commands: `{command_guard['failed_commands']}`",
            f"- Command Guard Total Commands: `{command_guard['total_commands']}`",
            f"- Lineage Source Match: `{lineage['source_match']}`",
            f"- Lineage Workflow Output Match: `{lineage['workflow_output_match']}`",
            f"- Lineage Issue Count: `{lineage['issue_count']}`",
            "",
            "## Structural Issues",
        ]
    )

    structural_issues = payload["structural_issues"]
    if structural_issues:
        lines.extend(f"- {item}" for item in structural_issues)
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Notes")
    notes = payload["notes"]
    if notes:
        lines.extend(f"- {item}" for item in notes)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    return {
        "governance_status": str(payload["overall_status"]),
        "governance_should_execute_workflow": "true"
        if payload["should_execute_workflow"]
        else "false",
        "governance_failed_checks": json.dumps(
            payload["failed_checks"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "governance_failed_check_count": str(payload["failed_check_count"]),
        "governance_report_json": str(output_json),
        "governance_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish Linux CI workflow governance report into CI decision payload"
    )
    parser.add_argument(
        "--governance-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance.json",
        help="P2-21 governance report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance_publish.json",
        help="Output publish JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance_publish.md",
        help="Output publish markdown path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print publish JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output files",
    )
    args = parser.parse_args()

    governance_report_path = Path(args.governance_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        governance_report = load_governance_report(governance_report_path)
        payload = build_governance_publish_payload(
            governance_report,
            source_path=governance_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-governance-publish-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"governance publish json: {output_json_path}")
        print(f"governance publish markdown: {output_markdown_path}")

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
        "governance publish summary: "
        f"status={payload['overall_status']} "
        f"should_execute_workflow={payload['should_execute_workflow']} "
        f"failed_checks={payload['failed_check_count']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return 0 if payload["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

