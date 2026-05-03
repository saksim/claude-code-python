"""Phase 2 card P2-44 gate for Linux CI workflow release follow-up dispatch.

This script consumes the P2-43 release delivery final verdict artifact and
converges the follow-up dispatch contract:
1) validate final verdict + evidence consistency,
2) normalize close/follow-up/escalate follow-up dispatch semantics,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES: set[str] = {
    "completed",
    "requires_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS: set[str] = {
    "close_release",
    "open_follow_up",
    "escalate_blocker",
    "abort_close",
}
ALLOWED_RELEASE_DELIVERY_FINAL_ANNOUNCEMENT_TARGETS: set[str] = {
    "release",
    "hold",
    "blocker",
}
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


def load_release_delivery_final_verdict_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release delivery final verdict report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release delivery final verdict payload must be object")

    required_fields = (
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

    final_status = _coerce_str(
        payload["release_delivery_final_verdict_status"],
        field="release_delivery_final_verdict_status",
        path=path,
    )
    if final_status not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES)}"
        )

    final_decision = _coerce_str(
        payload["release_delivery_final_verdict_decision"],
        field="release_delivery_final_verdict_decision",
        path=path,
    )
    if final_decision not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS)}"
        )

    final_exit_code = _coerce_int(
        payload["release_delivery_final_verdict_exit_code"],
        field="release_delivery_final_verdict_exit_code",
        path=path,
    )
    if final_exit_code < 0:
        raise ValueError(f"{path}: field 'release_delivery_final_verdict_exit_code' must be >= 0")

    announcement_target = _coerce_str(
        payload["final_announcement_target"],
        field="final_announcement_target",
        path=path,
    )
    if announcement_target not in ALLOWED_RELEASE_DELIVERY_FINAL_ANNOUNCEMENT_TARGETS:
        raise ValueError(
            f"{path}: field 'final_announcement_target' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_ANNOUNCEMENT_TARGETS)}"
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
        "incident_url": _coerce_str(
            payload["incident_url"],
            field="incident_url",
            path=path,
        ),
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
        "release_delivery_final_verdict_status": final_status,
        "release_delivery_final_verdict_decision": final_decision,
        "release_delivery_final_verdict_exit_code": final_exit_code,
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
        "final_announcement_target": announcement_target,
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


def build_release_follow_up_dispatch_payload(
    final_verdict_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    final_status = str(final_verdict_report["release_delivery_final_verdict_status"])
    final_decision = str(final_verdict_report["release_delivery_final_verdict_decision"])
    final_exit_code = int(final_verdict_report["release_delivery_final_verdict_exit_code"])
    final_should_close_release = bool(final_verdict_report["final_should_close_release"])
    final_should_open_follow_up = bool(final_verdict_report["final_should_open_follow_up"])
    final_should_page_owner = bool(final_verdict_report["final_should_page_owner"])
    final_announcement_target = str(final_verdict_report["final_announcement_target"])

    terminal_publish_status = str(final_verdict_report["release_delivery_terminal_publish_status"])
    incident_dispatch_status = str(final_verdict_report["incident_dispatch_status"])

    reason_codes = list(final_verdict_report["reason_codes"])
    structural_issues = list(final_verdict_report["structural_issues"])
    missing_artifacts = list(final_verdict_report["missing_artifacts"])
    evidence_manifest = list(final_verdict_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_follow_up_dispatch_evidence_missing")

    if final_status == "completed":
        if final_decision != "close_release":
            structural_issues.append("final_decision_mismatch_completed")
        if final_exit_code != 0:
            structural_issues.append("final_exit_code_mismatch_completed")
        if not final_should_close_release:
            structural_issues.append("final_should_close_release_mismatch_completed")
        if final_should_open_follow_up:
            structural_issues.append("final_should_open_follow_up_mismatch_completed")
        if final_should_page_owner:
            structural_issues.append("final_should_page_owner_mismatch_completed")
        if final_announcement_target != "release":
            structural_issues.append("final_announcement_target_mismatch_completed")
    elif final_status == "requires_follow_up":
        if final_decision != "open_follow_up":
            structural_issues.append("final_decision_mismatch_requires_follow_up")
        if final_exit_code == 0:
            structural_issues.append("final_exit_code_mismatch_requires_follow_up")
        if final_should_close_release:
            structural_issues.append("final_should_close_release_mismatch_requires_follow_up")
        if not final_should_open_follow_up:
            structural_issues.append("final_should_open_follow_up_mismatch_requires_follow_up")
        if final_should_page_owner:
            structural_issues.append("final_should_page_owner_mismatch_requires_follow_up")
        if final_announcement_target != "hold":
            structural_issues.append("final_announcement_target_mismatch_requires_follow_up")
    elif final_status == "blocked":
        if final_decision != "escalate_blocker":
            structural_issues.append("final_decision_mismatch_blocked")
        if final_exit_code == 0:
            structural_issues.append("final_exit_code_mismatch_blocked")
        if final_should_close_release:
            structural_issues.append("final_should_close_release_mismatch_blocked")
        if not final_should_open_follow_up:
            structural_issues.append("final_should_open_follow_up_mismatch_blocked")
        if not final_should_page_owner:
            structural_issues.append("final_should_page_owner_mismatch_blocked")
        if final_announcement_target != "blocker":
            structural_issues.append("final_announcement_target_mismatch_blocked")
        if incident_dispatch_status == "not_required":
            structural_issues.append("incident_dispatch_status_mismatch_blocked")
    elif final_status == "contract_failed":
        if final_decision != "abort_close":
            structural_issues.append("final_decision_mismatch_contract_failed")
        if final_exit_code == 0:
            structural_issues.append("final_exit_code_mismatch_contract_failed")
        if final_should_close_release:
            structural_issues.append("final_should_close_release_mismatch_contract_failed")
        if not final_should_open_follow_up:
            structural_issues.append("final_should_open_follow_up_mismatch_contract_failed")
        if not final_should_page_owner:
            structural_issues.append("final_should_page_owner_mismatch_contract_failed")
        if final_announcement_target != "blocker":
            structural_issues.append("final_announcement_target_mismatch_contract_failed")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        dispatch_status = "contract_failed"
        dispatch_decision = "abort_dispatch"
        dispatch_exit_code = 1
        follow_up_required = True
        escalation_required = True
        dispatch_target = "incident_commander"
        reason_codes.extend(structural_issues)
    elif final_status == "completed":
        dispatch_status = "closed"
        dispatch_decision = "no_action"
        dispatch_exit_code = 0
        follow_up_required = False
        escalation_required = False
        dispatch_target = "none"
        reason_codes = ["release_follow_up_dispatch_closed"]
    elif final_status == "requires_follow_up":
        dispatch_status = "follow_up_required"
        dispatch_decision = "dispatch_follow_up"
        dispatch_exit_code = max(1, final_exit_code)
        follow_up_required = True
        escalation_required = False
        dispatch_target = "follow_up_queue"
        reason_codes.append("release_follow_up_dispatch_required")
    else:
        dispatch_status = "escalated"
        dispatch_decision = "dispatch_escalation"
        dispatch_exit_code = max(1, final_exit_code)
        follow_up_required = True
        escalation_required = True
        dispatch_target = "incident_commander"
        reason_codes.append("release_follow_up_dispatch_escalated")

    if dispatch_status not in ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_STATUSES:
        raise ValueError("internal: unsupported release_follow_up_dispatch_status computed")
    if dispatch_decision not in ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_DECISIONS:
        raise ValueError("internal: unsupported release_follow_up_dispatch_decision computed")
    if dispatch_target not in ALLOWED_RELEASE_FOLLOW_UP_DISPATCH_TARGETS:
        raise ValueError("internal: unsupported release_follow_up_dispatch_target computed")

    reason_codes = _unique(reason_codes)
    release_follow_up_dispatch_summary = (
        f"release_delivery_final_verdict_status={final_status} "
        f"release_follow_up_dispatch_status={dispatch_status} "
        f"release_follow_up_dispatch_decision={dispatch_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_delivery_final_verdict_report": str(source_path),
        "source_release_delivery_terminal_publish_report": str(
            final_verdict_report["source_release_delivery_terminal_publish_report"]
        ),
        "source_release_delivery_report": str(final_verdict_report["source_release_delivery_report"]),
        "source_release_terminal_verdict_report": str(
            final_verdict_report["source_release_terminal_verdict_report"]
        ),
        "source_release_incident_report": str(final_verdict_report["source_release_incident_report"]),
        "source_release_verdict_report": str(final_verdict_report["source_release_verdict_report"]),
        "source_release_archive_report": str(final_verdict_report["source_release_archive_report"]),
        "release_archive_status": str(final_verdict_report["release_archive_status"]),
        "release_archive_decision": str(final_verdict_report["release_archive_decision"]),
        "release_archive_exit_code": int(final_verdict_report["release_archive_exit_code"]),
        "should_publish_archive": bool(final_verdict_report["should_publish_archive"]),
        "release_verdict_status": str(final_verdict_report["release_verdict_status"]),
        "release_verdict_decision": str(final_verdict_report["release_verdict_decision"]),
        "release_verdict_exit_code": int(final_verdict_report["release_verdict_exit_code"]),
        "should_ship_release": bool(final_verdict_report["should_ship_release"]),
        "should_open_incident": bool(final_verdict_report["should_open_incident"]),
        "should_dispatch_incident": bool(final_verdict_report["should_dispatch_incident"]),
        "incident_dispatch_status": incident_dispatch_status,
        "incident_dispatch_exit_code": int(final_verdict_report["incident_dispatch_exit_code"]),
        "incident_dispatch_attempted": bool(final_verdict_report["incident_dispatch_attempted"]),
        "incident_url": str(final_verdict_report["incident_url"]),
        "release_terminal_verdict_status": str(final_verdict_report["release_terminal_verdict_status"]),
        "release_terminal_verdict_decision": str(
            final_verdict_report["release_terminal_verdict_decision"]
        ),
        "release_terminal_verdict_exit_code": int(
            final_verdict_report["release_terminal_verdict_exit_code"]
        ),
        "terminal_should_ship_release": bool(final_verdict_report["terminal_should_ship_release"]),
        "terminal_requires_follow_up": bool(final_verdict_report["terminal_requires_follow_up"]),
        "terminal_incident_linked": bool(final_verdict_report["terminal_incident_linked"]),
        "release_delivery_status": str(final_verdict_report["release_delivery_status"]),
        "release_delivery_decision": str(final_verdict_report["release_delivery_decision"]),
        "release_delivery_exit_code": int(final_verdict_report["release_delivery_exit_code"]),
        "delivery_should_ship_release": bool(final_verdict_report["delivery_should_ship_release"]),
        "delivery_requires_human_action": bool(
            final_verdict_report["delivery_requires_human_action"]
        ),
        "delivery_should_announce_blocker": bool(
            final_verdict_report["delivery_should_announce_blocker"]
        ),
        "release_delivery_terminal_publish_status": terminal_publish_status,
        "release_delivery_terminal_publish_decision": str(
            final_verdict_report["release_delivery_terminal_publish_decision"]
        ),
        "release_delivery_terminal_publish_exit_code": int(
            final_verdict_report["release_delivery_terminal_publish_exit_code"]
        ),
        "terminal_publish_should_notify": bool(final_verdict_report["terminal_publish_should_notify"]),
        "terminal_publish_should_create_follow_up": bool(
            final_verdict_report["terminal_publish_should_create_follow_up"]
        ),
        "terminal_publish_channel": str(final_verdict_report["terminal_publish_channel"]),
        "release_delivery_final_verdict_status": final_status,
        "release_delivery_final_verdict_decision": final_decision,
        "release_delivery_final_verdict_exit_code": final_exit_code,
        "final_should_close_release": final_should_close_release,
        "final_should_open_follow_up": final_should_open_follow_up,
        "final_should_page_owner": final_should_page_owner,
        "final_announcement_target": final_announcement_target,
        "release_follow_up_dispatch_status": dispatch_status,
        "release_follow_up_dispatch_decision": dispatch_decision,
        "release_follow_up_dispatch_exit_code": dispatch_exit_code,
        "follow_up_required": follow_up_required,
        "escalation_required": escalation_required,
        "dispatch_target": dispatch_target,
        "release_run_id": final_verdict_report["release_run_id"],
        "release_run_url": str(final_verdict_report["release_run_url"]),
        "release_follow_up_dispatch_summary": release_follow_up_dispatch_summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Follow-Up Dispatch Report",
        "",
        (
            "- Release Follow-Up Dispatch Status: "
            f"**{str(payload['release_follow_up_dispatch_status']).upper()}**"
        ),
        (
            "- Release Follow-Up Dispatch Decision: "
            f"`{payload['release_follow_up_dispatch_decision']}`"
        ),
        (
            "- Release Follow-Up Dispatch Exit Code: "
            f"`{payload['release_follow_up_dispatch_exit_code']}`"
        ),
        f"- Follow Up Required: `{payload['follow_up_required']}`",
        f"- Escalation Required: `{payload['escalation_required']}`",
        f"- Dispatch Target: `{payload['dispatch_target']}`",
        (
            "- Release Delivery Final Verdict Status: "
            f"`{payload['release_delivery_final_verdict_status']}`"
        ),
        (
            "- Release Delivery Terminal Publish Status: "
            f"`{payload['release_delivery_terminal_publish_status']}`"
        ),
        f"- Incident Dispatch Status: `{payload['incident_dispatch_status']}`",
        f"- Incident URL: `{payload['incident_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_follow_up_dispatch_summary']}",
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
        "workflow_release_follow_up_dispatch_status": str(
            payload["release_follow_up_dispatch_status"]
        ),
        "workflow_release_follow_up_dispatch_decision": str(
            payload["release_follow_up_dispatch_decision"]
        ),
        "workflow_release_follow_up_dispatch_exit_code": str(
            payload["release_follow_up_dispatch_exit_code"]
        ),
        "workflow_release_follow_up_dispatch_follow_up_required": (
            "true" if payload["follow_up_required"] else "false"
        ),
        "workflow_release_follow_up_dispatch_escalation_required": (
            "true" if payload["escalation_required"] else "false"
        ),
        "workflow_release_follow_up_dispatch_target": str(payload["dispatch_target"]),
        "workflow_release_follow_up_dispatch_final_status": str(
            payload["release_delivery_final_verdict_status"]
        ),
        "workflow_release_follow_up_dispatch_incident_status": str(
            payload["incident_dispatch_status"]
        ),
        "workflow_release_follow_up_dispatch_incident_url": str(payload["incident_url"]),
        "workflow_release_follow_up_dispatch_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_follow_up_dispatch_run_url": str(payload["release_run_url"]),
        "workflow_release_follow_up_dispatch_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_follow_up_dispatch_report_json": str(output_json),
        "workflow_release_follow_up_dispatch_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release follow-up dispatch contract "
            "from P2-43 release delivery final verdict report"
        )
    )
    parser.add_argument(
        "--release-delivery-final-verdict-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json",
        help="P2-43 release delivery final verdict report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json",
        help="Output release follow-up dispatch JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.md",
        help="Output release follow-up dispatch markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release follow-up dispatch JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    final_verdict_report_path = Path(args.release_delivery_final_verdict_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        final_verdict_report = load_release_delivery_final_verdict_report(
            final_verdict_report_path
        )
        payload = build_release_follow_up_dispatch_payload(
            final_verdict_report,
            source_path=final_verdict_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            f"[p2-linux-ci-workflow-release-follow-up-dispatch-gate] {exc}",
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
        print(f"release follow-up dispatch json: {output_json_path}")
        print(f"release follow-up dispatch markdown: {output_markdown_path}")

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
        "release follow-up dispatch summary: "
        f"release_follow_up_dispatch_status={payload['release_follow_up_dispatch_status']} "
        f"release_follow_up_dispatch_decision={payload['release_follow_up_dispatch_decision']} "
        f"release_follow_up_dispatch_exit_code={payload['release_follow_up_dispatch_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_follow_up_dispatch_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
