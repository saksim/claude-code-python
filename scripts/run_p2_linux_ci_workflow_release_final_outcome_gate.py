"""Phase 2 card P2-48 gate for Linux CI workflow release final outcome.

This script consumes the P2-43 release delivery final verdict artifact and
P2-47 release follow-up final verdict artifact, then converges one final
release outcome contract:
1) validate delivery/follow-up verdict consistency,
2) normalize terminal release outcome semantics,
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
ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_STATUSES: set[str] = {
    "completed",
    "requires_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_DECISIONS: set[str] = {
    "close_follow_up",
    "keep_follow_up_open",
    "escalate_queue_failure",
    "abort_close",
}
ALLOWED_RELEASE_FOLLOW_UP_FINAL_ANNOUNCEMENT_TARGETS: set[str] = {
    "release",
    "follow_up",
    "blocker",
}
ALLOWED_RELEASE_FINAL_OUTCOME_STATUSES: set[str] = {
    "released",
    "released_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_OUTCOME_DECISIONS: set[str] = {
    "ship_and_close",
    "ship_with_follow_up_open",
    "escalate_blocker",
    "abort_outcome",
}
ALLOWED_RELEASE_FINAL_OUTCOME_TARGETS: set[str] = {"release", "follow_up", "blocker"}


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
        if "path" not in entry or "exists" not in entry:
            raise ValueError(f"{path}: {field}[{idx}] missing path/exists")

        entry_path = _coerce_str(entry["path"], field=f"{field}[{idx}].path", path=path)
        entry_exists = _coerce_bool(entry["exists"], field=f"{field}[{idx}].exists", path=path)
        evidence_manifest.append({"path": entry_path, "exists": entry_exists})
    return evidence_manifest


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

    status = _coerce_str(
        payload["release_delivery_final_verdict_status"],
        field="release_delivery_final_verdict_status",
        path=path,
    )
    if status not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES)}"
        )

    decision = _coerce_str(
        payload["release_delivery_final_verdict_decision"],
        field="release_delivery_final_verdict_decision",
        path=path,
    )
    if decision not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS)}"
        )

    exit_code = _coerce_int(
        payload["release_delivery_final_verdict_exit_code"],
        field="release_delivery_final_verdict_exit_code",
        path=path,
    )
    if exit_code < 0:
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_exit_code' must be >= 0"
        )

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

    return {
        "generated_at": payload.get("generated_at"),
        "source_release_delivery_terminal_publish_report": _coerce_str(
            payload["source_release_delivery_terminal_publish_report"],
            field="source_release_delivery_terminal_publish_report",
            path=path,
        ),
        "release_delivery_final_verdict_status": status,
        "release_delivery_final_verdict_decision": decision,
        "release_delivery_final_verdict_exit_code": exit_code,
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
        "release_run_url": _coerce_str(payload["release_run_url"], field="release_run_url", path=path),
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


def load_release_follow_up_final_verdict_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release follow-up final verdict report not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release follow-up final verdict payload must be object")

    required_fields = (
        "source_release_follow_up_terminal_publish_report",
        "release_follow_up_final_verdict_status",
        "release_follow_up_final_verdict_decision",
        "release_follow_up_final_verdict_exit_code",
        "final_should_close_follow_up",
        "final_should_open_follow_up",
        "final_should_page_owner",
        "final_announcement_target",
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

    status = _coerce_str(
        payload["release_follow_up_final_verdict_status"],
        field="release_follow_up_final_verdict_status",
        path=path,
    )
    if status not in ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_follow_up_final_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_STATUSES)}"
        )

    decision = _coerce_str(
        payload["release_follow_up_final_verdict_decision"],
        field="release_follow_up_final_verdict_decision",
        path=path,
    )
    if decision not in ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_follow_up_final_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_DECISIONS)}"
        )

    exit_code = _coerce_int(
        payload["release_follow_up_final_verdict_exit_code"],
        field="release_follow_up_final_verdict_exit_code",
        path=path,
    )
    if exit_code < 0:
        raise ValueError(
            f"{path}: field 'release_follow_up_final_verdict_exit_code' must be >= 0"
        )

    announcement_target = _coerce_str(
        payload["final_announcement_target"],
        field="final_announcement_target",
        path=path,
    )
    if announcement_target not in ALLOWED_RELEASE_FOLLOW_UP_FINAL_ANNOUNCEMENT_TARGETS:
        raise ValueError(
            f"{path}: field 'final_announcement_target' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_FINAL_ANNOUNCEMENT_TARGETS)}"
        )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    return {
        "generated_at": payload.get("generated_at"),
        "source_release_follow_up_terminal_publish_report": _coerce_str(
            payload["source_release_follow_up_terminal_publish_report"],
            field="source_release_follow_up_terminal_publish_report",
            path=path,
        ),
        "release_follow_up_final_verdict_status": status,
        "release_follow_up_final_verdict_decision": decision,
        "release_follow_up_final_verdict_exit_code": exit_code,
        "final_should_close_follow_up": _coerce_bool(
            payload["final_should_close_follow_up"],
            field="final_should_close_follow_up",
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
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(payload["release_run_url"], field="release_run_url", path=path),
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


def build_release_final_outcome_payload(
    delivery_final_verdict_report: dict[str, Any],
    follow_up_final_verdict_report: dict[str, Any],
    *,
    delivery_source_path: Path,
    follow_up_source_path: Path,
) -> dict[str, Any]:
    delivery_status = str(delivery_final_verdict_report["release_delivery_final_verdict_status"])
    delivery_decision = str(delivery_final_verdict_report["release_delivery_final_verdict_decision"])
    delivery_exit_code = int(delivery_final_verdict_report["release_delivery_final_verdict_exit_code"])
    delivery_close_release = bool(delivery_final_verdict_report["final_should_close_release"])
    delivery_open_follow_up = bool(delivery_final_verdict_report["final_should_open_follow_up"])
    delivery_page_owner = bool(delivery_final_verdict_report["final_should_page_owner"])
    delivery_target = str(delivery_final_verdict_report["final_announcement_target"])
    delivery_run_id = delivery_final_verdict_report["release_run_id"]
    delivery_run_url = str(delivery_final_verdict_report["release_run_url"])

    follow_status = str(follow_up_final_verdict_report["release_follow_up_final_verdict_status"])
    follow_decision = str(follow_up_final_verdict_report["release_follow_up_final_verdict_decision"])
    follow_exit_code = int(follow_up_final_verdict_report["release_follow_up_final_verdict_exit_code"])
    follow_close_follow_up = bool(follow_up_final_verdict_report["final_should_close_follow_up"])
    follow_open_follow_up = bool(follow_up_final_verdict_report["final_should_open_follow_up"])
    follow_page_owner = bool(follow_up_final_verdict_report["final_should_page_owner"])
    follow_target = str(follow_up_final_verdict_report["final_announcement_target"])
    follow_queue_url = str(follow_up_final_verdict_report["follow_up_queue_url"])
    follow_run_id = follow_up_final_verdict_report["release_run_id"]
    follow_run_url = str(follow_up_final_verdict_report["release_run_url"])

    reason_codes = list(delivery_final_verdict_report["reason_codes"]) + list(
        follow_up_final_verdict_report["reason_codes"]
    )
    structural_issues = list(delivery_final_verdict_report["structural_issues"]) + list(
        follow_up_final_verdict_report["structural_issues"]
    )
    missing_artifacts = list(delivery_final_verdict_report["missing_artifacts"]) + list(
        follow_up_final_verdict_report["missing_artifacts"]
    )
    evidence_manifest = [
        {"source": "delivery", "path": str(item["path"]), "exists": bool(item["exists"])}
        for item in delivery_final_verdict_report["evidence_manifest"]
    ] + [
        {"source": "follow_up", "path": str(item["path"]), "exists": bool(item["exists"])}
        for item in follow_up_final_verdict_report["evidence_manifest"]
    ]

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_final_outcome_evidence_missing")

    expected_delivery = {
        "completed": ("close_release", True, False, False),
        "requires_follow_up": ("open_follow_up", False, True, False),
        "blocked": ("escalate_blocker", False, True, True),
        "contract_failed": ("abort_close", False, True, True),
    }
    expected_follow_up = {
        "completed": ("close_follow_up", True, False, False),
        "requires_follow_up": ("keep_follow_up_open", False, True, False),
        "blocked": ("escalate_queue_failure", False, True, True),
        "contract_failed": ("abort_close", False, True, True),
    }

    expected_delivery_decision, expected_delivery_close, expected_delivery_open, expected_delivery_page = expected_delivery[
        delivery_status
    ]
    if delivery_decision != expected_delivery_decision:
        structural_issues.append("delivery_decision_mismatch")
    if delivery_close_release != expected_delivery_close:
        structural_issues.append("delivery_close_release_mismatch")
    if delivery_open_follow_up != expected_delivery_open:
        structural_issues.append("delivery_open_follow_up_mismatch")
    if delivery_page_owner != expected_delivery_page:
        structural_issues.append("delivery_page_owner_mismatch")
    if delivery_status == "completed":
        if delivery_exit_code != 0:
            structural_issues.append("delivery_exit_code_mismatch_completed")
        if delivery_target != "release":
            structural_issues.append("delivery_target_mismatch_completed")
    else:
        if delivery_exit_code == 0:
            structural_issues.append("delivery_exit_code_mismatch_non_completed")
        if delivery_target == "release":
            structural_issues.append("delivery_target_mismatch_non_completed")

    expected_follow_decision, expected_follow_close, expected_follow_open, expected_follow_page = expected_follow_up[
        follow_status
    ]
    if follow_decision != expected_follow_decision:
        structural_issues.append("follow_up_decision_mismatch")
    if follow_close_follow_up != expected_follow_close:
        structural_issues.append("follow_up_close_flag_mismatch")
    if follow_open_follow_up != expected_follow_open:
        structural_issues.append("follow_up_open_flag_mismatch")
    if follow_page_owner != expected_follow_page:
        structural_issues.append("follow_up_page_owner_mismatch")
    if follow_status == "completed":
        if follow_exit_code != 0:
            structural_issues.append("follow_up_exit_code_mismatch_completed")
        if follow_target not in {"release", "follow_up"}:
            structural_issues.append("follow_up_target_mismatch_completed")
    else:
        if follow_exit_code == 0:
            structural_issues.append("follow_up_exit_code_mismatch_non_completed")
        if follow_target == "release":
            structural_issues.append("follow_up_target_mismatch_non_completed")

    if delivery_run_id is not None and follow_run_id is not None and delivery_run_id != follow_run_id:
        structural_issues.append("release_run_id_mismatch")
    if delivery_run_url and follow_run_url and delivery_run_url != follow_run_url:
        structural_issues.append("release_run_url_mismatch")

    if delivery_status == "blocked" and follow_status == "completed":
        structural_issues.append("follow_up_completed_while_delivery_blocked")
    if delivery_status == "contract_failed" and follow_status != "contract_failed":
        structural_issues.append("follow_up_status_mismatch_delivery_contract_failed")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        outcome_status = "contract_failed"
        outcome_decision = "abort_outcome"
        outcome_exit_code = max(1, delivery_exit_code, follow_exit_code)
        final_should_ship_release = False
        final_follow_up_open = True
        final_should_page_owner = True
        final_outcome_target = "blocker"
        reason_codes.extend(structural_issues)
    elif delivery_status == "contract_failed" or follow_status == "contract_failed":
        outcome_status = "contract_failed"
        outcome_decision = "abort_outcome"
        outcome_exit_code = max(1, delivery_exit_code, follow_exit_code)
        final_should_ship_release = False
        final_follow_up_open = True
        final_should_page_owner = True
        final_outcome_target = "blocker"
        reason_codes.append("release_final_outcome_upstream_contract_failed")
    elif delivery_status == "blocked" or follow_status == "blocked":
        outcome_status = "blocked"
        outcome_decision = "escalate_blocker"
        outcome_exit_code = max(1, delivery_exit_code, follow_exit_code)
        final_should_ship_release = False
        final_follow_up_open = True
        final_should_page_owner = True
        final_outcome_target = "blocker"
        reason_codes.append("release_final_outcome_blocked")
    elif follow_status == "completed" and delivery_status in {"completed", "requires_follow_up"}:
        outcome_status = "released"
        outcome_decision = "ship_and_close"
        outcome_exit_code = 0
        final_should_ship_release = True
        final_follow_up_open = False
        final_should_page_owner = False
        final_outcome_target = "release"
        reason_codes.append("release_final_outcome_released")
    elif follow_status == "requires_follow_up" or delivery_status == "requires_follow_up":
        outcome_status = "released_with_follow_up"
        outcome_decision = "ship_with_follow_up_open"
        outcome_exit_code = max(1, delivery_exit_code, follow_exit_code)
        final_should_ship_release = True
        final_follow_up_open = True
        final_should_page_owner = False
        final_outcome_target = "follow_up"
        reason_codes.append("release_final_outcome_released_with_follow_up")
    elif delivery_status == "completed" and follow_status == "completed":
        outcome_status = "released"
        outcome_decision = "ship_and_close"
        outcome_exit_code = 0
        final_should_ship_release = True
        final_follow_up_open = False
        final_should_page_owner = False
        final_outcome_target = "release"
        reason_codes.append("release_final_outcome_released")
    else:
        outcome_status = "contract_failed"
        outcome_decision = "abort_outcome"
        outcome_exit_code = max(1, delivery_exit_code, follow_exit_code)
        final_should_ship_release = False
        final_follow_up_open = True
        final_should_page_owner = True
        final_outcome_target = "blocker"
        reason_codes.append("release_final_outcome_status_combination_unknown")

    if outcome_status not in ALLOWED_RELEASE_FINAL_OUTCOME_STATUSES:
        raise ValueError("internal: unsupported release_final_outcome_status computed")
    if outcome_decision not in ALLOWED_RELEASE_FINAL_OUTCOME_DECISIONS:
        raise ValueError("internal: unsupported release_final_outcome_decision computed")
    if final_outcome_target not in ALLOWED_RELEASE_FINAL_OUTCOME_TARGETS:
        raise ValueError("internal: unsupported release_final_outcome_target computed")

    reason_codes = _unique(reason_codes)
    release_run_id = follow_run_id if follow_run_id is not None else delivery_run_id
    release_run_url = follow_run_url if follow_run_url else delivery_run_url
    summary = (
        f"release_delivery_final_verdict_status={delivery_status} "
        f"release_follow_up_final_verdict_status={follow_status} "
        f"release_final_outcome_status={outcome_status} "
        f"release_final_outcome_decision={outcome_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_delivery_final_verdict_report": str(delivery_source_path),
        "source_release_follow_up_final_verdict_report": str(follow_up_source_path),
        "release_delivery_final_verdict_status": delivery_status,
        "release_delivery_final_verdict_decision": delivery_decision,
        "release_delivery_final_verdict_exit_code": delivery_exit_code,
        "release_follow_up_final_verdict_status": follow_status,
        "release_follow_up_final_verdict_decision": follow_decision,
        "release_follow_up_final_verdict_exit_code": follow_exit_code,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "follow_up_queue_url": follow_queue_url,
        "release_final_outcome_status": outcome_status,
        "release_final_outcome_decision": outcome_decision,
        "release_final_outcome_exit_code": outcome_exit_code,
        "final_should_ship_release": final_should_ship_release,
        "final_follow_up_open": final_follow_up_open,
        "final_should_page_owner": final_should_page_owner,
        "final_outcome_target": final_outcome_target,
        "release_final_outcome_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Final Outcome Report",
        "",
        f"- Release Final Outcome Status: **{str(payload['release_final_outcome_status']).upper()}**",
        f"- Release Final Outcome Decision: `{payload['release_final_outcome_decision']}`",
        f"- Release Final Outcome Exit Code: `{payload['release_final_outcome_exit_code']}`",
        f"- Final Should Ship Release: `{payload['final_should_ship_release']}`",
        f"- Final Follow-Up Open: `{payload['final_follow_up_open']}`",
        f"- Final Should Page Owner: `{payload['final_should_page_owner']}`",
        f"- Final Outcome Target: `{payload['final_outcome_target']}`",
        f"- Delivery Final Verdict Status: `{payload['release_delivery_final_verdict_status']}`",
        f"- Follow-Up Final Verdict Status: `{payload['release_follow_up_final_verdict_status']}`",
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_final_outcome_summary']}",
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
        "workflow_release_final_outcome_status": str(payload["release_final_outcome_status"]),
        "workflow_release_final_outcome_decision": str(payload["release_final_outcome_decision"]),
        "workflow_release_final_outcome_exit_code": str(payload["release_final_outcome_exit_code"]),
        "workflow_release_final_should_ship_release": (
            "true" if payload["final_should_ship_release"] else "false"
        ),
        "workflow_release_final_follow_up_open": (
            "true" if payload["final_follow_up_open"] else "false"
        ),
        "workflow_release_final_should_page_owner": (
            "true" if payload["final_should_page_owner"] else "false"
        ),
        "workflow_release_final_target": str(payload["final_outcome_target"]),
        "workflow_release_final_delivery_status": str(
            payload["release_delivery_final_verdict_status"]
        ),
        "workflow_release_final_follow_up_status": str(
            payload["release_follow_up_final_verdict_status"]
        ),
        "workflow_release_final_follow_up_queue_url": str(payload["follow_up_queue_url"]),
        "workflow_release_final_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_final_run_url": str(payload["release_run_url"]),
        "workflow_release_final_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_final_report_json": str(output_json),
        "workflow_release_final_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release final outcome contract "
            "from P2-43 and P2-47 final verdict reports"
        )
    )
    parser.add_argument(
        "--release-delivery-final-verdict-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json",
        help="P2-43 release delivery final verdict report JSON path",
    )
    parser.add_argument(
        "--release-follow-up-final-verdict-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json",
        help="P2-47 release follow-up final verdict report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json",
        help="Output release final outcome JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.md",
        help="Output release final outcome markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release final outcome JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    delivery_report_path = Path(args.release_delivery_final_verdict_report)
    follow_up_report_path = Path(args.release_follow_up_final_verdict_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        delivery_report = load_release_delivery_final_verdict_report(delivery_report_path)
        follow_up_report = load_release_follow_up_final_verdict_report(follow_up_report_path)
        payload = build_release_final_outcome_payload(
            delivery_report,
            follow_up_report,
            delivery_source_path=delivery_report_path.resolve(),
            follow_up_source_path=follow_up_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-final-outcome-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release final outcome json: {output_json_path}")
        print(f"release final outcome markdown: {output_markdown_path}")

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
        "release final outcome summary: "
        f"release_final_outcome_status={payload['release_final_outcome_status']} "
        f"release_final_outcome_decision={payload['release_final_outcome_decision']} "
        f"release_final_outcome_exit_code={payload['release_final_outcome_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_final_outcome_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
