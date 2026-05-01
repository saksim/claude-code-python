"""Phase 2 card P2-43 gate for Linux CI workflow release delivery final verdict.

This script consumes the P2-42 release delivery terminal publish artifact and
converges the final delivery verdict contract:
1) validate delivery terminal publish + incident consistency,
2) normalize close/follow-up/escalate/abort final semantics,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_STATUSES: set[str] = {
    "published",
    "pending_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_DECISIONS: set[str] = {
    "announce_release",
    "announce_hold",
    "announce_blocker",
    "abort_publish",
}
ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_CHANNELS: set[str] = {
    "release",
    "hold",
    "blocker",
}
ALLOWED_RELEASE_DELIVERY_STATUSES: set[str] = {
    "shipped",
    "pending_follow_up",
    "blocked_incident",
    "blocked_incident_failed",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_DELIVERY_DECISIONS: set[str] = {"deliver", "hold", "escalate", "block"}
ALLOWED_INCIDENT_DISPATCH_STATUSES: set[str] = {
    "not_required",
    "ready_dry_run",
    "dispatched",
    "dispatch_failed",
    "contract_failed",
}
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


def load_release_delivery_terminal_publish_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release delivery terminal publish report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release delivery terminal publish payload must be object")

    required_fields = (
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

    terminal_publish_status = _coerce_str(
        payload["release_delivery_terminal_publish_status"],
        field="release_delivery_terminal_publish_status",
        path=path,
    )
    if terminal_publish_status not in ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_STATUSES:
        raise ValueError(
            f"{path}: field 'release_delivery_terminal_publish_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_STATUSES)}"
        )

    terminal_publish_decision = _coerce_str(
        payload["release_delivery_terminal_publish_decision"],
        field="release_delivery_terminal_publish_decision",
        path=path,
    )
    if terminal_publish_decision not in ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_delivery_terminal_publish_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_DECISIONS)}"
        )

    terminal_publish_exit_code = _coerce_int(
        payload["release_delivery_terminal_publish_exit_code"],
        field="release_delivery_terminal_publish_exit_code",
        path=path,
    )
    if terminal_publish_exit_code < 0:
        raise ValueError(
            f"{path}: field 'release_delivery_terminal_publish_exit_code' must be >= 0"
        )

    terminal_publish_channel = _coerce_str(
        payload["terminal_publish_channel"],
        field="terminal_publish_channel",
        path=path,
    )
    if terminal_publish_channel not in ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_CHANNELS:
        raise ValueError(
            f"{path}: field 'terminal_publish_channel' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_TERMINAL_PUBLISH_CHANNELS)}"
        )

    release_delivery_status = _coerce_str(
        payload["release_delivery_status"],
        field="release_delivery_status",
        path=path,
    )
    if release_delivery_status not in ALLOWED_RELEASE_DELIVERY_STATUSES:
        raise ValueError(
            f"{path}: field 'release_delivery_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_STATUSES)}"
        )

    release_delivery_decision = _coerce_str(
        payload["release_delivery_decision"],
        field="release_delivery_decision",
        path=path,
    )
    if release_delivery_decision not in ALLOWED_RELEASE_DELIVERY_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_delivery_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_DECISIONS)}"
        )

    release_delivery_exit_code = _coerce_int(
        payload["release_delivery_exit_code"],
        field="release_delivery_exit_code",
        path=path,
    )
    if release_delivery_exit_code < 0:
        raise ValueError(f"{path}: field 'release_delivery_exit_code' must be >= 0")

    incident_dispatch_status = _coerce_str(
        payload["incident_dispatch_status"],
        field="incident_dispatch_status",
        path=path,
    )
    if incident_dispatch_status not in ALLOWED_INCIDENT_DISPATCH_STATUSES:
        raise ValueError(
            f"{path}: field 'incident_dispatch_status' must be one of "
            f"{sorted(ALLOWED_INCIDENT_DISPATCH_STATUSES)}"
        )

    incident_dispatch_exit_code = _coerce_int(
        payload["incident_dispatch_exit_code"],
        field="incident_dispatch_exit_code",
        path=path,
    )
    if incident_dispatch_exit_code < 0:
        raise ValueError(f"{path}: field 'incident_dispatch_exit_code' must be >= 0")

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
        "incident_dispatch_status": incident_dispatch_status,
        "incident_dispatch_exit_code": incident_dispatch_exit_code,
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
        "release_delivery_status": release_delivery_status,
        "release_delivery_decision": release_delivery_decision,
        "release_delivery_exit_code": release_delivery_exit_code,
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
        "release_delivery_terminal_publish_status": terminal_publish_status,
        "release_delivery_terminal_publish_decision": terminal_publish_decision,
        "release_delivery_terminal_publish_exit_code": terminal_publish_exit_code,
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
        "terminal_publish_channel": terminal_publish_channel,
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


def build_release_delivery_final_verdict_payload(
    terminal_publish_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    terminal_publish_status = str(
        terminal_publish_report["release_delivery_terminal_publish_status"]
    )
    terminal_publish_decision = str(
        terminal_publish_report["release_delivery_terminal_publish_decision"]
    )
    terminal_publish_exit_code = int(
        terminal_publish_report["release_delivery_terminal_publish_exit_code"]
    )
    terminal_publish_should_notify = bool(terminal_publish_report["terminal_publish_should_notify"])
    terminal_publish_should_create_follow_up = bool(
        terminal_publish_report["terminal_publish_should_create_follow_up"]
    )
    terminal_publish_channel = str(terminal_publish_report["terminal_publish_channel"])
    release_delivery_status = str(terminal_publish_report["release_delivery_status"])
    release_delivery_decision = str(terminal_publish_report["release_delivery_decision"])
    release_delivery_exit_code = int(terminal_publish_report["release_delivery_exit_code"])
    delivery_should_ship_release = bool(terminal_publish_report["delivery_should_ship_release"])
    delivery_requires_human_action = bool(terminal_publish_report["delivery_requires_human_action"])
    delivery_should_announce_blocker = bool(
        terminal_publish_report["delivery_should_announce_blocker"]
    )
    incident_dispatch_status = str(terminal_publish_report["incident_dispatch_status"])
    incident_dispatch_exit_code = int(terminal_publish_report["incident_dispatch_exit_code"])
    terminal_should_ship_release = bool(terminal_publish_report["terminal_should_ship_release"])
    terminal_requires_follow_up = bool(terminal_publish_report["terminal_requires_follow_up"])

    reason_codes = list(terminal_publish_report["reason_codes"])
    structural_issues = list(terminal_publish_report["structural_issues"])
    missing_artifacts = list(terminal_publish_report["missing_artifacts"])
    evidence_manifest = list(terminal_publish_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_delivery_final_evidence_missing")

    if terminal_publish_status == "published":
        if terminal_publish_decision != "announce_release":
            structural_issues.append("terminal_publish_decision_mismatch_published")
        if terminal_publish_exit_code != 0:
            structural_issues.append("terminal_publish_exit_code_mismatch_published")
        if not terminal_publish_should_notify:
            structural_issues.append("terminal_publish_should_notify_mismatch_published")
        if terminal_publish_should_create_follow_up:
            structural_issues.append("terminal_publish_follow_up_mismatch_published")
        if terminal_publish_channel != "release":
            structural_issues.append("terminal_publish_channel_mismatch_published")
        if release_delivery_status != "shipped":
            structural_issues.append("release_delivery_status_mismatch_published")
        if release_delivery_decision != "deliver":
            structural_issues.append("release_delivery_decision_mismatch_published")
        if release_delivery_exit_code != 0:
            structural_issues.append("release_delivery_exit_code_mismatch_published")
        if not delivery_should_ship_release:
            structural_issues.append("delivery_should_ship_mismatch_published")
        if delivery_requires_human_action:
            structural_issues.append("delivery_requires_human_action_mismatch_published")
        if incident_dispatch_status != "not_required":
            structural_issues.append("incident_status_mismatch_published")
        if not terminal_should_ship_release:
            structural_issues.append("terminal_should_ship_mismatch_published")
        if terminal_requires_follow_up:
            structural_issues.append("terminal_requires_follow_up_mismatch_published")
    elif terminal_publish_status == "pending_follow_up":
        if terminal_publish_decision != "announce_hold":
            structural_issues.append("terminal_publish_decision_mismatch_pending_follow_up")
        if terminal_publish_exit_code == 0:
            structural_issues.append("terminal_publish_exit_code_mismatch_pending_follow_up")
        if not terminal_publish_should_notify:
            structural_issues.append("terminal_publish_should_notify_mismatch_pending_follow_up")
        if not terminal_publish_should_create_follow_up:
            structural_issues.append("terminal_publish_follow_up_mismatch_pending_follow_up")
        if terminal_publish_channel != "hold":
            structural_issues.append("terminal_publish_channel_mismatch_pending_follow_up")
        if release_delivery_status != "pending_follow_up":
            structural_issues.append("release_delivery_status_mismatch_pending_follow_up")
        if release_delivery_decision != "hold":
            structural_issues.append("release_delivery_decision_mismatch_pending_follow_up")
        if release_delivery_exit_code == 0:
            structural_issues.append("release_delivery_exit_code_mismatch_pending_follow_up")
        if delivery_should_ship_release:
            structural_issues.append("delivery_should_ship_mismatch_pending_follow_up")
        if not delivery_requires_human_action:
            structural_issues.append("delivery_requires_human_action_mismatch_pending_follow_up")
    elif terminal_publish_status == "blocked":
        if terminal_publish_decision != "announce_blocker":
            structural_issues.append("terminal_publish_decision_mismatch_blocked")
        if terminal_publish_exit_code == 0:
            structural_issues.append("terminal_publish_exit_code_mismatch_blocked")
        if not terminal_publish_should_notify:
            structural_issues.append("terminal_publish_should_notify_mismatch_blocked")
        if not terminal_publish_should_create_follow_up:
            structural_issues.append("terminal_publish_follow_up_mismatch_blocked")
        if terminal_publish_channel != "blocker":
            structural_issues.append("terminal_publish_channel_mismatch_blocked")
        if release_delivery_status not in {"blocked_incident", "blocked_incident_failed", "blocked"}:
            structural_issues.append("release_delivery_status_mismatch_blocked")
        if release_delivery_decision not in {"escalate", "block", "hold"}:
            structural_issues.append("release_delivery_decision_mismatch_blocked")
        if release_delivery_exit_code == 0:
            structural_issues.append("release_delivery_exit_code_mismatch_blocked")
        if delivery_should_ship_release:
            structural_issues.append("delivery_should_ship_mismatch_blocked")
        if not delivery_requires_human_action:
            structural_issues.append("delivery_requires_human_action_mismatch_blocked")
        if release_delivery_status == "blocked_incident" and incident_dispatch_status not in {
            "ready_dry_run",
            "dispatched",
        }:
            structural_issues.append("incident_status_mismatch_blocked_incident")
        if release_delivery_status == "blocked_incident_failed" and incident_dispatch_status != "dispatch_failed":
            structural_issues.append("incident_status_mismatch_blocked_incident_failed")
        if not delivery_should_announce_blocker:
            structural_issues.append("delivery_should_announce_blocker_mismatch_blocked")
    elif terminal_publish_status == "contract_failed":
        if terminal_publish_decision != "abort_publish":
            structural_issues.append("terminal_publish_decision_mismatch_contract_failed")
        if terminal_publish_exit_code == 0:
            structural_issues.append("terminal_publish_exit_code_mismatch_contract_failed")
        if terminal_publish_channel != "blocker":
            structural_issues.append("terminal_publish_channel_mismatch_contract_failed")
        if release_delivery_exit_code == 0:
            structural_issues.append("release_delivery_exit_code_mismatch_contract_failed")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        final_status = "contract_failed"
        final_decision = "abort_close"
        final_exit_code = 1
        final_should_close_release = False
        final_should_open_follow_up = True
        final_should_page_owner = True
        final_announcement_target = "blocker"
        reason_codes.extend(structural_issues)
    elif terminal_publish_status == "published":
        final_status = "completed"
        final_decision = "close_release"
        final_exit_code = 0
        final_should_close_release = True
        final_should_open_follow_up = False
        final_should_page_owner = False
        final_announcement_target = "release"
        reason_codes = ["release_delivery_final_completed"]
    elif terminal_publish_status == "pending_follow_up":
        final_status = "requires_follow_up"
        final_decision = "open_follow_up"
        final_exit_code = max(1, terminal_publish_exit_code, release_delivery_exit_code)
        final_should_close_release = False
        final_should_open_follow_up = True
        final_should_page_owner = False
        final_announcement_target = "hold"
        reason_codes.append("release_delivery_final_follow_up_required")
    elif terminal_publish_status == "contract_failed":
        final_status = "contract_failed"
        final_decision = "abort_close"
        final_exit_code = max(1, terminal_publish_exit_code, release_delivery_exit_code)
        final_should_close_release = False
        final_should_open_follow_up = True
        final_should_page_owner = True
        final_announcement_target = "blocker"
        reason_codes.append("release_delivery_final_upstream_contract_failed")
    else:
        final_status = "blocked"
        final_decision = "escalate_blocker"
        final_exit_code = max(
            1,
            terminal_publish_exit_code,
            release_delivery_exit_code,
            incident_dispatch_exit_code,
        )
        final_should_close_release = False
        final_should_open_follow_up = True
        final_should_page_owner = True
        final_announcement_target = "blocker"
        reason_codes.append("release_delivery_final_blocked")

    if final_status not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES:
        raise ValueError("internal: unsupported release_delivery_final_verdict_status computed")
    if final_decision not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS:
        raise ValueError("internal: unsupported release_delivery_final_verdict_decision computed")
    if final_announcement_target not in ALLOWED_RELEASE_DELIVERY_FINAL_ANNOUNCEMENT_TARGETS:
        raise ValueError("internal: unsupported release_delivery_final_announcement_target computed")

    reason_codes = _unique(reason_codes)
    release_delivery_final_verdict_summary = (
        f"release_delivery_terminal_publish_status={terminal_publish_status} "
        f"release_delivery_final_verdict_status={final_status} "
        f"release_delivery_final_verdict_decision={final_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_delivery_terminal_publish_report": str(source_path),
        "source_release_delivery_report": str(terminal_publish_report["source_release_delivery_report"]),
        "source_release_terminal_verdict_report": str(
            terminal_publish_report["source_release_terminal_verdict_report"]
        ),
        "source_release_incident_report": str(terminal_publish_report["source_release_incident_report"]),
        "source_release_verdict_report": str(terminal_publish_report["source_release_verdict_report"]),
        "source_release_archive_report": str(terminal_publish_report["source_release_archive_report"]),
        "release_archive_status": str(terminal_publish_report["release_archive_status"]),
        "release_archive_decision": str(terminal_publish_report["release_archive_decision"]),
        "release_archive_exit_code": int(terminal_publish_report["release_archive_exit_code"]),
        "should_publish_archive": bool(terminal_publish_report["should_publish_archive"]),
        "release_verdict_status": str(terminal_publish_report["release_verdict_status"]),
        "release_verdict_decision": str(terminal_publish_report["release_verdict_decision"]),
        "release_verdict_exit_code": int(terminal_publish_report["release_verdict_exit_code"]),
        "should_ship_release": bool(terminal_publish_report["should_ship_release"]),
        "should_open_incident": bool(terminal_publish_report["should_open_incident"]),
        "should_dispatch_incident": bool(terminal_publish_report["should_dispatch_incident"]),
        "incident_dispatch_status": incident_dispatch_status,
        "incident_dispatch_exit_code": incident_dispatch_exit_code,
        "incident_dispatch_attempted": bool(terminal_publish_report["incident_dispatch_attempted"]),
        "incident_url": str(terminal_publish_report["incident_url"]),
        "release_terminal_verdict_status": str(
            terminal_publish_report["release_terminal_verdict_status"]
        ),
        "release_terminal_verdict_decision": str(
            terminal_publish_report["release_terminal_verdict_decision"]
        ),
        "release_terminal_verdict_exit_code": int(
            terminal_publish_report["release_terminal_verdict_exit_code"]
        ),
        "terminal_should_ship_release": terminal_should_ship_release,
        "terminal_requires_follow_up": terminal_requires_follow_up,
        "terminal_incident_linked": bool(terminal_publish_report["terminal_incident_linked"]),
        "release_delivery_status": release_delivery_status,
        "release_delivery_decision": release_delivery_decision,
        "release_delivery_exit_code": release_delivery_exit_code,
        "delivery_should_ship_release": delivery_should_ship_release,
        "delivery_requires_human_action": delivery_requires_human_action,
        "delivery_should_announce_blocker": delivery_should_announce_blocker,
        "release_delivery_terminal_publish_status": terminal_publish_status,
        "release_delivery_terminal_publish_decision": terminal_publish_decision,
        "release_delivery_terminal_publish_exit_code": terminal_publish_exit_code,
        "terminal_publish_should_notify": terminal_publish_should_notify,
        "terminal_publish_should_create_follow_up": terminal_publish_should_create_follow_up,
        "terminal_publish_channel": terminal_publish_channel,
        "release_delivery_final_verdict_status": final_status,
        "release_delivery_final_verdict_decision": final_decision,
        "release_delivery_final_verdict_exit_code": final_exit_code,
        "final_should_close_release": final_should_close_release,
        "final_should_open_follow_up": final_should_open_follow_up,
        "final_should_page_owner": final_should_page_owner,
        "final_announcement_target": final_announcement_target,
        "release_run_id": terminal_publish_report["release_run_id"],
        "release_run_url": str(terminal_publish_report["release_run_url"]),
        "release_delivery_final_verdict_summary": release_delivery_final_verdict_summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Delivery Final Verdict Report",
        "",
        (
            "- Release Delivery Final Verdict Status: "
            f"**{str(payload['release_delivery_final_verdict_status']).upper()}**"
        ),
        (
            "- Release Delivery Final Verdict Decision: "
            f"`{payload['release_delivery_final_verdict_decision']}`"
        ),
        (
            "- Release Delivery Final Verdict Exit Code: "
            f"`{payload['release_delivery_final_verdict_exit_code']}`"
        ),
        f"- Final Should Close Release: `{payload['final_should_close_release']}`",
        f"- Final Should Open Follow Up: `{payload['final_should_open_follow_up']}`",
        f"- Final Should Page Owner: `{payload['final_should_page_owner']}`",
        f"- Final Announcement Target: `{payload['final_announcement_target']}`",
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
        f"- {payload['release_delivery_final_verdict_summary']}",
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
        "workflow_release_delivery_final_verdict_status": str(
            payload["release_delivery_final_verdict_status"]
        ),
        "workflow_release_delivery_final_verdict_decision": str(
            payload["release_delivery_final_verdict_decision"]
        ),
        "workflow_release_delivery_final_verdict_exit_code": str(
            payload["release_delivery_final_verdict_exit_code"]
        ),
        "workflow_release_delivery_final_should_close_release": (
            "true" if payload["final_should_close_release"] else "false"
        ),
        "workflow_release_delivery_final_should_open_follow_up": (
            "true" if payload["final_should_open_follow_up"] else "false"
        ),
        "workflow_release_delivery_final_should_page_owner": (
            "true" if payload["final_should_page_owner"] else "false"
        ),
        "workflow_release_delivery_final_announcement_target": str(
            payload["final_announcement_target"]
        ),
        "workflow_release_delivery_final_terminal_publish_status": str(
            payload["release_delivery_terminal_publish_status"]
        ),
        "workflow_release_delivery_final_incident_status": str(payload["incident_dispatch_status"]),
        "workflow_release_delivery_final_incident_url": str(payload["incident_url"]),
        "workflow_release_delivery_final_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_delivery_final_run_url": str(payload["release_run_url"]),
        "workflow_release_delivery_final_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_delivery_final_report_json": str(output_json),
        "workflow_release_delivery_final_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release delivery final verdict contract "
            "from P2-42 release delivery terminal publish report"
        )
    )
    parser.add_argument(
        "--release-delivery-terminal-publish-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json",
        help="P2-42 release delivery terminal publish report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json",
        help="Output release delivery final verdict JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.md",
        help="Output release delivery final verdict markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release delivery final verdict JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    terminal_publish_report_path = Path(args.release_delivery_terminal_publish_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        terminal_publish_report = load_release_delivery_terminal_publish_report(
            terminal_publish_report_path
        )
        payload = build_release_delivery_final_verdict_payload(
            terminal_publish_report,
            source_path=terminal_publish_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            f"[p2-linux-ci-workflow-release-delivery-final-verdict-gate] {exc}",
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
        print(f"release delivery final verdict json: {output_json_path}")
        print(f"release delivery final verdict markdown: {output_markdown_path}")

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
        "release delivery final verdict summary: "
        f"release_delivery_final_verdict_status="
        f"{payload['release_delivery_final_verdict_status']} "
        f"release_delivery_final_verdict_decision="
        f"{payload['release_delivery_final_verdict_decision']} "
        f"release_delivery_final_verdict_exit_code="
        f"{payload['release_delivery_final_verdict_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_delivery_final_verdict_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

