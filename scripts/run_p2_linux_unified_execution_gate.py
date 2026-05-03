"""Phase 2 card P2-09 execution gate for Linux unified validation.

This script is intended for Linux stage execution. It can:
1) validate unified manifest integrity,
2) print or dry-run generated pytest commands,
3) execute curated test files sequentially and emit junit + json reports.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


def _load_unified_gate_module():
    script_path = Path(__file__).resolve().with_name("run_linux_unified_gate.py")
    spec = importlib.util.spec_from_file_location("linux_unified_gate_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_manifest(test_files: Sequence[str]) -> list[str]:
    missing: list[str] = []
    for test_file in test_files:
        if not Path(test_file).is_file():
            missing.append(test_file)
    return missing


def _format_shell_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _junit_report_path(report_dir: Path, test_file: str) -> Path:
    stem = Path(test_file).stem
    return report_dir / f"{stem}.xml"


def build_gate_commands(
    *,
    python_executable: str,
    test_files: Sequence[str],
    report_dir: Path,
    extra_pytest_args: Sequence[str] | None = None,
) -> list[list[str]]:
    commands: list[list[str]] = []
    for test_file in test_files:
        junit_path = _junit_report_path(report_dir, test_file)
        command = [
            python_executable,
            "-m",
            "pytest",
            "-q",
            "-c",
            "pytest.ini",
            test_file,
            "--junitxml",
            str(junit_path),
        ]
        if extra_pytest_args:
            command.extend(extra_pytest_args)
        commands.append(command)
    return commands


def select_shard_test_files(
    test_files: Sequence[str],
    *,
    shard_total: int,
    shard_index: int,
) -> list[str]:
    if shard_total < 1:
        raise ValueError("shard_total must be >= 1")
    if shard_index < 1 or shard_index > shard_total:
        raise ValueError("shard_index must be within [1, shard_total]")
    if shard_total == 1:
        return list(test_files)
    selected: list[str] = []
    target_mod = shard_index - 1
    for index, test_file in enumerate(test_files):
        if index % shard_total == target_mod:
            selected.append(test_file)
    return selected


def _build_result_payload(
    *,
    python_executable: str,
    report_dir: Path,
    manifest_test_files: Sequence[str],
    selected_test_files: Sequence[str],
    shard_total: int,
    shard_index: int,
    commands: Sequence[Sequence[str]],
    per_test_status: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    failed = sum(1 for item in per_test_status if item["exit_code"] != 0)
    passed = len(per_test_status) - failed
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_executable": python_executable,
        "report_dir": str(report_dir),
        "shard_total": shard_total,
        "shard_index": shard_index,
        "manifest_total_tests": len(manifest_test_files),
        "total_tests": len(selected_test_files),
        "passed": passed,
        "failed": failed,
        "test_files": list(selected_test_files),
        "commands": [_format_shell_command(command) for command in commands],
        "results": list(per_test_status),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute Linux unified gate manifest for Phase 0-2 regression chain"
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable to use (default: current interpreter)",
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List unified gate test files and exit",
    )
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="Print generated per-test pytest commands and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate manifest and print generated commands without executing tests",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Continue executing remaining tests after a test command fails",
    )
    parser.add_argument(
        "--report-dir",
        default=".claude/reports/linux_unified_gate",
        help="Directory for junit xml + summary json output",
    )
    parser.add_argument(
        "--shard-total",
        type=int,
        default=1,
        help="Total number of shards for parallel Linux execution (default: 1)",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        default=1,
        help="1-based shard index for this job (default: 1)",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra args forwarded to every pytest invocation after '--'",
    )
    args = parser.parse_args()

    unified_gate = _load_unified_gate_module()
    test_files: tuple[str, ...] = tuple(unified_gate.LINUX_UNIFIED_TEST_FILES)

    if args.list_tests:
        for test_file in test_files:
            print(test_file)
        return 0

    missing = _validate_manifest(test_files)
    if missing:
        for path in missing:
            print(f"[p2-linux-unified-execution-gate] missing test file: {path}", file=sys.stderr)
        return 2

    try:
        selected_test_files = select_shard_test_files(
            test_files,
            shard_total=args.shard_total,
            shard_index=args.shard_index,
        )
    except ValueError as exc:
        print(f"[p2-linux-unified-execution-gate] {exc}", file=sys.stderr)
        return 2

    forwarded_args = list(args.pytest_args)
    if forwarded_args and forwarded_args[0] == "--":
        forwarded_args = forwarded_args[1:]

    report_dir = Path(args.report_dir)
    commands = build_gate_commands(
        python_executable=args.python_executable,
        test_files=selected_test_files,
        report_dir=report_dir,
        extra_pytest_args=forwarded_args,
    )

    if args.print_commands or args.dry_run:
        print(
            (
                f"# shard {args.shard_index}/{args.shard_total} "
                f"(tests: {len(selected_test_files)}/{len(test_files)})"
            )
        )
        for idx, command in enumerate(commands, start=1):
            print(f"{idx}. {_format_shell_command(command)}")
        if args.print_commands and not args.dry_run:
            return 0
    if args.dry_run:
        return 0

    report_dir.mkdir(parents=True, exist_ok=True)
    project_root = Path(__file__).resolve().parents[1]
    if not selected_test_files:
        payload = _build_result_payload(
            python_executable=args.python_executable,
            report_dir=report_dir,
            manifest_test_files=test_files,
            selected_test_files=selected_test_files,
            shard_total=args.shard_total,
            shard_index=args.shard_index,
            commands=commands,
            per_test_status=[],
        )
        summary_path = report_dir / "summary.json"
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("no tests selected for this shard")
        print(f"summary: {summary_path}")
        return 0

    per_test_status: list[dict[str, Any]] = []
    overall_exit = 0
    for index, (test_file, command) in enumerate(zip(selected_test_files, commands), start=1):
        print(f"[{index}/{len(commands)}] {_format_shell_command(command)}")
        exit_code = subprocess.call(command, cwd=project_root)
        per_test_status.append(
            {
                "test_file": test_file,
                "exit_code": exit_code,
                "junit_xml": str(_junit_report_path(report_dir, test_file)),
            }
        )
        if exit_code != 0:
            overall_exit = 1
            if not args.continue_on_failure:
                break

    payload = _build_result_payload(
        python_executable=args.python_executable,
        report_dir=report_dir,
        manifest_test_files=test_files,
        selected_test_files=selected_test_files,
        shard_total=args.shard_total,
        shard_index=args.shard_index,
        commands=commands,
        per_test_status=per_test_status,
    )
    summary_path = report_dir / "summary.json"
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"summary: {summary_path}")
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
