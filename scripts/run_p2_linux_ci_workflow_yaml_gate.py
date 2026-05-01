"""Phase 2 card P2-18 gate for Linux CI workflow YAML rendering.

This script converts the P2-17 workflow-plan artifact into a GitHub Actions
workflow YAML so CI can consume fan-out/fan-in commands without manual edits.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def load_ci_workflow_plan(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: workflow plan file not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: workflow plan payload must be object")

    for field in ("shard_total", "manifest_total_tests", "selected_shards", "fan_out_matrix", "fan_in"):
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    shard_total = _coerce_int(payload["shard_total"], field="shard_total", path=path)
    manifest_total_tests = _coerce_int(
        payload["manifest_total_tests"],
        field="manifest_total_tests",
        path=path,
    )
    selected_shards = _coerce_int(payload["selected_shards"], field="selected_shards", path=path)

    if shard_total < 1:
        raise ValueError(f"{path}: shard_total must be >= 1")
    if manifest_total_tests < 0:
        raise ValueError(f"{path}: manifest_total_tests must be >= 0")
    if selected_shards < 0:
        raise ValueError(f"{path}: selected_shards must be >= 0")

    fan_out_matrix = payload["fan_out_matrix"]
    if not isinstance(fan_out_matrix, dict):
        raise ValueError(f"{path}: field 'fan_out_matrix' must be object")
    include = fan_out_matrix.get("include")
    if not isinstance(include, list):
        raise ValueError(f"{path}: field 'fan_out_matrix.include' must be list")

    normalized_include: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    include_summary_paths: list[str] = []
    include_total_tests = 0
    for index, shard in enumerate(include, start=1):
        if not isinstance(shard, dict):
            raise ValueError(f"{path}: fan_out_matrix.include[{index - 1}] must be object")

        for required in (
            "job_id",
            "shard_index",
            "shard_total",
            "total_tests",
            "report_dir",
            "summary_path",
            "command",
        ):
            if required not in shard:
                raise ValueError(
                    f"{path}: fan_out_matrix.include[{index - 1}] missing field '{required}'"
                )

        job_id = _coerce_str(
            shard["job_id"],
            field=f"fan_out_matrix.include[{index - 1}].job_id",
            path=path,
        )
        shard_index = _coerce_int(
            shard["shard_index"],
            field=f"fan_out_matrix.include[{index - 1}].shard_index",
            path=path,
        )
        nested_total = _coerce_int(
            shard["shard_total"],
            field=f"fan_out_matrix.include[{index - 1}].shard_total",
            path=path,
        )
        total_tests = _coerce_int(
            shard["total_tests"],
            field=f"fan_out_matrix.include[{index - 1}].total_tests",
            path=path,
        )
        report_dir = _coerce_str(
            shard["report_dir"],
            field=f"fan_out_matrix.include[{index - 1}].report_dir",
            path=path,
        )
        summary_path = _coerce_str(
            shard["summary_path"],
            field=f"fan_out_matrix.include[{index - 1}].summary_path",
            path=path,
        )
        command = _coerce_str(
            shard["command"],
            field=f"fan_out_matrix.include[{index - 1}].command",
            path=path,
        )

        if shard_index < 1 or shard_index > shard_total:
            raise ValueError(f"{path}: fan_out_matrix.include[{index - 1}].shard_index out of range")
        if nested_total != shard_total:
            raise ValueError(
                f"{path}: fan_out_matrix.include[{index - 1}].shard_total ({nested_total}) "
                f"!= top-level shard_total ({shard_total})"
            )
        if total_tests < 0:
            raise ValueError(f"{path}: fan_out_matrix.include[{index - 1}].total_tests must be >= 0")
        if shard_index in seen_indexes:
            raise ValueError(f"{path}: duplicate shard_index {shard_index} in fan_out_matrix.include")

        seen_indexes.add(shard_index)
        include_total_tests += total_tests
        include_summary_paths.append(summary_path)
        normalized_include.append(
            {
                "job_id": job_id,
                "shard_index": shard_index,
                "shard_total": nested_total,
                "total_tests": total_tests,
                "report_dir": report_dir,
                "summary_path": summary_path,
                "command": command,
            }
        )

    fan_in = payload["fan_in"]
    if not isinstance(fan_in, dict):
        raise ValueError(f"{path}: field 'fan_in' must be object")
    for required in (
        "summary_paths",
        "merged_summary_path",
        "aggregation_command",
        "publish_command",
        "final_report_json",
        "final_report_markdown",
    ):
        if required not in fan_in:
            raise ValueError(f"{path}: fan_in missing field '{required}'")

    summary_paths = _coerce_str_list(fan_in["summary_paths"], field="fan_in.summary_paths", path=path)
    merged_summary_path = _coerce_str(
        fan_in["merged_summary_path"],
        field="fan_in.merged_summary_path",
        path=path,
    )
    aggregation_command = _coerce_str(
        fan_in["aggregation_command"],
        field="fan_in.aggregation_command",
        path=path,
    )
    publish_command = _coerce_str(
        fan_in["publish_command"],
        field="fan_in.publish_command",
        path=path,
    )
    final_report_json = _coerce_str(
        fan_in["final_report_json"],
        field="fan_in.final_report_json",
        path=path,
    )
    final_report_markdown = _coerce_str(
        fan_in["final_report_markdown"],
        field="fan_in.final_report_markdown",
        path=path,
    )

    if selected_shards != len(normalized_include):
        raise ValueError(
            f"{path}: selected_shards ({selected_shards}) "
            f"!= fan_out_matrix.include count ({len(normalized_include)})"
        )
    if summary_paths != include_summary_paths:
        raise ValueError(
            f"{path}: fan_in.summary_paths must match fan_out_matrix.include[*].summary_path order"
        )
    if include_total_tests > manifest_total_tests:
        raise ValueError(
            f"{path}: fan_out_matrix.include total_tests ({include_total_tests}) "
            f"exceeds manifest_total_tests ({manifest_total_tests})"
        )

    return {
        "generated_at": payload.get("generated_at"),
        "source_ci_matrix": payload.get("source_ci_matrix"),
        "shard_total": shard_total,
        "manifest_total_tests": manifest_total_tests,
        "selected_shards": selected_shards,
        "skipped_empty_shards": bool(payload.get("skipped_empty_shards", False)),
        "fan_out_matrix": {"include": normalized_include},
        "fan_in": {
            "summary_paths": summary_paths,
            "merged_summary_path": merged_summary_path,
            "aggregation_command": aggregation_command,
            "publish_command": publish_command,
            "final_report_json": final_report_json,
            "final_report_markdown": final_report_markdown,
        },
    }


def build_ci_workflow_yaml(
    plan: dict[str, Any],
    *,
    workflow_name: str,
    python_version: str,
    artifact_prefix: str,
) -> str:
    include = plan["fan_out_matrix"]["include"]
    fan_in = plan["fan_in"]

    lines: list[str] = [
        "# Generated by scripts/run_p2_linux_ci_workflow_yaml_gate.py (P2-18).",
        f"name: {_yaml_scalar(workflow_name)}",
        "on:",
        "  workflow_dispatch:",
        "  pull_request:",
        "    branches:",
        "      - main",
        "jobs:",
        "  linux_fan_out:",
        '    name: "Linux Fan-out / shard ${{ matrix.shard_index }}"',
        "    runs-on: ubuntu-latest",
        "    strategy:",
        "      fail-fast: false",
        "      matrix:",
        "        include:",
    ]

    for shard in include:
        lines.extend(
            [
                f"          - job_id: {_yaml_scalar(shard['job_id'])}",
                f"            shard_index: {_yaml_scalar(shard['shard_index'])}",
                f"            shard_total: {_yaml_scalar(shard['shard_total'])}",
                f"            total_tests: {_yaml_scalar(shard['total_tests'])}",
                f"            report_dir: {_yaml_scalar(shard['report_dir'])}",
                f"            summary_path: {_yaml_scalar(shard['summary_path'])}",
                f"            command: {_yaml_scalar(shard['command'])}",
            ]
        )

    lines.extend(
        [
            "    steps:",
            "      - name: Checkout",
            "        uses: actions/checkout@v4",
            "      - name: Setup Python",
            "        uses: actions/setup-python@v5",
            "        with:",
            f"          python-version: {_yaml_scalar(python_version)}",
            "      - name: Install Dependencies",
            "        run: python -m pip install -r requirements.txt",
            "      - name: Run Linux Unified Gate Shard",
            "        run: ${{ matrix.command }}",
            "      - name: Upload Shard Summary",
            "        uses: actions/upload-artifact@v4",
            "        with:",
            f'          name: "{artifact_prefix}-${{{{ matrix.shard_index }}}}"',
            "          path: ${{ matrix.summary_path }}",
            "          if-no-files-found: error",
            "  linux_fan_in:",
            "    name: Linux Fan-in",
            "    runs-on: ubuntu-latest",
            "    needs: linux_fan_out",
            "    if: ${{ always() }}",
            "    steps:",
            "      - name: Checkout",
            "        uses: actions/checkout@v4",
            "      - name: Setup Python",
            "        uses: actions/setup-python@v5",
            "        with:",
            f"          python-version: {_yaml_scalar(python_version)}",
            "      - name: Install Dependencies",
            "        run: python -m pip install -r requirements.txt",
            "      - name: Download Shard Summaries",
            "        uses: actions/download-artifact@v4",
            "        with:",
            f"          pattern: {_yaml_scalar(f'{artifact_prefix}-*')}",
            "          path: .",
            "          merge-multiple: true",
            "      - name: Aggregate Shard Summaries",
            f"        run: {_yaml_scalar(fan_in['aggregation_command'])}",
            "      - name: Publish Final Linux Report",
            f"        run: {_yaml_scalar(fan_in['publish_command'])}",
            "      - name: Upload Final Linux Report",
            "        uses: actions/upload-artifact@v4",
            "        with:",
            '          name: "linux-unified-final-report"',
            "          path: |",
            f"            {fan_in['merged_summary_path']}",
            f"            {fan_in['final_report_json']}",
            f"            {fan_in['final_report_markdown']}",
            "          if-no-files-found: error",
        ]
    )
    return "\n".join(lines) + "\n"


def build_render_metadata(
    plan: dict[str, Any],
    *,
    source_plan_path: Path,
    workflow_output_path: Path,
    artifact_prefix: str,
) -> dict[str, Any]:
    fan_in = plan["fan_in"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_ci_workflow_plan": str(source_plan_path),
        "workflow_output_path": str(workflow_output_path),
        "workflow_name": "Linux Unified Gate",
        "shard_total": int(plan["shard_total"]),
        "manifest_total_tests": int(plan["manifest_total_tests"]),
        "selected_shards": int(plan["selected_shards"]),
        "artifact_prefix": artifact_prefix,
        "fan_in": {
            "summary_paths": list(fan_in["summary_paths"]),
            "merged_summary_path": str(fan_in["merged_summary_path"]),
            "aggregation_command": str(fan_in["aggregation_command"]),
            "publish_command": str(fan_in["publish_command"]),
            "final_report_json": str(fan_in["final_report_json"]),
            "final_report_markdown": str(fan_in["final_report_markdown"]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render GitHub Actions workflow from P2 Linux CI workflow plan"
    )
    parser.add_argument(
        "--ci-workflow-plan",
        default=".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        help="P2-17 CI workflow plan JSON path",
    )
    parser.add_argument(
        "--output-workflow",
        default=".github/workflows/linux_unified_gate.yml",
        help="Rendered GitHub Actions workflow YAML path",
    )
    parser.add_argument(
        "--output-metadata",
        default=".claude/reports/linux_unified_gate/ci_workflow_render.json",
        help="Rendered workflow metadata JSON path",
    )
    parser.add_argument(
        "--workflow-name",
        default="Linux Unified Gate",
        help="Workflow display name",
    )
    parser.add_argument(
        "--python-version",
        default="3.11",
        help="Python version in rendered workflow setup step",
    )
    parser.add_argument(
        "--artifact-prefix",
        default="linux-unified-summary",
        help="Artifact prefix for fan-out shard summary upload/download",
    )
    parser.add_argument(
        "--print-yaml",
        action="store_true",
        help="Print rendered workflow YAML",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files; only validate and print summary",
    )
    args = parser.parse_args()

    source_path = Path(args.ci_workflow_plan)
    workflow_output_path = Path(args.output_workflow)
    metadata_output_path = Path(args.output_metadata)

    try:
        plan = load_ci_workflow_plan(source_path)
        workflow_yaml = build_ci_workflow_yaml(
            plan,
            workflow_name=args.workflow_name,
            python_version=args.python_version,
            artifact_prefix=args.artifact_prefix,
        )
        metadata = build_render_metadata(
            plan,
            source_plan_path=source_path.resolve(),
            workflow_output_path=workflow_output_path,
            artifact_prefix=args.artifact_prefix,
        )
        metadata["workflow_name"] = args.workflow_name
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-yaml-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        workflow_output_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_output_path.write_text(workflow_yaml, encoding="utf-8")
        metadata_output_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_output_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"workflow yaml: {workflow_output_path}")
        print(f"workflow metadata: {metadata_output_path}")

    print(
        "workflow render summary: "
        f"{metadata['selected_shards']} shard job(s), "
        f"manifest_total_tests={metadata['manifest_total_tests']}"
    )
    if args.print_yaml or args.dry_run:
        print(workflow_yaml, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
