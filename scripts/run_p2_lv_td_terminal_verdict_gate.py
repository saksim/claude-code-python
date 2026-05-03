"""Phase 2 card P2-77 gate for Linux CI workflow Linux validation terminal dispatch terminal verdict.

This script consumes the P2-76 Linux validation terminal dispatch final publish archive artifact and
converges one terminal verdict contract:
1) validate Linux validation terminal dispatch final publish archive contract consistency,
2) normalize terminal verdict semantics for downstream consumers,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_STATUSES: set[str] = {
    "archived",
    "archived_with_follow_up",
    "in_progress",
    "blocked",
    "failed",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_DECISIONS: set[str] = {
    "archive_linux_validation_terminal_dispatch_validated",
    "archive_linux_validation_terminal_dispatch_validated_with_follow_up",
    "archive_linux_validation_terminal_dispatch_in_progress",
    "archive_linux_validation_terminal_dispatch_blocker",
    "archive_linux_validation_terminal_dispatch_failure",
    "abort_linux_validation_terminal_dispatch_final_publish_archive",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_CHANNELS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}

ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_VERDICT_STATUSES: set[str] = {
    "ready_for_linux_validation_terminal_dispatch",
    "ready_with_follow_up_for_linux_validation_terminal_dispatch",
    "in_progress",
    "blocked",
    "failed",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_VERDICT_DECISIONS: set[str] = {
    "proceed_linux_validation_terminal_dispatch",
    "proceed_linux_validation_terminal_dispatch_with_follow_up",
    "hold_linux_validation_terminal_dispatch_in_progress",
    "halt_linux_validation_terminal_dispatch_blocker",
    "halt_linux_validation_terminal_dispatch_failure",
    "abort_linux_validation_terminal_dispatch_terminal_verdict",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_VERDICT_CHANNELS: set[str] = {
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


def load_linux_validation_terminal_dispatch_final_publish_archive_report(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(
            f"{path}: Linux validation terminal dispatch final publish archive report not found"
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"{path}: Linux validation terminal dispatch final publish archive payload must be object"
        )

    required_fields = (
        "source_linux_validation_terminal_dispatch_final_verdict_publish_report",
        "source_linux_validation_terminal_dispatch_final_verdict_report",
        "source_linux_validation_terminal_dispatch_terminal_publish_report",
        "source_linux_validation_terminal_dispatch_completion_report",
        "source_linux_validation_terminal_dispatch_trace_report",
        "source_linux_validation_terminal_dispatch_execution_report",
        "source_linux_validation_terminal_dispatch_report",
        "linux_validation_terminal_dispatch_final_publish_archive_status",
        "linux_validation_terminal_dispatch_final_publish_archive_decision",
        "linux_validation_terminal_dispatch_final_publish_archive_exit_code",
        "linux_validation_terminal_dispatch_final_publish_archive_should_archive",
        "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action",
        "linux_validation_terminal_dispatch_final_publish_archive_should_page_owner",
        "linux_validation_terminal_dispatch_final_publish_archive_channel",
        "linux_validation_terminal_dispatch_final_publish_archive_summary",
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

    archive_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_publish_archive_status"],
        field="linux_validation_terminal_dispatch_final_publish_archive_status",
        path=path,
    )
    if (
        archive_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_STATUSES
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_publish_archive_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_STATUSES)}"
        )

    archive_decision = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_publish_archive_decision"],
        field="linux_validation_terminal_dispatch_final_publish_archive_decision",
        path=path,
    )
    if (
        archive_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_publish_archive_decision' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_DECISIONS)}"
        )

    archive_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"],
        field="linux_validation_terminal_dispatch_final_publish_archive_exit_code",
        path=path,
    )
    if archive_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_publish_archive_exit_code' must be >= 0"
        )

    archive_channel = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_publish_archive_channel"],
        field="linux_validation_terminal_dispatch_final_publish_archive_channel",
        path=path,
    )
    if (
        archive_channel
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_CHANNELS
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_publish_archive_channel' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_CHANNELS)}"
        )

    release_run_id = _coerce_optional_int(
        payload["release_run_id"],
        field="release_run_id",
        path=path,
    )

    report = dict(payload)
    report["linux_validation_terminal_dispatch_final_publish_archive_status"] = archive_status
    report["linux_validation_terminal_dispatch_final_publish_archive_decision"] = archive_decision
    report["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = archive_exit_code
    report["linux_validation_terminal_dispatch_final_publish_archive_should_archive"] = _coerce_bool(
        payload["linux_validation_terminal_dispatch_final_publish_archive_should_archive"],
        field="linux_validation_terminal_dispatch_final_publish_archive_should_archive",
        path=path,
    )
    report["linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action"] = _coerce_bool(
        payload["linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action"],
        field="linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action",
        path=path,
    )
    report["linux_validation_terminal_dispatch_final_publish_archive_should_page_owner"] = _coerce_bool(
        payload["linux_validation_terminal_dispatch_final_publish_archive_should_page_owner"],
        field="linux_validation_terminal_dispatch_final_publish_archive_should_page_owner",
        path=path,
    )
    report["linux_validation_terminal_dispatch_final_publish_archive_channel"] = archive_channel
    report["release_run_id"] = release_run_id
    report["release_run_url"] = _coerce_str(
        payload["release_run_url"],
        field="release_run_url",
        path=path,
    )
    report["follow_up_queue_url"] = _coerce_str(
        payload["follow_up_queue_url"],
        field="follow_up_queue_url",
        path=path,
    )
    report["reason_codes"] = _coerce_str_list(
        payload["reason_codes"],
        field="reason_codes",
        path=path,
    )
    report["structural_issues"] = _coerce_str_list(
        payload["structural_issues"],
        field="structural_issues",
        path=path,
    )
    report["missing_artifacts"] = _coerce_str_list(
        payload["missing_artifacts"],
        field="missing_artifacts",
        path=path,
    )
    return report


def build_linux_validation_terminal_dispatch_terminal_verdict_payload(
    final_publish_archive_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    archive_status = str(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_status"
        ]
    )
    archive_decision = str(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_decision"
        ]
    )
    archive_exit_code = int(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_exit_code"
        ]
    )
    archive_should_archive = bool(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_should_archive"
        ]
    )
    archive_requires_manual_action = bool(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action"
        ]
    )
    archive_should_page_owner = bool(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_should_page_owner"
        ]
    )
    archive_channel = str(
        final_publish_archive_report[
            "linux_validation_terminal_dispatch_final_publish_archive_channel"
        ]
    )

    reason_codes = list(final_publish_archive_report["reason_codes"])
    structural_issues = list(final_publish_archive_report["structural_issues"])
    missing_artifacts = list(final_publish_archive_report["missing_artifacts"])

    expected_archive = {
        "archived": (
            "archive_linux_validation_terminal_dispatch_validated",
            0,
            True,
            False,
            False,
            "release",
        ),
        "archived_with_follow_up": (
            "archive_linux_validation_terminal_dispatch_validated_with_follow_up",
            None,
            True,
            False,
            False,
            "follow_up",
        ),
        "in_progress": (
            "archive_linux_validation_terminal_dispatch_in_progress",
            0,
            False,
            False,
            False,
            None,
        ),
        "blocked": (
            "archive_linux_validation_terminal_dispatch_blocker",
            None,
            False,
            True,
            True,
            "blocker",
        ),
        "failed": (
            "archive_linux_validation_terminal_dispatch_failure",
            None,
            False,
            True,
            True,
            "blocker",
        ),
        "contract_failed": (
            "abort_linux_validation_terminal_dispatch_final_publish_archive",
            None,
            False,
            True,
            True,
            "blocker",
        ),
    }
    (
        expected_decision,
        expected_exit_code,
        expected_should_archive,
        expected_requires_manual_action,
        expected_should_page_owner,
        expected_channel,
    ) = expected_archive[archive_status]

    if archive_decision != expected_decision:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_decision_mismatch"
        )
    if archive_should_archive != expected_should_archive:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_should_archive_mismatch"
        )
    if archive_requires_manual_action != expected_requires_manual_action:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action_mismatch"
        )
    if archive_should_page_owner != expected_should_page_owner:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_should_page_owner_mismatch"
        )
    if archive_status == "in_progress":
        if archive_channel not in {"release", "follow_up"}:
            structural_issues.append(
                "linux_validation_terminal_dispatch_final_publish_archive_channel_mismatch"
            )
    elif expected_channel is not None and archive_channel != expected_channel:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_channel_mismatch"
        )
    if expected_exit_code == 0 and archive_exit_code != 0:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_exit_code_mismatch_zero"
        )
    if (
        expected_exit_code is None
        and archive_exit_code == 0
        and archive_status
        in {"archived_with_follow_up", "blocked", "failed", "contract_failed"}
    ):
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_publish_archive_exit_code_mismatch_nonzero"
        )

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    terminal_status: str
    terminal_decision: str
    terminal_exit_code: int
    terminal_should_proceed: bool
    terminal_requires_manual_action: bool
    terminal_should_page_owner: bool
    terminal_channel: str

    if structural_issues or missing_artifacts:
        terminal_status = "contract_failed"
        terminal_decision = "abort_linux_validation_terminal_dispatch_terminal_verdict"
        terminal_exit_code = max(1, archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_should_page_owner = True
        terminal_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif archive_status == "archived":
        terminal_status = "ready_for_linux_validation_terminal_dispatch"
        terminal_decision = "proceed_linux_validation_terminal_dispatch"
        terminal_exit_code = 0
        terminal_should_proceed = True
        terminal_requires_manual_action = False
        terminal_should_page_owner = False
        terminal_channel = "release"
        reason_codes = ["linux_validation_terminal_dispatch_terminal_verdict_ready"]
    elif archive_status == "archived_with_follow_up":
        terminal_status = "ready_with_follow_up_for_linux_validation_terminal_dispatch"
        terminal_decision = "proceed_linux_validation_terminal_dispatch_with_follow_up"
        terminal_exit_code = max(1, archive_exit_code)
        terminal_should_proceed = True
        terminal_requires_manual_action = False
        terminal_should_page_owner = False
        terminal_channel = "follow_up"
        reason_codes.append(
            "linux_validation_terminal_dispatch_terminal_verdict_ready_with_follow_up"
        )
    elif archive_status == "in_progress":
        terminal_status = "in_progress"
        terminal_decision = "hold_linux_validation_terminal_dispatch_in_progress"
        terminal_exit_code = 0
        terminal_should_proceed = False
        terminal_requires_manual_action = False
        terminal_should_page_owner = False
        terminal_channel = "follow_up" if archive_channel == "follow_up" else "release"
        reason_codes.append("linux_validation_terminal_dispatch_terminal_verdict_in_progress")
    elif archive_status == "blocked":
        terminal_status = "blocked"
        terminal_decision = "halt_linux_validation_terminal_dispatch_blocker"
        terminal_exit_code = max(1, archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_should_page_owner = True
        terminal_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_terminal_verdict_blocked")
    elif archive_status == "failed":
        terminal_status = "failed"
        terminal_decision = "halt_linux_validation_terminal_dispatch_failure"
        terminal_exit_code = max(1, archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_should_page_owner = True
        terminal_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_terminal_verdict_failed")
    else:
        terminal_status = "contract_failed"
        terminal_decision = "abort_linux_validation_terminal_dispatch_terminal_verdict"
        terminal_exit_code = max(1, archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_should_page_owner = True
        terminal_channel = "blocker"
        reason_codes.append(
            "linux_validation_terminal_dispatch_terminal_verdict_upstream_contract_failed"
        )

    if (
        terminal_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_VERDICT_STATUSES
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_terminal_verdict_status computed"
        )
    if (
        terminal_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_VERDICT_DECISIONS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_terminal_verdict_decision computed"
        )
    if (
        terminal_channel
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_VERDICT_CHANNELS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_terminal_verdict_channel computed"
        )

    reason_codes = _unique(reason_codes)
    summary = (
        "linux_validation_terminal_dispatch_final_publish_archive_status="
        f"{archive_status} "
        "linux_validation_terminal_dispatch_terminal_verdict_status="
        f"{terminal_status} "
        "linux_validation_terminal_dispatch_terminal_verdict_decision="
        f"{terminal_decision}"
    )

    payload = dict(final_publish_archive_report)
    payload.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_linux_validation_terminal_dispatch_final_publish_archive_report": str(
                source_path
            ),
            "linux_validation_terminal_dispatch_terminal_verdict_status": terminal_status,
            "linux_validation_terminal_dispatch_terminal_verdict_decision": terminal_decision,
            "linux_validation_terminal_dispatch_terminal_verdict_exit_code": terminal_exit_code,
            "linux_validation_terminal_dispatch_terminal_verdict_should_proceed": terminal_should_proceed,
            "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action": terminal_requires_manual_action,
            "linux_validation_terminal_dispatch_terminal_verdict_should_page_owner": terminal_should_page_owner,
            "linux_validation_terminal_dispatch_terminal_verdict_channel": terminal_channel,
            "linux_validation_terminal_dispatch_terminal_verdict_summary": summary,
            "reason_codes": reason_codes,
            "structural_issues": structural_issues,
            "missing_artifacts": missing_artifacts,
        }
    )
    return payload


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux Validation Terminal Dispatch Terminal Verdict Report",
        "",
        (
            "- Terminal Verdict Status: "
            f"**{str(payload['linux_validation_terminal_dispatch_terminal_verdict_status']).upper()}**"
        ),
        (
            "- Terminal Verdict Decision: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_verdict_decision']}`"
        ),
        (
            "- Terminal Verdict Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_verdict_exit_code']}`"
        ),
        (
            "- Should Proceed: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_verdict_should_proceed']}`"
        ),
        (
            "- Requires Manual Action: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action']}`"
        ),
        (
            "- Should Page Owner: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_verdict_should_page_owner']}`"
        ),
        (
            "- Channel: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_verdict_channel']}`"
        ),
        (
            "- Upstream Final Publish Archive Status: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_status']}`"
        ),
        (
            "- Upstream Final Publish Archive Channel: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_channel']}`"
        ),
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['linux_validation_terminal_dispatch_terminal_verdict_summary']}",
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
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_status": str(
            payload["linux_validation_terminal_dispatch_terminal_verdict_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_decision": str(
            payload["linux_validation_terminal_dispatch_terminal_verdict_decision"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_exit_code": str(
            payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_should_proceed": (
            "true"
            if payload["linux_validation_terminal_dispatch_terminal_verdict_should_proceed"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action": (
            "true"
            if payload[
                "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
            ]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_should_page_owner": (
            "true"
            if payload["linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_channel": str(
            payload["linux_validation_terminal_dispatch_terminal_verdict_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_final_publish_archive_status": str(
            payload["linux_validation_terminal_dispatch_final_publish_archive_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_final_publish_archive_channel": str(
            payload["linux_validation_terminal_dispatch_final_publish_archive_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_run_url": str(
            payload["release_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_report_json": str(
            output_json
        ),
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_report_markdown": str(
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
            "Converge Linux validation terminal dispatch terminal verdict contract "
            "from P2-76 final publish archive report"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-publish-archive-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json",
        help="P2-76 Linux validation terminal dispatch final publish archive report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json",
        help="Output Linux validation terminal dispatch terminal verdict JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.md",
        help="Output Linux validation terminal dispatch terminal verdict markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal dispatch terminal verdict JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    final_publish_archive_report_path = Path(
        args.linux_validation_terminal_dispatch_final_publish_archive_report
    )
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        final_publish_archive_report = (
            load_linux_validation_terminal_dispatch_final_publish_archive_report(
                final_publish_archive_report_path
            )
        )
        payload = build_linux_validation_terminal_dispatch_terminal_verdict_payload(
            final_publish_archive_report,
            source_path=final_publish_archive_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-terminal-verdict-gate] "
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
        output_markdown_path.write_text(
            render_markdown_report(payload),
            encoding="utf-8",
        )
        print(
            "linux validation terminal dispatch terminal verdict json: "
            f"{output_json_path}"
        )
        print(
            "linux validation terminal dispatch terminal verdict markdown: "
            f"{output_markdown_path}"
        )

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
        "linux validation terminal dispatch terminal verdict summary: "
        "linux_validation_terminal_dispatch_terminal_verdict_status="
        f"{payload['linux_validation_terminal_dispatch_terminal_verdict_status']} "
        "linux_validation_terminal_dispatch_terminal_verdict_decision="
        f"{payload['linux_validation_terminal_dispatch_terminal_verdict_decision']} "
        "linux_validation_terminal_dispatch_terminal_verdict_exit_code="
        f"{payload['linux_validation_terminal_dispatch_terminal_verdict_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
