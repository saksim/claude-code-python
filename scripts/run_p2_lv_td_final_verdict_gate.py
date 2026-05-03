"""Phase 2 card P2-74 gate for Linux CI workflow Linux validation terminal dispatch final verdict.

This script consumes the P2-73 Linux validation terminal dispatch terminal publish artifact and
converges one final verdict contract:
1) validate terminal-publish contract consistency,
2) normalize final dispatch-verdict semantics for downstream consumers,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_STATUSES: set[str] = {
    "validated",
    "validated_with_follow_up",
    "in_progress",
    "blocked",
    "failed",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_DECISIONS: set[str] = {
    "accept_linux_validation_terminal_dispatch",
    "accept_linux_validation_terminal_dispatch_with_follow_up",
    "keep_linux_validation_terminal_dispatch_in_progress",
    "escalate_linux_validation_terminal_dispatch_blocker",
    "escalate_linux_validation_terminal_dispatch_failure",
    "abort_linux_validation_terminal_dispatch_final_verdict",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_CHANNELS: set[str] = {
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


def load_linux_validation_terminal_dispatch_terminal_publish_report(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(
            f"{path}: Linux validation terminal dispatch terminal publish report not found"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"{path}: Linux validation terminal dispatch terminal publish payload must be object"
        )

    required_fields = (
        "source_linux_validation_terminal_dispatch_completion_report",
        "source_linux_validation_terminal_dispatch_trace_report",
        "source_linux_validation_terminal_dispatch_execution_report",
        "source_linux_validation_terminal_dispatch_report",
        "linux_validation_terminal_dispatch_completion_status",
        "linux_validation_terminal_dispatch_completion_exit_code",
        "linux_validation_terminal_dispatch_execution_status",
        "linux_validation_terminal_dispatch_execution_decision",
        "linux_validation_terminal_dispatch_execution_exit_code",
        "linux_validation_terminal_should_dispatch",
        "linux_validation_terminal_dispatch_attempted",
        "linux_validation_terminal_dispatch_trace_status",
        "linux_validation_terminal_dispatch_trace_exit_code",
        "should_poll_workflow_run",
        "allow_in_progress",
        "linux_validation_terminal_run_id",
        "linux_validation_terminal_run_url",
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "linux_validation_terminal_dispatch_terminal_publish_status",
        "linux_validation_terminal_dispatch_terminal_publish_decision",
        "linux_validation_terminal_dispatch_terminal_publish_exit_code",
        "linux_validation_terminal_dispatch_terminal_publish_should_notify",
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff",
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action",
        "linux_validation_terminal_dispatch_terminal_publish_channel",
        "linux_validation_terminal_dispatch_terminal_publish_summary",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    terminal_publish_status = _coerce_str(
        payload["linux_validation_terminal_dispatch_terminal_publish_status"],
        field="linux_validation_terminal_dispatch_terminal_publish_status",
        path=path,
    )
    if (
        terminal_publish_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_STATUSES
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_terminal_publish_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_STATUSES)}"
        )

    terminal_publish_decision = _coerce_str(
        payload["linux_validation_terminal_dispatch_terminal_publish_decision"],
        field="linux_validation_terminal_dispatch_terminal_publish_decision",
        path=path,
    )
    if (
        terminal_publish_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_terminal_publish_decision' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_DECISIONS)}"
        )

    terminal_publish_exit_code = _coerce_int(
        payload["linux_validation_terminal_dispatch_terminal_publish_exit_code"],
        field="linux_validation_terminal_dispatch_terminal_publish_exit_code",
        path=path,
    )
    if terminal_publish_exit_code < 0:
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_terminal_publish_exit_code' must be >= 0"
        )

    terminal_publish_channel = _coerce_str(
        payload["linux_validation_terminal_dispatch_terminal_publish_channel"],
        field="linux_validation_terminal_dispatch_terminal_publish_channel",
        path=path,
    )
    if (
        terminal_publish_channel
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_CHANNELS
    ):
        raise ValueError(
            f"{path}: field 'linux_validation_terminal_dispatch_terminal_publish_channel' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_TERMINAL_PUBLISH_CHANNELS)}"
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
        "source_linux_validation_terminal_dispatch_completion_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_completion_report"],
            field="source_linux_validation_terminal_dispatch_completion_report",
            path=path,
        ),
        "source_linux_validation_terminal_dispatch_trace_report": _coerce_str(
            payload["source_linux_validation_terminal_dispatch_trace_report"],
            field="source_linux_validation_terminal_dispatch_trace_report",
            path=path,
        ),
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
        "linux_validation_terminal_dispatch_completion_status": _coerce_str(
            payload["linux_validation_terminal_dispatch_completion_status"],
            field="linux_validation_terminal_dispatch_completion_status",
            path=path,
        ),
        "linux_validation_terminal_dispatch_completion_exit_code": _coerce_int(
            payload["linux_validation_terminal_dispatch_completion_exit_code"],
            field="linux_validation_terminal_dispatch_completion_exit_code",
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
        "should_poll_workflow_run": _coerce_bool(
            payload["should_poll_workflow_run"],
            field="should_poll_workflow_run",
            path=path,
        ),
        "allow_in_progress": _coerce_bool(
            payload["allow_in_progress"],
            field="allow_in_progress",
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
        "linux_validation_terminal_dispatch_terminal_publish_status": terminal_publish_status,
        "linux_validation_terminal_dispatch_terminal_publish_decision": terminal_publish_decision,
        "linux_validation_terminal_dispatch_terminal_publish_exit_code": terminal_publish_exit_code,
        "linux_validation_terminal_dispatch_terminal_publish_should_notify": _coerce_bool(
            payload["linux_validation_terminal_dispatch_terminal_publish_should_notify"],
            field="linux_validation_terminal_dispatch_terminal_publish_should_notify",
            path=path,
        ),
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff": _coerce_bool(
            payload["linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"],
            field="linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff",
            path=path,
        ),
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action": _coerce_bool(
            payload["linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"],
            field="linux_validation_terminal_dispatch_terminal_publish_requires_manual_action",
            path=path,
        ),
        "linux_validation_terminal_dispatch_terminal_publish_channel": terminal_publish_channel,
        "linux_validation_terminal_dispatch_terminal_publish_summary": _coerce_str(
            payload["linux_validation_terminal_dispatch_terminal_publish_summary"],
            field="linux_validation_terminal_dispatch_terminal_publish_summary",
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


def build_linux_validation_terminal_dispatch_final_verdict_payload(
    terminal_publish_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    terminal_publish_status = str(
        terminal_publish_report["linux_validation_terminal_dispatch_terminal_publish_status"]
    )
    terminal_publish_decision = str(
        terminal_publish_report["linux_validation_terminal_dispatch_terminal_publish_decision"]
    )
    terminal_publish_exit_code = int(
        terminal_publish_report["linux_validation_terminal_dispatch_terminal_publish_exit_code"]
    )
    terminal_publish_should_notify = bool(
        terminal_publish_report["linux_validation_terminal_dispatch_terminal_publish_should_notify"]
    )
    terminal_publish_ready_for_handoff = bool(
        terminal_publish_report[
            "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"
        ]
    )
    terminal_publish_requires_manual_action = bool(
        terminal_publish_report[
            "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"
        ]
    )
    terminal_publish_channel = str(
        terminal_publish_report["linux_validation_terminal_dispatch_terminal_publish_channel"]
    )

    reason_codes = list(terminal_publish_report["reason_codes"])
    structural_issues = list(terminal_publish_report["structural_issues"])
    missing_artifacts = list(terminal_publish_report["missing_artifacts"])

    expected_contract = {
        "terminal_published": (
            "announce_linux_validation_terminal_dispatch_completed",
            0,
            True,
            True,
            False,
            "release",
        ),
        "terminal_published_with_follow_up": (
            "announce_linux_validation_terminal_dispatch_completed_with_follow_up",
            None,
            True,
            True,
            False,
            "follow_up",
        ),
        "terminal_in_progress": (
            "announce_linux_validation_terminal_dispatch_in_progress",
            0,
            True,
            False,
            False,
            None,
        ),
        "terminal_blocked": (
            "announce_linux_validation_terminal_dispatch_blocker",
            None,
            True,
            False,
            True,
            "blocker",
        ),
        "terminal_failed": (
            "announce_linux_validation_terminal_dispatch_failed",
            None,
            True,
            False,
            True,
            "blocker",
        ),
        "terminal_contract_failed": (
            "abort_linux_validation_terminal_dispatch_terminal_publish",
            None,
            True,
            False,
            True,
            "blocker",
        ),
    }
    (
        expected_decision,
        expected_exit_code,
        expected_should_notify,
        expected_ready_for_handoff,
        expected_requires_manual_action,
        expected_channel,
    ) = expected_contract[terminal_publish_status]

    if terminal_publish_decision != expected_decision:
        structural_issues.append("linux_validation_terminal_dispatch_terminal_publish_decision_mismatch")
    if terminal_publish_should_notify != expected_should_notify:
        structural_issues.append("linux_validation_terminal_dispatch_terminal_publish_should_notify_mismatch")
    if terminal_publish_ready_for_handoff != expected_ready_for_handoff:
        structural_issues.append("linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff_mismatch")
    if terminal_publish_requires_manual_action != expected_requires_manual_action:
        structural_issues.append("linux_validation_terminal_dispatch_terminal_publish_requires_manual_action_mismatch")
    if expected_channel is not None and terminal_publish_channel != expected_channel:
        structural_issues.append("linux_validation_terminal_dispatch_terminal_publish_channel_mismatch")
    if expected_exit_code == 0 and terminal_publish_exit_code != 0:
        structural_issues.append("linux_validation_terminal_dispatch_terminal_publish_exit_code_mismatch_zero")
    if expected_exit_code is None and terminal_publish_exit_code == 0 and terminal_publish_status in {
        "terminal_published_with_follow_up",
        "terminal_blocked",
        "terminal_failed",
        "terminal_contract_failed",
    }:
        structural_issues.append(
            "linux_validation_terminal_dispatch_terminal_publish_exit_code_mismatch_nonzero"
        )

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    final_status: str
    final_decision: str
    final_exit_code: int
    final_should_accept: bool
    final_requires_follow_up: bool
    final_should_page_owner: bool
    final_channel: str

    if structural_issues or missing_artifacts:
        final_status = "contract_failed"
        final_decision = "abort_linux_validation_terminal_dispatch_final_verdict"
        final_exit_code = max(1, terminal_publish_exit_code)
        final_should_accept = False
        final_requires_follow_up = True
        final_should_page_owner = True
        final_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif terminal_publish_status == "terminal_contract_failed":
        final_status = "contract_failed"
        final_decision = "abort_linux_validation_terminal_dispatch_final_verdict"
        final_exit_code = max(1, terminal_publish_exit_code)
        final_should_accept = False
        final_requires_follow_up = True
        final_should_page_owner = True
        final_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_final_verdict_upstream_contract_failed")
    elif terminal_publish_status == "terminal_published":
        final_status = "validated"
        final_decision = "accept_linux_validation_terminal_dispatch"
        final_exit_code = 0
        final_should_accept = True
        final_requires_follow_up = False
        final_should_page_owner = False
        final_channel = "release"
        reason_codes = ["linux_validation_terminal_dispatch_final_verdict_validated"]
    elif terminal_publish_status == "terminal_published_with_follow_up":
        final_status = "validated_with_follow_up"
        final_decision = "accept_linux_validation_terminal_dispatch_with_follow_up"
        final_exit_code = max(1, terminal_publish_exit_code)
        final_should_accept = True
        final_requires_follow_up = True
        final_should_page_owner = False
        final_channel = "follow_up"
        reason_codes.append("linux_validation_terminal_dispatch_final_verdict_validated_with_follow_up")
    elif terminal_publish_status == "terminal_in_progress":
        final_status = "in_progress"
        final_decision = "keep_linux_validation_terminal_dispatch_in_progress"
        final_exit_code = 0
        final_should_accept = False
        final_requires_follow_up = True
        final_should_page_owner = False
        final_channel = (
            "follow_up"
            if terminal_publish_channel == "follow_up"
            else "release"
        )
        reason_codes.append("linux_validation_terminal_dispatch_final_verdict_in_progress")
    elif terminal_publish_status == "terminal_blocked":
        final_status = "blocked"
        final_decision = "escalate_linux_validation_terminal_dispatch_blocker"
        final_exit_code = max(1, terminal_publish_exit_code)
        final_should_accept = False
        final_requires_follow_up = True
        final_should_page_owner = True
        final_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_final_verdict_blocked")
    else:
        final_status = "failed"
        final_decision = "escalate_linux_validation_terminal_dispatch_failure"
        final_exit_code = max(1, terminal_publish_exit_code)
        final_should_accept = False
        final_requires_follow_up = True
        final_should_page_owner = True
        final_channel = "blocker"
        reason_codes.append("linux_validation_terminal_dispatch_final_verdict_failed")

    if (
        final_status
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_STATUSES
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_final_verdict_status computed"
        )
    if (
        final_decision
        not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_VERDICT_DECISIONS
    ):
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_final_verdict_decision computed"
        )
    if final_channel not in ALLOWED_LINUX_VALIDATION_TERMINAL_DISPATCH_FINAL_CHANNELS:
        raise ValueError(
            "internal: unsupported linux_validation_terminal_dispatch_final_channel computed"
        )

    reason_codes = _unique(reason_codes)
    summary = (
        f"linux_validation_terminal_dispatch_terminal_publish_status={terminal_publish_status} "
        f"linux_validation_terminal_dispatch_final_verdict_status={final_status} "
        f"linux_validation_terminal_dispatch_final_verdict_decision={final_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_linux_validation_terminal_dispatch_terminal_publish_report": str(source_path),
        "source_linux_validation_terminal_dispatch_completion_report": str(
            terminal_publish_report["source_linux_validation_terminal_dispatch_completion_report"]
        ),
        "source_linux_validation_terminal_dispatch_trace_report": str(
            terminal_publish_report["source_linux_validation_terminal_dispatch_trace_report"]
        ),
        "source_linux_validation_terminal_dispatch_execution_report": str(
            terminal_publish_report["source_linux_validation_terminal_dispatch_execution_report"]
        ),
        "source_linux_validation_terminal_dispatch_report": str(
            terminal_publish_report["source_linux_validation_terminal_dispatch_report"]
        ),
        "linux_validation_terminal_dispatch_completion_status": str(
            terminal_publish_report["linux_validation_terminal_dispatch_completion_status"]
        ),
        "linux_validation_terminal_dispatch_completion_exit_code": int(
            terminal_publish_report["linux_validation_terminal_dispatch_completion_exit_code"]
        ),
        "linux_validation_terminal_dispatch_execution_status": str(
            terminal_publish_report["linux_validation_terminal_dispatch_execution_status"]
        ),
        "linux_validation_terminal_dispatch_execution_decision": str(
            terminal_publish_report["linux_validation_terminal_dispatch_execution_decision"]
        ),
        "linux_validation_terminal_dispatch_execution_exit_code": int(
            terminal_publish_report["linux_validation_terminal_dispatch_execution_exit_code"]
        ),
        "linux_validation_terminal_should_dispatch": bool(
            terminal_publish_report["linux_validation_terminal_should_dispatch"]
        ),
        "linux_validation_terminal_dispatch_attempted": bool(
            terminal_publish_report["linux_validation_terminal_dispatch_attempted"]
        ),
        "linux_validation_terminal_dispatch_trace_status": str(
            terminal_publish_report["linux_validation_terminal_dispatch_trace_status"]
        ),
        "linux_validation_terminal_dispatch_trace_exit_code": int(
            terminal_publish_report["linux_validation_terminal_dispatch_trace_exit_code"]
        ),
        "should_poll_workflow_run": bool(
            terminal_publish_report["should_poll_workflow_run"]
        ),
        "allow_in_progress": bool(terminal_publish_report["allow_in_progress"]),
        "linux_validation_terminal_run_id": terminal_publish_report[
            "linux_validation_terminal_run_id"
        ],
        "linux_validation_terminal_run_url": str(
            terminal_publish_report["linux_validation_terminal_run_url"]
        ),
        "release_run_id": terminal_publish_report["release_run_id"],
        "release_run_url": str(terminal_publish_report["release_run_url"]),
        "follow_up_queue_url": str(terminal_publish_report["follow_up_queue_url"]),
        "linux_validation_terminal_dispatch_terminal_publish_status": terminal_publish_status,
        "linux_validation_terminal_dispatch_terminal_publish_decision": terminal_publish_decision,
        "linux_validation_terminal_dispatch_terminal_publish_exit_code": terminal_publish_exit_code,
        "linux_validation_terminal_dispatch_terminal_publish_should_notify": terminal_publish_should_notify,
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff": terminal_publish_ready_for_handoff,
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action": terminal_publish_requires_manual_action,
        "linux_validation_terminal_dispatch_terminal_publish_channel": terminal_publish_channel,
        "linux_validation_terminal_dispatch_terminal_publish_summary": str(
            terminal_publish_report["linux_validation_terminal_dispatch_terminal_publish_summary"]
        ),
        "linux_validation_terminal_dispatch_final_verdict_status": final_status,
        "linux_validation_terminal_dispatch_final_verdict_decision": final_decision,
        "linux_validation_terminal_dispatch_final_verdict_exit_code": final_exit_code,
        "linux_validation_terminal_dispatch_final_should_accept": final_should_accept,
        "linux_validation_terminal_dispatch_final_requires_follow_up": final_requires_follow_up,
        "linux_validation_terminal_dispatch_final_should_page_owner": final_should_page_owner,
        "linux_validation_terminal_dispatch_final_channel": final_channel,
        "linux_validation_terminal_dispatch_final_verdict_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux Validation Terminal Dispatch Final Verdict Report",
        "",
        (
            "- Final Verdict Status: "
            f"**{str(payload['linux_validation_terminal_dispatch_final_verdict_status']).upper()}**"
        ),
        (
            "- Final Verdict Decision: "
            f"`{payload['linux_validation_terminal_dispatch_final_verdict_decision']}`"
        ),
        (
            "- Final Verdict Exit Code: "
            f"`{payload['linux_validation_terminal_dispatch_final_verdict_exit_code']}`"
        ),
        (
            "- Final Should Accept: "
            f"`{payload['linux_validation_terminal_dispatch_final_should_accept']}`"
        ),
        (
            "- Final Requires Follow Up: "
            f"`{payload['linux_validation_terminal_dispatch_final_requires_follow_up']}`"
        ),
        (
            "- Final Should Page Owner: "
            f"`{payload['linux_validation_terminal_dispatch_final_should_page_owner']}`"
        ),
        (
            "- Final Channel: "
            f"`{payload['linux_validation_terminal_dispatch_final_channel']}`"
        ),
        (
            "- Terminal Publish Status: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_status']}`"
        ),
        (
            "- Terminal Publish Channel: "
            f"`{payload['linux_validation_terminal_dispatch_terminal_publish_channel']}`"
        ),
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['linux_validation_terminal_dispatch_final_verdict_summary']}",
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
        "workflow_linux_validation_terminal_dispatch_final_verdict_status": str(
            payload["linux_validation_terminal_dispatch_final_verdict_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_verdict_decision": str(
            payload["linux_validation_terminal_dispatch_final_verdict_decision"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_verdict_exit_code": str(
            payload["linux_validation_terminal_dispatch_final_verdict_exit_code"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_should_accept": (
            "true"
            if payload["linux_validation_terminal_dispatch_final_should_accept"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_final_requires_follow_up": (
            "true"
            if payload["linux_validation_terminal_dispatch_final_requires_follow_up"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_final_should_page_owner": (
            "true"
            if payload["linux_validation_terminal_dispatch_final_should_page_owner"]
            else "false"
        ),
        "workflow_linux_validation_terminal_dispatch_final_channel": str(
            payload["linux_validation_terminal_dispatch_final_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_terminal_publish_status": str(
            payload["linux_validation_terminal_dispatch_terminal_publish_status"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_terminal_publish_channel": str(
            payload["linux_validation_terminal_dispatch_terminal_publish_channel"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_terminal_dispatch_final_run_url": str(
            payload["release_run_url"]
        ),
        "workflow_linux_validation_terminal_dispatch_final_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_dispatch_final_report_json": str(output_json),
        "workflow_linux_validation_terminal_dispatch_final_report_markdown": str(
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
            "Publish Linux validation terminal dispatch final verdict contract "
            "from P2-73 terminal publish report"
        )
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-publish-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json",
        help="P2-73 Linux validation terminal dispatch terminal publish report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json",
        help="Output Linux validation terminal dispatch final verdict JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.md",
        help="Output Linux validation terminal dispatch final verdict markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal dispatch final verdict JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    terminal_publish_report_path = Path(
        args.linux_validation_terminal_dispatch_terminal_publish_report
    )
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        terminal_publish_report = (
            load_linux_validation_terminal_dispatch_terminal_publish_report(
                terminal_publish_report_path
            )
        )
        payload = build_linux_validation_terminal_dispatch_final_verdict_payload(
            terminal_publish_report,
            source_path=terminal_publish_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-dispatch-final-verdict-gate] "
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
        print(f"linux validation terminal dispatch final verdict json: {output_json_path}")
        print(f"linux validation terminal dispatch final verdict markdown: {output_markdown_path}")

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
        "linux validation terminal dispatch final verdict summary: "
        "linux_validation_terminal_dispatch_final_verdict_status="
        f"{payload['linux_validation_terminal_dispatch_final_verdict_status']} "
        "linux_validation_terminal_dispatch_final_verdict_decision="
        f"{payload['linux_validation_terminal_dispatch_final_verdict_decision']} "
        "linux_validation_terminal_dispatch_final_verdict_exit_code="
        f"{payload['linux_validation_terminal_dispatch_final_verdict_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_dispatch_final_verdict_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
