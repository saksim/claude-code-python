"""Phase 2 card P2-53 gate for Linux CI workflow release final archive.

This script consumes the P2-52 release final closure publish artifact and
converges one terminal final-archive contract:
1) validate final closure publish + evidence consistency,
2) normalize archive semantics for downstream consumers,
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
ALLOWED_RELEASE_FINAL_TERMINAL_PUBLISH_STATUSES: set[str] = {
    "published",
    "published_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_TERMINAL_PUBLISH_DECISIONS: set[str] = {
    "announce_release_closure",
    "announce_release_with_follow_up",
    "announce_blocker",
    "abort_publish",
}
ALLOWED_RELEASE_FINAL_HANDOFF_STATUSES: set[str] = {
    "completed",
    "completed_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_HANDOFF_DECISIONS: set[str] = {
    "handoff_release_closure",
    "handoff_release_with_follow_up",
    "handoff_blocker",
    "abort_handoff",
}
ALLOWED_RELEASE_FINAL_CLOSURE_STATUSES: set[str] = {
    "closed",
    "closed_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_CLOSURE_DECISIONS: set[str] = {
    "close_release",
    "close_with_follow_up",
    "close_blocker",
    "abort_close",
}
ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_STATUSES: set[str] = {
    "published",
    "published_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_DECISIONS: set[str] = {
    "announce_release_closed",
    "announce_release_closed_with_follow_up",
    "announce_release_blocker",
    "abort_publish",
}
ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_CHANNELS: set[str] = {"release", "follow_up", "blocker"}
ALLOWED_RELEASE_FINAL_ARCHIVE_STATUSES: set[str] = {
    "archived",
    "archived_with_follow_up",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_FINAL_ARCHIVE_DECISIONS: set[str] = {
    "archive_release_closed",
    "archive_release_closed_with_follow_up",
    "archive_release_blocker",
    "abort_archive",
}
ALLOWED_RELEASE_FINAL_ARCHIVE_CHANNELS: set[str] = {"release", "follow_up", "blocker"}


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

        entry_source = _coerce_str(entry["source"], field=f"{field}[{idx}].source", path=path)
        entry_path = _coerce_str(entry["path"], field=f"{field}[{idx}].path", path=path)
        entry_exists = _coerce_bool(entry["exists"], field=f"{field}[{idx}].exists", path=path)
        evidence_manifest.append(
            {"source": entry_source, "path": entry_path, "exists": entry_exists}
        )
    return evidence_manifest


def load_release_final_closure_publish_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release final closure publish report not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release final closure publish payload must be object")

    required_fields = (
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
        "release_run_id",
        "release_run_url",
        "follow_up_queue_url",
        "final_closure_publish_should_notify",
        "final_closure_publish_requires_manual_action",
        "final_closure_publish_channel",
        "release_final_closure_publish_summary",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        "evidence_manifest",
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    release_delivery_final_verdict_status = _coerce_str(
        payload["release_delivery_final_verdict_status"],
        field="release_delivery_final_verdict_status",
        path=path,
    )
    if release_delivery_final_verdict_status not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_STATUSES)}"
        )
    release_delivery_final_verdict_decision = _coerce_str(
        payload["release_delivery_final_verdict_decision"],
        field="release_delivery_final_verdict_decision",
        path=path,
    )
    if (
        release_delivery_final_verdict_decision
        not in ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'release_delivery_final_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_DELIVERY_FINAL_VERDICT_DECISIONS)}"
        )

    release_follow_up_final_verdict_status = _coerce_str(
        payload["release_follow_up_final_verdict_status"],
        field="release_follow_up_final_verdict_status",
        path=path,
    )
    if release_follow_up_final_verdict_status not in ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_follow_up_final_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_STATUSES)}"
        )
    release_follow_up_final_verdict_decision = _coerce_str(
        payload["release_follow_up_final_verdict_decision"],
        field="release_follow_up_final_verdict_decision",
        path=path,
    )
    if (
        release_follow_up_final_verdict_decision
        not in ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'release_follow_up_final_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FOLLOW_UP_FINAL_VERDICT_DECISIONS)}"
        )

    release_final_outcome_status = _coerce_str(
        payload["release_final_outcome_status"],
        field="release_final_outcome_status",
        path=path,
    )
    if release_final_outcome_status not in ALLOWED_RELEASE_FINAL_OUTCOME_STATUSES:
        raise ValueError(
            f"{path}: field 'release_final_outcome_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_OUTCOME_STATUSES)}"
        )
    release_final_outcome_decision = _coerce_str(
        payload["release_final_outcome_decision"],
        field="release_final_outcome_decision",
        path=path,
    )
    if release_final_outcome_decision not in ALLOWED_RELEASE_FINAL_OUTCOME_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_final_outcome_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_OUTCOME_DECISIONS)}"
        )

    release_final_terminal_publish_status = _coerce_str(
        payload["release_final_terminal_publish_status"],
        field="release_final_terminal_publish_status",
        path=path,
    )
    if release_final_terminal_publish_status not in ALLOWED_RELEASE_FINAL_TERMINAL_PUBLISH_STATUSES:
        raise ValueError(
            f"{path}: field 'release_final_terminal_publish_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_TERMINAL_PUBLISH_STATUSES)}"
        )
    release_final_terminal_publish_decision = _coerce_str(
        payload["release_final_terminal_publish_decision"],
        field="release_final_terminal_publish_decision",
        path=path,
    )
    if (
        release_final_terminal_publish_decision
        not in ALLOWED_RELEASE_FINAL_TERMINAL_PUBLISH_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'release_final_terminal_publish_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_TERMINAL_PUBLISH_DECISIONS)}"
        )

    release_final_handoff_status = _coerce_str(
        payload["release_final_handoff_status"],
        field="release_final_handoff_status",
        path=path,
    )
    if release_final_handoff_status not in ALLOWED_RELEASE_FINAL_HANDOFF_STATUSES:
        raise ValueError(
            f"{path}: field 'release_final_handoff_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_HANDOFF_STATUSES)}"
        )
    release_final_handoff_decision = _coerce_str(
        payload["release_final_handoff_decision"],
        field="release_final_handoff_decision",
        path=path,
    )
    if release_final_handoff_decision not in ALLOWED_RELEASE_FINAL_HANDOFF_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_final_handoff_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_HANDOFF_DECISIONS)}"
        )

    release_final_closure_status = _coerce_str(
        payload["release_final_closure_status"],
        field="release_final_closure_status",
        path=path,
    )
    if release_final_closure_status not in ALLOWED_RELEASE_FINAL_CLOSURE_STATUSES:
        raise ValueError(
            f"{path}: field 'release_final_closure_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_CLOSURE_STATUSES)}"
        )
    release_final_closure_decision = _coerce_str(
        payload["release_final_closure_decision"],
        field="release_final_closure_decision",
        path=path,
    )
    if release_final_closure_decision not in ALLOWED_RELEASE_FINAL_CLOSURE_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_final_closure_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_CLOSURE_DECISIONS)}"
        )

    release_final_closure_publish_status = _coerce_str(
        payload["release_final_closure_publish_status"],
        field="release_final_closure_publish_status",
        path=path,
    )
    if release_final_closure_publish_status not in ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_STATUSES:
        raise ValueError(
            f"{path}: field 'release_final_closure_publish_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_STATUSES)}"
        )
    release_final_closure_publish_decision = _coerce_str(
        payload["release_final_closure_publish_decision"],
        field="release_final_closure_publish_decision",
        path=path,
    )
    if (
        release_final_closure_publish_decision
        not in ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_DECISIONS
    ):
        raise ValueError(
            f"{path}: field 'release_final_closure_publish_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_DECISIONS)}"
        )
    final_closure_publish_channel = _coerce_str(
        payload["final_closure_publish_channel"],
        field="final_closure_publish_channel",
        path=path,
    )
    if final_closure_publish_channel not in ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_CHANNELS:
        raise ValueError(
            f"{path}: field 'final_closure_publish_channel' must be one of "
            f"{sorted(ALLOWED_RELEASE_FINAL_CLOSURE_PUBLISH_CHANNELS)}"
        )

    release_delivery_final_verdict_exit_code = _coerce_int(
        payload["release_delivery_final_verdict_exit_code"],
        field="release_delivery_final_verdict_exit_code",
        path=path,
    )
    release_follow_up_final_verdict_exit_code = _coerce_int(
        payload["release_follow_up_final_verdict_exit_code"],
        field="release_follow_up_final_verdict_exit_code",
        path=path,
    )
    release_final_outcome_exit_code = _coerce_int(
        payload["release_final_outcome_exit_code"],
        field="release_final_outcome_exit_code",
        path=path,
    )
    release_final_terminal_publish_exit_code = _coerce_int(
        payload["release_final_terminal_publish_exit_code"],
        field="release_final_terminal_publish_exit_code",
        path=path,
    )
    release_final_handoff_exit_code = _coerce_int(
        payload["release_final_handoff_exit_code"],
        field="release_final_handoff_exit_code",
        path=path,
    )
    release_final_closure_exit_code = _coerce_int(
        payload["release_final_closure_exit_code"],
        field="release_final_closure_exit_code",
        path=path,
    )
    release_final_closure_publish_exit_code = _coerce_int(
        payload["release_final_closure_publish_exit_code"],
        field="release_final_closure_publish_exit_code",
        path=path,
    )
    if release_delivery_final_verdict_exit_code < 0:
        raise ValueError(f"{path}: field 'release_delivery_final_verdict_exit_code' must be >= 0")
    if release_follow_up_final_verdict_exit_code < 0:
        raise ValueError(
            f"{path}: field 'release_follow_up_final_verdict_exit_code' must be >= 0"
        )
    if release_final_outcome_exit_code < 0:
        raise ValueError(f"{path}: field 'release_final_outcome_exit_code' must be >= 0")
    if release_final_terminal_publish_exit_code < 0:
        raise ValueError(
            f"{path}: field 'release_final_terminal_publish_exit_code' must be >= 0"
        )
    if release_final_handoff_exit_code < 0:
        raise ValueError(f"{path}: field 'release_final_handoff_exit_code' must be >= 0")
    if release_final_closure_exit_code < 0:
        raise ValueError(f"{path}: field 'release_final_closure_exit_code' must be >= 0")
    if release_final_closure_publish_exit_code < 0:
        raise ValueError(
            f"{path}: field 'release_final_closure_publish_exit_code' must be >= 0"
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
        "release_delivery_final_verdict_status": release_delivery_final_verdict_status,
        "release_delivery_final_verdict_decision": release_delivery_final_verdict_decision,
        "release_delivery_final_verdict_exit_code": release_delivery_final_verdict_exit_code,
        "release_follow_up_final_verdict_status": release_follow_up_final_verdict_status,
        "release_follow_up_final_verdict_decision": release_follow_up_final_verdict_decision,
        "release_follow_up_final_verdict_exit_code": release_follow_up_final_verdict_exit_code,
        "release_final_outcome_status": release_final_outcome_status,
        "release_final_outcome_decision": release_final_outcome_decision,
        "release_final_outcome_exit_code": release_final_outcome_exit_code,
        "release_final_terminal_publish_status": release_final_terminal_publish_status,
        "release_final_terminal_publish_decision": release_final_terminal_publish_decision,
        "release_final_terminal_publish_exit_code": release_final_terminal_publish_exit_code,
        "release_final_handoff_status": release_final_handoff_status,
        "release_final_handoff_decision": release_final_handoff_decision,
        "release_final_handoff_exit_code": release_final_handoff_exit_code,
        "release_final_closure_status": release_final_closure_status,
        "release_final_closure_decision": release_final_closure_decision,
        "release_final_closure_exit_code": release_final_closure_exit_code,
        "release_final_closure_publish_status": release_final_closure_publish_status,
        "release_final_closure_publish_decision": release_final_closure_publish_decision,
        "release_final_closure_publish_exit_code": release_final_closure_publish_exit_code,
        "release_run_id": release_run_id,
        "release_run_url": _coerce_str(payload["release_run_url"], field="release_run_url", path=path),
        "follow_up_queue_url": _coerce_str(
            payload["follow_up_queue_url"],
            field="follow_up_queue_url",
            path=path,
        ),
        "final_closure_publish_should_notify": _coerce_bool(
            payload["final_closure_publish_should_notify"],
            field="final_closure_publish_should_notify",
            path=path,
        ),
        "final_closure_publish_requires_manual_action": _coerce_bool(
            payload["final_closure_publish_requires_manual_action"],
            field="final_closure_publish_requires_manual_action",
            path=path,
        ),
        "final_closure_publish_channel": final_closure_publish_channel,
        "release_final_closure_publish_summary": _coerce_str(
            payload["release_final_closure_publish_summary"],
            field="release_final_closure_publish_summary",
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


def build_release_final_archive_payload(
    release_final_closure_publish_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    final_closure_publish_status = str(
        release_final_closure_publish_report["release_final_closure_publish_status"]
    )
    final_closure_publish_decision = str(
        release_final_closure_publish_report["release_final_closure_publish_decision"]
    )
    final_closure_publish_exit_code = int(
        release_final_closure_publish_report["release_final_closure_publish_exit_code"]
    )
    final_closure_publish_should_notify = bool(
        release_final_closure_publish_report["final_closure_publish_should_notify"]
    )
    final_closure_publish_requires_manual_action = bool(
        release_final_closure_publish_report["final_closure_publish_requires_manual_action"]
    )
    final_closure_publish_channel = str(
        release_final_closure_publish_report["final_closure_publish_channel"]
    )

    reason_codes = list(release_final_closure_publish_report["reason_codes"])
    structural_issues = list(release_final_closure_publish_report["structural_issues"])
    missing_artifacts = list(release_final_closure_publish_report["missing_artifacts"])
    evidence_manifest = list(release_final_closure_publish_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_final_archive_evidence_missing")

    expected = {
        "published": (
            "announce_release_closed",
            0,
            True,
            False,
            "release",
        ),
        "published_with_follow_up": (
            "announce_release_closed_with_follow_up",
            None,
            True,
            False,
            "follow_up",
        ),
        "blocked": (
            "announce_release_blocker",
            None,
            True,
            True,
            "blocker",
        ),
        "contract_failed": (
            "abort_publish",
            None,
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
        expected_channel,
    ) = expected[final_closure_publish_status]

    if final_closure_publish_decision != expected_decision:
        structural_issues.append("final_closure_publish_decision_mismatch")
    if final_closure_publish_should_notify != expected_should_notify:
        structural_issues.append("final_closure_publish_should_notify_mismatch")
    if final_closure_publish_requires_manual_action != expected_requires_manual_action:
        structural_issues.append("final_closure_publish_requires_manual_action_mismatch")
    if final_closure_publish_channel != expected_channel:
        structural_issues.append("final_closure_publish_channel_mismatch")
    if expected_exit_code == 0 and final_closure_publish_exit_code != 0:
        structural_issues.append("final_closure_publish_exit_code_mismatch_published")
    if expected_exit_code is None and final_closure_publish_exit_code == 0:
        structural_issues.append("final_closure_publish_exit_code_mismatch_non_published")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        archive_status = "contract_failed"
        archive_decision = "abort_archive"
        archive_exit_code = max(1, final_closure_publish_exit_code)
        archive_should_publish = False
        archive_requires_manual_action = True
        archive_channel = "blocker"
        reason_codes.extend(structural_issues)
    elif final_closure_publish_status == "published":
        archive_status = "archived"
        archive_decision = "archive_release_closed"
        archive_exit_code = 0
        archive_should_publish = True
        archive_requires_manual_action = False
        archive_channel = "release"
        reason_codes = ["release_final_archive_archived"]
    elif final_closure_publish_status == "published_with_follow_up":
        archive_status = "archived_with_follow_up"
        archive_decision = "archive_release_closed_with_follow_up"
        archive_exit_code = max(1, final_closure_publish_exit_code)
        archive_should_publish = True
        archive_requires_manual_action = False
        archive_channel = "follow_up"
        reason_codes.append("release_final_archive_archived_with_follow_up")
    elif final_closure_publish_status == "blocked":
        archive_status = "blocked"
        archive_decision = "archive_release_blocker"
        archive_exit_code = max(1, final_closure_publish_exit_code)
        archive_should_publish = False
        archive_requires_manual_action = True
        archive_channel = "blocker"
        reason_codes.append("release_final_archive_blocked")
    else:
        archive_status = "contract_failed"
        archive_decision = "abort_archive"
        archive_exit_code = max(1, final_closure_publish_exit_code)
        archive_should_publish = False
        archive_requires_manual_action = True
        archive_channel = "blocker"
        reason_codes.append("release_final_archive_upstream_contract_failed")

    if archive_status not in ALLOWED_RELEASE_FINAL_ARCHIVE_STATUSES:
        raise ValueError("internal: unsupported release_final_archive_status computed")
    if archive_decision not in ALLOWED_RELEASE_FINAL_ARCHIVE_DECISIONS:
        raise ValueError("internal: unsupported release_final_archive_decision computed")
    if archive_channel not in ALLOWED_RELEASE_FINAL_ARCHIVE_CHANNELS:
        raise ValueError("internal: unsupported release_final_archive_channel computed")

    reason_codes = _unique(reason_codes)
    summary = (
        f"release_final_closure_publish_status={final_closure_publish_status} "
        f"release_final_archive_status={archive_status} "
        f"release_final_archive_decision={archive_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_final_closure_publish_report": str(source_path),
        "source_release_final_closure_report": str(
            release_final_closure_publish_report["source_release_final_closure_report"]
        ),
        "source_release_final_handoff_report": str(
            release_final_closure_publish_report["source_release_final_handoff_report"]
        ),
        "source_release_final_terminal_publish_report": str(
            release_final_closure_publish_report["source_release_final_terminal_publish_report"]
        ),
        "source_release_final_outcome_report": str(
            release_final_closure_publish_report["source_release_final_outcome_report"]
        ),
        "source_release_delivery_final_verdict_report": str(
            release_final_closure_publish_report["source_release_delivery_final_verdict_report"]
        ),
        "source_release_follow_up_final_verdict_report": str(
            release_final_closure_publish_report["source_release_follow_up_final_verdict_report"]
        ),
        "release_delivery_final_verdict_status": str(
            release_final_closure_publish_report["release_delivery_final_verdict_status"]
        ),
        "release_delivery_final_verdict_decision": str(
            release_final_closure_publish_report["release_delivery_final_verdict_decision"]
        ),
        "release_delivery_final_verdict_exit_code": int(
            release_final_closure_publish_report["release_delivery_final_verdict_exit_code"]
        ),
        "release_follow_up_final_verdict_status": str(
            release_final_closure_publish_report["release_follow_up_final_verdict_status"]
        ),
        "release_follow_up_final_verdict_decision": str(
            release_final_closure_publish_report["release_follow_up_final_verdict_decision"]
        ),
        "release_follow_up_final_verdict_exit_code": int(
            release_final_closure_publish_report["release_follow_up_final_verdict_exit_code"]
        ),
        "release_final_outcome_status": str(
            release_final_closure_publish_report["release_final_outcome_status"]
        ),
        "release_final_outcome_decision": str(
            release_final_closure_publish_report["release_final_outcome_decision"]
        ),
        "release_final_outcome_exit_code": int(
            release_final_closure_publish_report["release_final_outcome_exit_code"]
        ),
        "release_final_terminal_publish_status": str(
            release_final_closure_publish_report["release_final_terminal_publish_status"]
        ),
        "release_final_terminal_publish_decision": str(
            release_final_closure_publish_report["release_final_terminal_publish_decision"]
        ),
        "release_final_terminal_publish_exit_code": int(
            release_final_closure_publish_report["release_final_terminal_publish_exit_code"]
        ),
        "release_final_handoff_status": str(
            release_final_closure_publish_report["release_final_handoff_status"]
        ),
        "release_final_handoff_decision": str(
            release_final_closure_publish_report["release_final_handoff_decision"]
        ),
        "release_final_handoff_exit_code": int(
            release_final_closure_publish_report["release_final_handoff_exit_code"]
        ),
        "release_final_closure_status": str(
            release_final_closure_publish_report["release_final_closure_status"]
        ),
        "release_final_closure_decision": str(
            release_final_closure_publish_report["release_final_closure_decision"]
        ),
        "release_final_closure_exit_code": int(
            release_final_closure_publish_report["release_final_closure_exit_code"]
        ),
        "release_final_closure_publish_status": final_closure_publish_status,
        "release_final_closure_publish_decision": final_closure_publish_decision,
        "release_final_closure_publish_exit_code": final_closure_publish_exit_code,
        "release_run_id": release_final_closure_publish_report["release_run_id"],
        "release_run_url": str(release_final_closure_publish_report["release_run_url"]),
        "follow_up_queue_url": str(release_final_closure_publish_report["follow_up_queue_url"]),
        "final_archive_should_publish": archive_should_publish,
        "final_archive_requires_manual_action": archive_requires_manual_action,
        "final_archive_channel": archive_channel,
        "release_final_archive_status": archive_status,
        "release_final_archive_decision": archive_decision,
        "release_final_archive_exit_code": archive_exit_code,
        "release_final_archive_summary": summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Final Archive Report",
        "",
        f"- Release Final Archive Status: **{str(payload['release_final_archive_status']).upper()}**",
        f"- Release Final Archive Decision: `{payload['release_final_archive_decision']}`",
        f"- Release Final Archive Exit Code: `{payload['release_final_archive_exit_code']}`",
        f"- Final Archive Should Publish: `{payload['final_archive_should_publish']}`",
        (
            f"- Final Archive Requires Manual Action: "
            f"`{payload['final_archive_requires_manual_action']}`"
        ),
        f"- Final Archive Channel: `{payload['final_archive_channel']}`",
        f"- Release Final Closure Publish Status: `{payload['release_final_closure_publish_status']}`",
        f"- Follow-Up Queue URL: `{payload['follow_up_queue_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_final_archive_summary']}",
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
        "workflow_release_final_archive_status": str(payload["release_final_archive_status"]),
        "workflow_release_final_archive_decision": str(payload["release_final_archive_decision"]),
        "workflow_release_final_archive_exit_code": str(payload["release_final_archive_exit_code"]),
        "workflow_release_final_archive_should_publish": (
            "true" if payload["final_archive_should_publish"] else "false"
        ),
        "workflow_release_final_archive_requires_manual_action": (
            "true" if payload["final_archive_requires_manual_action"] else "false"
        ),
        "workflow_release_final_archive_channel": str(payload["final_archive_channel"]),
        "workflow_release_final_archive_follow_up_queue_url": str(payload["follow_up_queue_url"]),
        "workflow_release_final_archive_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_final_archive_run_url": str(payload["release_run_url"]),
        "workflow_release_final_archive_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_final_archive_report_json": str(output_json),
        "workflow_release_final_archive_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release final archive contract "
            "from P2-52 release final closure publish report"
        )
    )
    parser.add_argument(
        "--release-final-closure-publish-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json",
        help="P2-52 release final closure publish report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json",
        help="Output release final archive JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.md",
        help="Output release final archive markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release final archive JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    release_final_closure_publish_report_path = Path(args.release_final_closure_publish_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        release_final_closure_publish_report = load_release_final_closure_publish_report(
            release_final_closure_publish_report_path
        )
        payload = build_release_final_archive_payload(
            release_final_closure_publish_report,
            source_path=release_final_closure_publish_report_path.resolve(),
        )
    except ValueError as exc:
        print(
            "[p2-linux-ci-workflow-release-final-archive-gate] "
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
        print(f"release final archive json: {output_json_path}")
        print(f"release final archive markdown: {output_markdown_path}")

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
        "release final archive summary: "
        f"release_final_archive_status={payload['release_final_archive_status']} "
        f"release_final_archive_decision={payload['release_final_archive_decision']} "
        f"release_final_archive_exit_code={payload['release_final_archive_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_final_archive_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
