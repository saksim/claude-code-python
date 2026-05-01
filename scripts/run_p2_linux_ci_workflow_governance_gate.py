"""Phase 2 card P2-21 gate for Linux CI workflow governance convergence.

This script aggregates the contracts from:
1) P2-19 workflow render drift sync gate,
2) P2-20 workflow command guard gate.

It produces one governance verdict for CI, so Linux fan-out/fan-in workflow
artifacts are validated as a unified contract before execution.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_module(*, script_name: str, module_name: str):
    script_path = Path(__file__).resolve().with_name(script_name)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_path(value: str) -> str:
    return Path(value).resolve().as_posix().lower()


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid {label} JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: {label} payload must be object")
    return payload


def build_governance_report(
    *,
    ci_workflow_plan_path: Path,
    workflow_path: Path,
    metadata_path: Path,
    workflow_name: str,
    python_version: str,
    artifact_prefix: str,
    strict_generated_at: bool,
) -> dict[str, Any]:
    sync_gate = _load_module(
        script_name="run_p2_linux_ci_workflow_sync_gate.py",
        module_name="p2_linux_ci_workflow_sync_gate_for_governance",
    )
    command_guard_gate = _load_module(
        script_name="run_p2_linux_ci_workflow_command_guard_gate.py",
        module_name="p2_linux_ci_workflow_command_guard_gate_for_governance",
    )

    expected_workflow_yaml, expected_metadata = sync_gate.build_expected_artifacts(
        plan_path=ci_workflow_plan_path,
        workflow_path=workflow_path,
        workflow_name=workflow_name,
        python_version=python_version,
        artifact_prefix=artifact_prefix,
    )
    drift = sync_gate.check_render_drift(
        expected_workflow_yaml=expected_workflow_yaml,
        expected_metadata=expected_metadata,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        strict_generated_at=strict_generated_at,
    )

    plan = command_guard_gate.load_ci_workflow_plan(ci_workflow_plan_path)
    normalized_plan, command_guard = command_guard_gate.guard_ci_workflow_plan_commands(plan)
    normalization_required = normalized_plan != plan

    expected_source_plan = str(ci_workflow_plan_path.resolve())
    expected_workflow_output = str(workflow_path.resolve())
    actual_source_plan: str | None = None
    actual_workflow_output: str | None = None
    source_match = False
    workflow_output_match = False
    lineage_issues: list[dict[str, str]] = []

    if metadata_path.is_file():
        metadata_payload = _load_json_object(metadata_path, label="workflow metadata")
        source_value = metadata_payload.get("source_ci_workflow_plan")
        if isinstance(source_value, str) and source_value:
            actual_source_plan = source_value
            source_match = _normalize_path(source_value) == _normalize_path(expected_source_plan)
        else:
            lineage_issues.append(
                {
                    "code": "missing_source_ci_workflow_plan",
                    "message": "workflow metadata missing non-empty source_ci_workflow_plan",
                }
            )

        workflow_value = metadata_payload.get("workflow_output_path")
        if isinstance(workflow_value, str) and workflow_value:
            actual_workflow_output = workflow_value
            workflow_output_match = _normalize_path(workflow_value) == _normalize_path(
                expected_workflow_output
            )
        else:
            lineage_issues.append(
                {
                    "code": "missing_workflow_output_path",
                    "message": "workflow metadata missing non-empty workflow_output_path",
                }
            )
    else:
        lineage_issues.append(
            {
                "code": "missing_workflow_metadata",
                "message": f"workflow metadata file not found: {metadata_path}",
            }
        )

    if actual_source_plan is not None and not source_match:
        lineage_issues.append(
            {
                "code": "source_ci_workflow_plan_mismatch",
                "message": (
                    f"metadata source_ci_workflow_plan '{actual_source_plan}' "
                    f"!= expected '{expected_source_plan}'"
                ),
            }
        )

    if actual_workflow_output is not None and not workflow_output_match:
        lineage_issues.append(
            {
                "code": "workflow_output_path_mismatch",
                "message": (
                    f"metadata workflow_output_path '{actual_workflow_output}' "
                    f"!= expected '{expected_workflow_output}'"
                ),
            }
        )

    failed_checks: list[str] = []
    if drift["workflow_drift"] or drift["metadata_drift"]:
        failed_checks.append("workflow_sync_drift")
    if command_guard["overall_status"] != "passed":
        failed_checks.append("command_guard_failed")
    if lineage_issues:
        failed_checks.append("lineage_mismatch")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_ci_workflow_plan": str(ci_workflow_plan_path),
        "workflow_path": str(workflow_path),
        "metadata_path": str(metadata_path),
        "strict_generated_at": strict_generated_at,
        "overall_status": "failed" if failed_checks else "passed",
        "failed_checks": failed_checks,
        "workflow_sync": drift,
        "command_guard": {
            "overall_status": str(command_guard["overall_status"]),
            "failed_commands": int(command_guard["failed_commands"]),
            "total_commands": int(command_guard["total_commands"]),
            "issue_count": len(command_guard["issues"]),
            "normalization_required": normalization_required,
            "issues": list(command_guard["issues"]),
        },
        "lineage": {
            "expected_source_ci_workflow_plan": expected_source_plan,
            "actual_source_ci_workflow_plan": actual_source_plan,
            "source_match": source_match,
            "expected_workflow_output_path": expected_workflow_output,
            "actual_workflow_output_path": actual_workflow_output,
            "workflow_output_match": workflow_output_match,
            "issues": lineage_issues,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Converge Linux CI workflow governance contracts (P2-19 + P2-20)"
    )
    parser.add_argument(
        "--ci-workflow-plan",
        default=".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        help="P2-17 CI workflow plan JSON path",
    )
    parser.add_argument(
        "--workflow-path",
        default=".github/workflows/linux_unified_gate.yml",
        help="Rendered workflow YAML path",
    )
    parser.add_argument(
        "--metadata-path",
        default=".claude/reports/linux_unified_gate/ci_workflow_render.json",
        help="Rendered metadata JSON path",
    )
    parser.add_argument(
        "--workflow-name",
        default="Linux Unified Gate",
        help="Workflow name forwarded to render/sync contract builder",
    )
    parser.add_argument(
        "--python-version",
        default="3.11",
        help="Python version forwarded to render/sync contract builder",
    )
    parser.add_argument(
        "--artifact-prefix",
        default="linux-unified-summary",
        help="Artifact prefix forwarded to render/sync contract builder",
    )
    parser.add_argument(
        "--strict-generated-at",
        action="store_true",
        help="Treat metadata generated_at drift as governance failure",
    )
    parser.add_argument(
        "--output",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance.json",
        help="Output governance report JSON path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print governance report JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write report file",
    )
    args = parser.parse_args()

    try:
        report = build_governance_report(
            ci_workflow_plan_path=Path(args.ci_workflow_plan),
            workflow_path=Path(args.workflow_path),
            metadata_path=Path(args.metadata_path),
            workflow_name=args.workflow_name,
            python_version=args.python_version,
            artifact_prefix=args.artifact_prefix,
            strict_generated_at=args.strict_generated_at,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-governance-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"governance report: {output_path}")

    print(
        "governance summary: "
        f"status={report['overall_status']} "
        f"failed_checks={len(report['failed_checks'])} "
        f"command_issues={report['command_guard']['issue_count']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 1 if report["overall_status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
