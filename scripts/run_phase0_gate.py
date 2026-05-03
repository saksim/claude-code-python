"""Phase 0 runtime regression gate entrypoint.

Runs the curated Phase 0 runtime regression test suite with one command.
This script is designed for local pre-merge checks and CI job reuse.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


PHASE0_GATE_TEST_FILES: tuple[str, ...] = (
    "tests/test_runtime_bootstrap.py",
    "tests/test_main_runtime.py",
    "tests/test_resume_runtime.py",
    "tests/test_commands_auth_runtime.py",
    "tests/test_features_runtime.py",
    "tests/test_review_command_runtime.py",
    "tests/test_session_history_memory_runtime.py",
    "tests/test_context_builder_runtime.py",
    "tests/test_hooks_runtime.py",
    "tests/test_doctor_runtime.py",
    "tests/test_plugins_runtime.py",
    "tests/test_phase0_regression_contract.py",
)


def build_phase0_pytest_command(
    *,
    python_executable: str | None = None,
    extra_pytest_args: Sequence[str] | None = None,
) -> list[str]:
    """Build subprocess command for Phase 0 gate."""
    python_bin = python_executable or sys.executable
    cmd: list[str] = [
        python_bin,
        "-m",
        "pytest",
        "-c",
        "pytest.ini",
        *PHASE0_GATE_TEST_FILES,
    ]
    if extra_pytest_args:
        cmd.extend(extra_pytest_args)
    return cmd


def _validate_gate_file_manifest() -> list[str]:
    """Return missing test files from manifest."""
    missing: list[str] = []
    for test_file in PHASE0_GATE_TEST_FILES:
        if not Path(test_file).is_file():
            missing.append(test_file)
    return missing


def _format_shell_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 0 regression gate tests")
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable to use (default: current interpreter)",
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List curated Phase 0 test files and exit",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the underlying pytest command and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate manifest and show command without executing tests",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra args forwarded to pytest after '--'",
    )
    args = parser.parse_args()

    if args.list_tests:
        for test_file in PHASE0_GATE_TEST_FILES:
            print(test_file)
        return 0

    missing = _validate_gate_file_manifest()
    if missing:
        for path in missing:
            print(f"[phase0-gate] missing test file: {path}", file=sys.stderr)
        return 2

    forwarded_args = list(args.pytest_args)
    if forwarded_args and forwarded_args[0] == "--":
        forwarded_args = forwarded_args[1:]

    command = build_phase0_pytest_command(
        python_executable=args.python_executable,
        extra_pytest_args=forwarded_args,
    )

    if args.print_command or args.dry_run:
        print(_format_shell_command(command))
        if args.print_command and not args.dry_run:
            return 0
    if args.dry_run:
        return 0

    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
