"""Phase 2 card P2-41 gate for Linux CI workflow release delivery closure.

This script consumes the P2-40 release terminal verdict artifact and converges
the final delivery contract:
1) validate release terminal verdict + incident consistency,
2) normalize final ship/hold/escalate/block delivery semantics,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_TERMINAL_VERDICT_STATUSES: set[str] = {
    "released",
    "awaiting_archive",
    "blocked_incident_ready_dry_run",
    "blocked_incident_dispatched",
    "blocked_incident_failed",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_TERMINAL_VERDICT_DECISIONS: set[str] = {"ship", "hold", "escalate", "block"}
ALLOWED_INCIDENT_DISPATCH_STATUSES: set[str] = {
    "not_required",
    "ready_dry_run",
    "dispatched",
    "dispatch_failed",
    "contract_failed",
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


def load_release_terminal_verdict_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release terminal verdict report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release terminal verdict payload must be object")

    required_fields = (
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

    terminal_verdict_status = _coerce_str(
        payload["release_terminal_verdict_status"],
        field="release_terminal_verdict_status",
        path=path,
    )
    if terminal_verdict_status not in ALLOWED_RELEASE_TERMINAL_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_terminal_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_TERMINAL_VERDICT_STATUSES)}"
        )

    terminal_verdict_decision = _coerce_str(
        payload["release_terminal_verdict_decision"],
        field="release_terminal_verdict_decision",
        path=path,
    )
    if terminal_verdict_decision not in ALLOWED_RELEASE_TERMINAL_VERDICT_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_terminal_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_TERMINAL_VERDICT_DECISIONS)}"
        )

    terminal_verdict_exit_code = _coerce_int(
        payload["release_terminal_verdict_exit_code"],
        field="release_terminal_verdict_exit_code",
        path=path,
    )
    if terminal_verdict_exit_code < 0:
        raise ValueError(f"{path}: field 'release_terminal_verdict_exit_code' must be >= 0")

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

    release_archive_exit_code = _coerce_int(
        payload["release_archive_exit_code"],
        field="release_archive_exit_code",
        path=path,
    )
    if release_archive_exit_code < 0:
        raise ValueError(f"{path}: field 'release_archive_exit_code' must be >= 0")

    release_verdict_exit_code = _coerce_int(
        payload["release_verdict_exit_code"],
        field="release_verdict_exit_code",
        path=path,
    )
    if release_verdict_exit_code < 0:
        raise ValueError(f"{path}: field 'release_verdict_exit_code' must be >= 0")

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
        "release_archive_exit_code": release_archive_exit_code,
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
        "release_verdict_exit_code": release_verdict_exit_code,
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
        "incident_url": _coerce_str(payload["incident_url"], field="incident_url", path=path),
        "release_terminal_verdict_status": terminal_verdict_status,
        "release_terminal_verdict_decision": terminal_verdict_decision,
        "release_terminal_verdict_exit_code": terminal_verdict_exit_code,
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


def build_release_delivery_payload(
    terminal_verdict_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    terminal_verdict_status = str(terminal_verdict_report["release_terminal_verdict_status"])
    terminal_verdict_decision = str(terminal_verdict_report["release_terminal_verdict_decision"])
    terminal_verdict_exit_code = int(terminal_verdict_report["release_terminal_verdict_exit_code"])
    terminal_should_ship_release = bool(terminal_verdict_report["terminal_should_ship_release"])
    terminal_requires_follow_up = bool(terminal_verdict_report["terminal_requires_follow_up"])
    should_dispatch_incident = bool(terminal_verdict_report["should_dispatch_incident"])
    incident_dispatch_status = str(terminal_verdict_report["incident_dispatch_status"])
    incident_dispatch_exit_code = int(terminal_verdict_report["incident_dispatch_exit_code"])

    reason_codes = list(terminal_verdict_report["reason_codes"])
    structural_issues = list(terminal_verdict_report["structural_issues"])
    missing_artifacts = list(terminal_verdict_report["missing_artifacts"])
    evidence_manifest = list(terminal_verdict_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_delivery_evidence_missing")

    if terminal_verdict_status == "released":
        if terminal_verdict_decision != "ship":
            structural_issues.append("terminal_decision_mismatch_released")
        if terminal_verdict_exit_code != 0:
            structural_issues.append("terminal_exit_code_mismatch_released")
        if not terminal_should_ship_release:
            structural_issues.append("terminal_should_ship_mismatch_released")
        if terminal_requires_follow_up:
            structural_issues.append("terminal_follow_up_mismatch_released")
        if incident_dispatch_status != "not_required":
            structural_issues.append("incident_status_mismatch_released")
    elif terminal_verdict_status == "awaiting_archive":
        if terminal_verdict_decision != "hold":
            structural_issues.append("terminal_decision_mismatch_awaiting_archive")
        if terminal_should_ship_release:
            structural_issues.append("terminal_should_ship_mismatch_awaiting_archive")
    elif terminal_verdict_status == "blocked_incident_ready_dry_run":
        if terminal_verdict_decision != "escalate":
            structural_issues.append("terminal_decision_mismatch_incident_ready_dry_run")
        if incident_dispatch_status != "ready_dry_run":
            structural_issues.append("incident_status_mismatch_incident_ready_dry_run")
        if not should_dispatch_incident:
            structural_issues.append("should_dispatch_incident_mismatch_ready_dry_run")
    elif terminal_verdict_status == "blocked_incident_dispatched":
        if terminal_verdict_decision != "escalate":
            structural_issues.append("terminal_decision_mismatch_incident_dispatched")
        if incident_dispatch_status != "dispatched":
            structural_issues.append("incident_status_mismatch_incident_dispatched")
    elif terminal_verdict_status == "blocked_incident_failed":
        if terminal_verdict_decision != "block":
            structural_issues.append("terminal_decision_mismatch_incident_failed")
        if incident_dispatch_status != "dispatch_failed":
            structural_issues.append("incident_status_mismatch_incident_failed")
    elif terminal_verdict_status == "blocked":
        if terminal_verdict_decision != "block":
            structural_issues.append("terminal_decision_mismatch_blocked")
    elif terminal_verdict_status == "contract_failed":
        if terminal_verdict_decision != "block":
            structural_issues.append("terminal_decision_mismatch_contract_failed")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        release_delivery_status = "contract_failed"
        release_delivery_decision = "block"
        release_delivery_exit_code = 1
        delivery_should_ship_release = False
        delivery_requires_human_action = True
        delivery_should_announce_blocker = True
        reason_codes.extend(structural_issues)
    elif terminal_verdict_status == "released":
        release_delivery_status = "shipped"
        release_delivery_decision = "deliver"
        release_delivery_exit_code = 0
        delivery_should_ship_release = True
        delivery_requires_human_action = False
        delivery_should_announce_blocker = False
        reason_codes = ["release_delivery_shipped"]
    elif terminal_verdict_status == "awaiting_archive":
        release_delivery_status = "pending_follow_up"
        release_delivery_decision = "hold"
        release_delivery_exit_code = max(1, terminal_verdict_exit_code)
        delivery_should_ship_release = False
        delivery_requires_human_action = True
        delivery_should_announce_blocker = True
    elif terminal_verdict_status in {"blocked_incident_ready_dry_run", "blocked_incident_dispatched"}:
        release_delivery_status = "blocked_incident"
        release_delivery_decision = "escalate"
        release_delivery_exit_code = max(1, terminal_verdict_exit_code, incident_dispatch_exit_code)
        delivery_should_ship_release = False
        delivery_requires_human_action = True
        delivery_should_announce_blocker = True
        reason_codes.append("release_delivery_incident_escalation_required")
    elif terminal_verdict_status == "blocked_incident_failed":
        release_delivery_status = "blocked_incident_failed"
        release_delivery_decision = "block"
        release_delivery_exit_code = max(1, incident_dispatch_exit_code, terminal_verdict_exit_code)
        delivery_should_ship_release = False
        delivery_requires_human_action = True
        delivery_should_announce_blocker = True
        reason_codes.append("release_delivery_incident_dispatch_failed")
    else:
        release_delivery_status = "blocked"
        release_delivery_decision = "hold"
        release_delivery_exit_code = max(1, terminal_verdict_exit_code)
        delivery_should_ship_release = False
        delivery_requires_human_action = True
        delivery_should_announce_blocker = True
        reason_codes.append("release_delivery_blocked")

    if release_delivery_status not in ALLOWED_RELEASE_DELIVERY_STATUSES:
        raise ValueError("internal: unsupported release_delivery_status computed")
    if release_delivery_decision not in ALLOWED_RELEASE_DELIVERY_DECISIONS:
        raise ValueError("internal: unsupported release_delivery_decision computed")

    reason_codes = _unique(reason_codes)
    release_delivery_summary = (
        f"release_terminal_verdict_status={terminal_verdict_status} "
        f"release_delivery_status={release_delivery_status} "
        f"release_delivery_decision={release_delivery_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_terminal_verdict_report": str(source_path),
        "source_release_incident_report": str(terminal_verdict_report["source_release_incident_report"]),
        "source_release_verdict_report": str(terminal_verdict_report["source_release_verdict_report"]),
        "source_release_archive_report": str(terminal_verdict_report["source_release_archive_report"]),
        "release_archive_status": str(terminal_verdict_report["release_archive_status"]),
        "release_archive_decision": str(terminal_verdict_report["release_archive_decision"]),
        "release_archive_exit_code": int(terminal_verdict_report["release_archive_exit_code"]),
        "should_publish_archive": bool(terminal_verdict_report["should_publish_archive"]),
        "release_verdict_status": str(terminal_verdict_report["release_verdict_status"]),
        "release_verdict_decision": str(terminal_verdict_report["release_verdict_decision"]),
        "release_verdict_exit_code": int(terminal_verdict_report["release_verdict_exit_code"]),
        "should_ship_release": bool(terminal_verdict_report["should_ship_release"]),
        "should_open_incident": bool(terminal_verdict_report["should_open_incident"]),
        "should_dispatch_incident": should_dispatch_incident,
        "incident_dispatch_status": incident_dispatch_status,
        "incident_dispatch_exit_code": incident_dispatch_exit_code,
        "incident_dispatch_attempted": bool(terminal_verdict_report["incident_dispatch_attempted"]),
        "incident_url": str(terminal_verdict_report["incident_url"]),
        "release_terminal_verdict_status": terminal_verdict_status,
        "release_terminal_verdict_decision": terminal_verdict_decision,
        "release_terminal_verdict_exit_code": terminal_verdict_exit_code,
        "terminal_should_ship_release": terminal_should_ship_release,
        "terminal_requires_follow_up": terminal_requires_follow_up,
        "terminal_incident_linked": bool(terminal_verdict_report["terminal_incident_linked"]),
        "release_delivery_status": release_delivery_status,
        "release_delivery_decision": release_delivery_decision,
        "release_delivery_exit_code": int(release_delivery_exit_code),
        "delivery_should_ship_release": delivery_should_ship_release,
        "delivery_requires_human_action": delivery_requires_human_action,
        "delivery_should_announce_blocker": delivery_should_announce_blocker,
        "release_run_id": terminal_verdict_report["release_run_id"],
        "release_run_url": str(terminal_verdict_report["release_run_url"]),
        "release_delivery_summary": release_delivery_summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Delivery Report",
        "",
        f"- Release Delivery Status: **{str(payload['release_delivery_status']).upper()}**",
        f"- Release Delivery Decision: `{payload['release_delivery_decision']}`",
        f"- Release Delivery Exit Code: `{payload['release_delivery_exit_code']}`",
        f"- Delivery Should Ship Release: `{payload['delivery_should_ship_release']}`",
        f"- Delivery Requires Human Action: `{payload['delivery_requires_human_action']}`",
        f"- Delivery Should Announce Blocker: `{payload['delivery_should_announce_blocker']}`",
        f"- Release Terminal Verdict Status: `{payload['release_terminal_verdict_status']}`",
        f"- Incident Dispatch Status: `{payload['incident_dispatch_status']}`",
        f"- Incident URL: `{payload['incident_url']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_delivery_summary']}",
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
        "workflow_release_delivery_status": str(payload["release_delivery_status"]),
        "workflow_release_delivery_decision": str(payload["release_delivery_decision"]),
        "workflow_release_delivery_exit_code": str(payload["release_delivery_exit_code"]),
        "workflow_release_delivery_should_ship_release": (
            "true" if payload["delivery_should_ship_release"] else "false"
        ),
        "workflow_release_delivery_requires_human_action": (
            "true" if payload["delivery_requires_human_action"] else "false"
        ),
        "workflow_release_delivery_should_announce_blocker": (
            "true" if payload["delivery_should_announce_blocker"] else "false"
        ),
        "workflow_release_delivery_terminal_verdict_status": str(
            payload["release_terminal_verdict_status"]
        ),
        "workflow_release_delivery_incident_status": str(payload["incident_dispatch_status"]),
        "workflow_release_delivery_incident_url": str(payload["incident_url"]),
        "workflow_release_delivery_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_delivery_run_url": str(payload["release_run_url"]),
        "workflow_release_delivery_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_delivery_report_json": str(output_json),
        "workflow_release_delivery_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release delivery contract from "
            "P2-40 release terminal verdict report"
        )
    )
    parser.add_argument(
        "--release-terminal-verdict-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json",
        help="P2-40 release terminal verdict report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery.json",
        help="Output release delivery JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery.md",
        help="Output release delivery markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release delivery JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    terminal_verdict_report_path = Path(args.release_terminal_verdict_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        terminal_verdict_report = load_release_terminal_verdict_report(terminal_verdict_report_path)
        payload = build_release_delivery_payload(
            terminal_verdict_report,
            source_path=terminal_verdict_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-delivery-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release delivery json: {output_json_path}")
        print(f"release delivery markdown: {output_markdown_path}")

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
        "release delivery summary: "
        f"release_delivery_status={payload['release_delivery_status']} "
        f"release_delivery_decision={payload['release_delivery_decision']} "
        f"release_delivery_exit_code={payload['release_delivery_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_delivery_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

