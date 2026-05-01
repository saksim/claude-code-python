"""Phase 2 card P2-36 gate for Linux CI workflow release closure publishing.

This script consumes the P2-35 release finalization artifact and converges
the terminal release closure contract:
1) validate release finalization contract consistency,
2) normalize closure decision/status for external consumers,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_FINALIZATION_STATUSES: set[str] = {
    "finalized",
    "awaiting_release",
    "failed",
    "contract_failed",
}

ALLOWED_RELEASE_FINALIZATION_DECISIONS: set[str] = {"finalize", "hold", "abort"}
ALLOWED_RELEASE_CLOSURE_STATUSES: set[str] = {"closed", "pending", "failed", "contract_failed"}
ALLOWED_RELEASE_CLOSURE_DECISIONS: set[str] = {"ship", "hold", "rollback"}


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


def load_release_finalization_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release finalization report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release finalization payload must be object")

    required_fields = (
        "release_finalization_status",
        "release_finalization_decision",
        "release_finalization_exit_code",
        "should_finalize_release",
        "on_hold_policy",
        "release_publish_status",
        "release_publish_exit_code",
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
        "source_release_terminal_publish_report",
        "source_release_completion_report",
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

    release_finalization_status = _coerce_str(
        payload["release_finalization_status"],
        field="release_finalization_status",
        path=path,
    )
    if release_finalization_status not in ALLOWED_RELEASE_FINALIZATION_STATUSES:
        raise ValueError(
            f"{path}: field 'release_finalization_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINALIZATION_STATUSES)}"
        )

    release_finalization_decision = _coerce_str(
        payload["release_finalization_decision"],
        field="release_finalization_decision",
        path=path,
    )
    if release_finalization_decision not in ALLOWED_RELEASE_FINALIZATION_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_finalization_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINALIZATION_DECISIONS)}"
        )

    release_finalization_exit_code = _coerce_int(
        payload["release_finalization_exit_code"],
        field="release_finalization_exit_code",
        path=path,
    )
    if release_finalization_exit_code < 0:
        raise ValueError(f"{path}: field 'release_finalization_exit_code' must be >= 0")

    should_finalize_release = _coerce_bool(
        payload["should_finalize_release"],
        field="should_finalize_release",
        path=path,
    )
    on_hold_policy = _coerce_str(payload["on_hold_policy"], field="on_hold_policy", path=path)
    if on_hold_policy not in {"pass", "fail"}:
        raise ValueError(f"{path}: field 'on_hold_policy' must be 'pass' or 'fail'")

    release_publish_status = _coerce_str(
        payload["release_publish_status"],
        field="release_publish_status",
        path=path,
    )
    release_publish_exit_code = _coerce_int(
        payload["release_publish_exit_code"],
        field="release_publish_exit_code",
        path=path,
    )
    if release_publish_exit_code < 0:
        raise ValueError(f"{path}: field 'release_publish_exit_code' must be >= 0")

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

    source_release_terminal_publish_report = _coerce_str(
        payload["source_release_terminal_publish_report"],
        field="source_release_terminal_publish_report",
        path=path,
    )
    source_release_completion_report = _coerce_str(
        payload["source_release_completion_report"],
        field="source_release_completion_report",
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
        "release_finalization_status": release_finalization_status,
        "release_finalization_decision": release_finalization_decision,
        "release_finalization_exit_code": release_finalization_exit_code,
        "should_finalize_release": should_finalize_release,
        "on_hold_policy": on_hold_policy,
        "release_publish_status": release_publish_status,
        "release_publish_exit_code": release_publish_exit_code,
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
        "source_release_terminal_publish_report": source_release_terminal_publish_report,
        "source_release_completion_report": source_release_completion_report,
        "source_release_trace_report": source_release_trace_report,
        "source_release_trigger_report": source_release_trigger_report,
        "source_release_handoff_report": source_release_handoff_report,
        "source_terminal_publish_report": source_terminal_publish_report,
        "source_dispatch_completion_report": source_dispatch_completion_report,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
    }


def build_release_closure_payload(
    release_finalization_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    release_finalization_status = str(release_finalization_report["release_finalization_status"])
    release_finalization_decision = str(
        release_finalization_report["release_finalization_decision"]
    )
    release_finalization_exit_code = int(
        release_finalization_report["release_finalization_exit_code"]
    )
    should_finalize_release = bool(release_finalization_report["should_finalize_release"])

    structural_issues = list(release_finalization_report["structural_issues"])
    reason_codes = list(release_finalization_report["reason_codes"])

    if release_finalization_status == "finalized":
        if release_finalization_decision != "finalize":
            structural_issues.append("release_finalization_decision_mismatch_finalized")
        if release_finalization_exit_code != 0:
            structural_issues.append("release_finalization_exit_code_mismatch_finalized")
        if not should_finalize_release:
            structural_issues.append("should_finalize_release_mismatch_finalized")
    elif release_finalization_status == "awaiting_release":
        if release_finalization_decision != "hold":
            structural_issues.append("release_finalization_decision_mismatch_awaiting")
        if should_finalize_release:
            structural_issues.append("should_finalize_release_mismatch_awaiting")
    elif release_finalization_status in {"failed", "contract_failed"}:
        if release_finalization_decision != "abort":
            structural_issues.append("release_finalization_decision_mismatch_failed")
        if should_finalize_release:
            structural_issues.append("should_finalize_release_mismatch_failed")
        if release_finalization_exit_code == 0:
            structural_issues.append("release_finalization_exit_code_mismatch_failed")

    structural_issues = _unique(structural_issues)

    if structural_issues:
        release_closure_status = "contract_failed"
        release_closure_decision = "rollback"
        release_closure_exit_code = 1
        should_close_release = False
        should_notify = True
        reason_codes.extend(structural_issues)
    elif release_finalization_status == "finalized":
        release_closure_status = "closed"
        release_closure_decision = "ship"
        release_closure_exit_code = 0
        should_close_release = True
        should_notify = True
        reason_codes = ["release_closed"]
    elif release_finalization_status == "awaiting_release":
        release_closure_status = "pending"
        release_closure_decision = "hold"
        release_closure_exit_code = release_finalization_exit_code
        should_close_release = False
        should_notify = True
    elif release_finalization_status == "failed":
        release_closure_status = "failed"
        release_closure_decision = "rollback"
        release_closure_exit_code = release_finalization_exit_code
        should_close_release = False
        should_notify = True
    else:
        release_closure_status = "contract_failed"
        release_closure_decision = "rollback"
        release_closure_exit_code = 1
        should_close_release = False
        should_notify = True

    if release_closure_status not in ALLOWED_RELEASE_CLOSURE_STATUSES:
        raise ValueError("internal: unsupported release_closure_status computed")
    if release_closure_decision not in ALLOWED_RELEASE_CLOSURE_DECISIONS:
        raise ValueError("internal: unsupported release_closure_decision computed")

    release_closure_summary = (
        f"release_finalization_status={release_finalization_status} "
        f"release_closure_status={release_closure_status} "
        f"release_closure_decision={release_closure_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_finalization_report": str(source_path),
        "release_finalization_status": release_finalization_status,
        "release_finalization_decision": release_finalization_decision,
        "release_finalization_exit_code": release_finalization_exit_code,
        "release_closure_status": release_closure_status,
        "release_closure_decision": release_closure_decision,
        "release_closure_exit_code": int(release_closure_exit_code),
        "should_close_release": should_close_release,
        "should_notify": should_notify,
        "release_closure_summary": release_closure_summary,
        "should_finalize_release": should_finalize_release,
        "on_hold_policy": str(release_finalization_report["on_hold_policy"]),
        "release_publish_status": str(release_finalization_report["release_publish_status"]),
        "release_publish_exit_code": int(release_finalization_report["release_publish_exit_code"]),
        "release_trigger_status": str(release_finalization_report["release_trigger_status"]),
        "release_tracking_status": str(release_finalization_report["release_tracking_status"]),
        "release_completion_status": str(release_finalization_report["release_completion_status"]),
        "release_completion_exit_code": int(
            release_finalization_report["release_completion_exit_code"]
        ),
        "allow_in_progress": bool(release_finalization_report["allow_in_progress"]),
        "should_poll_release_run": bool(release_finalization_report["should_poll_release_run"]),
        "release_run_id": release_finalization_report["release_run_id"],
        "release_run_url": str(release_finalization_report["release_run_url"]),
        "reason_codes": _unique(reason_codes),
        "failed_checks": list(release_finalization_report["failed_checks"]),
        "structural_issues": structural_issues,
        "missing_artifacts": list(release_finalization_report["missing_artifacts"]),
        "source_release_terminal_publish_report": str(
            release_finalization_report["source_release_terminal_publish_report"]
        ),
        "source_release_completion_report": str(
            release_finalization_report["source_release_completion_report"]
        ),
        "source_release_trace_report": str(
            release_finalization_report["source_release_trace_report"]
        ),
        "source_release_trigger_report": str(
            release_finalization_report["source_release_trigger_report"]
        ),
        "source_release_handoff_report": str(
            release_finalization_report["source_release_handoff_report"]
        ),
        "source_terminal_publish_report": str(
            release_finalization_report["source_terminal_publish_report"]
        ),
        "source_dispatch_completion_report": str(
            release_finalization_report["source_dispatch_completion_report"]
        ),
        "source_dispatch_trace_report": str(
            release_finalization_report["source_dispatch_trace_report"]
        ),
        "source_dispatch_execution_report": str(
            release_finalization_report["source_dispatch_execution_report"]
        ),
        "source_dispatch_report": str(release_finalization_report["source_dispatch_report"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Closure Report",
        "",
        f"- Release Closure Status: **{str(payload['release_closure_status']).upper()}**",
        f"- Release Closure Decision: `{payload['release_closure_decision']}`",
        f"- Should Close Release: `{payload['should_close_release']}`",
        f"- Should Notify: `{payload['should_notify']}`",
        f"- Release Closure Exit Code: `{payload['release_closure_exit_code']}`",
        f"- Release Finalization Status: `{payload['release_finalization_status']}`",
        f"- Release Finalization Decision: `{payload['release_finalization_decision']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Release Finalization Report: `{payload['source_release_finalization_report']}`",
        f"- Source Release Terminal Publish Report: `{payload['source_release_terminal_publish_report']}`",
        f"- Source Release Completion Report: `{payload['source_release_completion_report']}`",
        f"- Source Release Trace Report: `{payload['source_release_trace_report']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_closure_summary']}",
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
        "workflow_release_closure_status": str(payload["release_closure_status"]),
        "workflow_release_closure_decision": str(payload["release_closure_decision"]),
        "workflow_release_closure_should_close_release": (
            "true" if payload["should_close_release"] else "false"
        ),
        "workflow_release_closure_should_notify": "true" if payload["should_notify"] else "false",
        "workflow_release_closure_exit_code": str(payload["release_closure_exit_code"]),
        "workflow_release_closure_finalization_status": str(
            payload["release_finalization_status"]
        ),
        "workflow_release_closure_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_closure_run_url": str(payload["release_run_url"]),
        "workflow_release_closure_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_closure_report_json": str(output_json),
        "workflow_release_closure_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release closure contract from P2-35 finalization report"
        )
    )
    parser.add_argument(
        "--release-finalization-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_finalization.json",
        help="P2-35 release finalization report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_closure.json",
        help="Output release closure JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_closure.md",
        help="Output release closure markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release closure JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    release_finalization_report_path = Path(args.release_finalization_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        release_finalization_report = load_release_finalization_report(
            release_finalization_report_path
        )
        payload = build_release_closure_payload(
            release_finalization_report,
            source_path=release_finalization_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-closure-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release closure json: {output_json_path}")
        print(f"release closure markdown: {output_markdown_path}")

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
        "release closure summary: "
        f"release_closure_status={payload['release_closure_status']} "
        f"release_closure_decision={payload['release_closure_decision']} "
        f"release_closure_exit_code={payload['release_closure_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_closure_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
