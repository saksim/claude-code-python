"""Phase 2 card P2-59 gate for Linux CI workflow terminal verdict closure.

This script converges one terminal Linux-validation verdict by combining:
1) P2-56 release final publish archive report,
2) P2-57 gate manifest drift report.

It emits one normalized verdict contract for Linux-stage execution readiness.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_STATUSES: set[str] = {
    "archived",
    "archived_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_DECISIONS: set[str] = {
    "archive_release_shipped",
    "archive_release_shipped_with_follow_up",
    "archive_release_blocker",
    "abort_archive",
}
ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_CHANNELS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}

ALLOWED_GATE_MANIFEST_DRIFT_STATUSES: set[str] = {"passed", "failed"}

ALLOWED_TERMINAL_VERDICT_STATUSES: set[str] = {
    "ready_for_linux_validation",
    "ready_with_follow_up_for_linux_validation",
    "blocked",
    "contract_failed",
}
ALLOWED_TERMINAL_VERDICT_DECISIONS: set[str] = {
    "proceed_linux_validation",
    "proceed_linux_validation_with_follow_up",
    "halt_linux_validation_blocker",
    "abort_linux_validation",
}
ALLOWED_TERMINAL_VERDICT_CHANNELS: set[str] = {"release", "follow_up", "blocker"}


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


def load_release_final_publish_archive_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release final publish archive report not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release final publish archive payload must be object")

    required_fields = (
        "source_release_final_verdict_publish_report",
        "source_release_final_verdict_report",
        "source_release_final_archive_report",
        "source_release_final_closure_publish_report",
        "source_release_final_closure_report",
        "source_release_final_handoff_report",
        "source_release_final_terminal_publish_report",
        "source_release_final_outcome_report",
        "source_release_delivery_final_verdict_report",
        "source_release_follow_up_final_verdict_report",
        "release_delivery_final_verdict_status",
        "release_delivery_final_verdict_decision",
        "release_delivery_final_verdict_exit_code",
        "release_follow_up_final_verdict_status",
        "release_follow_up_final_verdict_decision",
        "release_follow_up_final_verdict_exit_code",
        "release_final_outcome_status",
        "release_final_outcome_decision",
        "release_final_outcome_exit_code",
        "release_final_terminal_publish_status",
        "release_final_terminal_publish_decision",
        "release_final_terminal_publish_exit_code",
        "release_final_handoff_status",
        "release_final_handoff_decision",
        "release_final_handoff_exit_code",
        "release_final_closure_status",
        "release_final_closure_decision",
        "release_final_closure_exit_code",
        "release_final_closure_publish_status",
        "release_final_closure_publish_decision",
        "release_final_closure_publish_exit_code",
        "release_final_archive_status",
        "release_final_archive_decision",
        "release_final_archive_exit_code",
        "release_final_verdict_status",
        "release_final_verdict_decision",
        "release_final_verdict_exit_code",
        "release_final_verdict_publish_status",
        "release_final_verdict_publish_decision",
        "release_final_verdict_publish_exit_code",
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "final_publish_archive_should_archive",
        "final_publish_archive_requires_manual_action",
        "final_publish_archive_channel",
        "release_final_publish_archive_status",
        "release_final_publish_archive_decision",
        "release_final_publish_archive_exit_code",
        "release_final_publish_archive_summary",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        "evidence_manifest",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    publish_archive_status = _coerce_str(
        payload["release_final_publish_archive_status"],
        field="release_final_publish_archive_status",
        path=path,
    )
    if publish_archive_status not in ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_STATUSES:
        raise ValueError(
            f"{path}: field 'release_final_publish_archive_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_STATUSES)}"
        )

    publish_archive_decision = _coerce_str(
        payload["release_final_publish_archive_decision"],
        field="release_final_publish_archive_decision",
        path=path,
    )
    if publish_archive_decision not in ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_final_publish_archive_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_DECISIONS)}"
        )

    publish_archive_channel = _coerce_str(
        payload["final_publish_archive_channel"],
        field="final_publish_archive_channel",
        path=path,
    )
    if publish_archive_channel not in ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_CHANNELS:
        raise ValueError(
            f"{path}: field 'final_publish_archive_channel' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_PUBLISH_ARCHIVE_CHANNELS)}"
        )

    publish_archive_exit_code = _coerce_int(
        payload["release_final_publish_archive_exit_code"],
        field="release_final_publish_archive_exit_code",
        path=path,
    )
    if publish_archive_exit_code < 0:
        raise ValueError(f"{path}: field 'release_final_publish_archive_exit_code' must be >= 0")

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    return {
        "generated_at": payload.get("generated_at"),
        "source_release_final_verdict_publish_report": _coerce_str(
            payload["source_release_final_verdict_publish_report"],
            field="source_release_final_verdict_publish_report",
            path=path,
        ),
        "source_release_final_verdict_report": _coerce_str(
            payload["source_release_final_verdict_report"],
            field="source_release_final_verdict_report",
            path=path,
        ),
        "source_release_final_archive_report": _coerce_str(
            payload["source_release_final_archive_report"],
            field="source_release_final_archive_report",
            path=path,
        ),
        "source_release_final_closure_publish_report": _coerce_str(
            payload["source_release_final_closure_publish_report"],
            field="source_release_final_closure_publish_report",
            path=path,
        ),
        "source_release_final_closure_report": _coerce_str(
            payload["source_release_final_closure_report"],
            field="source_release_final_closure_report",
            path=path,
        ),
        "source_release_final_handoff_report": _coerce_str(
            payload["source_release_final_handoff_report"],
            field="source_release_final_handoff_report",
            path=path,
        ),
        "source_release_final_terminal_publish_report": _coerce_str(
            payload["source_release_final_terminal_publish_report"],
            field="source_release_final_terminal_publish_report",
            path=path,
        ),
        "source_release_final_outcome_report": _coerce_str(
            payload["source_release_final_outcome_report"],
            field="source_release_final_outcome_report",
            path=path,
        ),
        "source_release_delivery_final_verdict_report": _coerce_str(
            payload["source_release_delivery_final_verdict_report"],
            field="source_release_delivery_final_verdict_report",
            path=path,
        ),
        "source_release_follow_up_final_verdict_report": _coerce_str(
            payload["source_release_follow_up_final_verdict_report"],
            field="source_release_follow_up_final_verdict_report",
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
        "release_follow_up_final_verdict_status": _coerce_str(
            payload["release_follow_up_final_verdict_status"],
            field="release_follow_up_final_verdict_status",
            path=path,
        ),
        "release_follow_up_final_verdict_decision": _coerce_str(
            payload["release_follow_up_final_verdict_decision"],
            field="release_follow_up_final_verdict_decision",
            path=path,
        ),
        "release_follow_up_final_verdict_exit_code": _coerce_int(
            payload["release_follow_up_final_verdict_exit_code"],
            field="release_follow_up_final_verdict_exit_code",
            path=path,
        ),
        "release_final_outcome_status": _coerce_str(
            payload["release_final_outcome_status"],
            field="release_final_outcome_status",
            path=path,
        ),
        "release_final_outcome_decision": _coerce_str(
            payload["release_final_outcome_decision"],
            field="release_final_outcome_decision",
            path=path,
        ),
        "release_final_outcome_exit_code": _coerce_int(
            payload["release_final_outcome_exit_code"],
            field="release_final_outcome_exit_code",
            path=path,
        ),
        "release_final_terminal_publish_status": _coerce_str(
            payload["release_final_terminal_publish_status"],
            field="release_final_terminal_publish_status",
            path=path,
        ),
        "release_final_terminal_publish_decision": _coerce_str(
            payload["release_final_terminal_publish_decision"],
            field="release_final_terminal_publish_decision",
            path=path,
        ),
        "release_final_terminal_publish_exit_code": _coerce_int(
            payload["release_final_terminal_publish_exit_code"],
            field="release_final_terminal_publish_exit_code",
            path=path,
        ),
        "release_final_handoff_status": _coerce_str(
            payload["release_final_handoff_status"],
            field="release_final_handoff_status",
            path=path,
        ),
        "release_final_handoff_decision": _coerce_str(
            payload["release_final_handoff_decision"],
            field="release_final_handoff_decision",
            path=path,
        ),
        "release_final_handoff_exit_code": _coerce_int(
            payload["release_final_handoff_exit_code"],
            field="release_final_handoff_exit_code",
            path=path,
        ),
        "release_final_closure_status": _coerce_str(
            payload["release_final_closure_status"],
            field="release_final_closure_status",
            path=path,
        ),
        "release_final_closure_decision": _coerce_str(
            payload["release_final_closure_decision"],
            field="release_final_closure_decision",
            path=path,
        ),
        "release_final_closure_exit_code": _coerce_int(
            payload["release_final_closure_exit_code"],
            field="release_final_closure_exit_code",
            path=path,
        ),
        "release_final_closure_publish_status": _coerce_str(
            payload["release_final_closure_publish_status"],
            field="release_final_closure_publish_status",
            path=path,
        ),
        "release_final_closure_publish_decision": _coerce_str(
            payload["release_final_closure_publish_decision"],
            field="release_final_closure_publish_decision",
            path=path,
        ),
        "release_final_closure_publish_exit_code": _coerce_int(
            payload["release_final_closure_publish_exit_code"],
            field="release_final_closure_publish_exit_code",
            path=path,
        ),
        "release_final_archive_status": _coerce_str(
            payload["release_final_archive_status"],
            field="release_final_archive_status",
            path=path,
        ),
        "release_final_archive_decision": _coerce_str(
            payload["release_final_archive_decision"],
            field="release_final_archive_decision",
            path=path,
        ),
        "release_final_archive_exit_code": _coerce_int(
            payload["release_final_archive_exit_code"],
            field="release_final_archive_exit_code",
            path=path,
        ),
        "release_final_verdict_status": _coerce_str(
            payload["release_final_verdict_status"],
            field="release_final_verdict_status",
            path=path,
        ),
        "release_final_verdict_decision": _coerce_str(
            payload["release_final_verdict_decision"],
            field="release_final_verdict_decision",
            path=path,
        ),
        "release_final_verdict_exit_code": _coerce_int(
            payload["release_final_verdict_exit_code"],
            field="release_final_verdict_exit_code",
            path=path,
        ),
        "release_final_verdict_publish_status": _coerce_str(
            payload["release_final_verdict_publish_status"],
            field="release_final_verdict_publish_status",
            path=path,
        ),
        "release_final_verdict_publish_decision": _coerce_str(
            payload["release_final_verdict_publish_decision"],
            field="release_final_verdict_publish_decision",
            path=path,
        ),
        "release_final_verdict_publish_exit_code": _coerce_int(
            payload["release_final_verdict_publish_exit_code"],
            field="release_final_verdict_publish_exit_code",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(payload["release_run_url"], field="release_run_url", path=path),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "final_publish_archive_should_archive": _coerce_bool(
            payload["final_publish_archive_should_archive"],
            field="final_publish_archive_should_archive",
            path=path,
        ),
        "final_publish_archive_requires_manual_action": _coerce_bool(
            payload["final_publish_archive_requires_manual_action"],
            field="final_publish_archive_requires_manual_action",
            path=path,
        ),
        "final_publish_archive_channel": publish_archive_channel,
        "release_final_publish_archive_status": publish_archive_status,
        "release_final_publish_archive_decision": publish_archive_decision,
        "release_final_publish_archive_exit_code": publish_archive_exit_code,
        "release_final_publish_archive_summary": _coerce_str(
            payload["release_final_publish_archive_summary"],
            field="release_final_publish_archive_summary",
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


def load_gate_manifest_drift_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: gate manifest drift report not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: gate manifest drift payload must be object")

    required_fields = (
        "status",
        "missing_runtime_tests",
        "missing_manifest_entries",
        "orphan_manifest_entries",
        "structural_issues",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    status = _coerce_str(payload["status"], field="status", path=path)
    if status not in ALLOWED_GATE_MANIFEST_DRIFT_STATUSES:
        raise ValueError(
            f"{path}: field 'status' must be one of "
            f"{sorted(ALLOWED_GATE_MANIFEST_DRIFT_STATUSES)}"
        )

    return {
        "status": status,
        "missing_runtime_tests": _coerce_str_list(
            payload["missing_runtime_tests"],
            field="missing_runtime_tests",
            path=path,
        ),
        "missing_manifest_entries": _coerce_str_list(
            payload["missing_manifest_entries"],
            field="missing_manifest_entries",
            path=path,
        ),
        "orphan_manifest_entries": _coerce_str_list(
            payload["orphan_manifest_entries"],
            field="orphan_manifest_entries",
            path=path,
        ),
        "structural_issues": _coerce_str_list(
            payload["structural_issues"],
            field="structural_issues",
            path=path,
        ),
    }


def build_terminal_verdict_payload(
    release_final_publish_archive_report: dict[str, Any],
    gate_manifest_drift_report: dict[str, Any],
    *,
    release_source_path: Path,
    drift_source_path: Path,
) -> dict[str, Any]:
    publish_archive_status = str(
        release_final_publish_archive_report["release_final_publish_archive_status"]
    )
    publish_archive_decision = str(
        release_final_publish_archive_report["release_final_publish_archive_decision"]
    )
    publish_archive_exit_code = int(
        release_final_publish_archive_report["release_final_publish_archive_exit_code"]
    )
    publish_archive_should_archive = bool(
        release_final_publish_archive_report["final_publish_archive_should_archive"]
    )
    publish_archive_requires_manual_action = bool(
        release_final_publish_archive_report["final_publish_archive_requires_manual_action"]
    )
    publish_archive_channel = str(
        release_final_publish_archive_report["final_publish_archive_channel"]
    )

    drift_status = str(gate_manifest_drift_report["status"])
    drift_missing_runtime_tests = list(gate_manifest_drift_report["missing_runtime_tests"])
    drift_missing_manifest_entries = list(gate_manifest_drift_report["missing_manifest_entries"])
    drift_orphan_manifest_entries = list(gate_manifest_drift_report["orphan_manifest_entries"])
    drift_structural_issues = list(gate_manifest_drift_report["structural_issues"])

    reason_codes = list(release_final_publish_archive_report["reason_codes"])
    structural_issues = list(release_final_publish_archive_report["structural_issues"])
    missing_artifacts = list(release_final_publish_archive_report["missing_artifacts"])
    evidence_manifest = list(release_final_publish_archive_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("terminal_verdict_evidence_missing")

    expected_publish_archive = {
        "archived": ("archive_release_shipped", True, False, "release", 0),
        "archived_with_follow_up": (
            "archive_release_shipped_with_follow_up",
            True,
            False,
            "follow_up",
            None,
        ),
        "blocked": ("archive_release_blocker", False, True, "blocker", None),
        "contract_failed": ("abort_archive", False, True, "blocker", None),
    }
    (
        expected_decision,
        expected_should_archive,
        expected_requires_manual_action,
        expected_channel,
        expected_exit_code,
    ) = expected_publish_archive[publish_archive_status]

    if publish_archive_decision != expected_decision:
        structural_issues.append("final_publish_archive_decision_mismatch")
    if publish_archive_should_archive != expected_should_archive:
        structural_issues.append("final_publish_archive_should_archive_mismatch")
    if publish_archive_requires_manual_action != expected_requires_manual_action:
        structural_issues.append("final_publish_archive_requires_manual_action_mismatch")
    if publish_archive_channel != expected_channel:
        structural_issues.append("final_publish_archive_channel_mismatch")
    if expected_exit_code == 0 and publish_archive_exit_code != 0:
        structural_issues.append("final_publish_archive_exit_code_mismatch_archived")
    if expected_exit_code is None and publish_archive_exit_code == 0:
        structural_issues.append("final_publish_archive_exit_code_mismatch_non_archived")

    if drift_status == "failed":
        structural_issues.append("gate_manifest_drift_failed")
        reason_codes.append("terminal_verdict_gate_manifest_drift_failed")
    if drift_missing_runtime_tests:
        structural_issues.append("gate_manifest_drift_missing_runtime_tests")
    if drift_missing_manifest_entries:
        structural_issues.append("gate_manifest_drift_missing_manifest_entries")
    if drift_orphan_manifest_entries:
        structural_issues.append("gate_manifest_drift_orphan_manifest_entries")
    if drift_structural_issues:
        structural_issues.extend(drift_structural_issues)

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    drift_missing_total = (
        len(drift_missing_runtime_tests)
        + len(drift_missing_manifest_entries)
        + len(drift_orphan_manifest_entries)
    )

    if structural_issues or missing_artifacts or drift_missing_total > 0:
        terminal_status = "contract_failed"
        terminal_decision = "abort_linux_validation"
        terminal_exit_code = max(1, publish_archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif publish_archive_status == "archived":
        terminal_status = "ready_for_linux_validation"
        terminal_decision = "proceed_linux_validation"
        terminal_exit_code = 0
        terminal_should_proceed = True
        terminal_requires_manual_action = False
        terminal_channel = "release"
        reason_codes = ["terminal_verdict_ready_for_linux_validation"]
    elif publish_archive_status == "archived_with_follow_up":
        terminal_status = "ready_with_follow_up_for_linux_validation"
        terminal_decision = "proceed_linux_validation_with_follow_up"
        terminal_exit_code = max(1, publish_archive_exit_code)
        terminal_should_proceed = True
        terminal_requires_manual_action = False
        terminal_channel = "follow_up"
        reason_codes.append("terminal_verdict_ready_with_follow_up_for_linux_validation")
    elif publish_archive_status == "blocked":
        terminal_status = "blocked"
        terminal_decision = "halt_linux_validation_blocker"
        terminal_exit_code = max(1, publish_archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.append("terminal_verdict_blocked")
    else:
        terminal_status = "contract_failed"
        terminal_decision = "abort_linux_validation"
        terminal_exit_code = max(1, publish_archive_exit_code)
        terminal_should_proceed = False
        terminal_requires_manual_action = True
        terminal_channel = "blocker"
        reason_codes.append("terminal_verdict_upstream_contract_failed")

    if terminal_status not in ALLOWED_TERMINAL_VERDICT_STATUSES:
        raise ValueError("internal: unsupported terminal_verdict_status computed")
    if terminal_decision not in ALLOWED_TERMINAL_VERDICT_DECISIONS:
        raise ValueError("internal: unsupported terminal_verdict_decision computed")
    if terminal_channel not in ALLOWED_TERMINAL_VERDICT_CHANNELS:
        raise ValueError("internal: unsupported terminal_verdict_channel computed")

    reason_codes = _unique(reason_codes)
    summary = (
        f"release_final_publish_archive_status={publish_archive_status} "
        f"gate_manifest_drift_status={drift_status} "
        f"terminal_verdict_status={terminal_status} "
        f"terminal_verdict_decision={terminal_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_final_publish_archive_report": str(release_source_path),
        "source_gate_manifest_drift_report": str(drift_source_path),
        "source_release_final_verdict_publish_report": str(
            release_final_publish_archive_report["source_release_final_verdict_publish_report"]
        ),
        "source_release_final_verdict_report": str(
            release_final_publish_archive_report["source_release_final_verdict_report"]
        ),
        "source_release_final_archive_report": str(
            release_final_publish_archive_report["source_release_final_archive_report"]
        ),
        "source_release_final_closure_publish_report": str(
            release_final_publish_archive_report["source_release_final_closure_publish_report"]
        ),
        "source_release_final_closure_report": str(
            release_final_publish_archive_report["source_release_final_closure_report"]
        ),
        "source_release_final_handoff_report": str(
            release_final_publish_archive_report["source_release_final_handoff_report"]
        ),
        "source_release_final_terminal_publish_report": str(
            release_final_publish_archive_report["source_release_final_terminal_publish_report"]
        ),
        "source_release_final_outcome_report": str(
            release_final_publish_archive_report["source_release_final_outcome_report"]
        ),
        "source_release_delivery_final_verdict_report": str(
            release_final_publish_archive_report["source_release_delivery_final_verdict_report"]
        ),
        "source_release_follow_up_final_verdict_report": str(
            release_final_publish_archive_report["source_release_follow_up_final_verdict_report"]
        ),
        "release_delivery_final_verdict_status": str(
            release_final_publish_archive_report["release_delivery_final_verdict_status"]
        ),
        "release_delivery_final_verdict_decision": str(
            release_final_publish_archive_report["release_delivery_final_verdict_decision"]
        ),
        "release_delivery_final_verdict_exit_code": int(
            release_final_publish_archive_report["release_delivery_final_verdict_exit_code"]
        ),
        "release_follow_up_final_verdict_status": str(
            release_final_publish_archive_report["release_follow_up_final_verdict_status"]
        ),
        "release_follow_up_final_verdict_decision": str(
            release_final_publish_archive_report["release_follow_up_final_verdict_decision"]
        ),
        "release_follow_up_final_verdict_exit_code": int(
            release_final_publish_archive_report["release_follow_up_final_verdict_exit_code"]
        ),
        "release_final_outcome_status": str(
            release_final_publish_archive_report["release_final_outcome_status"]
        ),
        "release_final_outcome_decision": str(
            release_final_publish_archive_report["release_final_outcome_decision"]
        ),
        "release_final_outcome_exit_code": int(
            release_final_publish_archive_report["release_final_outcome_exit_code"]
        ),
        "release_final_terminal_publish_status": str(
            release_final_publish_archive_report["release_final_terminal_publish_status"]
        ),
        "release_final_terminal_publish_decision": str(
            release_final_publish_archive_report["release_final_terminal_publish_decision"]
        ),
        "release_final_terminal_publish_exit_code": int(
            release_final_publish_archive_report["release_final_terminal_publish_exit_code"]
        ),
        "release_final_handoff_status": str(
            release_final_publish_archive_report["release_final_handoff_status"]
        ),
        "release_final_handoff_decision": str(
            release_final_publish_archive_report["release_final_handoff_decision"]
        ),
        "release_final_handoff_exit_code": int(
            release_final_publish_archive_report["release_final_handoff_exit_code"]
        ),
        "release_final_closure_status": str(
            release_final_publish_archive_report["release_final_closure_status"]
        ),
        "release_final_closure_decision": str(
            release_final_publish_archive_report["release_final_closure_decision"]
        ),
        "release_final_closure_exit_code": int(
            release_final_publish_archive_report["release_final_closure_exit_code"]
        ),
        "release_final_closure_publish_status": str(
            release_final_publish_archive_report["release_final_closure_publish_status"]
        ),
        "release_final_closure_publish_decision": str(
            release_final_publish_archive_report["release_final_closure_publish_decision"]
        ),
        "release_final_closure_publish_exit_code": int(
            release_final_publish_archive_report["release_final_closure_publish_exit_code"]
        ),
        "release_final_archive_status": str(
            release_final_publish_archive_report["release_final_archive_status"]
        ),
        "release_final_archive_decision": str(
            release_final_publish_archive_report["release_final_archive_decision"]
        ),
        "release_final_archive_exit_code": int(
            release_final_publish_archive_report["release_final_archive_exit_code"]
        ),
        "release_final_verdict_status": str(
            release_final_publish_archive_report["release_final_verdict_status"]
        ),
        "release_final_verdict_decision": str(
            release_final_publish_archive_report["release_final_verdict_decision"]
        ),
        "release_final_verdict_exit_code": int(
            release_final_publish_archive_report["release_final_verdict_exit_code"]
        ),
        "release_final_verdict_publish_status": str(
            release_final_publish_archive_report["release_final_verdict_publish_status"]
        ),
        "release_final_verdict_publish_decision": str(
            release_final_publish_archive_report["release_final_verdict_publish_decision"]
        ),
        "release_final_verdict_publish_exit_code": int(
            release_final_publish_archive_report["release_final_verdict_publish_exit_code"]
        ),
        "release_final_publish_archive_status": publish_archive_status,
        "release_final_publish_archive_decision": publish_archive_decision,
        "release_final_publish_archive_exit_code": publish_archive_exit_code,
        "release_run_id": release_final_publish_archive_report["release_run_id"],
        "release_run_url": str(release_final_publish_archive_report["release_run_url"]),
        "follow_up_queue_url": str(release_final_publish_archive_report["follow_up_queue_url"]),
        "gate_manifest_drift_status": drift_status,
        "gate_manifest_drift_missing_runtime_tests": drift_missing_runtime_tests,
        "gate_manifest_drift_missing_manifest_entries": drift_missing_manifest_entries,
        "gate_manifest_drift_orphan_manifest_entries": drift_orphan_manifest_entries,
        "terminal_verdict_should_proceed": terminal_should_proceed,
        "terminal_verdict_requires_manual_action": terminal_requires_manual_action,
        "terminal_verdict_channel": terminal_channel,
        "terminal_verdict_status": terminal_status,
        "terminal_verdict_decision": terminal_decision,
        "terminal_verdict_exit_code": terminal_exit_code,
        "terminal_verdict_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Terminal Verdict Report",
        "",
        f"- Terminal Verdict Status: **{str(payload['terminal_verdict_status']).upper()}**",
        f"- Terminal Verdict Decision: `{payload['terminal_verdict_decision']}`",
        f"- Terminal Verdict Exit Code: `{payload['terminal_verdict_exit_code']}`",
        f"- Terminal Verdict Should Proceed: `{payload['terminal_verdict_should_proceed']}`",
        (
            "- Terminal Verdict Requires Manual Action: "
            f"`{payload['terminal_verdict_requires_manual_action']}`"
        ),
        f"- Terminal Verdict Channel: `{payload['terminal_verdict_channel']}`",
        (
            "- Release Final Publish Archive Status: "
            f"`{payload['release_final_publish_archive_status']}`"
        ),
        f"- Gate Manifest Drift Status: `{payload['gate_manifest_drift_status']}`",
        (
            "- Drift Missing Runtime Tests: "
            f"`{len(payload['gate_manifest_drift_missing_runtime_tests'])}`"
        ),
        (
            "- Drift Missing Manifest Entries: "
            f"`{len(payload['gate_manifest_drift_missing_manifest_entries'])}`"
        ),
        (
            "- Drift Orphan Manifest Entries: "
            f"`{len(payload['gate_manifest_drift_orphan_manifest_entries'])}`"
        ),
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['terminal_verdict_summary']}",
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

    lines.extend(["", "## Gate Manifest Drift Details"])
    drift_runtime = payload["gate_manifest_drift_missing_runtime_tests"]
    if drift_runtime:
        lines.extend(f"- missing runtime test: `{item}`" for item in drift_runtime)
    else:
        lines.append("- missing runtime test: none")

    drift_manifest = payload["gate_manifest_drift_missing_manifest_entries"]
    if drift_manifest:
        lines.extend(f"- missing manifest entry: `{item}`" for item in drift_manifest)
    else:
        lines.append("- missing manifest entry: none")

    drift_orphan = payload["gate_manifest_drift_orphan_manifest_entries"]
    if drift_orphan:
        lines.extend(f"- orphan manifest entry: `{item}`" for item in drift_orphan)
    else:
        lines.append("- orphan manifest entry: none")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    return {
        "workflow_terminal_verdict_status": str(payload["terminal_verdict_status"]),
        "workflow_terminal_verdict_decision": str(payload["terminal_verdict_decision"]),
        "workflow_terminal_verdict_exit_code": str(payload["terminal_verdict_exit_code"]),
        "workflow_terminal_verdict_should_proceed": (
            "true" if payload["terminal_verdict_should_proceed"] else "false"
        ),
        "workflow_terminal_verdict_requires_manual_action": (
            "true" if payload["terminal_verdict_requires_manual_action"] else "false"
        ),
        "workflow_terminal_verdict_channel": str(payload["terminal_verdict_channel"]),
        "workflow_terminal_verdict_gate_manifest_drift_status": str(
            payload["gate_manifest_drift_status"]
        ),
        "workflow_terminal_verdict_gate_manifest_drift_missing_runtime_tests": str(
            len(payload["gate_manifest_drift_missing_runtime_tests"])
        ),
        "workflow_terminal_verdict_gate_manifest_drift_missing_manifest_entries": str(
            len(payload["gate_manifest_drift_missing_manifest_entries"])
        ),
        "workflow_terminal_verdict_gate_manifest_drift_orphan_manifest_entries": str(
            len(payload["gate_manifest_drift_orphan_manifest_entries"])
        ),
        "workflow_terminal_verdict_release_final_publish_archive_status": str(
            payload["release_final_publish_archive_status"]
        ),
        "workflow_terminal_verdict_follow_up_queue_url": str(payload["follow_up_queue_url"]),
        "workflow_terminal_verdict_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_terminal_verdict_run_url": str(payload["release_run_url"]),
        "workflow_terminal_verdict_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_terminal_verdict_report_json": str(output_json),
        "workflow_terminal_verdict_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow terminal verdict contract "
            "from P2-56 release final publish archive and P2-57 gate manifest drift"
        )
    )
    parser.add_argument(
        "--release-final-publish-archive-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json",
        help="P2-56 release final publish archive report JSON path",
    )
    parser.add_argument(
        "--gate-manifest-drift-report",
        default=".claude/reports/linux_unified_gate/linux_gate_manifest_drift.json",
        help="P2-57 gate manifest drift report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json",
        help="Output terminal verdict JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.md",
        help="Output terminal verdict markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print terminal verdict JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    release_report_path = Path(args.release_final_publish_archive_report)
    drift_report_path = Path(args.gate_manifest_drift_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        release_report = load_release_final_publish_archive_report(release_report_path)
        drift_report = load_gate_manifest_drift_report(drift_report_path)
        payload = build_terminal_verdict_payload(
            release_report,
            drift_report,
            release_source_path=release_report_path.resolve(),
            drift_source_path=drift_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-terminal-verdict-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"terminal verdict json: {output_json_path}")
        print(f"terminal verdict markdown: {output_markdown_path}")

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
        "terminal verdict summary: "
        f"terminal_verdict_status={payload['terminal_verdict_status']} "
        f"terminal_verdict_decision={payload['terminal_verdict_decision']} "
        f"terminal_verdict_exit_code={payload['terminal_verdict_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["terminal_verdict_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
