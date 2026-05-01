"""Phase 2 card P2-14 gate for Linux unified pipeline orchestration.

This script composes the Linux validation chain end-to-end:
1) run unified execution gate (P2-09/P2-11),
2) aggregate shard summaries (P2-12),
3) publish final report artifacts (P2-13).
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _format_shell_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _execution_summary_path(report_dir: Path) -> Path:
    return report_dir / "summary.json"


def build_execution_command(
    *,
    python_executable: str,
    report_dir: Path,
    shard_total: int,
    shard_index: int,
    continue_on_failure: bool,
    pytest_args: Sequence[str] | None,
) -> list[str]:
    command = [
        python_executable,
        "scripts/run_p2_linux_unified_execution_gate.py",
        "--report-dir",
        str(report_dir),
        "--shard-total",
        str(shard_total),
        "--shard-index",
        str(shard_index),
    ]
    if continue_on_failure:
        command.append("--continue-on-failure")
    if pytest_args:
        command.extend(["--", *pytest_args])
    return command


def build_aggregation_command(
    *,
    python_executable: str,
    summary_paths: Sequence[str],
    summary_globs: Sequence[str],
    artifacts_dir: str | None,
    output_path: Path,
) -> list[str]:
    command = [
        python_executable,
        "scripts/run_p2_linux_shard_aggregation_gate.py",
        "--output",
        str(output_path),
    ]
    for path in summary_paths:
        command.extend(["--summary", path])
    for pattern in summary_globs:
        command.extend(["--summary-glob", pattern])
    if artifacts_dir:
        command.extend(["--artifacts-dir", artifacts_dir])
    return command


def build_publish_command(
    *,
    python_executable: str,
    merged_summary: Path,
    output_json: Path,
    output_markdown: Path,
) -> list[str]:
    return [
        python_executable,
        "scripts/run_p2_linux_report_publish_gate.py",
        "--merged-summary",
        str(merged_summary),
        "--output-json",
        str(output_json),
        "--output-markdown",
        str(output_markdown),
    ]


def build_pipeline_commands(
    *,
    python_executable: str,
    execution_report_dir: Path,
    shard_total: int,
    shard_index: int,
    continue_on_failure: bool,
    skip_execution: bool,
    skip_aggregation: bool,
    skip_publish: bool,
    summary_paths: Sequence[str],
    summary_globs: Sequence[str],
    artifacts_dir: str | None,
    merged_summary_output: Path,
    final_report_json: Path,
    final_report_markdown: Path,
    pytest_args: Sequence[str] | None,
) -> list[tuple[str, list[str]]]:
    pipeline: list[tuple[str, list[str]]] = []

    if not skip_execution:
        pipeline.append(
            (
                "execution",
                build_execution_command(
                    python_executable=python_executable,
                    report_dir=execution_report_dir,
                    shard_total=shard_total,
                    shard_index=shard_index,
                    continue_on_failure=continue_on_failure,
                    pytest_args=pytest_args,
                ),
            )
        )

    if not skip_aggregation:
        aggregation_summaries = list(summary_paths)
        if not skip_execution:
            aggregation_summaries.append(str(_execution_summary_path(execution_report_dir)))
        pipeline.append(
            (
                "aggregation",
                build_aggregation_command(
                    python_executable=python_executable,
                    summary_paths=aggregation_summaries,
                    summary_globs=summary_globs,
                    artifacts_dir=artifacts_dir,
                    output_path=merged_summary_output,
                ),
            )
        )

    if not skip_publish:
        pipeline.append(
            (
                "publish",
                build_publish_command(
                    python_executable=python_executable,
                    merged_summary=merged_summary_output,
                    output_json=final_report_json,
                    output_markdown=final_report_markdown,
                ),
            )
        )

    return pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Linux unified validation pipeline: execution -> aggregation -> publish"
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable to use for all sub-commands (default: current interpreter)",
    )
    parser.add_argument(
        "--execution-report-dir",
        default=".claude/reports/linux_unified_gate",
        help="Report dir passed to execution gate (writes summary.json + junit XMLs)",
    )
    parser.add_argument(
        "--shard-total",
        type=int,
        default=1,
        help="Total shard count forwarded to execution gate (default: 1)",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        default=1,
        help="1-based shard index forwarded to execution gate (default: 1)",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Forward continue-on-failure flag to execution gate",
    )
    parser.add_argument(
        "--summary",
        action="append",
        default=[],
        help="Additional summary.json path for aggregation (repeatable)",
    )
    parser.add_argument(
        "--summary-glob",
        action="append",
        default=[],
        help="Additional summary glob for aggregation (repeatable)",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=None,
        help="Directory recursively scanned for summary.json by aggregation gate",
    )
    parser.add_argument(
        "--merged-summary-output",
        default=".claude/reports/linux_unified_gate/merged_summary.json",
        help="Merged summary output path for aggregation stage",
    )
    parser.add_argument(
        "--final-report-json",
        default=".claude/reports/linux_unified_gate/final_report.json",
        help="Final JSON report path for publish stage",
    )
    parser.add_argument(
        "--final-report-markdown",
        default=".claude/reports/linux_unified_gate/final_report.md",
        help="Final Markdown report path for publish stage",
    )
    parser.add_argument(
        "--skip-execution",
        action="store_true",
        help="Skip execution stage (expect existing summaries from external jobs)",
    )
    parser.add_argument(
        "--skip-aggregation",
        action="store_true",
        help="Skip aggregation stage (expect existing merged summary)",
    )
    parser.add_argument(
        "--skip-publish",
        action="store_true",
        help="Skip publish stage",
    )
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="Print planned commands and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Alias of --print-commands",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at first non-zero stage exit code (default keeps running remaining stages)",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra args forwarded to execution gate pytest invocations after '--'",
    )
    args = parser.parse_args()

    forwarded_args = list(args.pytest_args)
    if forwarded_args and forwarded_args[0] == "--":
        forwarded_args = forwarded_args[1:]

    pipeline = build_pipeline_commands(
        python_executable=args.python_executable,
        execution_report_dir=Path(args.execution_report_dir),
        shard_total=args.shard_total,
        shard_index=args.shard_index,
        continue_on_failure=args.continue_on_failure,
        skip_execution=args.skip_execution,
        skip_aggregation=args.skip_aggregation,
        skip_publish=args.skip_publish,
        summary_paths=args.summary,
        summary_globs=args.summary_glob,
        artifacts_dir=args.artifacts_dir,
        merged_summary_output=Path(args.merged_summary_output),
        final_report_json=Path(args.final_report_json),
        final_report_markdown=Path(args.final_report_markdown),
        pytest_args=forwarded_args,
    )
    if not pipeline:
        print("[p2-linux-unified-pipeline-gate] no stages selected")
        return 0

    if args.print_commands or args.dry_run:
        for index, (stage, command) in enumerate(pipeline, start=1):
            print(f"{index}. [{stage}] {_format_shell_command(command)}")
        if args.dry_run or args.print_commands:
            return 0

    project_root = Path(__file__).resolve().parents[1]
    overall_exit = 0
    for index, (stage, command) in enumerate(pipeline, start=1):
        print(f"[{index}/{len(pipeline)}] stage={stage} {_format_shell_command(command)}")
        exit_code = subprocess.call(command, cwd=project_root)
        if exit_code != 0:
            if overall_exit == 0:
                overall_exit = exit_code
            if args.fail_fast:
                return exit_code
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
