"""Phase 2 card P2-30 gate for Linux CI workflow release handoff.

This script converts the P2-29 terminal publish artifact into a downstream
release handoff contract:
1) validate terminal publish contract consistency,
2) normalize promote/hold/blocked handoff decision,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_PUBLISH_STATUSES: set[str] = {
    "passed",
    "blocked",
    "in_progress",
    "failed",
    "contract_failed",
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


def load_terminal_publish_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: terminal publish report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: terminal publish payload must be object")

    required_fields = (
        "publish_status",
        "publish_exit_code",
        "should_promote",
        "completion_status",
        "completion_exit_code",
        "publish_summary",
        "run_id",
        "run_url",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
        "source_dispatch_completion_report",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    publish_status = _coerce_str(payload["publish_status"], field="publish_status", path=path)
    if publish_status not in ALLOWED_PUBLISH_STATUSES:
        raise ValueError(
            f"{path}: field 'publish_status' must be one of "
            f"{sorted(ALLOWED_PUBLISH_STATUSES)}"
        )

    publish_exit_code = _coerce_int(
        payload["publish_exit_code"],
        field="publish_exit_code",
        path=path,
    )
    if publish_exit_code < 0:
        raise ValueError(f"{path}: field 'publish_exit_code' must be >= 0")

    should_promote = _coerce_bool(payload["should_promote"], field="should_promote", path=path)
    completion_status = _coerce_str(
        payload["completion_status"],
        field="completion_status",
        path=path,
    )
    completion_exit_code = _coerce_int(
        payload["completion_exit_code"],
        field="completion_exit_code",
        path=path,
    )
    if completion_exit_code < 0:
        raise ValueError(f"{path}: field 'completion_exit_code' must be >= 0")

    publish_summary = _coerce_str(payload["publish_summary"], field="publish_summary", path=path)

    run_id_raw = payload["run_id"]
    if run_id_raw is None:
        run_id = None
    else:
        run_id = _coerce_int(run_id_raw, field="run_id", path=path)
        if run_id < 1:
            raise ValueError(f"{path}: field 'run_id' must be >= 1 when present")

    run_url = _coerce_str(payload["run_url"], field="run_url", path=path)
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
        "publish_status": publish_status,
        "publish_exit_code": publish_exit_code,
        "should_promote": should_promote,
        "completion_status": completion_status,
        "completion_exit_code": completion_exit_code,
        "publish_summary": publish_summary,
        "run_id": run_id,
        "run_url": run_url,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "source_dispatch_completion_report": source_dispatch_completion_report,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
    }


def build_release_handoff_payload(
    terminal_publish_report: dict[str, Any],
    *,
    source_path: Path,
    target_environment: str,
    release_channel: str,
) -> dict[str, Any]:
    publish_status = str(terminal_publish_report["publish_status"])
    publish_exit_code = int(terminal_publish_report["publish_exit_code"])
    should_promote = bool(terminal_publish_report["should_promote"])

    structural_issues = list(terminal_publish_report["structural_issues"])
    reason_codes = list(terminal_publish_report["reason_codes"])
    failed_checks = list(terminal_publish_report["failed_checks"])
    missing_artifacts = list(terminal_publish_report["missing_artifacts"])

    if publish_status == "passed":
        if publish_exit_code != 0:
            structural_issues.append("publish_exit_code_mismatch_passed")
        if not should_promote:
            structural_issues.append("should_promote_mismatch_passed")
    else:
        if should_promote:
            structural_issues.append("should_promote_mismatch_non_passed")

    if publish_status == "blocked" and publish_exit_code != 0:
        structural_issues.append("publish_exit_code_mismatch_blocked")
    if publish_status == "in_progress" and publish_exit_code != 0:
        structural_issues.append("publish_exit_code_mismatch_in_progress")
    if publish_status in {"failed", "contract_failed"} and publish_exit_code == 0:
        structural_issues.append("publish_exit_code_mismatch_failed")

    structural_issues = _unique(structural_issues)

    if structural_issues:
        handoff_status = "contract_failed"
        should_trigger_release = False
        release_exit_code = 1
        handoff_action = "hold"
        reason_codes.extend(structural_issues)
    elif publish_status == "passed":
        handoff_status = "ready_for_release"
        should_trigger_release = True
        release_exit_code = 0
        handoff_action = "promote"
        reason_codes = ["release_ready"]
    elif publish_status == "in_progress":
        handoff_status = "awaiting_completion"
        should_trigger_release = False
        release_exit_code = 0
        handoff_action = "hold"
    elif publish_status == "blocked":
        handoff_status = "blocked"
        should_trigger_release = False
        release_exit_code = 0
        handoff_action = "hold"
    else:
        handoff_status = "failed"
        should_trigger_release = False
        release_exit_code = 1
        handoff_action = "reject"

    handoff_summary = (
        f"publish_status={publish_status} "
        f"handoff_status={handoff_status} "
        f"should_trigger_release={should_trigger_release} "
        f"target_environment={target_environment} "
        f"release_channel={release_channel}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_terminal_publish_report": str(source_path),
        "source_dispatch_completion_report": str(
            terminal_publish_report["source_dispatch_completion_report"]
        ),
        "source_dispatch_trace_report": str(terminal_publish_report["source_dispatch_trace_report"]),
        "source_dispatch_execution_report": str(
            terminal_publish_report["source_dispatch_execution_report"]
        ),
        "source_dispatch_report": str(terminal_publish_report["source_dispatch_report"]),
        "target_environment": target_environment,
        "release_channel": release_channel,
        "publish_status": publish_status,
        "publish_exit_code": publish_exit_code,
        "should_promote": should_promote,
        "completion_status": str(terminal_publish_report["completion_status"]),
        "completion_exit_code": int(terminal_publish_report["completion_exit_code"]),
        "handoff_status": handoff_status,
        "handoff_action": handoff_action,
        "should_trigger_release": should_trigger_release,
        "release_exit_code": int(release_exit_code),
        "handoff_summary": handoff_summary,
        "publish_summary": str(terminal_publish_report["publish_summary"]),
        "run_id": terminal_publish_report["run_id"],
        "run_url": str(terminal_publish_report["run_url"]),
        "reason_codes": _unique(reason_codes),
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Handoff Report",
        "",
        f"- Handoff Status: **{str(payload['handoff_status']).upper()}**",
        f"- Handoff Action: `{payload['handoff_action']}`",
        f"- Should Trigger Release: `{payload['should_trigger_release']}`",
        f"- Release Exit Code: `{payload['release_exit_code']}`",
        f"- Target Environment: `{payload['target_environment']}`",
        f"- Release Channel: `{payload['release_channel']}`",
        f"- Publish Status: `{payload['publish_status']}`",
        f"- Completion Status: `{payload['completion_status']}`",
        f"- Run ID: `{payload['run_id']}`",
        f"- Run URL: `{payload['run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Terminal Publish Report: `{payload['source_terminal_publish_report']}`",
        f"- Source Dispatch Completion Report: `{payload['source_dispatch_completion_report']}`",
        f"- Source Dispatch Trace Report: `{payload['source_dispatch_trace_report']}`",
        f"- Source Dispatch Execution Report: `{payload['source_dispatch_execution_report']}`",
        f"- Source Dispatch Report: `{payload['source_dispatch_report']}`",
        "",
        "## Handoff Summary",
        "",
        f"- {payload['handoff_summary']}",
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
    run_id = payload["run_id"]
    return {
        "workflow_release_handoff_status": str(payload["handoff_status"]),
        "workflow_release_handoff_action": str(payload["handoff_action"]),
        "workflow_release_handoff_should_trigger_release": "true"
        if payload["should_trigger_release"]
        else "false",
        "workflow_release_handoff_release_exit_code": str(payload["release_exit_code"]),
        "workflow_release_handoff_target_environment": str(payload["target_environment"]),
        "workflow_release_handoff_release_channel": str(payload["release_channel"]),
        "workflow_release_handoff_publish_status": str(payload["publish_status"]),
        "workflow_release_handoff_completion_status": str(payload["completion_status"]),
        "workflow_release_handoff_run_id": "" if run_id is None else str(run_id),
        "workflow_release_handoff_run_url": str(payload["run_url"]),
        "workflow_release_handoff_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_handoff_report_json": str(output_json),
        "workflow_release_handoff_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build Linux CI workflow release handoff report from P2-29 terminal publish artifact"
        )
    )
    parser.add_argument(
        "--terminal-publish-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json",
        help="P2-29 terminal publish report JSON path",
    )
    parser.add_argument(
        "--target-environment",
        default="production",
        help="Release target environment label",
    )
    parser.add_argument(
        "--release-channel",
        default="stable",
        help="Release channel label",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_handoff.json",
        help="Output release handoff JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_handoff.md",
        help="Output release handoff markdown path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release handoff JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    terminal_publish_report_path = Path(args.terminal_publish_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        terminal_publish_report = load_terminal_publish_report(terminal_publish_report_path)
        payload = build_release_handoff_payload(
            terminal_publish_report,
            source_path=terminal_publish_report_path.resolve(),
            target_environment=args.target_environment,
            release_channel=args.release_channel,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-handoff-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release handoff json: {output_json_path}")
        print(f"release handoff markdown: {output_markdown_path}")

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
        "release handoff summary: "
        f"handoff_status={payload['handoff_status']} "
        f"should_trigger_release={payload['should_trigger_release']} "
        f"release_exit_code={payload['release_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
