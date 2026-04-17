"""Read-only syntax check for Python files.

This script avoids .pyc writes (unlike compileall) and is safe in restricted
workspaces. It reports syntax errors and exits non-zero when any are found.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def scan_python_syntax(root: Path) -> dict[str, Any]:
    files = sorted(root.rglob("*.py"))
    errors: list[dict[str, Any]] = []

    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except SyntaxError as exc:
            errors.append(
                {
                    "path": str(path).replace("\\", "/"),
                    "line": exc.lineno,
                    "message": exc.msg,
                    "type": exc.__class__.__name__,
                }
            )

    return {
        "root": str(root.resolve()).replace("\\", "/"),
        "total_files": len(files),
        "syntax_errors": len(errors),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only syntax checker")
    parser.add_argument(
        "--root",
        default="claude_code",
        help="Root folder to scan (default: claude_code)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output",
    )
    args = parser.parse_args()

    result = scan_python_syntax(Path(args.root))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"root={result['root']}")
        print(f"total_files={result['total_files']}")
        print(f"syntax_errors={result['syntax_errors']}")
        for err in result["errors"]:
            print(f"{err['path']}:{err['line']} {err['type']}: {err['message']}")

    return 1 if result["syntax_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

