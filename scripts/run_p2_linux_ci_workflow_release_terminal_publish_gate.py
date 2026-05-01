"""Phase 2 card P2-34 gate for Linux CI workflow release terminal publish.

This script converts P2-33 release completion artifacts into a single
release terminal publish contract:
1) normalize release completion verdict to final release publish status,
2) provide finalize/hold decision fields for downstream release governance,
3) emit JSON/Markdown reports + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_COMPLETION_STATUSES: set[str] = {
    "blocked",
    "awaiting_completion",
    "handoff_failed",
    "release_trigger_failed",
    "release_ready_dry_run",
    "release_run_tracking_missing",
    "release_run_tracking_ready",
    "release_run_in_progress",
    "release_run_completed_success",
    "release_run_completed_failure",
    "release_run_poll_failed",
    "release_run_await_timeout",
}


def _coerce_bool(value: Any, *, field: str, path: Path) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path}: field '{field}' must be bool")
    return value


def _coerce_int(value: Any, *, field: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path}: field '{field}' must be int")
    return value


def _coerce_str(value: Any, *, field: str, path: Path) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path}: field '{field}' must be string")
    return value


def _coerce_str_list(value: Any, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: field '{field}' must be string list")
    return list(value)


def _unique(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def load_release_completion_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release completion report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release completion payload must be object")

    required_fields = (
        "release_trigger_status",
        "release_tracking_status",
        "release_completion_status",
        "release_completion_exit_code",
        "allow_in_progress",
        "should_poll_release_run",
        "release_run_id",
        "release_run_url",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
        "source_release_trace_report",
        "source_release_trigger_report",
        "source_release_handoff_report",
        "source_terminal_publish_report",
        "source_dispatch_completion_report",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    release_trigger_status = _coerce_str(
        payload["release_trigger_status"],
        field="release_trigger_status",
        path=path,
    )
    release_tracking_status = _coerce_str(
        payload["release_tracking_status"],
        field="release_tracking_status",
        path=path,
    )
    release_completion_status = _coerce_str(
        payload["release_completion_status"],
        field="release_completion_status",
        path=path,
    )
    if release_completion_status not in ALLOWED_RELEASE_COMPLETION_STATUSES:
        raise ValueError(
            f"{path}: field 'release_completion_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_COMPLETION_STATUSES)}"
        )

    release_completion_exit_code = _coerce_int(
        payload["release_completion_exit_code"],
        field="release_completion_exit_code",
        path=path,
    )
    if release_completion_exit_code < 0:
        raise ValueError(f"{path}: field 'release_completion_exit_code' must be >= 0")

    allow_in_progress = _coerce_bool(
        payload["allow_in_progress"],
        field="allow_in_progress",
        path=path,
    )
    should_poll_release_run = _coerce_bool(
        payload["should_poll_release_run"],
        field="should_poll_release_run",
        path=path,
    )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(
            release_run_id_raw,
            field="release_run_id",
            path=path,
        )
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    release_run_url = _coerce_str(payload["release_run_url"], field="release_run_url", path=path)
    reason_codes = _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path)
    failed_checks = _coerce_str_list(payload["failed_checks"], field="failed_checks", path=path)
    structural_issues = _coerce_str_list(
        payload["structural_issues"],
        field="structural_issues",
        path=path,
    )
    missing_artifacts = _coerce_str_list(
        payload["missing_artifacts"],
        field="missing_artifacts",
        path=path,
    )

    source_release_trace_report = _coerce_str(
        payload["source_release_trace_report"],
        field="source_release_trace_report",
        path=path,
    )
    source_release_trigger_report = _coerce_str(
        payload["source_release_trigger_report"],
        field="source_release_trigger_report",
        path=path,
    )
    source_release_handoff_report = _coerce_str(
        payload["source_release_handoff_report"],
        field="source_release_handoff_report",
        path=path,
    )
    source_terminal_publish_report = _coerce_str(
        payload["source_terminal_publish_report"],
        field="source_terminal_publish_report",
        path=path,
    )
    source_dispatch_completion_report = _coerce_str(
        payload["source_dispatch_completion_report"],
        field="source_dispatch_completion_report",
        path=path,
    )
    source_dispatch_trace_report = _coerce_str(
        payload["source_dispatch_trace_report"],
        field="source_dispatch_trace_report",
        path=path,
    )
    source_dispatch_execution_report = _coerce_str(
        payload["source_dispatch_execution_report"],
        field="source_dispatch_execution_report",
        path=path,
    )
    source_dispatch_report = _coerce_str(
        payload["source_dispatch_report"],
        field="source_dispatch_report",
        path=path,
    )

    return {
        "generated_at": payload.get("generated_at"),
        "release_trigger_status": release_trigger_status,
        "release_tracking_status": release_tracking_status,
        "release_completion_status": release_completion_status,
        "release_completion_exit_code": release_completion_exit_code,
        "allow_in_progress": allow_in_progress,
        "should_poll_release_run": should_poll_release_run,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "source_release_trace_report": source_release_trace_report,
        "source_release_trigger_report": source_release_trigger_report,
        "source_release_handoff_report": source_release_handoff_report,
        "source_terminal_publish_report": source_terminal_publish_report,
        "source_dispatch_completion_report": source_dispatch_completion_report,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
    }


def build_release_terminal_publish_payload(
    completion_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    release_completion_status = str(completion_report["release_completion_status"])
    release_completion_exit_code = int(completion_report["release_completion_exit_code"])
    allow_in_progress = bool(completion_report["allow_in_progress"])

    structural_issues = list(completion_report["structural_issues"])
    reason_codes = list(completion_report["reason_codes"])

    failure_statuses = {
        "release_run_tracking_missing",
        "release_run_completed_failure",
        "release_run_poll_failed",
        "release_trigger_failed",
        "handoff_failed",
    }
    blocked_statuses = {
        "blocked",
        "release_ready_dry_run",
        "awaiting_completion",
        "release_run_tracking_ready",
    }
    in_progress_statuses = {"release_run_in_progress", "release_run_await_timeout"}

    if (
        release_completion_status == "release_run_completed_success"
        and release_completion_exit_code != 0
    ):
        structural_issues.append("release_completion_exit_code_mismatch_success")
    if (
        release_completion_status in failure_statuses
        and release_completion_exit_code == 0
    ):
        structural_issues.append("release_completion_exit_code_mismatch_failure")
    if release_completion_status in blocked_statuses and release_completion_exit_code != 0:
        structural_issues.append("release_completion_exit_code_mismatch_blocked")
    if (
        release_completion_status == "release_run_await_timeout"
        and release_completion_exit_code == 0
        and not allow_in_progress
    ):
        structural_issues.append("release_completion_timeout_policy_mismatch")

    structural_issues = _unique(structural_issues)

    if structural_issues:
        release_publish_status = "contract_failed"
        release_publish_exit_code = 1
        should_finalize_release = False
        reason_codes.extend(structural_issues)
    elif release_completion_status == "release_run_completed_success":
        release_publish_status = "passed"
        release_publish_exit_code = 0
        should_finalize_release = True
        reason_codes = ["release_completed_success"]
    elif release_completion_status in blocked_statuses:
        release_publish_status = "blocked"
        release_publish_exit_code = release_completion_exit_code
        should_finalize_release = False
    elif release_completion_status in in_progress_statuses:
        if release_completion_exit_code == 0:
            release_publish_status = "in_progress"
            release_publish_exit_code = 0
        else:
            release_publish_status = "failed"
            release_publish_exit_code = release_completion_exit_code
        should_finalize_release = False
    else:
        release_publish_status = "failed"
        release_publish_exit_code = (
            1 if release_completion_exit_code == 0 else release_completion_exit_code
        )
        should_finalize_release = False

    release_terminal_publish_summary = (
        f"release_completion_status={release_completion_status} "
        f"release_publish_status={release_publish_status} "
        f"should_finalize_release={should_finalize_release}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_completion_report": str(source_path),
        "release_trigger_status": str(completion_report["release_trigger_status"]),
        "release_tracking_status": str(completion_report["release_tracking_status"]),
        "release_completion_status": release_completion_status,
        "release_completion_exit_code": release_completion_exit_code,
        "release_publish_status": release_publish_status,
        "release_publish_exit_code": int(release_publish_exit_code),
        "should_finalize_release": should_finalize_release,
        "release_terminal_publish_summary": release_terminal_publish_summary,
        "allow_in_progress": allow_in_progress,
        "should_poll_release_run": bool(completion_report["should_poll_release_run"]),
        "release_run_id": completion_report["release_run_id"],
        "release_run_url": str(completion_report["release_run_url"]),
        "reason_codes": _unique(reason_codes),
        "failed_checks": list(completion_report["failed_checks"]),
        "structural_issues": structural_issues,
        "missing_artifacts": list(completion_report["missing_artifacts"]),
        "source_release_trace_report": str(completion_report["source_release_trace_report"]),
        "source_release_trigger_report": str(completion_report["source_release_trigger_report"]),
        "source_release_handoff_report": str(completion_report["source_release_handoff_report"]),
        "source_terminal_publish_report": str(completion_report["source_terminal_publish_report"]),
        "source_dispatch_completion_report": str(
            completion_report["source_dispatch_completion_report"]
        ),
        "source_dispatch_trace_report": str(completion_report["source_dispatch_trace_report"]),
        "source_dispatch_execution_report": str(
            completion_report["source_dispatch_execution_report"]
        ),
        "source_dispatch_report": str(completion_report["source_dispatch_report"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Terminal Publish Report",
        "",
        f"- Release Publish Status: **{str(payload['release_publish_status']).upper()}**",
        f"- Release Publish Exit Code: `{payload['release_publish_exit_code']}`",
        f"- Should Finalize Release: `{payload['should_finalize_release']}`",
        f"- Release Completion Status: `{payload['release_completion_status']}`",
        f"- Release Completion Exit Code: `{payload['release_completion_exit_code']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Release Completion Report: `{payload['source_release_completion_report']}`",
        f"- Source Release Trace Report: `{payload['source_release_trace_report']}`",
        f"- Source Release Trigger Report: `{payload['source_release_trigger_report']}`",
        f"- Source Release Handoff Report: `{payload['source_release_handoff_report']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_terminal_publish_summary']}",
        "",
        "## Reason Codes",
    ]

    reason_codes = payload["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{item}`" for item in reason_codes)
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
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    return {
        "workflow_release_terminal_publish_status": str(payload["release_publish_status"]),
        "workflow_release_terminal_publish_exit_code": str(payload["release_publish_exit_code"]),
        "workflow_release_terminal_publish_should_finalize_release": (
            "true" if payload["should_finalize_release"] else "false"
        ),
        "workflow_release_terminal_publish_completion_status": str(
            payload["release_completion_status"]
        ),
        "workflow_release_terminal_publish_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_terminal_publish_run_url": str(payload["release_run_url"]),
        "workflow_release_terminal_publish_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_terminal_publish_report_json": str(output_json),
        "workflow_release_terminal_publish_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release terminal verdict from P2-33 completion report"
        )
    )
    parser.add_argument(
        "--release-completion-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_completion.json",
        help="P2-33 release completion report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json",
        help="Output release terminal publish JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.md",
        help="Output release terminal publish markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release terminal publish JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    release_completion_report_path = Path(args.release_completion_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        completion_report = load_release_completion_report(release_completion_report_path)
        payload = build_release_terminal_publish_payload(
            completion_report,
            source_path=release_completion_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            f"[p2-linux-ci-workflow-release-terminal-publish-gate] {exc}",
            file=sys.stderr,
        )
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release terminal publish json: {output_json_path}")
        print(f"release terminal publish markdown: {output_markdown_path}")

    if args.github_output:
        write_github_output(
            Path(args.github_output),
            build_github_output_values(
                payload,
                output_json=output_json_path,
                output_markdown=output_markdown_path,
            ),
        )
        print(f"github output: {args.github_output}")

    print(
        "release terminal publish summary: "
        f"release_publish_status={payload['release_publish_status']} "
        f"should_finalize_release={payload['should_finalize_release']} "
        f"release_publish_exit_code={payload['release_publish_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_publish_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

