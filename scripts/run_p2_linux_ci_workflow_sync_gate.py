"""Phase 2 card P2-19 gate for Linux CI workflow drift sync.

This script verifies that workflow/metadata artifacts rendered from the
P2-17 workflow plan stay synchronized with the expected generated outputs.
It can optionally rewrite drifted artifacts in place.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_yaml_gate_module():
    script_path = Path(__file__).resolve().with_name("run_p2_linux_ci_workflow_yaml_gate.py")
    spec = importlib.util.spec_from_file_location("p2_linux_ci_workflow_yaml_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n")


def _build_unified_diff(*, expected: str, actual: str, expected_name: str, actual_name: str) -> str:
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            expected_lines,
            actual_lines,
            fromfile=expected_name,
            tofile=actual_name,
        )
    )
    return "".join(diff_lines)


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid {label} JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: {label} payload must be object")
    return payload


def _normalize_metadata(payload: dict[str, Any], *, strict_generated_at: bool) -> dict[str, Any]:
    normalized = copy.deepcopy(payload)
    if not strict_generated_at:
        normalized.pop("generated_at", None)
    return normalized


def _format_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def build_expected_artifacts(
    *,
    plan_path: Path,
    workflow_path: Path,
    workflow_name: str,
    python_version: str,
    artifact_prefix: str,
) -> tuple[str, dict[str, Any]]:
    yaml_gate = _load_yaml_gate_module()
    plan = yaml_gate.load_ci_workflow_plan(plan_path)
    workflow_yaml = yaml_gate.build_ci_workflow_yaml(
        plan,
        workflow_name=workflow_name,
        python_version=python_version,
        artifact_prefix=artifact_prefix,
    )
    metadata = yaml_gate.build_render_metadata(
        plan,
        source_plan_path=plan_path.resolve(),
        workflow_output_path=workflow_path,
        artifact_prefix=artifact_prefix,
    )
    metadata["workflow_name"] = workflow_name
    return workflow_yaml, metadata


def check_render_drift(
    *,
    expected_workflow_yaml: str,
    expected_metadata: dict[str, Any],
    workflow_path: Path,
    metadata_path: Path,
    strict_generated_at: bool,
) -> dict[str, Any]:
    workflow_missing = not workflow_path.is_file()
    metadata_missing = not metadata_path.is_file()

    workflow_diff = ""
    metadata_diff = ""

    if not workflow_missing:
        actual_workflow_yaml = _normalize_text(workflow_path.read_text(encoding="utf-8"))
        expected_workflow_yaml = _normalize_text(expected_workflow_yaml)
        if actual_workflow_yaml != expected_workflow_yaml:
            workflow_diff = _build_unified_diff(
                expected=expected_workflow_yaml,
                actual=actual_workflow_yaml,
                expected_name="expected-workflow.yml",
                actual_name=str(workflow_path),
            )

    if not metadata_missing:
        actual_metadata = _load_json_object(metadata_path, label="workflow metadata")
        actual_metadata_normalized = _normalize_metadata(
            actual_metadata,
            strict_generated_at=strict_generated_at,
        )
        expected_metadata_normalized = _normalize_metadata(
            expected_metadata,
            strict_generated_at=strict_generated_at,
        )
        if actual_metadata_normalized != expected_metadata_normalized:
            metadata_diff = _build_unified_diff(
                expected=_format_json(expected_metadata_normalized),
                actual=_format_json(actual_metadata_normalized),
                expected_name="expected-metadata.json",
                actual_name=str(metadata_path),
            )

    return {
        "workflow_missing": workflow_missing,
        "metadata_missing": metadata_missing,
        "workflow_drift": workflow_missing or bool(workflow_diff),
        "metadata_drift": metadata_missing or bool(metadata_diff),
        "workflow_diff": workflow_diff,
        "metadata_diff": metadata_diff,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate/sync rendered Linux CI workflow artifacts from workflow plan"
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
        help="Workflow display name forwarded to P2-18 renderer",
    )
    parser.add_argument(
        "--python-version",
        default="3.11",
        help="Python version forwarded to P2-18 renderer",
    )
    parser.add_argument(
        "--artifact-prefix",
        default="linux-unified-summary",
        help="Artifact prefix forwarded to P2-18 renderer",
    )
    parser.add_argument(
        "--strict-generated-at",
        action="store_true",
        help="Treat generated_at drift in metadata as validation failure",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite workflow and metadata artifacts to expected generated outputs",
    )
    parser.add_argument(
        "--print-diff",
        action="store_true",
        help="Print unified diffs when drift is detected",
    )
    args = parser.parse_args()

    plan_path = Path(args.ci_workflow_plan)
    workflow_path = Path(args.workflow_path)
    metadata_path = Path(args.metadata_path)

    try:
        expected_workflow_yaml, expected_metadata = build_expected_artifacts(
            plan_path=plan_path,
            workflow_path=workflow_path,
            workflow_name=args.workflow_name,
            python_version=args.python_version,
            artifact_prefix=args.artifact_prefix,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-sync-gate] {exc}", file=sys.stderr)
        return 2

    if args.write:
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(expected_workflow_yaml, encoding="utf-8")
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(expected_metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"workflow synced: {workflow_path}")
        print(f"metadata synced: {metadata_path}")

    try:
        drift = check_render_drift(
            expected_workflow_yaml=expected_workflow_yaml,
            expected_metadata=expected_metadata,
            workflow_path=workflow_path,
            metadata_path=metadata_path,
            strict_generated_at=args.strict_generated_at,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-sync-gate] {exc}", file=sys.stderr)
        return 2

    drift_count = int(drift["workflow_drift"]) + int(drift["metadata_drift"])
    print(
        "sync summary: "
        f"workflow_drift={drift['workflow_drift']} "
        f"metadata_drift={drift['metadata_drift']} "
        f"drift_count={drift_count}"
    )

    if drift["workflow_missing"]:
        print(f"missing workflow: {workflow_path}")
    if drift["metadata_missing"]:
        print(f"missing metadata: {metadata_path}")

    if args.print_diff:
        if drift["workflow_diff"]:
            print("workflow diff:")
            print(drift["workflow_diff"], end="")
        if drift["metadata_diff"]:
            print("metadata diff:")
            print(drift["metadata_diff"], end="")

    if drift["workflow_drift"] or drift["metadata_drift"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
