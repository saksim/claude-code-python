"""Phase 2 card P2-67 gate for Linux CI workflow Linux-validation terminal verdict.

This script consumes the P2-66 Linux-validation final publish archive artifact and converges
one terminal verdict contract for Linux validation:
1) validate Linux validation final publish archive + evidence consistency,
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


ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_STATUSES: set[str] = {
    "archived",
    "archived_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_DECISIONS: set[str] = {
    "archive_release_shipped",
    "archive_release_shipped_with_follow_up",
    "archive_release_blocker",
    "abort_archive",
}
ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_CHANNELS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}

ALLOWED_LINUX_VALIDATION_TERMINAL_VERDICT_STATUSES: set[str] = {
    "ready_for_linux_validation",
    "ready_with_follow_up_for_linux_validation",
    "blocked",
    "contract_failed",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_VERDICT_DECISIONS: set[str] = {
    "proceed_linux_validation",
    "proceed_linux_validation_with_follow_up",
    "halt_linux_validation_blocker",
    "abort_linux_validation",
}
ALLOWED_LINUX_VALIDATION_TERMINAL_VERDICT_CHANNELS: set[str] = {
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


def _load_evidence_manifest(value: Any, *, field: str, path: Path) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{path}: field '{field}' must be object list")

    evidence_manifest: list[dict[str, Any]] = []
    for idx, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: {field}[{idx}] must be object")
        if "source" not in entry or "path" not in entry or "exists" not in entry:
            raise ValueError(f"{path}: {field}[{idx}] missing source/path/exists")
        evidence_manifest.append(
            {
                "source": _coerce_str(entry["source"], field=f"{field}[{idx}].source", path=path),
                "path": _coerce_str(entry["path"], field=f"{field}[{idx}].path", path=path),
                "exists": _coerce_bool(entry["exists"], field=f"{field}[{idx}].exists", path=path),
            }
        )
    return evidence_manifest


def load_linux_validation_final_publish_archive_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: Linux validation final publish archive report not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: Linux validation final publish archive payload must be object")

    required_fields = (
        "source_linux_validation_dispatch_report",
        "project_root",
        "source_terminal_verdict_report",
        "source_release_final_publish_archive_report",
        "source_gate_manifest_drift_report",
        "release_final_publish_archive_status",
        "gate_manifest_drift_status",
        "gate_manifest_drift_missing_runtime_tests",
        "gate_manifest_drift_missing_manifest_entries",
        "gate_manifest_drift_orphan_manifest_entries",
        "terminal_verdict_status",
        "terminal_verdict_decision",
        "terminal_verdict_exit_code",
        "terminal_verdict_should_proceed",
        "terminal_verdict_requires_manual_action",
        "terminal_verdict_channel",
        "linux_validation_should_dispatch",
        "linux_validation_requires_manual_action",
        "linux_validation_channel",
        "linux_validation_dispatch_status",
        "linux_validation_dispatch_decision",
        "linux_validation_dispatch_exit_code",
        "linux_validation_dispatch_attempted",
        "linux_validation_dispatch_command_returncode",
        "linux_validation_final_publish_archive_status",
        "linux_validation_final_publish_archive_decision",
        "linux_validation_final_publish_archive_exit_code",
        "linux_validation_final_publish_archive_should_archive",
        "linux_validation_final_publish_archive_requires_manual_action",
        "linux_validation_final_publish_archive_channel",
        "linux_validation_final_publish_archive_attempted",
        "linux_validation_final_publish_archive_timeout_seconds",
        "linux_validation_final_publish_archive_command",
        "linux_validation_final_publish_archive_command_parts",
        "dry_run",
        "verdict_command_returncode",
        "verdict_command_stdout_tail",
        "verdict_command_stderr_tail",
        "verdict_error_type",
        "verdict_error_message",
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "linux_validation_dispatch_summary",
        "linux_validation_final_publish_archive_summary",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        "evidence_manifest",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    verdict_status = _coerce_str(
        payload["linux_validation_final_publish_archive_status"],
        field="linux_validation_final_publish_archive_status",
        path=path,
    )
    if verdict_status not in ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_STATUSES:
        raise ValueError(
            f"{path}: field 'linux_validation_final_publish_archive_status' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_STATUSES)}"
        )

    verdict_decision = _coerce_str(
        payload["linux_validation_final_publish_archive_decision"],
        field="linux_validation_final_publish_archive_decision",
        path=path,
    )
    if verdict_decision not in ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_DECISIONS:
        raise ValueError(
            f"{path}: field 'linux_validation_final_publish_archive_decision' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_DECISIONS)}"
        )

    verdict_exit_code = _coerce_int(
        payload["linux_validation_final_publish_archive_exit_code"],
        field="linux_validation_final_publish_archive_exit_code",
        path=path,
    )
    if verdict_exit_code < 0:
        raise ValueError(f"{path}: field 'linux_validation_final_publish_archive_exit_code' must be >= 0")

    verdict_channel = _coerce_str(
        payload["linux_validation_final_publish_archive_channel"],
        field="linux_validation_final_publish_archive_channel",
        path=path,
    )
    if verdict_channel not in ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_CHANNELS:
        raise ValueError(
            f"{path}: field 'linux_validation_final_publish_archive_channel' must be one of "
            f"{sorted(ALLOWED_LINUX_VALIDATION_FINAL_PUBLISH_ARCHIVE_CHANNELS)}"
        )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    dispatch_command_returncode = _coerce_optional_int(
        payload["linux_validation_dispatch_command_returncode"],
        field="linux_validation_dispatch_command_returncode",
        path=path,
    )
    verdict_command_returncode = _coerce_optional_int(
        payload["verdict_command_returncode"],
        field="verdict_command_returncode",
        path=path,
    )

    return {
        "generated_at": payload.get("generated_at"),
        "source_linux_validation_dispatch_report": _coerce_str(
            payload["source_linux_validation_dispatch_report"],
            field="source_linux_validation_dispatch_report",
            path=path,
        ),
        "project_root": _coerce_str(payload["project_root"], field="project_root", path=path),
        "source_terminal_verdict_report": _coerce_str(
            payload["source_terminal_verdict_report"],
            field="source_terminal_verdict_report",
            path=path,
        ),
        "source_release_final_publish_archive_report": _coerce_str(
            payload["source_release_final_publish_archive_report"],
            field="source_release_final_publish_archive_report",
            path=path,
        ),
        "source_gate_manifest_drift_report": _coerce_str(
            payload["source_gate_manifest_drift_report"],
            field="source_gate_manifest_drift_report",
            path=path,
        ),
        "release_final_publish_archive_status": _coerce_str(
            payload["release_final_publish_archive_status"],
            field="release_final_publish_archive_status",
            path=path,
        ),
        "gate_manifest_drift_status": _coerce_str(
            payload["gate_manifest_drift_status"],
            field="gate_manifest_drift_status",
            path=path,
        ),
        "gate_manifest_drift_missing_runtime_tests": _coerce_str_list(
            payload["gate_manifest_drift_missing_runtime_tests"],
            field="gate_manifest_drift_missing_runtime_tests",
            path=path,
        ),
        "gate_manifest_drift_missing_manifest_entries": _coerce_str_list(
            payload["gate_manifest_drift_missing_manifest_entries"],
            field="gate_manifest_drift_missing_manifest_entries",
            path=path,
        ),
        "gate_manifest_drift_orphan_manifest_entries": _coerce_str_list(
            payload["gate_manifest_drift_orphan_manifest_entries"],
            field="gate_manifest_drift_orphan_manifest_entries",
            path=path,
        ),
        "terminal_verdict_status": _coerce_str(
            payload["terminal_verdict_status"],
            field="terminal_verdict_status",
            path=path,
        ),
        "terminal_verdict_decision": _coerce_str(
            payload["terminal_verdict_decision"],
            field="terminal_verdict_decision",
            path=path,
        ),
        "terminal_verdict_exit_code": _coerce_int(
            payload["terminal_verdict_exit_code"],
            field="terminal_verdict_exit_code",
            path=path,
        ),
        "terminal_verdict_should_proceed": _coerce_bool(
            payload["terminal_verdict_should_proceed"],
            field="terminal_verdict_should_proceed",
            path=path,
        ),
        "terminal_verdict_requires_manual_action": _coerce_bool(
            payload["terminal_verdict_requires_manual_action"],
            field="terminal_verdict_requires_manual_action",
            path=path,
        ),
        "terminal_verdict_channel": _coerce_str(
            payload["terminal_verdict_channel"],
            field="terminal_verdict_channel",
            path=path,
        ),
        "linux_validation_should_dispatch": _coerce_bool(
            payload["linux_validation_should_dispatch"],
            field="linux_validation_should_dispatch",
            path=path,
        ),
        "linux_validation_requires_manual_action": _coerce_bool(
            payload["linux_validation_requires_manual_action"],
            field="linux_validation_requires_manual_action",
            path=path,
        ),
        "linux_validation_channel": _coerce_str(
            payload["linux_validation_channel"],
            field="linux_validation_channel",
            path=path,
        ),
        "linux_validation_dispatch_status": _coerce_str(
            payload["linux_validation_dispatch_status"],
            field="linux_validation_dispatch_status",
            path=path,
        ),
        "linux_validation_dispatch_decision": _coerce_str(
            payload["linux_validation_dispatch_decision"],
            field="linux_validation_dispatch_decision",
            path=path,
        ),
        "linux_validation_dispatch_exit_code": _coerce_int(
            payload["linux_validation_dispatch_exit_code"],
            field="linux_validation_dispatch_exit_code",
            path=path,
        ),
        "linux_validation_dispatch_attempted": _coerce_bool(
            payload["linux_validation_dispatch_attempted"],
            field="linux_validation_dispatch_attempted",
            path=path,
        ),
        "linux_validation_dispatch_command_returncode": dispatch_command_returncode,
        "linux_validation_final_publish_archive_status": verdict_status,
        "linux_validation_final_publish_archive_decision": verdict_decision,
        "linux_validation_final_publish_archive_exit_code": verdict_exit_code,
        "linux_validation_final_publish_archive_should_archive": _coerce_bool(
            payload["linux_validation_final_publish_archive_should_archive"],
            field="linux_validation_final_publish_archive_should_archive",
            path=path,
        ),
        "linux_validation_final_publish_archive_requires_manual_action": _coerce_bool(
            payload["linux_validation_final_publish_archive_requires_manual_action"],
            field="linux_validation_final_publish_archive_requires_manual_action",
            path=path,
        ),
        "linux_validation_final_publish_archive_channel": verdict_channel,
        "linux_validation_final_publish_archive_attempted": _coerce_bool(
            payload["linux_validation_final_publish_archive_attempted"],
            field="linux_validation_final_publish_archive_attempted",
            path=path,
        ),
        "linux_validation_final_publish_archive_timeout_seconds": _coerce_int(
            payload["linux_validation_final_publish_archive_timeout_seconds"],
            field="linux_validation_final_publish_archive_timeout_seconds",
            path=path,
        ),
        "linux_validation_final_publish_archive_command": _coerce_str(
            payload["linux_validation_final_publish_archive_command"],
            field="linux_validation_final_publish_archive_command",
            path=path,
        ),
        "linux_validation_final_publish_archive_command_parts": _coerce_str_list(
            payload["linux_validation_final_publish_archive_command_parts"],
            field="linux_validation_final_publish_archive_command_parts",
            path=path,
        ),
        "dry_run": _coerce_bool(payload["dry_run"], field="dry_run", path=path),
        "verdict_command_returncode": verdict_command_returncode,
        "verdict_command_stdout_tail": _coerce_str(
            payload["verdict_command_stdout_tail"],
            field="verdict_command_stdout_tail",
            path=path,
        ),
        "verdict_command_stderr_tail": _coerce_str(
            payload["verdict_command_stderr_tail"],
            field="verdict_command_stderr_tail",
            path=path,
        ),
        "verdict_error_type": _coerce_str(
            payload["verdict_error_type"],
            field="verdict_error_type",
            path=path,
        ),
        "verdict_error_message": _coerce_str(
            payload["verdict_error_message"],
            field="verdict_error_message",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(payload["release_run_url"], field="release_run_url", path=path),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "linux_validation_dispatch_summary": _coerce_str(
            payload["linux_validation_dispatch_summary"],
            field="linux_validation_dispatch_summary",
            path=path,
        ),
        "linux_validation_final_publish_archive_summary": _coerce_str(
            payload["linux_validation_final_publish_archive_summary"],
            field="linux_validation_final_publish_archive_summary",
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
        "evidence_manifest": _load_evidence_manifest(
            payload["evidence_manifest"],
            field="evidence_manifest",
            path=path,
        ),
    }


def build_linux_validation_terminal_verdict_payload(
    linux_validation_final_publish_archive_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    verdict_status = str(
        linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_status"]
    )
    verdict_decision = str(
        linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_decision"]
    )
    verdict_exit_code = int(
        linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_exit_code"]
    )
    verdict_should_archive = bool(
        linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_should_archive"]
    )
    verdict_requires_manual_action = bool(
        linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_requires_manual_action"]
    )
    verdict_channel = str(
        linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_channel"]
    )

    reason_codes = list(linux_validation_final_publish_archive_report["reason_codes"])
    structural_issues = list(linux_validation_final_publish_archive_report["structural_issues"])
    missing_artifacts = list(linux_validation_final_publish_archive_report["missing_artifacts"])
    evidence_manifest = list(linux_validation_final_publish_archive_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("linux_validation_terminal_verdict_evidence_missing")

    expected_archive = {
        "archived": (
            "archive_release_shipped",
            0,
            True,
            False,
            "release",
        ),
        "archived_with_follow_up": (
            "archive_release_shipped_with_follow_up",
            None,
            True,
            False,
            "follow_up",
        ),
        "blocked": (
            "archive_release_blocker",
            None,
            False,
            True,
            "blocker",
        ),
        "contract_failed": (
            "abort_archive",
            None,
            False,
            True,
            "blocker",
        ),
    }
    (
        expected_decision,
        expected_exit_code,
        expected_should_archive,
        expected_requires_manual_action,
        expected_channel,
    ) = expected_archive[verdict_status]

    if verdict_decision != expected_decision:
        structural_issues.append("linux_validation_final_publish_archive_decision_mismatch")
    if verdict_should_archive != expected_should_archive:
        structural_issues.append("linux_validation_final_publish_archive_should_archive_mismatch")
    if verdict_requires_manual_action != expected_requires_manual_action:
        structural_issues.append("linux_validation_final_publish_archive_requires_manual_action_mismatch")
    if verdict_channel != expected_channel:
        structural_issues.append("linux_validation_final_publish_archive_channel_mismatch")
    if expected_exit_code == 0 and verdict_exit_code != 0:
        structural_issues.append("linux_validation_final_publish_archive_exit_code_mismatch_archived")
    if expected_exit_code is None and verdict_exit_code == 0 and verdict_status != "archived":
        structural_issues.append("linux_validation_final_publish_archive_exit_code_mismatch_non_archived")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    terminal_status: str
    terminal_decision: str
    terminal_exit_code: int
    terminal_should_proceed: bool
    terminal_requires_manual_action: bool
    terminal_channel: str

    if structural_issues or missing_artifacts:
        terminal_status = "contract_failed"
        terminal_decision = "abort_linux_validation"
        terminal_exit_code = max(1, verdict_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif verdict_status == "archived":
        terminal_status = "ready_for_linux_validation"
        terminal_decision = "proceed_linux_validation"
        terminal_exit_code = 0
        terminal_should_proceed = True
        terminal_requires_manual_action = False
        terminal_channel = "release"
        reason_codes = ["linux_validation_terminal_verdict_ready_for_linux_validation"]
    elif verdict_status == "archived_with_follow_up":
        terminal_status = "ready_with_follow_up_for_linux_validation"
        terminal_decision = "proceed_linux_validation_with_follow_up"
        terminal_exit_code = max(1, verdict_exit_code)
        terminal_should_proceed = True
        terminal_requires_manual_action = False
        terminal_channel = "follow_up"
        reason_codes.append("linux_validation_terminal_verdict_ready_with_follow_up_for_linux_validation")
    elif verdict_status == "blocked":
        terminal_status = "blocked"
        terminal_decision = "halt_linux_validation_blocker"
        terminal_exit_code = max(1, verdict_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.append("linux_validation_terminal_verdict_blocked")
    else:
        terminal_status = "contract_failed"
        terminal_decision = "abort_linux_validation"
        terminal_exit_code = max(1, verdict_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.append("linux_validation_terminal_verdict_upstream_contract_failed")

    if terminal_status not in ALLOWED_LINUX_VALIDATION_TERMINAL_VERDICT_STATUSES:
        raise ValueError("internal: unsupported linux_validation_terminal_verdict_status computed")
    if terminal_decision not in ALLOWED_LINUX_VALIDATION_TERMINAL_VERDICT_DECISIONS:
        raise ValueError("internal: unsupported linux_validation_terminal_verdict_decision computed")
    if terminal_channel not in ALLOWED_LINUX_VALIDATION_TERMINAL_VERDICT_CHANNELS:
        raise ValueError("internal: unsupported linux_validation_terminal_verdict_channel computed")

    reason_codes = _unique(reason_codes)
    summary = (
        f"linux_validation_final_publish_archive_status={verdict_status} "
        f"linux_validation_terminal_verdict_status={terminal_status} "
        f"linux_validation_terminal_verdict_decision={terminal_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_linux_validation_final_publish_archive_report": str(source_path),
        "source_linux_validation_dispatch_report": str(
            linux_validation_final_publish_archive_report["source_linux_validation_dispatch_report"]
        ),
        "project_root": str(linux_validation_final_publish_archive_report["project_root"]),
        "source_terminal_verdict_report": str(
            linux_validation_final_publish_archive_report["source_terminal_verdict_report"]
        ),
        "source_release_final_publish_archive_report": str(
            linux_validation_final_publish_archive_report["source_release_final_publish_archive_report"]
        ),
        "source_gate_manifest_drift_report": str(
            linux_validation_final_publish_archive_report["source_gate_manifest_drift_report"]
        ),
        "release_final_publish_archive_status": str(
            linux_validation_final_publish_archive_report["release_final_publish_archive_status"]
        ),
        "gate_manifest_drift_status": str(
            linux_validation_final_publish_archive_report["gate_manifest_drift_status"]
        ),
        "gate_manifest_drift_missing_runtime_tests": list(
            linux_validation_final_publish_archive_report["gate_manifest_drift_missing_runtime_tests"]
        ),
        "gate_manifest_drift_missing_manifest_entries": list(
            linux_validation_final_publish_archive_report["gate_manifest_drift_missing_manifest_entries"]
        ),
        "gate_manifest_drift_orphan_manifest_entries": list(
            linux_validation_final_publish_archive_report["gate_manifest_drift_orphan_manifest_entries"]
        ),
        "terminal_verdict_status": str(linux_validation_final_publish_archive_report["terminal_verdict_status"]),
        "terminal_verdict_decision": str(
            linux_validation_final_publish_archive_report["terminal_verdict_decision"]
        ),
        "terminal_verdict_exit_code": int(
            linux_validation_final_publish_archive_report["terminal_verdict_exit_code"]
        ),
        "terminal_verdict_should_proceed": bool(
            linux_validation_final_publish_archive_report["terminal_verdict_should_proceed"]
        ),
        "terminal_verdict_requires_manual_action": bool(
            linux_validation_final_publish_archive_report["terminal_verdict_requires_manual_action"]
        ),
        "terminal_verdict_channel": str(linux_validation_final_publish_archive_report["terminal_verdict_channel"]),
        "linux_validation_should_dispatch": bool(
            linux_validation_final_publish_archive_report["linux_validation_should_dispatch"]
        ),
        "linux_validation_requires_manual_action": bool(
            linux_validation_final_publish_archive_report["linux_validation_requires_manual_action"]
        ),
        "linux_validation_channel": str(linux_validation_final_publish_archive_report["linux_validation_channel"]),
        "linux_validation_dispatch_status": str(
            linux_validation_final_publish_archive_report["linux_validation_dispatch_status"]
        ),
        "linux_validation_dispatch_decision": str(
            linux_validation_final_publish_archive_report["linux_validation_dispatch_decision"]
        ),
        "linux_validation_dispatch_exit_code": int(
            linux_validation_final_publish_archive_report["linux_validation_dispatch_exit_code"]
        ),
        "linux_validation_dispatch_attempted": bool(
            linux_validation_final_publish_archive_report["linux_validation_dispatch_attempted"]
        ),
        "linux_validation_dispatch_command_returncode": linux_validation_final_publish_archive_report[
            "linux_validation_dispatch_command_returncode"
        ],
        "linux_validation_final_publish_archive_status": verdict_status,
        "linux_validation_final_publish_archive_decision": verdict_decision,
        "linux_validation_final_publish_archive_exit_code": verdict_exit_code,
        "linux_validation_final_publish_archive_should_archive": verdict_should_archive,
        "linux_validation_final_publish_archive_requires_manual_action": verdict_requires_manual_action,
        "linux_validation_final_publish_archive_channel": verdict_channel,
        "linux_validation_final_publish_archive_attempted": bool(
            linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_attempted"]
        ),
        "linux_validation_final_publish_archive_timeout_seconds": int(
            linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_timeout_seconds"]
        ),
        "linux_validation_final_publish_archive_command": str(
            linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_command"]
        ),
        "linux_validation_final_publish_archive_command_parts": list(
            linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_command_parts"]
        ),
        "dry_run": bool(linux_validation_final_publish_archive_report["dry_run"]),
        "verdict_command_returncode": linux_validation_final_publish_archive_report["verdict_command_returncode"],
        "verdict_command_stdout_tail": str(
            linux_validation_final_publish_archive_report["verdict_command_stdout_tail"]
        ),
        "verdict_command_stderr_tail": str(
            linux_validation_final_publish_archive_report["verdict_command_stderr_tail"]
        ),
        "verdict_error_type": str(linux_validation_final_publish_archive_report["verdict_error_type"]),
        "verdict_error_message": str(linux_validation_final_publish_archive_report["verdict_error_message"]),
        "release_run_id": linux_validation_final_publish_archive_report["release_run_id"],
        "release_run_url": str(linux_validation_final_publish_archive_report["release_run_url"]),
        "follow_up_queue_url": str(linux_validation_final_publish_archive_report["follow_up_queue_url"]),
        "linux_validation_dispatch_summary": str(
            linux_validation_final_publish_archive_report["linux_validation_dispatch_summary"]
        ),
        "linux_validation_final_publish_archive_summary": str(
            linux_validation_final_publish_archive_report["linux_validation_final_publish_archive_summary"]
        ),
        "linux_validation_terminal_verdict_status": terminal_status,
        "linux_validation_terminal_verdict_decision": terminal_decision,
        "linux_validation_terminal_verdict_exit_code": terminal_exit_code,
        "linux_validation_terminal_verdict_should_proceed": terminal_should_proceed,
        "linux_validation_terminal_verdict_requires_manual_action": terminal_requires_manual_action,
        "linux_validation_terminal_verdict_channel": terminal_channel,
        "linux_validation_terminal_verdict_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Linux Validation Terminal Verdict Report",
        "",
        (
            "- Linux Validation Terminal Verdict Status: "
            f"**{str(payload['linux_validation_terminal_verdict_status']).upper()}**"
        ),
        (
            "- Linux Validation Terminal Verdict Decision: "
            f"`{payload['linux_validation_terminal_verdict_decision']}`"
        ),
        (
            "- Linux Validation Terminal Verdict Exit Code: "
            f"`{payload['linux_validation_terminal_verdict_exit_code']}`"
        ),
        (
            "- Linux Validation Terminal Verdict Should Proceed: "
            f"`{payload['linux_validation_terminal_verdict_should_proceed']}`"
        ),
        (
            "- Linux Validation Terminal Verdict Requires Manual Action: "
            f"`{payload['linux_validation_terminal_verdict_requires_manual_action']}`"
        ),
        (
            "- Linux Validation Terminal Verdict Channel: "
            f"`{payload['linux_validation_terminal_verdict_channel']}`"
        ),
        (
            "- Linux Validation Final Publish Archive Status: "
            f"`{payload['linux_validation_final_publish_archive_status']}`"
        ),
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['linux_validation_terminal_verdict_summary']}",
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
        "workflow_linux_validation_terminal_verdict_status": str(
            payload["linux_validation_terminal_verdict_status"]
        ),
        "workflow_linux_validation_terminal_verdict_decision": str(
            payload["linux_validation_terminal_verdict_decision"]
        ),
        "workflow_linux_validation_terminal_verdict_exit_code": str(
            payload["linux_validation_terminal_verdict_exit_code"]
        ),
        "workflow_linux_validation_terminal_verdict_should_proceed": (
            "true" if payload["linux_validation_terminal_verdict_should_proceed"] else "false"
        ),
        "workflow_linux_validation_terminal_verdict_requires_manual_action": (
            "true"
            if payload["linux_validation_terminal_verdict_requires_manual_action"]
            else "false"
        ),
        "workflow_linux_validation_terminal_verdict_channel": str(
            payload["linux_validation_terminal_verdict_channel"]
        ),
        "workflow_linux_validation_terminal_verdict_follow_up_queue_url": str(
            payload["follow_up_queue_url"]
        ),
        "workflow_linux_validation_terminal_verdict_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_linux_validation_terminal_verdict_run_url": str(payload["release_run_url"]),
        "workflow_linux_validation_terminal_verdict_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_linux_validation_terminal_verdict_report_json": str(output_json),
        "workflow_linux_validation_terminal_verdict_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow Linux validation terminal verdict contract "
            "from P2-66 Linux validation final publish archive report"
        )
    )
    parser.add_argument(
        "--linux-validation-final-publish-archive-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.json",
        help="P2-66 Linux validation final publish archive report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.json",
        help="Output Linux validation terminal verdict JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.md",
        help="Output Linux validation terminal verdict markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print Linux validation terminal verdict JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    verdict_report_path = Path(args.linux_validation_final_publish_archive_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        verdict_report = load_linux_validation_final_publish_archive_report(verdict_report_path)
        payload = build_linux_validation_terminal_verdict_payload(
            verdict_report,
            source_path=verdict_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-linux-validation-terminal-verdict-gate] "
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
        print(f"linux validation terminal verdict json: {output_json_path}")
        print(f"linux validation terminal verdict markdown: {output_markdown_path}")

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
        "linux validation terminal verdict summary: "
        f"linux_validation_terminal_verdict_status="
        f"{payload['linux_validation_terminal_verdict_status']} "
        f"linux_validation_terminal_verdict_decision="
        f"{payload['linux_validation_terminal_verdict_decision']} "
        f"linux_validation_terminal_verdict_exit_code="
        f"{payload['linux_validation_terminal_verdict_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["linux_validation_terminal_verdict_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
