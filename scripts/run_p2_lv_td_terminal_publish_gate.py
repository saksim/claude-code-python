"""Phase 2 card P2-73 gate for Linux CI workflow Linux validation terminal dispatch terminal publish.

This script consumes the P2-72 Linux validation terminal dispatch completion artifact and
converges one terminal publish contract:
1) validate Linux validation terminal dispatch completion contract,
2) normalize terminal publish semantics for downstream handoff consumers,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_COMPLETION_STATUSES: set[str] = {
    "ready_dry_run",
    "ready_with_follow_up_dry_run",
    "dispatch_failed",
    "blocked",
    "contract_failed",
    "run_tracking_ready",
    "run_tracking_missing",
    "run_poll_failed",
    "run_in_progress",
    "run_completed_success",
    "run_completed_failure",
    "run_await_timeout",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_STATUSES: set[str] = {
    "terminal_published",
    "terminal_published_with_follow_up",
    "terminal_in_progress",
    "terminal_blocked",
    "terminal_failed",
    "terminal_contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_DECISIONS: set[str] = {
    "announce_linux_validation_terminal_dispatch_completed",
    "announce_linux_validation_terminal_dispatch_completed_with_follow_up",
    "announce_linux_validation_terminal_dispatch_in_progress",
    "announce_linux_validation_terminal_dispatch_blocker",
    "announce_linux_validation_terminal_dispatch_failed",
    "abort_linux_validation_terminal_dispatch_terminal_publish",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_CHANNELS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}


def _coerce_bool(value: Any, *, field: str, path: Path) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path}: field '{field}' must be bool")
    return value


def _coerce_int(value: Any, *, field: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path}: field '{field}' must be int")
    return value


def _coerce_optional_int(value: Any, *, field: str, path: Path) -> int | None:
    if value is None:
        return None
    return _coerce_int(value, field=field, path=path)


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


def load_linux_validation_terminal_dispatch_completion_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: Linux validation terminal dispatch completion report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"{path}: Linux validation terminal dispatch completion payload must be object"
        )

    required_fields = (
        "source_linux_validation_terminal_dispatch_trace_report",
        "project_root",
        "source_linux_validation_terminal_dispatch_execution_report",
        "source_linux_validation_terminal_dispatch_report",
        "linux_validation_terminal_dispatch_execution_status",
        "linux_validation_terminal_dispatch_execution_decision",
        "linux_validation_terminal_dispatch_execution_exit_code",
        "linux_validation_terminal_should_dispatch",
        "linux_validation_terminal_dispatch_attempted",
        "linux_validation_terminal_dispatch_trace_status",
        "linux_validation_terminal_dispatch_trace_exit_code",
        "linux_validation_terminal_dispatch_completion_status",
        "linux_validation_terminal_dispatch_completion_exit_code",
        "dry_run",
        "allow_in_progress",
        "should_poll_workflow_run",
        "linux_validation_terminal_run_id",
        "linux_validation_terminal_run_url",
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    completion_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_completion_status"],
        field="linux_validation_terminal_dispatch_completion_status",
        path=path,
    )
    if (
        completion_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_COMPLETION_STATUSES
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_completion_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_COMPLETION_STATUSES)}"
        )

    completion_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_completion_exit_code"],
        field="linux_validation_terminal_dispatch_completion_exit_code",
        path=path,
    )
    if completion_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_completion_exit_code' must be >= 0"
        )

    run_id = _coerce_optional_int(
        payload["linux_validation_terminal_run_id"],
        field="linux_validation_terminal_run_id",
        path=path,
    )
    release_run_id = _coerce_optional_int(
        payload["release_run_id"],
        field="release_run_id",
        path=path,
    )

    return {
        "generated_at": payload.get("generated_at"),
        "source_linux_validation_terminal_dispatch_trace_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_trace_report"],
            field="source_linux_validation_terminal_dispatch_trace_report",
            path=path,
        ),
        "project_root": _coerce_str(payload["project_root"], field="project_root", path=path),
        "source_linux_validation_terminal_dispatch_execution_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_execution_report"],
            field="source_linux_validation_terminal_dispatch_execution_report",
            path=path,
        ),
        "source_linux_validation_terminal_dispatch_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_report"],
            field="source_linux_validation_terminal_dispatch_report",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_status": _coerce_str(
            payload["linux_validation_terminal_dispatch_execution_status"],
            field="linux_validation_terminal_dispatch_execution_status",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_decision": _coerce_str(
            payload["linux_validation_terminal_dispatch_execution_decision"],
            field="linux_validation_terminal_dispatch_execution_decision",
            path=path,
        ),
        "linux_validation_terminal_dispatch_execution_exit_code": _coerce_int(
            payload["linux_validation_terminal_dispatch_execution_exit_code"],
            field="linux_validation_terminal_dispatch_execution_exit_code",
            path=path,
        ),
        "linux_validation_terminal_should_dispatch": _coerce_bool(
            payload["linux_validation_terminal_should_dispatch"],
            field="linux_validation_terminal_should_dispatch",
            path=path,
        ),
        "linux_validation_terminal_dispatch_attempted": _coerce_bool(
            payload["linux_validation_terminal_dispatch_attempted"],
            field="linux_validation_terminal_dispatch_attempted",
            path=path,
        ),
        "linux_validation_terminal_dispatch_trace_status": _coerce_str(
            payload["linux_validation_terminal_dispatch_trace_status"],
            field="linux_validation_terminal_dispatch_trace_status",
            path=path,
        ),
        "linux_validation_terminal_dispatch_trace_exit_code": _coerce_int(
            payload["linux_validation_terminal_dispatch_trace_exit_code"],
            field="linux_validation_terminal_dispatch_trace_exit_code",
            path=path,
        ),
        "linux_validation_terminal_dispatch_completion_status": completion_status,
        "linux_validation_terminal_dispatch_completion_exit_code": completion_exit_code,
        "dry_run": _coerce_bool(payload["dry_run"], field="dry_run", path=path),
        "allow_in_progress": _coerce_bool(
            payload["allow_in_progress"],
            field="allow_in_progress",
            path=path,
        ),
        "should_poll_workflow_run": _coerce_bool(
            payload["should_poll_workflow_run"],
            field="should_poll_workflow_run",
            path=path,
        ),
        "linux_validation_terminal_run_id": run_id,
        "linux_validation_terminal_run_url": _coerce_str(
            payload["linux_validation_terminal_run_url"],
            field="linux_validation_terminal_run_url",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(
            payload["release_run_url"],
            field="release_run_url",
            path=path,
        ),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "reason_codes": _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path),
        "structural_issues": _coerce_str_list(
            payload["structural_issues"],
            field="structural_issues",
            path=path,
        ),
        "missing_artifacts": _coerce_str_list(
            payload["missing_artifacts"],
            field="missing_artifacts",
            path=path,
        ),
    }


def build_linux_validation_terminal_dispatch_terminal_publish_payload(
    completion_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    completion_status = str(completion_report["linux_validation_terminal_dispatch_completion_status"])
    completion_exit_code = int(completion_report["linux_validation_terminal_dispatch_completion_exit_code"])
    reason_codes = list(completion_report["reason_codes"])
    structural_issues = list(completion_report["structural_issues"])
    missing_artifacts = list(completion_report["missing_artifacts"])

    execution_status = str(completion_report["linux_validation_terminal_dispatch_execution_status"])
    execution_decision = str(completion_report["linux_validation_terminal_dispatch_execution_decision"])
    follow_up_queue_url = str(completion_report["follow_up_queue_url"])
    is_follow_up = (
        execution_decision.endswith("_with_follow_up")
        or execution_status == "ready_with_follow_up_dry_run"
        or bool(follow_up_queue_url)
    )

    if completion_status == "run_completed_success" and completion_exit_code != 0:
        structural_issues.append("linux_validation_terminal_dispatch_completion_exit_code_mismatch_success")
    if completion_status in {
        "run_tracking_missing",
        "run_completed_failure",
        "run_poll_failed",
        "dispatch_failed",
    } and completion_exit_code == 0:
        structural_issues.append("linux_validation_terminal_dispatch_completion_exit_code_mismatch_failure")
    if completion_status == "run_await_timeout":
        allow_in_progress = bool(completion_report["allow_in_progress"])
        if allow_in_progress and completion_exit_code != 0:
            structural_issues.append("linux_validation_terminal_dispatch_completion_timeout_policy_mismatch")
        if not allow_in_progress and completion_exit_code == 0:
            structural_issues.append("linux_validation_terminal_dispatch_completion_timeout_policy_mismatch")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        terminal_publish_status = "terminal_contract_failed"
        terminal_publish_decision = "abort_linux_validation_terminal_dispatch_terminal_publish"
        terminal_publish_exit_code = max(1, completion_exit_code)
        terminal_publish_should_notify = True
        terminal_publish_ready_for_handoff = False
        terminal_publish_requires_manual_action = True
        terminal_publish_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif completion_status == "contract_failed":
        terminal_publish_status = "terminal_contract_failed"
        terminal_publish_decision = "abort_linux_validation_terminal_dispatch_terminal_publish"
        terminal_publish_exit_code = max(1, completion_exit_code)
        terminal_publish_should_notify = True
        terminal_publish_ready_for_handoff = False
        terminal_publish_requires_manual_action = True
        terminal_publish_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_completion_contract_failed")
    elif completion_status == "run_completed_success":
        terminal_publish_should_notify = True
        terminal_publish_ready_for_handoff = True
        terminal_publish_requires_manual_action = False
        if is_follow_up:
            terminal_publish_status = "terminal_published_with_follow_up"
            terminal_publish_decision = "announce_linux_validation_terminal_dispatch_completed_with_follow_up"
            terminal_publish_exit_code = max(1, completion_exit_code)
            terminal_publish_channel = "follow_up"
            reason_codes.append("linux_validation_terminal_dispatch_terminal_publish_with_follow_up")
        else:
            terminal_publish_status = "terminal_published"
            terminal_publish_decision = "announce_linux_validation_terminal_dispatch_completed"
            terminal_publish_exit_code = 0
            terminal_publish_channel = "release"
            reason_codes = ["linux_validation_terminal_dispatch_terminal_publish_completed"]
    elif completion_status in {"run_in_progress", "run_tracking_ready"} or (
        completion_status == "run_await_timeout"
        and bool(completion_report["allow_in_progress"])
        and completion_exit_code == 0
    ):
        terminal_publish_status = "terminal_in_progress"
        terminal_publish_decision = "announce_linux_validation_terminal_dispatch_in_progress"
        terminal_publish_exit_code = 0
        terminal_publish_should_notify = True
        terminal_publish_ready_for_handoff = False
        terminal_publish_requires_manual_action = False
        terminal_publish_channel = "follow_up" if is_follow_up else "release"
        reason_codes.append("linux_validation_terminal_dispatch_terminal_publish_in_progress")
    elif completion_status in {"ready_dry_run", "ready_with_follow_up_dry_run", "blocked"}:
        terminal_publish_status = "terminal_blocked"
        terminal_publish_decision = "announce_linux_validation_terminal_dispatch_blocker"
        terminal_publish_exit_code = max(1, completion_exit_code)
        terminal_publish_should_notify = True
        terminal_publish_ready_for_handoff = False
        terminal_publish_requires_manual_action = True
        terminal_publish_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_terminal_publish_blocked")
    else:
        terminal_publish_status = "terminal_failed"
        terminal_publish_decision = "announce_linux_validation_terminal_dispatch_failed"
        terminal_publish_exit_code = max(1, completion_exit_code)
        terminal_publish_should_notify = True
        terminal_publish_ready_for_handoff = False
        terminal_publish_requires_manual_action = True
        terminal_publish_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_terminal_publish_failed")

    if (
        terminal_publish_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_STATUSES
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_terminal_publish_status computed"
        )
    if (
        terminal_publish_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_DECISIONS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_terminal_publish_decision computed"
        )
    if (
        terminal_publish_channel
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_CHANNELS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_terminal_publish_channel computed"
        )

    reason_codes = _unique(reason_codes)
    summary = (
        f"linux_validation_terminal_dispatch_completion_status={completion_status} "
        f"linux_validation_terminal_dispatch_terminal_publish_status={terminal_publish_status} "
        f"linux_validation_terminal_dispatch_terminal_publish_decision={terminal_publish_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_linux_validation_terminal_dispatch_completion_report": str(source_path),
        "source_linux_validation_terminal_dispatch_trace_report": str(
            completion_report["source_linux_validation_terminal_dispatch_trace_report"]
        ),
        "source_linux_validation_terminal_dispatch_execution_report": str(
            completion_report["source_linux_validation_terminal_dispatch_execution_report"]
        ),
        "source_linux_validation_terminal_dispatch_report": str(
            completion_report["source_linux_validation_terminal_dispatch_report"]
        ),
        "linux_validation_terminal_dispatch_completion_status": completion_status,
        "linux_validation_terminal_dispatch_completion_exit_code": completion_exit_code,
        "linux_validation_terminal_dispatch_execution_status": execution_status,
        "linux_validation_terminal_dispatch_execution_decision": execution_decision,
        "linux_validation_terminal_dispatch_execution_exit_code": int(
            completion_report["linux_validation_terminal_dispatch_execution_exit_code"]
        ),
        "linux_validation_terminal_should_dispatch": bool(
            completion_report["linux_validation_terminal_should_dispatch"]
        ),
        "linux_validation_terminal_dispatch_attempted": bool(
            completion_report["linux_validation_terminal_dispatch_attempted"]
        ),
        "linux_validation_terminal_dispatch_trace_status": str(
            completion_report["linux_validation_terminal_dispatch_trace_status"]
        ),
        "linux_validation_terminal_dispatch_trace_exit_code": int(
            completion_report["linux_validation_terminal_dispatch_trace_exit_code"]
        ),
        "should_poll_workflow_run": bool(completion_report["should_poll_workflow_run"]),
        "allow_in_progress": bool(completion_report["allow_in_progress"]),
        "linux_validation_terminal_run_id": completion_report["linux_validation_terminal_run_id"],
        "linux_validation_terminal_run_url": str(completion_report["linux_validation_terminal_run_url"]),
        "release_run_id": completion_report["release_run_id"],
        "release_run_url": str(completion_report["release_run_url"]),
        "follow_up_queue_url": follow_up_queue_url,
        "linux_validation_terminal_dispatch_terminal_publish_status": terminal_publish_status,
        "linux_validation_terminal_dispatch_terminal_publish_decision": terminal_publish_decision,
        "linux_validation_terminal_dispatch_terminal_publish_exit_code": terminal_publish_exit_code,
        "linux_validation_terminal_dispatch_terminal_publish_should_notify": terminal_publish_should_notify,
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff": terminal_publish_ready_for_handoff,
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action": terminal_publish_requires_manual_action,
        "linux_validation_terminal_dispatch_terminal_publish_channel": terminal_publish_channel,
        "linux_validation_terminal_dispatch_terminal_publish_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux Validation Terminal Dispatch Terminal Publish Report",
        "",
        (
            "- Terminal Publish Status: "
            f"**{str(payload['linux_validation_terminal_dispatch_terminal_publish_status']).upper()}**"
        ),
        (
            "- Terminal Publish Decision: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_decision']}`"
        ),
        (
            "- Terminal Publish Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_exit_code']}`"
        ),
        (
            "- Should Notify: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_should_notify']}`"
        ),
        (
            "- Ready For Handoff: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff']}`"
        ),
        (
            "- Requires Manual Action: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_requires_manual_action']}`"
        ),
        (
            "- Channel: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_channel']}`"
        ),
        f"- Completion Status: `{payload['linux_validation_terminal_dispatch_completion_status']}`",
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['linux_validation_terminal_dispatch_terminal_publish_summary']}",
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

    lines.extend(["", "## Missing Artifacts"])
    missing_artifacts = payload["missing_artifacts"]
    if missing_artifacts:
        lines.extend(f"- `{item}`" for item in missing_artifacts)
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    return {
        "workflow_linux_validation_terminal_dispatch_terminal_publish_status": str(
            payload["linux_validation_terminal_dispatch_terminal_publish_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_decision": str(
            payload["linux_validation_terminal_dispatch_terminal_publish_decision"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_exit_code": str(
            payload["linux_validation_terminal_dispatch_terminal_publish_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_should_notify": (
            "true"
            if payload["linux_validation_terminal_dispatch_terminal_publish_should_notify"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff": (
            "true"
            if payload["linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_requires_manual_action": (
            "true"
            if payload["linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_channel": str(
            payload["linux_validation_terminal_dispatch_terminal_publish_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_run_url": str(
            payload["release_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_report_json": str(output_json),
        "workflow_linux_validation_terminal_dispatch_terminal_publish_report_markdown": str(
            output_markdown
        ),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux validation terminal dispatch terminal publish contract "
            "from P2-72 completion report"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-completion-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.json",
        help="P2-72 Linux validation terminal dispatch completion report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json",
        help="Output Linux validation terminal dispatch terminal publish JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.md",
        help="Output Linux validation terminal dispatch terminal publish markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal dispatch terminal publish JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    completion_report_path = Path(args.linux_validation_terminal_dispatch_completion_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        completion_report = load_linux_validation_terminal_dispatch_completion_report(
            completion_report_path
        )
        payload = build_linux_validation_terminal_dispatch_terminal_publish_payload(
            completion_report,
            source_path=completion_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-terminal-publish-gate] "
            f"{exc}",
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
        print(f"linux validation terminal dispatch terminal publish json: {output_json_path}")
        print(f"linux validation terminal dispatch terminal publish markdown: {output_markdown_path}")

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
        "linux validation terminal dispatch terminal publish summary: "
        "linux_validation_terminal_dispatch_terminal_publish_status="
        f"{payload['linux_validation_terminal_dispatch_terminal_publish_status']} "
        "linux_validation_terminal_dispatch_terminal_publish_decision="
        f"{payload['linux_validation_terminal_dispatch_terminal_publish_decision']} "
        "linux_validation_terminal_dispatch_terminal_publish_exit_code="
        f"{payload['linux_validation_terminal_dispatch_terminal_publish_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_terminal_publish_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
