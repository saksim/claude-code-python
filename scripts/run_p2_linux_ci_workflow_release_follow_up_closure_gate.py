"""Phase 2 card P2-45 gate for Linux CI workflow release follow-up closure.

This script consumes the P2-44 release follow-up dispatch artifact and
converges the follow-up closure contract:
1) validate follow-up dispatch + evidence consistency,
2) optionally execute follow-up/escalation queue command,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
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

URL_PATTERN = re.compile(r"https?://[^\s]+")


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


def _format_shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _tail_text(text: str, *, max_lines: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def _extract_url(text: str) -> str:
    for line in text.splitlines():
        match = URL_PATTERN.search(line)
        if match:
            return match.group(0)
    return ""


def _unique(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def load_release_follow_up_dispatch_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release follow-up dispatch report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release follow-up dispatch payload must be object")

    required_fields = (
        "source_release_delivery_final_verdict_report",
        "source_release_delivery_terminal_publish_report",
        "source_release_delivery_report",
        "source_release_terminal_verdict_report",
        "source_release_incident_report",
        "source_release_verdict_report",
        "source_release_archive_report",
        "release_archive_status",
        "release_archive_decision",
        "release_archive_exit_code",
        "should_publish_archive",
        "release_verdict_status",
        "release_verdict_decision",
        "release_verdict_exit_code",
        "should_ship_release",
        "should_open_incident",
        "should_dispatch_incident",
        "incident_dispatch_status",
        "incident_dispatch_exit_code",
        "incident_dispatch_attempted",
        "incident_url",
        "release_terminal_verdict_status",
        "release_terminal_verdict_decision",
        "release_terminal_verdict_exit_code",
        "terminal_should_ship_release",
        "terminal_requires_follow_up",
        "terminal_incident_linked",
        "release_delivery_status",
        "release_delivery_decision",
        "release_delivery_exit_code",
        "delivery_should_ship_release",
        "delivery_requires_human_action",
        "delivery_should_announce_blocker",
        "release_delivery_terminal_publish_status",
        "release_delivery_terminal_publish_decision",
        "release_delivery_terminal_publish_exit_code",
        "terminal_publish_should_notify",
        "terminal_publish_should_create_follow_up",
        "terminal_publish_channel",
        "release_delivery_final_verdict_status",
        "release_delivery_final_verdict_decision",
        "release_delivery_final_verdict_exit_code",
        "final_should_close_release",
        "final_should_open_follow_up",
        "final_should_page_owner",
        "final_announcement_target",
        "release_follow_up_dispatch_status",
        "release_follow_up_dispatch_decision",
        "release_follow_up_dispatch_exit_code",
        "follow_up_required",
        "escalation_required",
        "dispatch_target",
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
        "source_release_delivery_final_verdict_report": _coerce_str(
            payload["source_release_delivery_final_verdict_report"],
            field="source_release_delivery_final_verdict_report",
            path=path,
        ),
        "source_release_delivery_terminal_publish_report": _coerce_str(
            payload["source_release_delivery_terminal_publish_report"],
            field="source_release_delivery_terminal_publish_report",
            path=path,
        ),
        "source_release_delivery_report": _coerce_str(
            payload["source_release_delivery_report"],
            field="source_release_delivery_report",
            path=path,
        ),
        "source_release_terminal_verdict_report": _coerce_str(
            payload["source_release_terminal_verdict_report"],
            field="source_release_terminal_verdict_report",
            path=path,
        ),
        "source_release_incident_report": _coerce_str(
            payload["source_release_incident_report"],
            field="source_release_incident_report",
            path=path,
        ),
        "source_release_verdict_report": _coerce_str(
            payload["source_release_verdict_report"],
            field="source_release_verdict_report",
            path=path,
        ),
        "source_release_archive_report": _coerce_str(
            payload["source_release_archive_report"],
            field="source_release_archive_report",
            path=path,
        ),
        "release_archive_status": _coerce_str(
            payload["release_archive_status"],
            field="release_archive_status",
            path=path,
        ),
        "release_archive_decision": _coerce_str(
            payload["release_archive_decision"],
            field="release_archive_decision",
            path=path,
        ),
        "release_archive_exit_code": _coerce_int(
            payload["release_archive_exit_code"],
            field="release_archive_exit_code",
            path=path,
        ),
        "should_publish_archive": _coerce_bool(
            payload["should_publish_archive"],
            field="should_publish_archive",
            path=path,
        ),
        "release_verdict_status": _coerce_str(
            payload["release_verdict_status"],
            field="release_verdict_status",
            path=path,
        ),
        "release_verdict_decision": _coerce_str(
            payload["release_verdict_decision"],
            field="release_verdict_decision",
            path=path,
        ),
        "release_verdict_exit_code": _coerce_int(
            payload["release_verdict_exit_code"],
            field="release_verdict_exit_code",
            path=path,
        ),
        "should_ship_release": _coerce_bool(
            payload["should_ship_release"],
            field="should_ship_release",
            path=path,
        ),
        "should_open_incident": _coerce_bool(
            payload["should_open_incident"],
            field="should_open_incident",
            path=path,
        ),
        "should_dispatch_incident": _coerce_bool(
            payload["should_dispatch_incident"],
            field="should_dispatch_incident",
            path=path,
        ),
        "incident_dispatch_status": _coerce_str(
            payload["incident_dispatch_status"],
            field="incident_dispatch_status",
            path=path,
        ),
        "incident_dispatch_exit_code": _coerce_int(
            payload["incident_dispatch_exit_code"],
            field="incident_dispatch_exit_code",
            path=path,
        ),
        "incident_dispatch_attempted": _coerce_bool(
            payload["incident_dispatch_attempted"],
            field="incident_dispatch_attempted",
            path=path,
        ),
        "incident_url": _coerce_str(payload["incident_url"], field="incident_url", path=path),
        "release_terminal_verdict_status": _coerce_str(
            payload["release_terminal_verdict_status"],
            field="release_terminal_verdict_status",
            path=path,
        ),
        "release_terminal_verdict_decision": _coerce_str(
            payload["release_terminal_verdict_decision"],
            field="release_terminal_verdict_decision",
            path=path,
        ),
        "release_terminal_verdict_exit_code": _coerce_int(
            payload["release_terminal_verdict_exit_code"],
            field="release_terminal_verdict_exit_code",
            path=path,
        ),
        "terminal_should_ship_release": _coerce_bool(
            payload["terminal_should_ship_release"],
            field="terminal_should_ship_release",
            path=path,
        ),
        "terminal_requires_follow_up": _coerce_bool(
            payload["terminal_requires_follow_up"],
            field="terminal_requires_follow_up",
            path=path,
        ),
        "terminal_incident_linked": _coerce_bool(
            payload["terminal_incident_linked"],
            field="terminal_incident_linked",
            path=path,
        ),
        "release_delivery_status": _coerce_str(
            payload["release_delivery_status"],
            field="release_delivery_status",
            path=path,
        ),
        "release_delivery_decision": _coerce_str(
            payload["release_delivery_decision"],
            field="release_delivery_decision",
            path=path,
        ),
        "release_delivery_exit_code": _coerce_int(
            payload["release_delivery_exit_code"],
            field="release_delivery_exit_code",
            path=path,
        ),
        "delivery_should_ship_release": _coerce_bool(
            payload["delivery_should_ship_release"],
            field="delivery_should_ship_release",
            path=path,
        ),
        "delivery_requires_human_action": _coerce_bool(
            payload["delivery_requires_human_action"],
            field="delivery_requires_human_action",
            path=path,
        ),
        "delivery_should_announce_blocker": _coerce_bool(
            payload["delivery_should_announce_blocker"],
            field="delivery_should_announce_blocker",
            path=path,
        ),
        "release_delivery_terminal_publish_status": _coerce_str(
            payload["release_delivery_terminal_publish_status"],
            field="release_delivery_terminal_publish_status",
            path=path,
        ),
        "release_delivery_terminal_publish_decision": _coerce_str(
            payload["release_delivery_terminal_publish_decision"],
            field="release_delivery_terminal_publish_decision",
            path=path,
        ),
        "release_delivery_terminal_publish_exit_code": _coerce_int(
            payload["release_delivery_terminal_publish_exit_code"],
            field="release_delivery_terminal_publish_exit_code",
            path=path,
        ),
        "terminal_publish_should_notify": _coerce_bool(
            payload["terminal_publish_should_notify"],
            field="terminal_publish_should_notify",
            path=path,
        ),
        "terminal_publish_should_create_follow_up": _coerce_bool(
            payload["terminal_publish_should_create_follow_up"],
            field="terminal_publish_should_create_follow_up",
            path=path,
        ),
        "terminal_publish_channel": _coerce_str(
            payload["terminal_publish_channel"],
            field="terminal_publish_channel",
            path=path,
        ),
        "release_delivery_final_verdict_status": _coerce_str(
            payload["release_delivery_final_verdict_status"],
            field="release_delivery_final_verdict_status",
            path=path,
        ),
        "release_delivery_final_verdict_decision": _coerce_str(
            payload["release_delivery_final_verdict_decision"],
            field="release_delivery_final_verdict_decision",
            path=path,
        ),
        "release_delivery_final_verdict_exit_code": _coerce_int(
            payload["release_delivery_final_verdict_exit_code"],
            field="release_delivery_final_verdict_exit_code",
            path=path,
        ),
        "final_should_close_release": _coerce_bool(
            payload["final_should_close_release"],
            field="final_should_close_release",
            path=path,
        ),
        "final_should_open_follow_up": _coerce_bool(
            payload["final_should_open_follow_up"],
            field="final_should_open_follow_up",
            path=path,
        ),
        "final_should_page_owner": _coerce_bool(
            payload["final_should_page_owner"],
            field="final_should_page_owner",
            path=path,
        ),
        "final_announcement_target": _coerce_str(
            payload["final_announcement_target"],
            field="final_announcement_target",
            path=path,
        ),
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


def build_follow_up_command_parts(
    dispatch_report: dict[str, Any],
    *,
    source_report_path: Path,
    gh_executable: str,
    follow_up_command: str,
    follow_up_repo: str,
    follow_up_label: str,
    follow_up_title_prefix: str,
) -> list[str]:
    if follow_up_command.strip():
        try:
            custom_parts = shlex.split(follow_up_command)
        except ValueError as exc:
            raise ValueError(f"invalid --follow-up-command ({exc})") from exc
        if not custom_parts:
            raise ValueError("invalid --follow-up-command (empty command)")
        return custom_parts

    dispatch_status = str(dispatch_report["release_follow_up_dispatch_status"])
    dispatch_decision = str(dispatch_report["release_follow_up_dispatch_decision"])
    dispatch_target = str(dispatch_report["dispatch_target"])
    release_run_url = str(dispatch_report["release_run_url"])
    reason_codes = list(dispatch_report["reason_codes"])
    reason_codes_text = ", ".join(reason_codes) if reason_codes else "none"

    title = (
        f"{follow_up_title_prefix} release_follow_up_dispatch_status={dispatch_status} "
        f"release_follow_up_dispatch_decision={dispatch_decision}"
    )
    body = "\n".join(
        [
            "Automated follow-up opened by P2-45 release follow-up closure gate.",
            "",
            f"- release_follow_up_dispatch_status: {dispatch_status}",
            f"- release_follow_up_dispatch_decision: {dispatch_decision}",
            f"- release_follow_up_dispatch_exit_code: {dispatch_report['release_follow_up_dispatch_exit_code']}",
            f"- dispatch_target: {dispatch_target}",
            f"- release_run_id: {dispatch_report['release_run_id']}",
            f"- release_run_url: {release_run_url}",
            f"- source_release_follow_up_dispatch_report: {source_report_path}",
            f"- reason_codes: {reason_codes_text}",
        ]
    )

    parts = [
        gh_executable,
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
    ]
    if follow_up_label.strip():
        parts.extend(["--label", follow_up_label])
    if follow_up_repo.strip():
        parts.extend(["--repo", follow_up_repo])
    return parts


def execute_follow_up_command(
    command_parts: list[str], *, cwd: Path, timeout_seconds: int
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command_parts,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "attempted": True,
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "error_type": "command_not_found",
            "error_message": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "attempted": True,
            "returncode": 124,
            "stdout_tail": _tail_text(stdout),
            "stderr_tail": _tail_text(stderr),
            "error_type": "timeout",
            "error_message": f"follow-up command timeout after {timeout_seconds}s",
        }

    return {
        "attempted": True,
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(completed.stdout or ""),
        "stderr_tail": _tail_text(completed.stderr or ""),
        "error_type": "",
        "error_message": "",
    }


def build_release_follow_up_closure_payload(
    dispatch_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    follow_up_repo: str,
    follow_up_label: str,
    follow_up_title_prefix: str,
    follow_up_command_parts: list[str],
    dry_run: bool,
    command_result: dict[str, Any] | None,
) -> dict[str, Any]:
    dispatch_status = str(dispatch_report["release_follow_up_dispatch_status"])
    dispatch_decision = str(dispatch_report["release_follow_up_dispatch_decision"])
    dispatch_exit_code = int(dispatch_report["release_follow_up_dispatch_exit_code"])
    follow_up_required = bool(dispatch_report["follow_up_required"])
    escalation_required = bool(dispatch_report["escalation_required"])
    dispatch_target = str(dispatch_report["dispatch_target"])

    reason_codes = list(dispatch_report["reason_codes"])
    structural_issues = list(dispatch_report["structural_issues"])
    missing_artifacts = list(dispatch_report["missing_artifacts"])
    evidence_manifest = list(dispatch_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_follow_up_closure_evidence_missing")

    if dispatch_status == "closed":
        if dispatch_decision != "no_action":
            structural_issues.append("dispatch_decision_mismatch_closed")
        if dispatch_exit_code != 0:
            structural_issues.append("dispatch_exit_code_mismatch_closed")
        if follow_up_required:
            structural_issues.append("follow_up_required_mismatch_closed")
        if escalation_required:
            structural_issues.append("escalation_required_mismatch_closed")
        if dispatch_target != "none":
            structural_issues.append("dispatch_target_mismatch_closed")
    elif dispatch_status == "follow_up_required":
        if dispatch_decision != "dispatch_follow_up":
            structural_issues.append("dispatch_decision_mismatch_follow_up_required")
        if dispatch_exit_code == 0:
            structural_issues.append("dispatch_exit_code_mismatch_follow_up_required")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_follow_up_required")
        if escalation_required:
            structural_issues.append("escalation_required_mismatch_follow_up_required")
        if dispatch_target != "follow_up_queue":
            structural_issues.append("dispatch_target_mismatch_follow_up_required")
    elif dispatch_status == "escalated":
        if dispatch_decision != "dispatch_escalation":
            structural_issues.append("dispatch_decision_mismatch_escalated")
        if dispatch_exit_code == 0:
            structural_issues.append("dispatch_exit_code_mismatch_escalated")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_escalated")
        if not escalation_required:
            structural_issues.append("escalation_required_mismatch_escalated")
        if dispatch_target != "incident_commander":
            structural_issues.append("dispatch_target_mismatch_escalated")
    else:
        if dispatch_decision != "abort_dispatch":
            structural_issues.append("dispatch_decision_mismatch_contract_failed")
        if dispatch_exit_code == 0:
            structural_issues.append("dispatch_exit_code_mismatch_contract_failed")
        if not follow_up_required:
            structural_issues.append("follow_up_required_mismatch_contract_failed")
        if not escalation_required:
            structural_issues.append("escalation_required_mismatch_contract_failed")
        if dispatch_target != "incident_commander":
            structural_issues.append("dispatch_target_mismatch_contract_failed")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)
    reason_codes = _unique(reason_codes)

    follow_up_command = (
        _format_shell_command(follow_up_command_parts) if follow_up_command_parts else ""
    )
    should_queue_follow_up = follow_up_required and not structural_issues and not missing_artifacts
    follow_up_queue_attempted = False
    follow_up_task_queued = False
    escalation_task_queued = False
    follow_up_queue_url = ""
    command_returncode: int | None = None
    command_stdout_tail = ""
    command_stderr_tail = ""
    follow_up_error_type = ""
    follow_up_error_message = ""

    closure_status = "closed"
    closure_decision = "no_action"
    closure_exit_code = 0

    if structural_issues or missing_artifacts:
        closure_status = "contract_failed"
        closure_decision = "abort_queue"
        closure_exit_code = 1
        reason_codes.extend(structural_issues)
    elif not should_queue_follow_up:
        closure_status = "closed"
        closure_decision = "no_action"
        closure_exit_code = 0
        if dispatch_status == "closed":
            reason_codes = ["release_follow_up_closed_no_action"]
    elif dry_run:
        closure_status = "queued_dry_run"
        closure_decision = (
            "queue_escalation" if escalation_required else "queue_follow_up"
        )
        closure_exit_code = 0
    else:
        follow_up_queue_attempted = True
        if command_result is None:
            closure_status = "queue_failed"
            closure_decision = "abort_queue"
            closure_exit_code = 1
            reason_codes.append("follow_up_command_result_missing")
        else:
            command_returncode = int(command_result["returncode"])
            command_stdout_tail = str(command_result.get("stdout_tail", ""))
            command_stderr_tail = str(command_result.get("stderr_tail", ""))
            follow_up_error_type = str(command_result.get("error_type", ""))
            follow_up_error_message = str(command_result.get("error_message", ""))

            if command_returncode == 0:
                closure_status = "queued"
                closure_decision = (
                    "queue_escalation" if escalation_required else "queue_follow_up"
                )
                closure_exit_code = 0
                follow_up_task_queued = True
                escalation_task_queued = escalation_required
                follow_up_queue_url = _extract_url(command_stdout_tail)
                reason_codes = (
                    ["release_follow_up_escalation_queued"]
                    if escalation_required
                    else ["release_follow_up_queued"]
                )
            else:
                closure_status = "queue_failed"
                closure_decision = "abort_queue"
                closure_exit_code = 1
                if follow_up_error_type == "command_not_found":
                    reason_codes.append("release_follow_up_cli_unavailable")
                elif follow_up_error_type == "timeout":
                    reason_codes.append("release_follow_up_timeout")
                else:
                    reason_codes.append("release_follow_up_command_failed")

    reason_codes = _unique(reason_codes)

    if closure_status not in ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_STATUSES:
        raise ValueError("internal: unsupported follow-up closure status computed")
    if closure_decision not in ALLOWED_RELEASE_FOLLOW_UP_CLOSURE_DECISIONS:
        raise ValueError("internal: unsupported follow-up closure decision computed")

    closure_summary = (
        f"release_follow_up_dispatch_status={dispatch_status} "
        f"release_follow_up_closure_status={closure_status} "
        f"should_queue_follow_up={should_queue_follow_up}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_follow_up_dispatch_report": str(source_path),
        "project_root": str(project_root),
        "source_release_delivery_final_verdict_report": str(
            dispatch_report["source_release_delivery_final_verdict_report"]
        ),
        "source_release_delivery_terminal_publish_report": str(
            dispatch_report["source_release_delivery_terminal_publish_report"]
        ),
        "source_release_delivery_report": str(dispatch_report["source_release_delivery_report"]),
        "source_release_terminal_verdict_report": str(
            dispatch_report["source_release_terminal_verdict_report"]
        ),
        "source_release_incident_report": str(dispatch_report["source_release_incident_report"]),
        "source_release_verdict_report": str(dispatch_report["source_release_verdict_report"]),
        "source_release_archive_report": str(dispatch_report["source_release_archive_report"]),
        "release_archive_status": str(dispatch_report["release_archive_status"]),
        "release_archive_decision": str(dispatch_report["release_archive_decision"]),
        "release_archive_exit_code": int(dispatch_report["release_archive_exit_code"]),
        "should_publish_archive": bool(dispatch_report["should_publish_archive"]),
        "release_verdict_status": str(dispatch_report["release_verdict_status"]),
        "release_verdict_decision": str(dispatch_report["release_verdict_decision"]),
        "release_verdict_exit_code": int(dispatch_report["release_verdict_exit_code"]),
        "should_ship_release": bool(dispatch_report["should_ship_release"]),
        "should_open_incident": bool(dispatch_report["should_open_incident"]),
        "should_dispatch_incident": bool(dispatch_report["should_dispatch_incident"]),
        "incident_dispatch_status": str(dispatch_report["incident_dispatch_status"]),
        "incident_dispatch_exit_code": int(dispatch_report["incident_dispatch_exit_code"]),
        "incident_dispatch_attempted": bool(dispatch_report["incident_dispatch_attempted"]),
        "incident_url": str(dispatch_report["incident_url"]),
        "release_terminal_verdict_status": str(dispatch_report["release_terminal_verdict_status"]),
        "release_terminal_verdict_decision": str(
            dispatch_report["release_terminal_verdict_decision"]
        ),
        "release_terminal_verdict_exit_code": int(
            dispatch_report["release_terminal_verdict_exit_code"]
        ),
        "terminal_should_ship_release": bool(dispatch_report["terminal_should_ship_release"]),
        "terminal_requires_follow_up": bool(dispatch_report["terminal_requires_follow_up"]),
        "terminal_incident_linked": bool(dispatch_report["terminal_incident_linked"]),
        "release_delivery_status": str(dispatch_report["release_delivery_status"]),
        "release_delivery_decision": str(dispatch_report["release_delivery_decision"]),
        "release_delivery_exit_code": int(dispatch_report["release_delivery_exit_code"]),
        "delivery_should_ship_release": bool(dispatch_report["delivery_should_ship_release"]),
        "delivery_requires_human_action": bool(dispatch_report["delivery_requires_human_action"]),
        "delivery_should_announce_blocker": bool(
            dispatch_report["delivery_should_announce_blocker"]
        ),
        "release_delivery_terminal_publish_status": str(
            dispatch_report["release_delivery_terminal_publish_status"]
        ),
        "release_delivery_terminal_publish_decision": str(
            dispatch_report["release_delivery_terminal_publish_decision"]
        ),
        "release_delivery_terminal_publish_exit_code": int(
            dispatch_report["release_delivery_terminal_publish_exit_code"]
        ),
        "terminal_publish_should_notify": bool(dispatch_report["terminal_publish_should_notify"]),
        "terminal_publish_should_create_follow_up": bool(
            dispatch_report["terminal_publish_should_create_follow_up"]
        ),
        "terminal_publish_channel": str(dispatch_report["terminal_publish_channel"]),
        "release_delivery_final_verdict_status": str(
            dispatch_report["release_delivery_final_verdict_status"]
        ),
        "release_delivery_final_verdict_decision": str(
            dispatch_report["release_delivery_final_verdict_decision"]
        ),
        "release_delivery_final_verdict_exit_code": int(
            dispatch_report["release_delivery_final_verdict_exit_code"]
        ),
        "final_should_close_release": bool(dispatch_report["final_should_close_release"]),
        "final_should_open_follow_up": bool(dispatch_report["final_should_open_follow_up"]),
        "final_should_page_owner": bool(dispatch_report["final_should_page_owner"]),
        "final_announcement_target": str(dispatch_report["final_announcement_target"]),
        "release_follow_up_dispatch_status": dispatch_status,
        "release_follow_up_dispatch_decision": dispatch_decision,
        "release_follow_up_dispatch_exit_code": dispatch_exit_code,
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
        "follow_up_command": follow_up_command,
        "follow_up_command_parts": list(follow_up_command_parts),
        "follow_up_command_returncode": command_returncode,
        "follow_up_command_stdout_tail": command_stdout_tail,
        "follow_up_command_stderr_tail": command_stderr_tail,
        "follow_up_error_type": follow_up_error_type,
        "follow_up_error_message": follow_up_error_message,
        "follow_up_repo": follow_up_repo,
        "follow_up_label": follow_up_label,
        "follow_up_title_prefix": follow_up_title_prefix,
        "follow_up_queue_url": follow_up_queue_url,
        "release_run_id": dispatch_report["release_run_id"],
        "release_run_url": str(dispatch_report["release_run_url"]),
        "release_follow_up_closure_summary": closure_summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Follow-Up Closure Report",
        "",
        (
            "- Release Follow-Up Closure Status: "
            f"**{str(payload['release_follow_up_closure_status']).upper()}**"
        ),
        (
            "- Release Follow-Up Closure Decision: "
            f"`{payload['release_follow_up_closure_decision']}`"
        ),
        (
            "- Release Follow-Up Closure Exit Code: "
            f"`{payload['release_follow_up_closure_exit_code']}`"
        ),
        f"- Should Queue Follow Up: `{payload['should_queue_follow_up']}`",
        f"- Follow Up Queue Attempted: `{payload['follow_up_queue_attempted']}`",
        f"- Follow Up Task Queued: `{payload['follow_up_task_queued']}`",
        f"- Escalation Task Queued: `{payload['escalation_task_queued']}`",
        f"- Dispatch Target: `{payload['dispatch_target']}`",
        f"- Follow Up Queue URL: `{payload['follow_up_queue_url']}`",
        (
            "- Release Follow-Up Dispatch Status: "
            f"`{payload['release_follow_up_dispatch_status']}`"
        ),
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Follow-Up Command",
    ]

    follow_up_command = str(payload["follow_up_command"])
    if follow_up_command:
        lines.append(f"- `{follow_up_command}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Summary", "", f"- {payload['release_follow_up_closure_summary']}", "", "## Reason Codes"])
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
        "workflow_release_follow_up_closure_status": str(payload["release_follow_up_closure_status"]),
        "workflow_release_follow_up_closure_decision": str(payload["release_follow_up_closure_decision"]),
        "workflow_release_follow_up_closure_exit_code": str(payload["release_follow_up_closure_exit_code"]),
        "workflow_release_follow_up_closure_should_queue": (
            "true" if payload["should_queue_follow_up"] else "false"
        ),
        "workflow_release_follow_up_closure_attempted": (
            "true" if payload["follow_up_queue_attempted"] else "false"
        ),
        "workflow_release_follow_up_closure_follow_up_queued": (
            "true" if payload["follow_up_task_queued"] else "false"
        ),
        "workflow_release_follow_up_closure_escalation_queued": (
            "true" if payload["escalation_task_queued"] else "false"
        ),
        "workflow_release_follow_up_closure_target": str(payload["dispatch_target"]),
        "workflow_release_follow_up_closure_queue_url": str(payload["follow_up_queue_url"]),
        "workflow_release_follow_up_closure_dispatch_status": str(
            payload["release_follow_up_dispatch_status"]
        ),
        "workflow_release_follow_up_closure_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_follow_up_closure_run_url": str(payload["release_run_url"]),
        "workflow_release_follow_up_closure_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_follow_up_closure_report_json": str(output_json),
        "workflow_release_follow_up_closure_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Linux CI workflow release follow-up closure gate "
            "from P2-44 release follow-up dispatch report"
        )
    )
    parser.add_argument(
        "--release-follow-up-dispatch-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json",
        help="P2-44 release follow-up dispatch report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for follow-up command execution",
    )
    parser.add_argument(
        "--gh-executable",
        default="gh",
        help="GitHub CLI executable used when auto-building follow-up command",
    )
    parser.add_argument(
        "--follow-up-command",
        default="",
        help="Optional explicit follow-up command string (overrides auto command)",
    )
    parser.add_argument(
        "--follow-up-repo",
        default="",
        help="Optional GitHub repo for follow-up creation (OWNER/REPO)",
    )
    parser.add_argument(
        "--follow-up-label",
        default="release-follow-up",
        help="Follow-up label forwarded to auto-built command",
    )
    parser.add_argument(
        "--follow-up-title-prefix",
        default="[release-follow-up]",
        help="Follow-up title prefix for auto-built command",
    )
    parser.add_argument(
        "--follow-up-timeout-seconds",
        type=int,
        default=600,
        help="Follow-up command timeout in seconds",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json",
        help="Output release follow-up closure JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.md",
        help="Output release follow-up closure markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release follow-up closure JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate contract and skip follow-up command execution",
    )
    args = parser.parse_args()

    if args.follow_up_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-release-follow-up-closure-gate] "
            "--follow-up-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    dispatch_report_path = Path(args.release_follow_up_dispatch_report)
    project_root = Path(args.project_root)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        dispatch_report = load_release_follow_up_dispatch_report(dispatch_report_path)
    except ValueError as exc:
        print(
            f"[p2-linux-ci-workflow-release-follow-up-closure-gate] {exc}",
            file=sys.stderr,
        )
        return 2

    follow_up_command_parts: list[str] = []
    if dispatch_report["follow_up_required"]:
        try:
            follow_up_command_parts = build_follow_up_command_parts(
                dispatch_report,
                source_report_path=dispatch_report_path.resolve(),
                gh_executable=args.gh_executable,
                follow_up_command=args.follow_up_command,
                follow_up_repo=args.follow_up_repo,
                follow_up_label=args.follow_up_label,
                follow_up_title_prefix=args.follow_up_title_prefix,
            )
        except ValueError as exc:
            print(
                f"[p2-linux-ci-workflow-release-follow-up-closure-gate] {exc}",
                file=sys.stderr,
            )
            return 2

    command_result: dict[str, Any] | None = None
    if dispatch_report["follow_up_required"] and not args.dry_run:
        command_result = execute_follow_up_command(
            follow_up_command_parts,
            cwd=project_root,
            timeout_seconds=args.follow_up_timeout_seconds,
        )

    payload = build_release_follow_up_closure_payload(
        dispatch_report,
        source_path=dispatch_report_path.resolve(),
        project_root=project_root.resolve(),
        follow_up_repo=args.follow_up_repo,
        follow_up_label=args.follow_up_label,
        follow_up_title_prefix=args.follow_up_title_prefix,
        follow_up_command_parts=follow_up_command_parts,
        dry_run=args.dry_run,
        command_result=command_result,
    )

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release follow-up closure json: {output_json_path}")
        print(f"release follow-up closure markdown: {output_markdown_path}")

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
        "release follow-up closure summary: "
        f"release_follow_up_closure_status={payload['release_follow_up_closure_status']} "
        f"should_queue_follow_up={payload['should_queue_follow_up']} "
        f"release_follow_up_closure_exit_code={payload['release_follow_up_closure_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_follow_up_closure_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
