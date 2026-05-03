"""Phase 2 card P2-46 gate for Linux CI workflow release follow-up terminal publish.

This script consumes the P2-45 release follow-up closure artifact and
converges the terminal publish contract:
1) validate follow-up closure + evidence consistency,
2) normalize terminal publish semantics for downstream consumers,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_STATUSES: set[str] = {
    "closed",
    "follow_up_required",
    "escalated",
    "contract_failed",
}
ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_DECISIONS: set[str] = {
    "no_action",
    "dispatch_follow_up",
    "dispatch_escalation",
    "abort_dispatch",
}
ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_TARGETS: set[str] = {
    "none",
    "follow_up_queue",
    "incident_commander",
}
ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_STATUSES: set[str] = {
    "closed",
    "queued_dry_run",
    "queued",
    "queue_failed",
    "contract_failed",
}
ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_DECISIONS: set[str] = {
    "no_action",
    "queue_follow_up",
    "queue_escalation",
    "abort_queue",
}
ALLOWED_RELEASE_FOLLOW_UP_TERMINAL_PUBLISH_STATUSES: set[str] = {
    "published",
    "pending_queue",
    "queue_failed",
    "contract_failed",
}
ALLOWED_RELEASE_FOLLOW_UP_TERMINAL_PUBLISH_DECISIONS: set[str] = {
    "announce_closed",
    "announce_queued",
    "announce_pending_queue",
    "announce_queue_failure",
    "abort_publish",
}
ALLOWED_RELEASE_FOLLOW_UP_TERMINAL_PUBLISH_CHANNELS: set[str] = {
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


def load_release_follow_up_closure_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release follow-up closure report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release follow-up closure payload must be object")

    required_fields = (
        "source_release_follow_up_dispatch_report",
        "project_root",
        "release_follow_up_dispatch_status",
        "release_follow_up_dispatch_decision",
        "release_follow_up_dispatch_exit_code",
        "follow_up_required",
        "escalation_required",
        "dispatch_target",
        "should_queue_follow_up",
        "release_follow_up_closure_status",
        "release_follow_up_closure_decision",
        "release_follow_up_closure_exit_code",
        "follow_up_queue_attempted",
        "follow_up_task_queued",
        "escalation_task_queued",
        "follow_up_command",
        "follow_up_command_parts",
        "follow_up_command_returncode",
        "follow_up_command_stdout_tail",
        "follow_up_command_stderr_tail",
        "follow_up_error_type",
        "follow_up_error_message",
        "follow_up_repo",
        "follow_up_label",
        "follow_up_title_prefix",
        "follow_up_queue_url",
        "release_run_id",
        "release_run_url",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        "evidence_manifest",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    dispatch_status = _coerce_str(
        payload["release_follow_up_dispatch_status"],
        field="release_follow_up_dispatch_status",
        path=path,
    )
    if dispatch_status not in ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_STATUSES:
        raise ValueError(
            f"{path}: field 'release_follow_up_dispatch_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_STATUSES)}"
        )

    dispatch_decision = _coerce_str(
        payload["release_follow_up_dispatch_decision"],
        field="release_follow_up_dispatch_decision",
        path=path,
    )
    if dispatch_decision not in ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_follow_up_dispatch_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_DECISIONS)}"
        )

    dispatch_exit_code = _coerce_int(
        payload["release_follow_up_dispatch_exit_code"],
        field="release_follow_up_dispatch_exit_code",
        path=path,
    )
    if dispatch_exit_code < 0:
        raise ValueError(f"{path}: field 'release_follow_up_dispatch_exit_code' must be >= 0")

    dispatch_target = _coerce_str(payload["dispatch_target"], field="dispatch_target", path=path)
    if dispatch_target not in ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_TARGETS:
        raise ValueError(
            f"{path}: field 'dispatch_target' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_TARGETS)}"
        )

    closure_status = _coerce_str(
        payload["release_follow_up_closure_status"],
        field="release_follow_up_closure_status",
        path=path,
    )
    if closure_status not in ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_STATUSES:
        raise ValueError(
            f"{path}: field 'release_follow_up_closure_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_STATUSES)}"
        )

    closure_decision = _coerce_str(
        payload["release_follow_up_closure_decision"],
        field="release_follow_up_closure_decision",
        path=path,
    )
    if closure_decision not in ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_follow_up_closure_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_DECISIONS)}"
        )

    closure_exit_code = _coerce_int(
        payload["release_follow_up_closure_exit_code"],
        field="release_follow_up_closure_exit_code",
        path=path,
    )
    if closure_exit_code < 0:
        raise ValueError(f"{path}: field 'release_follow_up_closure_exit_code' must be >= 0")

    follow_up_command_returncode_raw = payload["follow_up_command_returncode"]
    if follow_up_command_returncode_raw is None:
        follow_up_command_returncode = None
    else:
        follow_up_command_returncode = _coerce_int(
            follow_up_command_returncode_raw,
            field="follow_up_command_returncode",
            path=path,
        )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    evidence_manifest_raw = payload["evidence_manifest"]
    if not isinstance(evidence_manifest_raw, list):
        raise ValueError(f"{path}: field 'evidence_manifest' must be object list")
    evidence_manifest: list[dict[str, Any]] = []
    for idx, entry in enumerate(evidence_manifest_raw):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: evidence_manifest[{idx}] must be object")
        if "path" not in entry or "exists" not in entry:
            raise ValueError(f"{path}: evidence_manifest[{idx}] missing path/exists")
        evidence_path = _coerce_str(entry["path"], field=f"evidence_manifest[{idx}].path", path=path)
        evidence_exists = _coerce_bool(
            entry["exists"],
            field=f"evidence_manifest[{idx}].exists",
            path=path,
        )
        evidence_manifest.append({"path": evidence_path, "exists": evidence_exists})

    return {
        "generated_at": payload.get("generated_at"),
        "source_release_follow_up_dispatch_report": _coerce_str(
            payload["source_release_follow_up_dispatch_report"],
            field="source_release_follow_up_dispatch_report",
            path=path,
        ),
        "project_root": _coerce_str(payload["project_root"], field="project_root", path=path),
        "release_follow_up_dispatch_status": dispatch_status,
        "release_follow_up_dispatch_decision": dispatch_decision,
        "release_follow_up_dispatch_exit_code": dispatch_exit_code,
        "follow_up_required": _coerce_bool(
            payload["follow_up_required"],
            field="follow_up_required",
            path=path,
        ),
        "escalation_required": _coerce_bool(
            payload["escalation_required"],
            field="escalation_required",
            path=path,
        ),
        "dispatch_target": dispatch_target,
        "should_queue_follow_up": _coerce_bool(
            payload["should_queue_follow_up"],
            field="should_queue_follow_up",
            path=path,
        ),
        "release_follow_up_closure_status": closure_status,
        "release_follow_up_closure_decision": closure_decision,
        "release_follow_up_closure_exit_code": closure_exit_code,
        "follow_up_queue_attempted": _coerce_bool(
            payload["follow_up_queue_attempted"],
            field="follow_up_queue_attempted",
            path=path,
        ),
        "follow_up_task_queued": _coerce_bool(
            payload["follow_up_task_queued"],
            field="follow_up_task_queued",
            path=path,
        ),
        "escalation_task_queued": _coerce_bool(
            payload["escalation_task_queued"],
            field="escalation_task_queued",
            path=path,
        ),
        "follow_up_command": _coerce_str(
            payload["follow_up_command"],
            field="follow_up_command",
            path=path,
        ),
        "follow_up_command_parts": _coerce_str_list(
            payload["follow_up_command_parts"],
            field="follow_up_command_parts",
            path=path,
        ),
        "follow_up_command_returncode": follow_up_command_returncode,
        "follow_up_command_stdout_tail": _coerce_str(
            payload["follow_up_command_stdout_tail"],
            field="follow_up_command_stdout_tail",
            path=path,
        ),
        "follow_up_command_stderr_tail": _coerce_str(
            payload["follow_up_command_stderr_tail"],
            field="follow_up_command_stderr_tail",
            path=path,
        ),
        "follow_up_error_type": _coerce_str(
            payload["follow_up_error_type"],
            field="follow_up_error_type",
            path=path,
        ),
        "follow_up_error_message": _coerce_str(
            payload["follow_up_error_message"],
            field="follow_up_error_message",
            path=path,
        ),
        "follow_up_repo": _coerce_str(payload["follow_up_repo"], field="follow_up_repo", path=path),
        "follow_up_label": _coerce_str(payload["follow_up_label"], field="follow_up_label", path=path),
        "follow_up_title_prefix": _coerce_str(
            payload["follow_up_title_prefix"],
            field="follow_up_title_prefix",
            path=path,
        ),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(
            payload["release_run_url"],
            field="release_run_url",
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
        "evidence_manifest": evidence_manifest,
    }


def build_release_follow_up_terminal_publish_payload(
    closure_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    closure_status = str(closure_report["release_follow_up_closure_status"])
    closure_decision = str(closure_report["release_follow_up_closure_decision"])
    closure_exit_code = int(closure_report["release_follow_up_closure_exit_code"])
    should_queue_follow_up = bool(closure_report["should_queue_follow_up"])
    follow_up_queue_attempted = bool(closure_report["follow_up_queue_attempted"])
    follow_up_task_queued = bool(closure_report["follow_up_task_queued"])
    escalation_task_queued = bool(closure_report["escalation_task_queued"])
    follow_up_required = bool(closure_report["follow_up_required"])
    escalation_required = bool(closure_report["escalation_required"])
    dispatch_target = str(closure_report["dispatch_target"])

    reason_codes = list(closure_report["reason_codes"])
    structural_issues = list(closure_report["structural_issues"])
    missing_artifacts = list(closure_report["missing_artifacts"])
    evidence_manifest = list(closure_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_follow_up_terminal_publish_evidence_missing")

    if closure_status == "closed":
        if closure_decision != "no_action":
            structural_issues.append("closure_decision_mismatch_closed")
        if closure_exit_code != 0:
            structural_issues.append("closure_exit_code_mismatch_closed")
        if should_queue_follow_up:
            structural_issues.append("should_queue_follow_up_mismatch_closed")
        if follow_up_queue_attempted:
            structural_issues.append("follow_up_queue_attempted_mismatch_closed")
        if follow_up_task_queued:
            structural_issues.append("follow_up_task_queued_mismatch_closed")
        if escalation_task_queued:
            structural_issues.append("escalation_task_queued_mismatch_closed")
        if dispatch_target != "none":
            structural_issues.append("dispatch_target_mismatch_closed")
        if follow_up_required:
            structural_issues.append("follow_up_required_mismatch_closed")
    elif closure_status == "queued_dry_run":
        if closure_decision not in {"queue_follow_up", "queue_escalation"}:
            structural_issues.append("closure_decision_mismatch_queued_dry_run")
        if closure_exit_code != 0:
            structural_issues.append("closure_exit_code_mismatch_queued_dry_run")
        if not should_queue_follow_up:
            structural_issues.append("should_queue_follow_up_mismatch_queued_dry_run")
        if follow_up_queue_attempted:
            structural_issues.append("follow_up_queue_attempted_mismatch_queued_dry_run")
        if follow_up_task_queued:
            structural_issues.append("follow_up_task_queued_mismatch_queued_dry_run")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_queued_dry_run")
    elif closure_status == "queued":
        if closure_decision not in {"queue_follow_up", "queue_escalation"}:
            structural_issues.append("closure_decision_mismatch_queued")
        if closure_exit_code != 0:
            structural_issues.append("closure_exit_code_mismatch_queued")
        if not should_queue_follow_up:
            structural_issues.append("should_queue_follow_up_mismatch_queued")
        if not follow_up_queue_attempted:
            structural_issues.append("follow_up_queue_attempted_mismatch_queued")
        if not follow_up_task_queued:
            structural_issues.append("follow_up_task_queued_mismatch_queued")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_queued")
        if escalation_required and not escalation_task_queued:
            structural_issues.append("escalation_task_queued_mismatch_queued")
    elif closure_status == "queue_failed":
        if closure_decision != "abort_queue":
            structural_issues.append("closure_decision_mismatch_queue_failed")
        if closure_exit_code == 0:
            structural_issues.append("closure_exit_code_mismatch_queue_failed")
        if not should_queue_follow_up:
            structural_issues.append("should_queue_follow_up_mismatch_queue_failed")
        if not follow_up_queue_attempted:
            structural_issues.append("follow_up_queue_attempted_mismatch_queue_failed")
        if follow_up_task_queued:
            structural_issues.append("follow_up_task_queued_mismatch_queue_failed")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_queue_failed")
    else:
        if closure_decision != "abort_queue":
            structural_issues.append("closure_decision_mismatch_contract_failed")
        if closure_exit_code == 0:
            structural_issues.append("closure_exit_code_mismatch_contract_failed")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_contract_failed")

    if closure_status in {"queued_dry_run", "queued", "queue_failed"} and dispatch_target == "none":
        structural_issues.append("dispatch_target_mismatch_queue_path")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        terminal_status = "contract_failed"
        terminal_decision = "abort_publish"
        terminal_exit_code = 1
        terminal_should_notify = True
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif closure_status == "closed":
        terminal_status = "published"
        terminal_decision = "announce_closed"
        terminal_exit_code = 0
        terminal_should_notify = True
        terminal_requires_manual_action = False
        terminal_channel = "release"
        reason_codes = ["release_follow_up_terminal_closed"]
    elif closure_status == "queued":
        terminal_status = "published"
        terminal_decision = "announce_queued"
        terminal_exit_code = 0
        terminal_should_notify = True
        terminal_requires_manual_action = False
        terminal_channel = "follow_up"
        reason_codes = (
            ["release_follow_up_terminal_escalation_queued"]
            if escalation_required
            else ["release_follow_up_terminal_queued"]
        )
    elif closure_status == "queued_dry_run":
        terminal_status = "pending_queue"
        terminal_decision = "announce_pending_queue"
        terminal_exit_code = max(1, closure_exit_code)
        terminal_should_notify = True
        terminal_requires_manual_action = True
        terminal_channel = "follow_up"
        reason_codes.append("release_follow_up_terminal_pending_queue")
    elif closure_status == "queue_failed":
        terminal_status = "queue_failed"
        terminal_decision = "announce_queue_failure"
        terminal_exit_code = max(1, closure_exit_code)
        terminal_should_notify = True
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.append("release_follow_up_terminal_queue_failed")
    else:
        terminal_status = "contract_failed"
        terminal_decision = "abort_publish"
        terminal_exit_code = max(1, closure_exit_code)
        terminal_should_notify = True
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.append("release_follow_up_terminal_upstream_contract_failed")

    if terminal_status not in ALLOWED_RELEASE_FOLLOW_UP_TERMINAL_PUBLISH_STATUSES:
        raise ValueError("internal: unsupported release_follow_up_terminal_publish_status computed")
    if terminal_decision not in ALLOWED_RELEASE_FOLLOW_UP_TERMINAL_PUBLISH_DECISIONS:
        raise ValueError("internal: unsupported release_follow_up_terminal_publish_decision computed")
    if terminal_channel not in ALLOWED_RELEASE_FOLLOW_UP_TERMINAL_PUBLISH_CHANNELS:
        raise ValueError("internal: unsupported release_follow_up_terminal_publish_channel computed")

    reason_codes = _unique(reason_codes)
    summary = (
        f"release_follow_up_closure_status={closure_status} "
        f"release_follow_up_terminal_publish_status={terminal_status} "
        f"release_follow_up_terminal_publish_decision={terminal_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_follow_up_closure_report": str(source_path),
        "source_release_follow_up_dispatch_report": str(
            closure_report["source_release_follow_up_dispatch_report"]
        ),
        "project_root": str(closure_report["project_root"]),
        "release_follow_up_dispatch_status": str(closure_report["release_follow_up_dispatch_status"]),
        "release_follow_up_dispatch_decision": str(closure_report["release_follow_up_dispatch_decision"]),
        "release_follow_up_dispatch_exit_code": int(closure_report["release_follow_up_dispatch_exit_code"]),
        "follow_up_required": follow_up_required,
        "escalation_required": escalation_required,
        "dispatch_target": dispatch_target,
        "should_queue_follow_up": should_queue_follow_up,
        "release_follow_up_closure_status": closure_status,
        "release_follow_up_closure_decision": closure_decision,
        "release_follow_up_closure_exit_code": closure_exit_code,
        "follow_up_queue_attempted": follow_up_queue_attempted,
        "follow_up_task_queued": follow_up_task_queued,
        "escalation_task_queued": escalation_task_queued,
        "follow_up_command": str(closure_report["follow_up_command"]),
        "follow_up_command_parts": list(closure_report["follow_up_command_parts"]),
        "follow_up_command_returncode": closure_report["follow_up_command_returncode"],
        "follow_up_command_stdout_tail": str(closure_report["follow_up_command_stdout_tail"]),
        "follow_up_command_stderr_tail": str(closure_report["follow_up_command_stderr_tail"]),
        "follow_up_error_type": str(closure_report["follow_up_error_type"]),
        "follow_up_error_message": str(closure_report["follow_up_error_message"]),
        "follow_up_repo": str(closure_report["follow_up_repo"]),
        "follow_up_label": str(closure_report["follow_up_label"]),
        "follow_up_title_prefix": str(closure_report["follow_up_title_prefix"]),
        "follow_up_queue_url": str(closure_report["follow_up_queue_url"]),
        "release_run_id": closure_report["release_run_id"],
        "release_run_url": str(closure_report["release_run_url"]),
        "release_follow_up_terminal_publish_status": terminal_status,
        "release_follow_up_terminal_publish_decision": terminal_decision,
        "release_follow_up_terminal_publish_exit_code": terminal_exit_code,
        "follow_up_terminal_publish_should_notify": terminal_should_notify,
        "follow_up_terminal_requires_manual_action": terminal_requires_manual_action,
        "follow_up_terminal_publish_channel": terminal_channel,
        "release_follow_up_terminal_publish_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Follow-Up Terminal Publish Report",
        "",
        (
            "- Release Follow-Up Terminal Publish Status: "
            f"**{str(payload['release_follow_up_terminal_publish_status']).upper()}**"
        ),
        (
            "- Release Follow-Up Terminal Publish Decision: "
            f"`{payload['release_follow_up_terminal_publish_decision']}`"
        ),
        (
            "- Release Follow-Up Terminal Publish Exit Code: "
            f"`{payload['release_follow_up_terminal_publish_exit_code']}`"
        ),
        (
            "- Follow-Up Terminal Publish Should Notify: "
            f"`{payload['follow_up_terminal_publish_should_notify']}`"
        ),
        (
            "- Follow-Up Terminal Requires Manual Action: "
            f"`{payload['follow_up_terminal_requires_manual_action']}`"
        ),
        f"- Follow-Up Terminal Publish Channel: `{payload['follow_up_terminal_publish_channel']}`",
        f"- Release Follow-Up Closure Status: `{payload['release_follow_up_closure_status']}`",
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_follow_up_terminal_publish_summary']}",
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
        "workflow_release_follow_up_terminal_publish_status": str(
            payload["release_follow_up_terminal_publish_status"]
        ),
        "workflow_release_follow_up_terminal_publish_decision": str(
            payload["release_follow_up_terminal_publish_decision"]
        ),
        "workflow_release_follow_up_terminal_publish_exit_code": str(
            payload["release_follow_up_terminal_publish_exit_code"]
        ),
        "workflow_release_follow_up_terminal_publish_should_notify": (
            "true" if payload["follow_up_terminal_publish_should_notify"] else "false"
        ),
        "workflow_release_follow_up_terminal_publish_manual_action": (
            "true" if payload["follow_up_terminal_requires_manual_action"] else "false"
        ),
        "workflow_release_follow_up_terminal_publish_channel": str(
            payload["follow_up_terminal_publish_channel"]
        ),
        "workflow_release_follow_up_terminal_publish_closure_status": str(
            payload["release_follow_up_closure_status"]
        ),
        "workflow_release_follow_up_terminal_publish_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_release_follow_up_terminal_publish_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_follow_up_terminal_publish_run_url": str(payload["release_run_url"]),
        "workflow_release_follow_up_terminal_publish_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_follow_up_terminal_publish_report_json": str(output_json),
        "workflow_release_follow_up_terminal_publish_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release follow-up terminal publish contract "
            "from P2-45 release follow-up closure report"
        )
    )
    parser.add_argument(
        "--release-follow-up-closure-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json",
        help="P2-45 release follow-up closure report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json",
        help="Output release follow-up terminal publish JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.md",
        help="Output release follow-up terminal publish markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release follow-up terminal publish JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    closure_report_path = Path(args.release_follow_up_closure_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        closure_report = load_release_follow_up_closure_report(closure_report_path)
        payload = build_release_follow_up_terminal_publish_payload(
            closure_report,
            source_path=closure_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            f"[p2-linux-ci-workflow-release-follow-up-terminal-publish-gate] {exc}",
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
        print(f"release follow-up terminal publish json: {output_json_path}")
        print(f"release follow-up terminal publish markdown: {output_markdown_path}")

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
        "release follow-up terminal publish summary: "
        f"release_follow_up_terminal_publish_status={payload['release_follow_up_terminal_publish_status']} "
        f"release_follow_up_terminal_publish_decision={payload['release_follow_up_terminal_publish_decision']} "
        f"release_follow_up_terminal_publish_exit_code={payload['release_follow_up_terminal_publish_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_follow_up_terminal_publish_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
