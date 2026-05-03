"""Phase 2 card P2-29 gate for Linux CI workflow terminal publish.

This script converts P2-28 dispatch completion artifacts into a single
terminal publish contract:
1) normalize completion verdict to final CI publish status,
2) provide promote/hold decision fields for downstream stages,
3) emit JSON/Markdown reports + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_COMPLETION_STATUSES: set[str] = {
    "blocked",
    "ready_dry_run",
    "run_tracking_missing",
    "run_completed_success",
    "run_completed_failure",
    "run_poll_failed",
    "run_await_timeout",
    "run_in_progress",
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


def load_dispatch_completion_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: dispatch completion report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: dispatch completion payload must be object")

    required_fields = (
        "completion_status",
        "completion_exit_code",
        "execution_status",
        "tracking_status",
        "allow_in_progress",
        "should_poll_workflow_run",
        "run_id",
        "run_url",
        "reason_codes",
        "failed_checks",
        "structural_issues",
        "missing_artifacts",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    completion_status = _coerce_str(
        payload["completion_status"],
        field="completion_status",
        path=path,
    )
    if completion_status not in ALLOWED_COMPLETION_STATUSES:
        raise ValueError(
            f"{path}: field 'completion_status' must be one of "
            f"{sorted(ALLOWED_COMPLETION_STATUSES)}"
        )

    completion_exit_code = _coerce_int(
        payload["completion_exit_code"],
        field="completion_exit_code",
        path=path,
    )
    if completion_exit_code < 0:
        raise ValueError(f"{path}: field 'completion_exit_code' must be >= 0")

    execution_status = _coerce_str(
        payload["execution_status"],
        field="execution_status",
        path=path,
    )
    tracking_status = _coerce_str(
        payload["tracking_status"],
        field="tracking_status",
        path=path,
    )
    allow_in_progress = _coerce_bool(
        payload["allow_in_progress"],
        field="allow_in_progress",
        path=path,
    )
    should_poll_workflow_run = _coerce_bool(
        payload["should_poll_workflow_run"],
        field="should_poll_workflow_run",
        path=path,
    )

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
        "completion_status": completion_status,
        "completion_exit_code": completion_exit_code,
        "execution_status": execution_status,
        "tracking_status": tracking_status,
        "allow_in_progress": allow_in_progress,
        "should_poll_workflow_run": should_poll_workflow_run,
        "run_id": run_id,
        "run_url": run_url,
        "reason_codes": reason_codes,
        "failed_checks": failed_checks,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "source_dispatch_trace_report": source_dispatch_trace_report,
        "source_dispatch_execution_report": source_dispatch_execution_report,
        "source_dispatch_report": source_dispatch_report,
    }


def build_terminal_publish_payload(
    completion_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    completion_status = str(completion_report["completion_status"])
    completion_exit_code = int(completion_report["completion_exit_code"])
    structural_issues = list(completion_report["structural_issues"])
    reason_codes = list(completion_report["reason_codes"])

    if completion_status == "run_completed_success" and completion_exit_code != 0:
        structural_issues.append("completion_exit_code_mismatch_success")
    if completion_status in {
        "run_tracking_missing",
        "run_completed_failure",
        "run_poll_failed",
    } and completion_exit_code == 0:
        structural_issues.append("completion_exit_code_mismatch_failure")
    if completion_status == "run_await_timeout" and completion_exit_code == 0:
        if not bool(completion_report["allow_in_progress"]):
            structural_issues.append("completion_timeout_policy_mismatch")

    structural_issues = _unique(structural_issues)

    if structural_issues:
        publish_status = "contract_failed"
        publish_exit_code = 1
        should_promote = False
        reason_codes.extend(structural_issues)
    elif completion_status == "run_completed_success":
        publish_status = "passed"
        publish_exit_code = 0
        should_promote = True
        reason_codes = ["workflow_completed_success"]
    elif completion_status in {"blocked", "ready_dry_run"}:
        publish_status = "blocked"
        publish_exit_code = completion_exit_code
        should_promote = False
    elif completion_status in {"run_await_timeout", "run_in_progress"}:
        if completion_exit_code == 0:
            publish_status = "in_progress"
            publish_exit_code = 0
        else:
            publish_status = "failed"
            publish_exit_code = 1
        should_promote = False
    else:
        publish_status = "failed"
        publish_exit_code = 1 if completion_exit_code == 0 else completion_exit_code
        should_promote = False

    publish_summary = (
        f"completion_status={completion_status} "
        f"publish_status={publish_status} "
        f"should_promote={should_promote}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dispatch_completion_report": str(source_path),
        "completion_status": completion_status,
        "completion_exit_code": completion_exit_code,
        "publish_status": publish_status,
        "publish_exit_code": int(publish_exit_code),
        "should_promote": should_promote,
        "publish_summary": publish_summary,
        "execution_status": str(completion_report["execution_status"]),
        "tracking_status": str(completion_report["tracking_status"]),
        "allow_in_progress": bool(completion_report["allow_in_progress"]),
        "should_poll_workflow_run": bool(completion_report["should_poll_workflow_run"]),
        "run_id": completion_report["run_id"],
        "run_url": str(completion_report["run_url"]),
        "reason_codes": _unique(reason_codes),
        "failed_checks": list(completion_report["failed_checks"]),
        "structural_issues": structural_issues,
        "missing_artifacts": list(completion_report["missing_artifacts"]),
        "source_dispatch_trace_report": str(completion_report["source_dispatch_trace_report"]),
        "source_dispatch_execution_report": str(completion_report["source_dispatch_execution_report"]),
        "source_dispatch_report": str(completion_report["source_dispatch_report"]),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Terminal Publish Report",
        "",
        f"- Publish Status: **{str(payload['publish_status']).upper()}**",
        f"- Publish Exit Code: `{payload['publish_exit_code']}`",
        f"- Should Promote: `{payload['should_promote']}`",
        f"- Completion Status: `{payload['completion_status']}`",
        f"- Completion Exit Code: `{payload['completion_exit_code']}`",
        f"- Run ID: `{payload['run_id']}`",
        f"- Run URL: `{payload['run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Paths",
        "",
        f"- Source Dispatch Completion Report: `{payload['source_dispatch_completion_report']}`",
        f"- Source Dispatch Trace Report: `{payload['source_dispatch_trace_report']}`",
        f"- Source Dispatch Execution Report: `{payload['source_dispatch_execution_report']}`",
        f"- Source Dispatch Report: `{payload['source_dispatch_report']}`",
        "",
        "## Publish Summary",
        "",
        f"- {payload['publish_summary']}",
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
        "workflow_terminal_publish_status": str(payload["publish_status"]),
        "workflow_terminal_publish_exit_code": str(payload["publish_exit_code"]),
        "workflow_terminal_publish_should_promote": "true" if payload["should_promote"] else "false",
        "workflow_terminal_publish_completion_status": str(payload["completion_status"]),
        "workflow_terminal_publish_run_id": "" if run_id is None else str(run_id),
        "workflow_terminal_publish_run_url": str(payload["run_url"]),
        "workflow_terminal_publish_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_terminal_publish_report_json": str(output_json),
        "workflow_terminal_publish_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish Linux CI workflow terminal verdict from P2-28 completion report"
    )
    parser.add_argument(
        "--dispatch-completion-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json",
        help="P2-28 dispatch completion report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json",
        help="Output terminal publish JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.md",
        help="Output terminal publish markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print terminal publish JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    dispatch_completion_report_path = Path(args.dispatch_completion_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        completion_report = load_dispatch_completion_report(dispatch_completion_report_path)
        payload = build_terminal_publish_payload(
            completion_report,
            source_path=dispatch_completion_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-terminal-publish-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"terminal publish json: {output_json_path}")
        print(f"terminal publish markdown: {output_markdown_path}")

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
        "terminal publish summary: "
        f"publish_status={payload['publish_status']} "
        f"should_promote={payload['should_promote']} "
        f"publish_exit_code={payload['publish_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["publish_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

