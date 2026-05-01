"""Phase 2 card P2-13 gate for Linux final report publishing.

This script reads merged shard summary from P2-12, validates the contract,
emits a compact JSON payload plus Markdown report, and returns pass/fail exit
status for Linux CI recovery stage.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coerce_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"field '{field}' must be int")
    return value


def load_merged_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: merged summary file not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: merged summary payload must be object")

    required_fields = (
        "manifest_total_tests",
        "shard_total",
        "shards_present",
        "shards_missing",
        "totals",
        "structural_issues",
        "overall_status",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    manifest_total_tests = _coerce_int(payload["manifest_total_tests"], field="manifest_total_tests")
    shard_total = _coerce_int(payload["shard_total"], field="shard_total")
    totals = payload["totals"]
    if not isinstance(totals, dict):
        raise ValueError(f"{path}: field 'totals' must be object")
    total_tests = _coerce_int(totals.get("total_tests"), field="totals.total_tests")
    passed = _coerce_int(totals.get("passed"), field="totals.passed")
    failed = _coerce_int(totals.get("failed"), field="totals.failed")

    shards_present = payload["shards_present"]
    shards_missing = payload["shards_missing"]
    structural_issues = payload["structural_issues"]
    overall_status = payload["overall_status"]

    if not isinstance(shards_present, list) or not all(isinstance(item, int) for item in shards_present):
        raise ValueError(f"{path}: field 'shards_present' must be int list")
    if not isinstance(shards_missing, list) or not all(isinstance(item, int) for item in shards_missing):
        raise ValueError(f"{path}: field 'shards_missing' must be int list")
    if not isinstance(structural_issues, list) or not all(
        isinstance(item, str) for item in structural_issues
    ):
        raise ValueError(f"{path}: field 'structural_issues' must be string list")
    if overall_status not in {"passed", "failed"}:
        raise ValueError(f"{path}: field 'overall_status' must be 'passed' or 'failed'")

    if manifest_total_tests < 0:
        raise ValueError(f"{path}: manifest_total_tests must be >= 0")
    if shard_total < 1:
        raise ValueError(f"{path}: shard_total must be >= 1")
    if total_tests < 0 or passed < 0 or failed < 0:
        raise ValueError(f"{path}: totals must be >= 0")
    if passed + failed > total_tests:
        raise ValueError(f"{path}: passed + failed exceeds total_tests")

    return payload


def build_publish_payload(merged_summary: dict[str, Any], *, source_path: Path) -> dict[str, Any]:
    totals = merged_summary["totals"]
    total_tests = int(totals["total_tests"])
    passed = int(totals["passed"])
    failed = int(totals["failed"])
    structural_issues = list(merged_summary["structural_issues"])
    shards_missing = list(merged_summary["shards_missing"])

    computed_status = (
        "passed"
        if failed == 0 and not structural_issues and not shards_missing
        else "failed"
    )
    reported_status = merged_summary["overall_status"]
    status_mismatch = computed_status != reported_status
    final_status = "failed" if status_mismatch else reported_status

    notes: list[str] = []
    if status_mismatch:
        notes.append(
            "overall_status mismatch between computed and merged summary"
            f" (computed={computed_status}, reported={reported_status})"
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_merged_summary": str(source_path),
        "overall_status": final_status,
        "manifest_total_tests": int(merged_summary["manifest_total_tests"]),
        "shard_total": int(merged_summary["shard_total"]),
        "shards_present": list(merged_summary["shards_present"]),
        "shards_missing": shards_missing,
        "totals": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
        },
        "structural_issues": structural_issues,
        "notes": notes,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    status = payload["overall_status"]
    totals = payload["totals"]
    lines = [
        "# Linux Unified Gate Final Report",
        "",
        f"- Status: **{status.upper()}**",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        f"- Source Summary: `{payload['source_merged_summary']}`",
        "",
        "## Totals",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Manifest Total Tests | {payload['manifest_total_tests']} |",
        f"| Selected Total Tests | {totals['total_tests']} |",
        f"| Passed | {totals['passed']} |",
        f"| Failed | {totals['failed']} |",
        f"| Shard Total | {payload['shard_total']} |",
        "",
        "## Shards",
        "",
        f"- Present: {payload['shards_present']}",
        f"- Missing: {payload['shards_missing']}",
        "",
        "## Structural Issues",
    ]

    issues = payload["structural_issues"]
    if issues:
        lines.extend(f"- {item}" for item in issues)
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Notes")
    notes = payload["notes"]
    if notes:
        lines.extend(f"- {item}" for item in notes)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish final Linux unified gate report from merged shard summary"
    )
    parser.add_argument(
        "--merged-summary",
        default=".claude/reports/linux_unified_gate/merged_summary.json",
        help="Merged summary JSON produced by P2-12 aggregation gate",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/final_report.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/final_report.md",
        help="Output Markdown report path",
    )
    args = parser.parse_args()

    merged_summary_path = Path(args.merged_summary)
    try:
        merged_summary = load_merged_summary(merged_summary_path)
        payload = build_publish_payload(merged_summary, source_path=merged_summary_path.resolve())
    except ValueError as exc:
        print(f"[p2-linux-report-publish-gate] {exc}", file=sys.stderr)
        return 2

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    output_markdown = Path(args.output_markdown)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text(render_markdown_report(payload), encoding="utf-8")

    print(f"final json: {output_json}")
    print(f"final markdown: {output_markdown}")
    print(
        "totals: "
        f"{payload['totals']['passed']} passed, {payload['totals']['failed']} failed, "
        f"{payload['totals']['total_tests']} total"
    )
    print(f"overall_status: {payload['overall_status']}")
    return 0 if payload["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
