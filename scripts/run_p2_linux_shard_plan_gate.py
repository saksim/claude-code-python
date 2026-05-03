"""Phase 2 card P2-15 gate for Linux shard execution plan generation.

This script generates a deterministic shard execution plan from
`run_linux_unified_gate.py` manifest so Linux CI can fan out jobs with
consistent shard slicing and command contracts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
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


def _load_execution_gate_module():
    script_path = Path(__file__).resolve().with_name("run_p2_linux_unified_execution_gate.py")
    spec = importlib.util.spec_from_file_location("p2_linux_unified_execution_gate", script_path)
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


def build_shard_execution_command(
    *,
    python_executable: str,
    shard_total: int,
    shard_index: int,
    report_dir: Path,
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


def build_shard_plan_payload(
    *,
    python_executable: str,
    test_files: Sequence[str],
    shard_total: int,
    report_root: Path,
    continue_on_failure: bool,
    pytest_args: Sequence[str] | None,
) -> dict[str, Any]:
    if shard_total < 1:
        raise ValueError("shard_total must be >= 1")

    execution_gate = _load_execution_gate_module()

    shards: list[dict[str, Any]] = []
    for shard_index in range(1, shard_total + 1):
        selected_test_files = execution_gate.select_shard_test_files(
            test_files,
            shard_total=shard_total,
            shard_index=shard_index,
        )
        report_dir = report_root / f"shard-{shard_index}"
        command_parts = build_shard_execution_command(
            python_executable=python_executable,
            shard_total=shard_total,
            shard_index=shard_index,
            report_dir=report_dir,
            continue_on_failure=continue_on_failure,
            pytest_args=pytest_args,
        )
        shards.append(
            {
                "shard_index": shard_index,
                "total_tests": len(selected_test_files),
                "test_files": list(selected_test_files),
                "report_dir": str(report_dir),
                "summary_path": str(report_dir / "summary.json"),
                "command": _format_shell_command(command_parts),
                "command_parts": command_parts,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_executable": python_executable,
        "shard_total": shard_total,
        "manifest_total_tests": len(test_files),
        "continue_on_failure": continue_on_failure,
        "pytest_args": list(pytest_args or []),
        "report_root": str(report_root),
        "shards": shards,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic Linux shard execution plan for unified gate"
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable to use in generated shard commands",
    )
    parser.add_argument(
        "--shard-total",
        type=int,
        required=True,
        help="Total shard count for Linux parallel jobs",
    )
    parser.add_argument(
        "--report-root",
        default=".claude/reports/linux_unified_gate/shards",
        help="Root directory used to derive per-shard report dirs",
    )
    parser.add_argument(
        "--output",
        default=".claude/reports/linux_unified_gate/shard_plan.json",
        help="Shard plan output JSON path",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Include continue-on-failure flag in generated shard commands",
    )
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="Print per-shard execution commands",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output file; only print generated plan details",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra args forwarded to each execution-gate command after '--'",
    )
    args = parser.parse_args()

    unified_gate = _load_unified_gate_module()
    test_files: tuple[str, ...] = tuple(unified_gate.LINUX_UNIFIED_TEST_FILES)

    missing = _validate_manifest(test_files)
    if missing:
        for path in missing:
            print(f"[p2-linux-shard-plan-gate] missing test file: {path}", file=sys.stderr)
        return 2

    forwarded_args = list(args.pytest_args)
    if forwarded_args and forwarded_args[0] == "--":
        forwarded_args = forwarded_args[1:]

    try:
        payload = build_shard_plan_payload(
            python_executable=args.python_executable,
            test_files=test_files,
            shard_total=args.shard_total,
            report_root=Path(args.report_root),
            continue_on_failure=args.continue_on_failure,
            pytest_args=forwarded_args,
        )
    except ValueError as exc:
        print(f"[p2-linux-shard-plan-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"shard plan: {output_path}")

    print(
        "plan summary: "
        f"{payload['manifest_total_tests']} tests across {payload['shard_total']} shards"
    )
    for shard in payload["shards"]:
        print(f"- shard {shard['shard_index']}: {shard['total_tests']} tests")

    if args.print_commands or args.dry_run:
        for shard in payload["shards"]:
            print(f"[shard {shard['shard_index']}] {shard['command']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
