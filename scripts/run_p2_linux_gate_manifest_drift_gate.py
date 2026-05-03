"""Phase 2 card P2-57 gate for Linux unified gate manifest drift closure.

This script validates gate runtime contract closure across three layers:
1) scripts/run_*_gate.py scripts,
2) tests/test_*_gate_runtime.py runtime contracts,
3) scripts/run_linux_unified_gate.py Linux unified manifest entries.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_GATE_SCRIPT_PATTERN = re.compile(r"^run_(.+_gate)\.py$")


def _strip_prefix(value: str, prefix: str) -> str:
    if value.startswith(prefix):
        return value[len(prefix) :]
    return value


def _strip_suffix(value: str, suffix: str) -> str:
    if suffix and value.endswith(suffix):
        return value[: -len(suffix)]
    return value


def _load_linux_unified_gate_module(project_root: Path) -> Any:
    script_path = project_root / "scripts" / "run_linux_unified_gate.py"
    spec = importlib.util.spec_from_file_location("linux_unified_gate_script", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_gate_script_basenames(*, scripts_dir: Path) -> list[str]:
    basenames: list[str] = []
    for path in sorted(scripts_dir.glob("run_*_gate.py")):
        if path.name == "run_linux_unified_gate.py":
            continue
        if _GATE_SCRIPT_PATTERN.match(path.name) is None:
            continue
        basenames.append(path.name)
    return basenames


def expected_runtime_test_for_gate(gate_script_basename: str) -> str:
    stem = _strip_suffix(gate_script_basename, ".py")
    return f"test_{_strip_prefix(stem, 'run_')}_runtime.py"


def build_manifest_drift_report(*, project_root: Path) -> dict[str, Any]:
    scripts_dir = project_root / "scripts"
    tests_dir = project_root / "tests"

    gate_scripts = collect_gate_script_basenames(scripts_dir=scripts_dir)
    gate_tests: list[str] = [expected_runtime_test_for_gate(name) for name in gate_scripts]

    missing_runtime_tests: list[str] = []
    existing_runtime_tests: list[str] = []
    for runtime_test in gate_tests:
        if (tests_dir / runtime_test).is_file():
            existing_runtime_tests.append(runtime_test)
        else:
            missing_runtime_tests.append(runtime_test)

    linux_unified_gate = _load_linux_unified_gate_module(project_root)
    manifest_entries = set(getattr(linux_unified_gate, "LINUX_UNIFIED_TEST_FILES", ()))

    missing_manifest_entries: list[str] = []
    existing_manifest_entries: list[str] = []
    for runtime_test in gate_tests:
        manifest_path = f"tests/{runtime_test}"
        if manifest_path in manifest_entries:
            existing_manifest_entries.append(manifest_path)
        else:
            missing_manifest_entries.append(manifest_path)

    orphan_manifest_entries: list[str] = []
    for manifest_path in sorted(manifest_entries):
        if not manifest_path.startswith("tests/test_"):
            continue
        if not manifest_path.endswith("_gate_runtime.py"):
            continue
        basename = Path(manifest_path).name
        expected_script = (
            "run_"
            + _strip_suffix(_strip_prefix(basename, "test_"), "_runtime.py")
            + ".py"
        )
        if (scripts_dir / expected_script).is_file():
            continue
        orphan_manifest_entries.append(manifest_path)

    structural_issues: list[str] = []
    if missing_runtime_tests:
        structural_issues.append("missing_gate_runtime_tests")
    if missing_manifest_entries:
        structural_issues.append("missing_manifest_entries")
    if orphan_manifest_entries:
        structural_issues.append("orphan_manifest_gate_tests")

    status = "passed" if not structural_issues else "failed"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root.resolve()),
        "status": status,
        "gate_scripts_scanned": gate_scripts,
        "gate_runtime_tests_expected": gate_tests,
        "existing_runtime_tests": existing_runtime_tests,
        "missing_runtime_tests": missing_runtime_tests,
        "existing_manifest_entries": existing_manifest_entries,
        "missing_manifest_entries": missing_manifest_entries,
        "orphan_manifest_entries": orphan_manifest_entries,
        "structural_issues": structural_issues,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# P2-57 Linux Gate Manifest Drift Report",
        "",
        f"- Status: **{str(payload['status']).upper()}**",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        f"- Project Root: `{payload['project_root']}`",
        f"- Gate Scripts Scanned: {len(payload['gate_scripts_scanned'])}",
        "",
        "## Missing Runtime Tests",
    ]

    missing_runtime_tests = payload["missing_runtime_tests"]
    if missing_runtime_tests:
        lines.extend(f"- `{item}`" for item in missing_runtime_tests)
    else:
        lines.append("- none")

    lines.extend(["", "## Missing Manifest Entries"])
    missing_manifest_entries = payload["missing_manifest_entries"]
    if missing_manifest_entries:
        lines.extend(f"- `{item}`" for item in missing_manifest_entries)
    else:
        lines.append("- none")

    lines.extend(["", "## Orphan Manifest Gate Tests"])
    orphan_manifest_entries = payload["orphan_manifest_entries"]
    if orphan_manifest_entries:
        lines.extend(f"- `{item}`" for item in orphan_manifest_entries)
    else:
        lines.append("- none")

    lines.extend(["", "## Structural Issues"])
    structural_issues = payload["structural_issues"]
    if structural_issues:
        lines.extend(f"- `{item}`" for item in structural_issues)
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    *,
    payload: dict[str, Any],
    output_json: Path,
    output_markdown: Path,
) -> dict[str, str]:
    return {
        "linux_gate_manifest_drift_status": str(payload["status"]),
        "linux_gate_manifest_drift_missing_runtime_tests": str(
            len(payload["missing_runtime_tests"])
        ),
        "linux_gate_manifest_drift_missing_manifest_entries": str(
            len(payload["missing_manifest_entries"])
        ),
        "linux_gate_manifest_drift_orphan_manifest_entries": str(
            len(payload["orphan_manifest_entries"])
        ),
        "linux_gate_manifest_drift_report_json": str(output_json),
        "linux_gate_manifest_drift_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Linux gate runtime contract drift across scripts/tests/manifest"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root containing scripts/ and tests/ (default: current directory)",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/linux_gate_manifest_drift.json",
        help="Output JSON report path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/linux_gate_manifest_drift.md",
        help="Output Markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print report JSON to stdout",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing report files",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root)
    scripts_dir = project_root / "scripts"
    tests_dir = project_root / "tests"
    if not scripts_dir.is_dir() or not tests_dir.is_dir():
        print(
            "[p2-linux-gate-manifest-drift-gate] project root must contain scripts/ and tests/",
            file=sys.stderr,
        )
        return 2

    try:
        payload = build_manifest_drift_report(project_root=project_root)
    except Exception as exc:  # defensive for import/runtime failures
        print(f"[p2-linux-gate-manifest-drift-gate] {exc}", file=sys.stderr)
        return 2

    output_json = Path(args.output_json)
    output_markdown = Path(args.output_markdown)

    if not args.dry_run:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.write_text(render_markdown_report(payload), encoding="utf-8")

        print(f"report json: {output_json}")
        print(f"report markdown: {output_markdown}")

    if args.github_output:
        values = build_github_output_values(
            payload=payload,
            output_json=output_json,
            output_markdown=output_markdown,
        )
        write_github_output(Path(args.github_output), values)
        print(f"github output: {args.github_output}")

    print(
        "manifest drift summary: "
        f"status={payload['status']} "
        f"missing_runtime_tests={len(payload['missing_runtime_tests'])} "
        f"missing_manifest_entries={len(payload['missing_manifest_entries'])} "
        f"orphan_manifest_entries={len(payload['orphan_manifest_entries'])}"
    )

    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
