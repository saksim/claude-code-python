"""Phase 2 card P2-17 gate for Linux CI workflow plan generation.

This script converts the P2-16 CI matrix artifact into a workflow-level plan
that Linux CI can consume directly:
1) fan-out shard job descriptors,
2) fan-in aggregation command,
3) fan-in final publish command.
"""

from __future__ import annotations

import argparse
import json
import shlex
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
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: field '{field}' must be string list")
    return list(value)


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def load_ci_matrix(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: ci matrix file not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: ci matrix payload must be object")

    required_fields = (
        "shard_total",
        "manifest_total_tests",
        "selected_shards",
        "matrix",
        "summary_paths",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    shard_total = _coerce_int(payload["shard_total"], field="shard_total", path=path)
    manifest_total_tests = _coerce_int(
        payload["manifest_total_tests"],
        field="manifest_total_tests",
        path=path,
    )
    selected_shards = _coerce_int(
        payload["selected_shards"],
        field="selected_shards",
        path=path,
    )
    if shard_total < 1:
        raise ValueError(f"{path}: shard_total must be >= 1")
    if manifest_total_tests < 0:
        raise ValueError(f"{path}: manifest_total_tests must be >= 0")
    if selected_shards < 0:
        raise ValueError(f"{path}: selected_shards must be >= 0")

    skipped_empty_shards = payload.get("skipped_empty_shards", False)
    if not isinstance(skipped_empty_shards, bool):
        raise ValueError(f"{path}: field 'skipped_empty_shards' must be bool")

    matrix = payload["matrix"]
    if not isinstance(matrix, dict):
        raise ValueError(f"{path}: field 'matrix' must be object")
    include = matrix.get("include")
    if not isinstance(include, list):
        raise ValueError(f"{path}: field 'matrix.include' must be list")

    summary_paths = _coerce_str_list(
        payload["summary_paths"],
        field="summary_paths",
        path=path,
    )

    normalized_include: list[dict[str, Any]] = []
    include_summary_paths: list[str] = []
    seen_indexes: set[int] = set()
    include_total_tests = 0
    for index, shard in enumerate(include, start=1):
        if not isinstance(shard, dict):
            raise ValueError(f"{path}: matrix.include[{index - 1}] must be object")

        for required in (
            "shard_index",
            "shard_total",
            "total_tests",
            "report_dir",
            "summary_path",
            "command",
            "command_parts",
        ):
            if required not in shard:
                raise ValueError(f"{path}: matrix.include[{index - 1}] missing field '{required}'")

        shard_index = _coerce_int(
            shard["shard_index"],
            field=f"matrix.include[{index - 1}].shard_index",
            path=path,
        )
        nested_total = _coerce_int(
            shard["shard_total"],
            field=f"matrix.include[{index - 1}].shard_total",
            path=path,
        )
        total_tests = _coerce_int(
            shard["total_tests"],
            field=f"matrix.include[{index - 1}].total_tests",
            path=path,
        )
        report_dir = _coerce_str(
            shard["report_dir"],
            field=f"matrix.include[{index - 1}].report_dir",
            path=path,
        )
        summary_path = _coerce_str(
            shard["summary_path"],
            field=f"matrix.include[{index - 1}].summary_path",
            path=path,
        )
        command = _coerce_str(
            shard["command"],
            field=f"matrix.include[{index - 1}].command",
            path=path,
        )
        command_parts = _coerce_str_list(
            shard["command_parts"],
            field=f"matrix.include[{index - 1}].command_parts",
            path=path,
        )
        if shard_index < 1 or shard_index > shard_total:
            raise ValueError(f"{path}: matrix.include[{index - 1}].shard_index out of range")
        if nested_total != shard_total:
            raise ValueError(
                f"{path}: matrix.include[{index - 1}].shard_total ({nested_total}) "
                f"!= top-level shard_total ({shard_total})"
            )
        if shard_index in seen_indexes:
            raise ValueError(f"{path}: duplicate shard_index {shard_index} in matrix.include")
        if total_tests < 0:
            raise ValueError(f"{path}: matrix.include[{index - 1}].total_tests must be >= 0")

        seen_indexes.add(shard_index)
        include_total_tests += total_tests
        include_summary_paths.append(summary_path)
        normalized_include.append(
            {
                "shard_index": shard_index,
                "shard_total": nested_total,
                "total_tests": total_tests,
                "report_dir": report_dir,
                "summary_path": summary_path,
                "command": command,
                "command_parts": command_parts,
            }
        )

    if selected_shards != len(normalized_include):
        raise ValueError(
            f"{path}: selected_shards ({selected_shards}) "
            f"!= matrix.include count ({len(normalized_include)})"
        )
    if summary_paths != include_summary_paths:
        raise ValueError(f"{path}: summary_paths must match matrix.include[*].summary_path order")
    if include_total_tests > manifest_total_tests:
        raise ValueError(
            f"{path}: matrix.include total_tests ({include_total_tests}) "
            f"exceeds manifest_total_tests ({manifest_total_tests})"
        )
    if not skipped_empty_shards and include_total_tests != manifest_total_tests:
        raise ValueError(
            f"{path}: matrix.include total_tests ({include_total_tests}) "
            f"must equal manifest_total_tests ({manifest_total_tests}) when skipped_empty_shards is false"
        )

    return {
        "generated_at": payload.get("generated_at"),
        "source_shard_plan": payload.get("source_shard_plan"),
        "shard_total": shard_total,
        "manifest_total_tests": manifest_total_tests,
        "selected_shards": selected_shards,
        "skipped_empty_shards": skipped_empty_shards,
        "matrix": {"include": normalized_include},
        "summary_paths": summary_paths,
    }


def build_ci_workflow_plan_payload(
    ci_matrix: dict[str, Any],
    *,
    source_path: Path,
    python_executable: str,
    merged_summary_output: Path,
    final_report_json: Path,
    final_report_markdown: Path,
) -> dict[str, Any]:
    fan_out_jobs: list[dict[str, Any]] = []
    for shard in ci_matrix["matrix"]["include"]:
        shard_index = int(shard["shard_index"])
        fan_out_jobs.append(
            {
                "job_id": f"linux-shard-{shard_index}",
                "shard_index": shard_index,
                "shard_total": int(shard["shard_total"]),
                "total_tests": int(shard["total_tests"]),
                "report_dir": str(shard["report_dir"]),
                "summary_path": str(shard["summary_path"]),
                "command": str(shard["command"]),
                "command_parts": list(shard["command_parts"]),
            }
        )

    summary_paths = [str(path) for path in ci_matrix["summary_paths"]]
    aggregation_command_parts = [
        python_executable,
        "scripts/run_p2_linux_shard_aggregation_gate.py",
        "--output",
        str(merged_summary_output),
    ]
    for summary_path in summary_paths:
        aggregation_command_parts.extend(["--summary", summary_path])

    publish_command_parts = [
        python_executable,
        "scripts/run_p2_linux_report_publish_gate.py",
        "--merged-summary",
        str(merged_summary_output),
        "--output-json",
        str(final_report_json),
        "--output-markdown",
        str(final_report_markdown),
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_ci_matrix": str(source_path),
        "shard_total": int(ci_matrix["shard_total"]),
        "manifest_total_tests": int(ci_matrix["manifest_total_tests"]),
        "selected_shards": int(ci_matrix["selected_shards"]),
        "skipped_empty_shards": bool(ci_matrix["skipped_empty_shards"]),
        "fan_out_matrix": {
            "include": fan_out_jobs,
        },
        "fan_out_jobs": fan_out_jobs,
        "fan_in": {
            "summary_paths": summary_paths,
            "merged_summary_path": str(merged_summary_output),
            "aggregation_command": _format_shell_command(aggregation_command_parts),
            "aggregation_command_parts": aggregation_command_parts,
            "final_report_json": str(final_report_json),
            "final_report_markdown": str(final_report_markdown),
            "publish_command": _format_shell_command(publish_command_parts),
            "publish_command_parts": publish_command_parts,
        },
    }


def build_github_output_values(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "fan_out_matrix": json.dumps(payload["fan_out_matrix"], ensure_ascii=False, separators=(",", ":")),
        "fan_in_summary_paths": json.dumps(
            payload["fan_in"]["summary_paths"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "aggregation_command": str(payload["fan_in"]["aggregation_command"]),
        "publish_command": str(payload["fan_in"]["publish_command"]),
        "selected_shards": str(payload["selected_shards"]),
        "manifest_total_tests": str(payload["manifest_total_tests"]),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Linux CI workflow plan from P2 CI matrix artifact"
    )
    parser.add_argument(
        "--ci-matrix",
        default=".claude/reports/linux_unified_gate/ci_matrix.json",
        help="CI matrix JSON produced by run_p2_linux_ci_matrix_gate.py",
    )
    parser.add_argument(
        "--output",
        default=".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        help="Output CI workflow plan JSON path",
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable used when generating fan-in commands",
    )
    parser.add_argument(
        "--merged-summary-output",
        default=".claude/reports/linux_unified_gate/merged_summary.json",
        help="Merged summary path consumed by aggregation/publish stages",
    )
    parser.add_argument(
        "--final-report-json",
        default=".claude/reports/linux_unified_gate/final_report.json",
        help="Final report JSON path used in publish stage command",
    )
    parser.add_argument(
        "--final-report-markdown",
        default=".claude/reports/linux_unified_gate/final_report.md",
        help="Final report markdown path used in publish stage command",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-plan",
        action="store_true",
        help="Print generated CI workflow plan JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and print summary without writing output file",
    )
    args = parser.parse_args()

    ci_matrix_path = Path(args.ci_matrix)
    try:
        ci_matrix = load_ci_matrix(ci_matrix_path)
        payload = build_ci_workflow_plan_payload(
            ci_matrix,
            source_path=ci_matrix_path.resolve(),
            python_executable=args.python_executable,
            merged_summary_output=Path(args.merged_summary_output),
            final_report_json=Path(args.final_report_json),
            final_report_markdown=Path(args.final_report_markdown),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-plan-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"ci workflow plan: {output_path}")

    if args.github_output:
        write_github_output(Path(args.github_output), build_github_output_values(payload))
        print(f"github output: {args.github_output}")

    print(
        "workflow plan summary: "
        f"{payload['selected_shards']} fan-out shard job(s), "
        f"manifest_total_tests={payload['manifest_total_tests']}"
    )
    if args.print_plan or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
