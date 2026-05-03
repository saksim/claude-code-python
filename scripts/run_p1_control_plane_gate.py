"""Phase 1 control-plane regression gate entrypoint.

Runs the curated P1-01 daemon/API runtime tests with one command.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


P1_CONTROL_PLANE_TEST_FILES: tuple[str, ...] = (
    "tests/test_main_runtime.py",
    "tests/test_server_runtime.py",
)


def build_p1_control_plane_pytest_command(
    *,
    python_executable: str | None = None,
    extra_pytest_args: Sequence[str] | None = None,
) -> list[str]:
    python_bin = python_executable or sys.executable
    command: list[str] = [
        python_bin,
        "-m",
        "pytest",
        "-c",
        "pytest.ini",
        *P1_CONTROL_PLANE_TEST_FILES,
    ]
    if extra_pytest_args:
        command.extend(extra_pytest_args)
    return command


def _validate_manifest() -> list[str]:
    missing: list[str] = []
    for test_file in P1_CONTROL_PLANE_TEST_FILES:
        if not Path(test_file).is_file():
            missing.append(test_file)
    return missing


def _format_shell_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 control-plane gate tests")
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable to use (default: current interpreter)",
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

    missing = _validate_manifest()
    if missing:
        for path in missing:
            print(f"[p1-control-plane-gate] missing test file: {path}", file=sys.stderr)
        return 2

    forwarded = list(args.pytest_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    command = build_p1_control_plane_pytest_command(
        python_executable=args.python_executable,
        extra_pytest_args=forwarded,
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
