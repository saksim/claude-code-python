"""Phase 2 card P2-20 gate for Linux CI workflow command integrity.

This script validates command-level integrity for the P2-17 workflow plan:
1) command string <-> command_parts consistency,
2) expected script-target and required-flag contracts,
3) fan-out/fan-in path binding correctness.

It can optionally rewrite command strings to canonical shell-quoted form.
"""

from __future__ import annotations

import argparse
import copy
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
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{path}: field '{field}' must be non-empty string list")
    return list(value)


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _looks_like_python_executable(value: str) -> bool:
    name = Path(value).name.lower()
    return name.startswith("python")


def _extract_single_flag_value(parts: list[str], flag: str) -> str | None:
    for index in range(len(parts) - 1):
        if parts[index] == flag:
            return parts[index + 1]
    return None


def _extract_repeated_flag_values(parts: list[str], flag: str) -> list[str] | None:
    values: list[str] = []
    index = 0
    while index < len(parts):
        token = parts[index]
        if token != flag:
            index += 1
            continue
        if index + 1 >= len(parts):
            return None
        values.append(parts[index + 1])
        index += 2
    return values


def _add_issue(
    issues: list[dict[str, Any]],
    *,
    scope: str,
    code: str,
    message: str,
    index: int | None = None,
) -> None:
    issue: dict[str, Any] = {
        "scope": scope,
        "code": code,
        "message": message,
    }
    if index is not None:
        issue["index"] = index
    issues.append(issue)


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
    include_summary_paths: list[str] = []
    seen_indexes: set[int] = set()
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
            "command_parts",
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
        command_parts = _coerce_str_list(
            shard["command_parts"],
            field=f"fan_out_matrix.include[{index - 1}].command_parts",
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
            raise ValueError(
                f"{path}: fan_out_matrix.include[{index - 1}].total_tests must be >= 0"
            )
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
                "command_parts": command_parts,
            }
        )

    fan_in = payload["fan_in"]
    if not isinstance(fan_in, dict):
        raise ValueError(f"{path}: field 'fan_in' must be object")
    for required in (
        "summary_paths",
        "merged_summary_path",
        "aggregation_command",
        "aggregation_command_parts",
        "publish_command",
        "publish_command_parts",
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
    aggregation_command_parts = _coerce_str_list(
        fan_in["aggregation_command_parts"],
        field="fan_in.aggregation_command_parts",
        path=path,
    )
    publish_command = _coerce_str(
        fan_in["publish_command"],
        field="fan_in.publish_command",
        path=path,
    )
    publish_command_parts = _coerce_str_list(
        fan_in["publish_command_parts"],
        field="fan_in.publish_command_parts",
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

    normalized_fan_out_jobs: list[dict[str, Any]] | None = None
    if "fan_out_jobs" in payload:
        fan_out_jobs = payload["fan_out_jobs"]
        if not isinstance(fan_out_jobs, list):
            raise ValueError(f"{path}: field 'fan_out_jobs' must be list when present")
        if len(fan_out_jobs) != len(normalized_include):
            raise ValueError(
                f"{path}: fan_out_jobs count ({len(fan_out_jobs)}) "
                f"!= fan_out_matrix.include count ({len(normalized_include)})"
            )
        normalized_fan_out_jobs = []
        for index, job in enumerate(fan_out_jobs, start=1):
            if not isinstance(job, dict):
                raise ValueError(f"{path}: fan_out_jobs[{index - 1}] must be object")
            for required in (
                "job_id",
                "shard_index",
                "shard_total",
                "total_tests",
                "report_dir",
                "summary_path",
                "command",
                "command_parts",
            ):
                if required not in job:
                    raise ValueError(f"{path}: fan_out_jobs[{index - 1}] missing field '{required}'")
            normalized_fan_out_jobs.append(
                {
                    "job_id": _coerce_str(
                        job["job_id"],
                        field=f"fan_out_jobs[{index - 1}].job_id",
                        path=path,
                    ),
                    "shard_index": _coerce_int(
                        job["shard_index"],
                        field=f"fan_out_jobs[{index - 1}].shard_index",
                        path=path,
                    ),
                    "shard_total": _coerce_int(
                        job["shard_total"],
                        field=f"fan_out_jobs[{index - 1}].shard_total",
                        path=path,
                    ),
                    "total_tests": _coerce_int(
                        job["total_tests"],
                        field=f"fan_out_jobs[{index - 1}].total_tests",
                        path=path,
                    ),
                    "report_dir": _coerce_str(
                        job["report_dir"],
                        field=f"fan_out_jobs[{index - 1}].report_dir",
                        path=path,
                    ),
                    "summary_path": _coerce_str(
                        job["summary_path"],
                        field=f"fan_out_jobs[{index - 1}].summary_path",
                        path=path,
                    ),
                    "command": _coerce_str(
                        job["command"],
                        field=f"fan_out_jobs[{index - 1}].command",
                        path=path,
                    ),
                    "command_parts": _coerce_str_list(
                        job["command_parts"],
                        field=f"fan_out_jobs[{index - 1}].command_parts",
                        path=path,
                    ),
                }
            )

    return {
        "generated_at": payload.get("generated_at"),
        "source_ci_matrix": payload.get("source_ci_matrix"),
        "shard_total": shard_total,
        "manifest_total_tests": manifest_total_tests,
        "selected_shards": selected_shards,
        "skipped_empty_shards": bool(payload.get("skipped_empty_shards", False)),
        "fan_out_matrix": {"include": normalized_include},
        "fan_out_jobs": normalized_fan_out_jobs,
        "fan_in": {
            "summary_paths": summary_paths,
            "merged_summary_path": merged_summary_path,
            "aggregation_command": aggregation_command,
            "aggregation_command_parts": aggregation_command_parts,
            "publish_command": publish_command,
            "publish_command_parts": publish_command_parts,
            "final_report_json": final_report_json,
            "final_report_markdown": final_report_markdown,
        },
    }


def _validate_command_contract(
    *,
    scope: str,
    command: str,
    command_parts: list[str],
    expected_script: str,
    required_flags: list[str],
    issues: list[dict[str, Any]],
    index: int | None = None,
) -> str:
    try:
        parsed_parts = shlex.split(command, posix=True)
    except ValueError as exc:
        _add_issue(
            issues,
            scope=scope,
            index=index,
            code="invalid_shell_command",
            message=f"command parsing failed: {exc}",
        )
        parsed_parts = []

    if parsed_parts != command_parts:
        _add_issue(
            issues,
            scope=scope,
            index=index,
            code="command_parts_mismatch",
            message="command string does not match command_parts",
        )

    canonical_command = _format_shell_command(command_parts)
    if command != canonical_command:
        _add_issue(
            issues,
            scope=scope,
            index=index,
            code="non_canonical_command",
            message="command string is not canonical shell-quoted form",
        )

    if len(command_parts) < 2:
        _add_issue(
            issues,
            scope=scope,
            index=index,
            code="malformed_command_parts",
            message="command_parts must include python executable and script path",
        )
        return canonical_command

    if not _looks_like_python_executable(command_parts[0]):
        _add_issue(
            issues,
            scope=scope,
            index=index,
            code="unexpected_python_executable",
            message=f"command_parts[0] must point to python executable, got '{command_parts[0]}'",
        )
    if command_parts[1] != expected_script:
        _add_issue(
            issues,
            scope=scope,
            index=index,
            code="unexpected_script_target",
            message=f"expected '{expected_script}', got '{command_parts[1]}'",
        )

    for flag in required_flags:
        if flag not in command_parts:
            _add_issue(
                issues,
                scope=scope,
                index=index,
                code="missing_required_flag",
                message=f"required flag '{flag}' is missing in command_parts",
            )

    return canonical_command


def guard_ci_workflow_plan_commands(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized_plan = copy.deepcopy(plan)
    issues: list[dict[str, Any]] = []
    command_scopes: list[str] = []

    include = plan["fan_out_matrix"]["include"]
    normalized_include = normalized_plan["fan_out_matrix"]["include"]

    for index, shard in enumerate(include, start=1):
        scope = "fan_out"
        command_scopes.append(f"{scope}:{index}")
        canonical_command = _validate_command_contract(
            scope=scope,
            command=shard["command"],
            command_parts=list(shard["command_parts"]),
            expected_script="scripts/run_p2_linux_unified_execution_gate.py",
            required_flags=["--report-dir", "--shard-total", "--shard-index"],
            issues=issues,
            index=index,
        )
        normalized_include[index - 1]["command"] = canonical_command

        expected_report_dir = str(shard["report_dir"])
        expected_shard_total = str(shard["shard_total"])
        expected_shard_index = str(shard["shard_index"])
        report_dir_value = _extract_single_flag_value(shard["command_parts"], "--report-dir")
        shard_total_value = _extract_single_flag_value(shard["command_parts"], "--shard-total")
        shard_index_value = _extract_single_flag_value(shard["command_parts"], "--shard-index")

        if report_dir_value is not None and report_dir_value != expected_report_dir:
            _add_issue(
                issues,
                scope=scope,
                index=index,
                code="report_dir_mismatch",
                message=(
                    f"command '--report-dir' value '{report_dir_value}' "
                    f"!= shard report_dir '{expected_report_dir}'"
                ),
            )
        if shard_total_value is not None and shard_total_value != expected_shard_total:
            _add_issue(
                issues,
                scope=scope,
                index=index,
                code="shard_total_mismatch",
                message=(
                    f"command '--shard-total' value '{shard_total_value}' "
                    f"!= shard_total '{expected_shard_total}'"
                ),
            )
        if shard_index_value is not None and shard_index_value != expected_shard_index:
            _add_issue(
                issues,
                scope=scope,
                index=index,
                code="shard_index_mismatch",
                message=(
                    f"command '--shard-index' value '{shard_index_value}' "
                    f"!= shard_index '{expected_shard_index}'"
                ),
            )

    if normalized_plan["fan_out_jobs"] is not None:
        jobs = plan["fan_out_jobs"]
        normalized_jobs = normalized_plan["fan_out_jobs"]
        assert jobs is not None
        assert normalized_jobs is not None
        for index, job in enumerate(jobs, start=1):
            matrix_shard = include[index - 1]
            if (
                job["job_id"] != matrix_shard["job_id"]
                or job["shard_index"] != matrix_shard["shard_index"]
                or job["summary_path"] != matrix_shard["summary_path"]
            ):
                _add_issue(
                    issues,
                    scope="fan_out_jobs",
                    index=index,
                    code="fan_out_job_matrix_mismatch",
                    message="fan_out_jobs entry does not match fan_out_matrix.include at same index",
                )

            canonical_command = _validate_command_contract(
                scope="fan_out_jobs",
                command=job["command"],
                command_parts=list(job["command_parts"]),
                expected_script="scripts/run_p2_linux_unified_execution_gate.py",
                required_flags=["--report-dir", "--shard-total", "--shard-index"],
                issues=issues,
                index=index,
            )
            normalized_jobs[index - 1]["command"] = canonical_command
            command_scopes.append(f"fan_out_jobs:{index}")

    fan_in = plan["fan_in"]
    normalized_fan_in = normalized_plan["fan_in"]

    command_scopes.append("fan_in:aggregation")
    normalized_fan_in["aggregation_command"] = _validate_command_contract(
        scope="fan_in_aggregation",
        command=fan_in["aggregation_command"],
        command_parts=list(fan_in["aggregation_command_parts"]),
        expected_script="scripts/run_p2_linux_shard_aggregation_gate.py",
        required_flags=["--output", "--summary"],
        issues=issues,
    )
    command_scopes.append("fan_in:publish")
    normalized_fan_in["publish_command"] = _validate_command_contract(
        scope="fan_in_publish",
        command=fan_in["publish_command"],
        command_parts=list(fan_in["publish_command_parts"]),
        expected_script="scripts/run_p2_linux_report_publish_gate.py",
        required_flags=["--merged-summary", "--output-json", "--output-markdown"],
        issues=issues,
    )

    summary_values = _extract_repeated_flag_values(fan_in["aggregation_command_parts"], "--summary")
    if summary_values is None:
        _add_issue(
            issues,
            scope="fan_in_aggregation",
            code="malformed_summary_flags",
            message="aggregation_command_parts has '--summary' without value",
        )
    elif summary_values != fan_in["summary_paths"]:
        _add_issue(
            issues,
            scope="fan_in_aggregation",
            code="summary_paths_mismatch",
            message="aggregation '--summary' values must match fan_in.summary_paths order",
        )

    output_value = _extract_single_flag_value(fan_in["aggregation_command_parts"], "--output")
    if output_value is not None and output_value != fan_in["merged_summary_path"]:
        _add_issue(
            issues,
            scope="fan_in_aggregation",
            code="merged_summary_mismatch",
            message=(
                f"aggregation '--output' value '{output_value}' "
                f"!= merged_summary_path '{fan_in['merged_summary_path']}'"
            ),
        )

    merged_summary_value = _extract_single_flag_value(fan_in["publish_command_parts"], "--merged-summary")
    if merged_summary_value is not None and merged_summary_value != fan_in["merged_summary_path"]:
        _add_issue(
            issues,
            scope="fan_in_publish",
            code="publish_merged_summary_mismatch",
            message=(
                f"publish '--merged-summary' value '{merged_summary_value}' "
                f"!= merged_summary_path '{fan_in['merged_summary_path']}'"
            ),
        )
    output_json_value = _extract_single_flag_value(fan_in["publish_command_parts"], "--output-json")
    if output_json_value is not None and output_json_value != fan_in["final_report_json"]:
        _add_issue(
            issues,
            scope="fan_in_publish",
            code="publish_output_json_mismatch",
            message=(
                f"publish '--output-json' value '{output_json_value}' "
                f"!= final_report_json '{fan_in['final_report_json']}'"
            ),
        )
    output_markdown_value = _extract_single_flag_value(fan_in["publish_command_parts"], "--output-markdown")
    if output_markdown_value is not None and output_markdown_value != fan_in["final_report_markdown"]:
        _add_issue(
            issues,
            scope="fan_in_publish",
            code="publish_output_markdown_mismatch",
            message=(
                f"publish '--output-markdown' value '{output_markdown_value}' "
                f"!= final_report_markdown '{fan_in['final_report_markdown']}'"
            ),
        )

    failed_scopes = set()
    for issue in issues:
        issue_scope = str(issue["scope"])
        issue_index = issue.get("index")
        failed_scopes.add((issue_scope, issue_index))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "failed" if issues else "passed",
        "total_commands": len(command_scopes),
        "failed_commands": len(failed_scopes),
        "issues": issues,
    }
    return normalized_plan, report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Linux CI workflow plan command integrity contracts"
    )
    parser.add_argument(
        "--ci-workflow-plan",
        default=".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        help="P2-17 CI workflow plan JSON path",
    )
    parser.add_argument(
        "--output",
        default=".claude/reports/linux_unified_gate/ci_workflow_command_guard.json",
        help="Output guard report JSON path",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite workflow plan command strings to canonical shell-quoted form",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print guard report JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write guard report file",
    )
    args = parser.parse_args()

    plan_path = Path(args.ci_workflow_plan)
    try:
        plan = load_ci_workflow_plan(plan_path)
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-command-guard-gate] {exc}", file=sys.stderr)
        return 2

    normalized_plan, report = guard_ci_workflow_plan_commands(plan)
    report["source_ci_workflow_plan"] = str(plan_path)

    if args.write:
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(normalized_plan, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"workflow plan normalized: {plan_path}")

    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"command guard report: {output_path}")

    print(
        "command guard summary: "
        f"status={report['overall_status']} "
        f"failed_commands={report['failed_commands']} "
        f"total_commands={report['total_commands']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 1 if report["overall_status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
