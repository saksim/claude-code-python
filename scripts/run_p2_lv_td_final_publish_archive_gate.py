"""Phase 2 card P2-76 gate for Linux CI workflow Linux validation terminal dispatch final publish archive.

This script consumes the P2-75 Linux validation terminal dispatch final verdict publish artifact and
converges one final publish archive contract:
1) validate Linux validation terminal dispatch final verdict publish contract consistency,
2) normalize final publish archive semantics for downstream consumers,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_STATUSES: set[str] = {
    "published",
    "published_with_follow_up",
    "in_progress",
    "blocked",
    "failed",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_DECISIONS: set[str] = {
    "announce_linux_validation_terminal_dispatch_validated",
    "announce_linux_validation_terminal_dispatch_validated_with_follow_up",
    "announce_linux_validation_terminal_dispatch_in_progress",
    "announce_linux_validation_terminal_dispatch_blocker",
    "announce_linux_validation_terminal_dispatch_failure",
    "abort_linux_validation_terminal_dispatch_final_verdict_publish",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_CHANNELS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}

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


def load_linux_validation_terminal_dispatch_final_verdict_publish_report(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(
            f"{path}: Linux validation terminal dispatch final verdict publish report not found"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"{path}: Linux validation terminal dispatch final verdict publish payload must be object"
        )

    required_fields = (
        "source_linux_validation_terminal_dispatch_final_verdict_report",
        "source_linux_validation_terminal_dispatch_terminal_publish_report",
        "source_linux_validation_terminal_dispatch_completion_report",
        "source_linux_validation_terminal_dispatch_trace_report",
        "source_linux_validation_terminal_dispatch_execution_report",
        "source_linux_validation_terminal_dispatch_report",
        "linux_validation_terminal_dispatch_final_verdict_status",
        "linux_validation_terminal_dispatch_final_verdict_decision",
        "linux_validation_terminal_dispatch_final_verdict_exit_code",
        "linux_validation_terminal_dispatch_final_should_accept",
        "linux_validation_terminal_dispatch_final_requires_follow_up",
        "linux_validation_terminal_dispatch_final_should_page_owner",
        "linux_validation_terminal_dispatch_final_channel",
        "linux_validation_terminal_dispatch_final_verdict_publish_status",
        "linux_validation_terminal_dispatch_final_verdict_publish_decision",
        "linux_validation_terminal_dispatch_final_verdict_publish_exit_code",
        "linux_validation_terminal_dispatch_final_verdict_publish_should_notify",
        "linux_validation_terminal_dispatch_final_verdict_publish_requires_manual_action",
        "linux_validation_terminal_dispatch_final_verdict_publish_should_page_owner",
        "linux_validation_terminal_dispatch_final_verdict_publish_channel",
        "linux_validation_terminal_dispatch_final_verdict_publish_summary",
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

    verdict_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_verdict_publish_status"],
        field="linux_validation_terminal_dispatch_final_verdict_publish_status",
        path=path,
    )
    if (
        verdict_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_STATUSES
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_verdict_publish_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_STATUSES)}"
        )

    verdict_decision = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_verdict_publish_decision"],
        field="linux_validation_terminal_dispatch_final_verdict_publish_decision",
        path=path,
    )
    if (
        verdict_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_verdict_publish_decision' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_DECISIONS)}"
        )

    verdict_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_final_verdict_publish_exit_code"],
        field="linux_validation_terminal_dispatch_final_verdict_publish_exit_code",
        path=path,
    )
    if verdict_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_verdict_publish_exit_code' must be >= 0"
        )

    verdict_channel = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_verdict_publish_channel"],
        field="linux_validation_terminal_dispatch_final_verdict_publish_channel",
        path=path,
    )
    if (
        verdict_channel
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_CHANNELS
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_final_verdict_publish_channel' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_PUBLISH_CHANNELS)}"
        )

    release_run_id = _coerce_optional_int(
        payload["release_run_id"],
        field="release_run_id",
        path=path,
    )

    report = dict(payload)
    report["linux_validation_terminal_dispatch_final_verdict_publish_status"] = verdict_status
    report["linux_validation_terminal_dispatch_final_verdict_publish_decision"] = verdict_decision
    report["linux_validation_terminal_dispatch_final_verdict_publish_exit_code"] = verdict_exit_code
    report["linux_validation_terminal_dispatch_final_verdict_publish_should_notify"] = _coerce_bool(
        payload["linux_validation_terminal_dispatch_final_verdict_publish_should_notify"],
        field="linux_validation_terminal_dispatch_final_verdict_publish_should_notify",
        path=path,
    )
    report[
        "linux_validation_terminal_dispatch_final_verdict_publish_requires_manual_action"
    ] = _coerce_bool(
        payload[
            "linux_validation_terminal_dispatch_final_verdict_publish_requires_manual_action"
        ],
        field="linux_validation_terminal_dispatch_final_verdict_publish_requires_manual_action",
        path=path,
    )
    report["linux_validation_terminal_dispatch_final_verdict_publish_should_page_owner"] = (
        _coerce_bool(
            payload["linux_validation_terminal_dispatch_final_verdict_publish_should_page_owner"],
            field="linux_validation_terminal_dispatch_final_verdict_publish_should_page_owner",
            path=path,
        )
    )
    report["linux_validation_terminal_dispatch_final_verdict_publish_channel"] = verdict_channel
    report["linux_validation_terminal_dispatch_final_verdict_status"] = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_verdict_status"],
        field="linux_validation_terminal_dispatch_final_verdict_status",
        path=path,
    )
    report["linux_validation_terminal_dispatch_final_channel"] = _coerce_str(
        payload["linux_validation_terminal_dispatch_final_channel"],
        field="linux_validation_terminal_dispatch_final_channel",
        path=path,
    )
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


def build_linux_validation_terminal_dispatch_final_publish_archive_payload(
    final_verdict_publish_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    verdict_status = str(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_status"
        ]
    )
    verdict_decision = str(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_decision"
        ]
    )
    verdict_exit_code = int(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_exit_code"
        ]
    )
    verdict_should_notify = bool(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_should_notify"
        ]
    )
    verdict_requires_manual_action = bool(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_requires_manual_action"
        ]
    )
    verdict_should_page_owner = bool(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_should_page_owner"
        ]
    )
    verdict_channel = str(
        final_verdict_publish_report[
            "linux_validation_terminal_dispatch_final_verdict_publish_channel"
        ]
    )

    reason_codes = list(final_verdict_publish_report["reason_codes"])
    structural_issues = list(final_verdict_publish_report["structural_issues"])
    missing_artifacts = list(final_verdict_publish_report["missing_artifacts"])

    expected_verdict = {
        "published": (
            "announce_linux_validation_terminal_dispatch_validated",
            0,
            True,
            False,
            False,
            "release",
        ),
        "published_with_follow_up": (
            "announce_linux_validation_terminal_dispatch_validated_with_follow_up",
            None,
            True,
            False,
            False,
            "follow_up",
        ),
        "in_progress": (
            "announce_linux_validation_terminal_dispatch_in_progress",
            0,
            True,
            False,
            False,
            None,
        ),
        "blocked": (
            "announce_linux_validation_terminal_dispatch_blocker",
            None,
            True,
            True,
            True,
            "blocker",
        ),
        "failed": (
            "announce_linux_validation_terminal_dispatch_failure",
            None,
            True,
            True,
            True,
            "blocker",
        ),
        "contract_failed": (
            "abort_linux_validation_terminal_dispatch_final_verdict_publish",
            None,
            True,
            True,
            True,
            "blocker",
        ),
    }
    (
        expected_decision,
        expected_exit_code,
        expected_should_notify,
        expected_requires_manual_action,
        expected_should_page_owner,
        expected_channel,
    ) = expected_verdict[verdict_status]

    if verdict_decision != expected_decision:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_decision_mismatch"
        )
    if verdict_should_notify != expected_should_notify:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_should_notify_mismatch"
        )
    if verdict_requires_manual_action != expected_requires_manual_action:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_requires_manual_action_mismatch"
        )
    if verdict_should_page_owner != expected_should_page_owner:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_should_page_owner_mismatch"
        )
    if verdict_status == "in_progress":
        if verdict_channel not in {"release", "follow_up"}:
            structural_issues.append(
                "linux_validation_terminal_dispatch_final_verdict_publish_channel_mismatch"
            )
    elif expected_channel is not None and verdict_channel != expected_channel:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_channel_mismatch"
        )
    if expected_exit_code == 0 and verdict_exit_code != 0:
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_exit_code_mismatch_zero"
        )
    if (
        expected_exit_code is None
        and verdict_exit_code == 0
        and verdict_status
        in {"published_with_follow_up", "blocked", "failed", "contract_failed"}
    ):
        structural_issues.append(
            "linux_validation_terminal_dispatch_final_verdict_publish_exit_code_mismatch_nonzero"
        )

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    archive_status: str
    archive_decision: str
    archive_exit_code: int
    archive_should_archive: bool
    archive_requires_manual_action: bool
    archive_should_page_owner: bool
    archive_channel: str

    if structural_issues or missing_artifacts:
        archive_status = "contract_failed"
        archive_decision = "abort_linux_validation_terminal_dispatch_final_publish_archive"
        archive_exit_code = max(1, verdict_exit_code)
        archive_should_archive = False
        archive_requires_manual_action = True
        archive_should_page_owner = True
        archive_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif verdict_status == "published":
        archive_status = "archived"
        archive_decision = "archive_linux_validation_terminal_dispatch_validated"
        archive_exit_code = 0
        archive_should_archive = True
        archive_requires_manual_action = False
        archive_should_page_owner = False
        archive_channel = "release"
        reason_codes = ["linux_validation_terminal_dispatch_final_publish_archive_archived"]
    elif verdict_status == "published_with_follow_up":
        archive_status = "archived_with_follow_up"
        archive_decision = (
            "archive_linux_validation_terminal_dispatch_validated_with_follow_up"
        )
        archive_exit_code = max(1, verdict_exit_code)
        archive_should_archive = True
        archive_requires_manual_action = False
        archive_should_page_owner = False
        archive_channel = "follow_up"
        reason_codes.append(
            "linux_validation_terminal_dispatch_final_publish_archive_archived_with_follow_up"
        )
    elif verdict_status == "in_progress":
        archive_status = "in_progress"
        archive_decision = "archive_linux_validation_terminal_dispatch_in_progress"
        archive_exit_code = 0
        archive_should_archive = False
        archive_requires_manual_action = False
        archive_should_page_owner = False
        archive_channel = "follow_up" if verdict_channel == "follow_up" else "release"
        reason_codes.append(
            "linux_validation_terminal_dispatch_final_publish_archive_in_progress"
        )
    elif verdict_status == "blocked":
        archive_status = "blocked"
        archive_decision = "archive_linux_validation_terminal_dispatch_blocker"
        archive_exit_code = max(1, verdict_exit_code)
        archive_should_archive = False
        archive_requires_manual_action = True
        archive_should_page_owner = True
        archive_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_final_publish_archive_blocked")
    elif verdict_status == "failed":
        archive_status = "failed"
        archive_decision = "archive_linux_validation_terminal_dispatch_failure"
        archive_exit_code = max(1, verdict_exit_code)
        archive_should_archive = False
        archive_requires_manual_action = True
        archive_should_page_owner = True
        archive_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_final_publish_archive_failed")
    else:
        archive_status = "contract_failed"
        archive_decision = "abort_linux_validation_terminal_dispatch_final_publish_archive"
        archive_exit_code = max(1, verdict_exit_code)
        archive_should_archive = False
        archive_requires_manual_action = True
        archive_should_page_owner = True
        archive_channel = "blocker"
        reason_codes.append(
            "linux_validation_terminal_dispatch_final_publish_archive_upstream_contract_failed"
        )

    if (
        archive_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_STATUSES
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_final_publish_archive_status computed"
        )
    if (
        archive_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_DECISIONS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_final_publish_archive_decision computed"
        )
    if (
        archive_channel
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_PUBLISH_ARCHIVE_CHANNELS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_final_publish_archive_channel computed"
        )

    reason_codes = _unique(reason_codes)
    summary = (
        "linux_validation_terminal_dispatch_final_verdict_publish_status="
        f"{verdict_status} "
        "linux_validation_terminal_dispatch_final_publish_archive_status="
        f"{archive_status} "
        "linux_validation_terminal_dispatch_final_publish_archive_decision="
        f"{archive_decision}"
    )

    payload = dict(final_verdict_publish_report)
    payload.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_linux_validation_terminal_dispatch_final_verdict_publish_report": str(
                source_path
            ),
            "linux_validation_terminal_dispatch_final_publish_archive_status": archive_status,
            "linux_validation_terminal_dispatch_final_publish_archive_decision": archive_decision,
            "linux_validation_terminal_dispatch_final_publish_archive_exit_code": archive_exit_code,
            "linux_validation_terminal_dispatch_final_publish_archive_should_archive": archive_should_archive,
            "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action": archive_requires_manual_action,
            "linux_validation_terminal_dispatch_final_publish_archive_should_page_owner": archive_should_page_owner,
            "linux_validation_terminal_dispatch_final_publish_archive_channel": archive_channel,
            "linux_validation_terminal_dispatch_final_publish_archive_summary": summary,
            "reason_codes": reason_codes,
            "structural_issues": structural_issues,
            "missing_artifacts": missing_artifacts,
        }
    )
    return payload


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux Validation Terminal Dispatch Final Publish Archive Report",
        "",
        (
            "- Final Publish Archive Status: "
            f"**{str(payload['linux_validation_terminal_dispatch_final_publish_archive_status']).upper()}**"
        ),
        (
            "- Final Publish Archive Decision: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_decision']}`"
        ),
        (
            "- Final Publish Archive Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_exit_code']}`"
        ),
        (
            "- Should Archive: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_should_archive']}`"
        ),
        (
            "- Requires Manual Action: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action']}`"
        ),
        (
            "- Should Page Owner: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_should_page_owner']}`"
        ),
        (
            "- Channel: "
            f"`{payload['linux_validation_terminal_dispatch_final_publish_archive_channel']}`"
        ),
        (
            "- Upstream Publish Status: "
            f"`{payload['linux_validation_terminal_dispatch_final_verdict_publish_status']}`"
        ),
        (
            "- Upstream Publish Channel: "
            f"`{payload['linux_validation_terminal_dispatch_final_verdict_publish_channel']}`"
        ),
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['linux_validation_terminal_dispatch_final_publish_archive_summary']}",
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
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_status": str(
            payload["linux_validation_terminal_dispatch_final_publish_archive_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_decision": str(
            payload["linux_validation_terminal_dispatch_final_publish_archive_decision"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_exit_code": str(
            payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_should_archive": (
            "true"
            if payload["linux_validation_terminal_dispatch_final_publish_archive_should_archive"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action": (
            "true"
            if payload[
                "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action"
            ]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_should_page_owner": (
            "true"
            if payload[
                "linux_validation_terminal_dispatch_final_publish_archive_should_page_owner"
            ]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_channel": str(
            payload["linux_validation_terminal_dispatch_final_publish_archive_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_publish_status": str(
            payload["linux_validation_terminal_dispatch_final_verdict_publish_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_publish_channel": str(
            payload["linux_validation_terminal_dispatch_final_verdict_publish_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_run_url": str(
            payload["release_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_report_json": str(
            output_json
        ),
        "workflow_linux_validation_terminal_dispatch_final_publish_archive_report_markdown": str(
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
            "Archive Linux validation terminal dispatch final publish contract "
            "from P2-75 final verdict publish report"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-verdict-publish-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.json",
        help="P2-75 Linux validation terminal dispatch final verdict publish report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json",
        help="Output Linux validation terminal dispatch final publish archive JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.md",
        help="Output Linux validation terminal dispatch final publish archive markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal dispatch final publish archive JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    final_verdict_publish_report_path = Path(
        args.linux_validation_terminal_dispatch_final_verdict_publish_report
    )
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        final_verdict_publish_report = (
            load_linux_validation_terminal_dispatch_final_verdict_publish_report(
                final_verdict_publish_report_path
            )
        )
        payload = build_linux_validation_terminal_dispatch_final_publish_archive_payload(
            final_verdict_publish_report,
            source_path=final_verdict_publish_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-final-publish-archive-gate] "
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
            "linux validation terminal dispatch final publish archive json: "
            f"{output_json_path}"
        )
        print(
            "linux validation terminal dispatch final publish archive markdown: "
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
        "linux validation terminal dispatch final publish archive summary: "
        "linux_validation_terminal_dispatch_final_publish_archive_status="
        f"{payload['linux_validation_terminal_dispatch_final_publish_archive_status']} "
        "linux_validation_terminal_dispatch_final_publish_archive_decision="
        f"{payload['linux_validation_terminal_dispatch_final_publish_archive_decision']} "
        "linux_validation_terminal_dispatch_final_publish_archive_exit_code="
        f"{payload['linux_validation_terminal_dispatch_final_publish_archive_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
