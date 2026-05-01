"""Phase 2 card P2-38 gate for Linux CI workflow release verdict closure.

This script consumes the P2-37 release archive artifact and converges
the terminal release verdict contract:
1) validate release archive contract consistency,
2) normalize terminal release verdict for CI exit semantics,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_ARCHIVE_STATUSES: set[str] = {"ready", "pending", "failed", "contract_failed"}
ALLOWED_RELEASE_ARCHIVE_DECISIONS: set[str] = {"publish", "hold", "block"}
ALLOWED_RELEASE_VERDICT_STATUSES: set[str] = {
    "published",
    "awaiting_archive",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_VERDICT_DECISIONS: set[str] = {"ship", "hold", "block"}


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


def load_release_archive_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release archive report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release archive payload must be object")

    required_fields = (
        "release_archive_status",
        "release_archive_decision",
        "release_archive_exit_code",
        "should_publish_archive",
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

    release_archive_status = _coerce_str(
        payload["release_archive_status"],
        field="release_archive_status",
        path=path,
    )
    if release_archive_status not in ALLOWED_RELEASE_ARCHIVE_STATUSES:
        raise ValueError(
            f"{path}: field 'release_archive_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_ARCHIVE_STATUSES)}"
        )

    release_archive_decision = _coerce_str(
        payload["release_archive_decision"],
        field="release_archive_decision",
        path=path,
    )
    if release_archive_decision not in ALLOWED_RELEASE_ARCHIVE_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_archive_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_ARCHIVE_DECISIONS)}"
        )

    release_archive_exit_code = _coerce_int(
        payload["release_archive_exit_code"],
        field="release_archive_exit_code",
        path=path,
    )
    if release_archive_exit_code < 0:
        raise ValueError(f"{path}: field 'release_archive_exit_code' must be >= 0")

    should_publish_archive = _coerce_bool(
        payload["should_publish_archive"],
        field="should_publish_archive",
        path=path,
    )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(
            release_run_id_raw,
            field="release_run_id",
            path=path,
        )
        if release_run_id < 1:
            raise ValueError(f"{path}: field 'release_run_id' must be >= 1 when present")

    release_run_url = _coerce_str(payload["release_run_url"], field="release_run_url", path=path)
    reason_codes = _coerce_str_list(payload["reason_codes"], field="reason_codes", path=path)
    structural_issues = _coerce_str_list(
        payload["structural_issues"],
        field="structural_issues",
        path=path,
    )
    missing_artifacts = _coerce_str_list(
        payload["missing_artifacts"],
        field="missing_artifacts",
        path=path,
    )

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
        "source_release_closure_report": _coerce_str(
            payload.get("source_release_closure_report", ""),
            field="source_release_closure_report",
            path=path,
        ),
        "release_archive_status": release_archive_status,
        "release_archive_decision": release_archive_decision,
        "release_archive_exit_code": release_archive_exit_code,
        "should_publish_archive": should_publish_archive,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def build_release_verdict_payload(
    release_archive_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    release_archive_status = str(release_archive_report["release_archive_status"])
    release_archive_decision = str(release_archive_report["release_archive_decision"])
    release_archive_exit_code = int(release_archive_report["release_archive_exit_code"])
    should_publish_archive = bool(release_archive_report["should_publish_archive"])

    reason_codes = list(release_archive_report["reason_codes"])
    structural_issues = list(release_archive_report["structural_issues"])
    missing_artifacts = list(release_archive_report["missing_artifacts"])
    evidence_manifest = list(release_archive_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_verdict_evidence_missing")

    if release_archive_status == "ready":
        if release_archive_decision != "publish":
            structural_issues.append("release_archive_decision_mismatch_ready")
        if release_archive_exit_code != 0:
            structural_issues.append("release_archive_exit_code_mismatch_ready")
        if not should_publish_archive:
            structural_issues.append("should_publish_archive_mismatch_ready")
    elif release_archive_status == "pending":
        if release_archive_decision != "hold":
            structural_issues.append("release_archive_decision_mismatch_pending")
        if should_publish_archive:
            structural_issues.append("should_publish_archive_mismatch_pending")
    elif release_archive_status in {"failed", "contract_failed"}:
        if release_archive_decision != "block":
            structural_issues.append("release_archive_decision_mismatch_failed")
        if should_publish_archive:
            structural_issues.append("should_publish_archive_mismatch_failed")
        if release_archive_exit_code == 0:
            structural_issues.append("release_archive_exit_code_mismatch_failed")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        release_verdict_status = "contract_failed"
        release_verdict_decision = "block"
        release_verdict_exit_code = 1
        should_ship_release = False
        should_open_incident = True
        reason_codes.extend(structural_issues)
    elif release_archive_status == "ready":
        release_verdict_status = "published"
        release_verdict_decision = "ship"
        release_verdict_exit_code = 0
        should_ship_release = True
        should_open_incident = False
        reason_codes = ["release_verdict_published"]
    elif release_archive_status == "pending":
        release_verdict_status = "awaiting_archive"
        release_verdict_decision = "hold"
        release_verdict_exit_code = max(1, release_archive_exit_code)
        should_ship_release = False
        should_open_incident = False
    else:
        release_verdict_status = "blocked"
        release_verdict_decision = "block"
        release_verdict_exit_code = max(1, release_archive_exit_code)
        should_ship_release = False
        should_open_incident = True

    if release_verdict_status not in ALLOWED_RELEASE_VERDICT_STATUSES:
        raise ValueError("internal: unsupported release_verdict_status computed")
    if release_verdict_decision not in ALLOWED_RELEASE_VERDICT_DECISIONS:
        raise ValueError("internal: unsupported release_verdict_decision computed")

    release_verdict_summary = (
        f"release_archive_status={release_archive_status} "
        f"release_verdict_status={release_verdict_status} "
        f"release_verdict_decision={release_verdict_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_archive_report": str(source_path),
        "release_archive_status": release_archive_status,
        "release_archive_decision": release_archive_decision,
        "release_archive_exit_code": release_archive_exit_code,
        "release_verdict_status": release_verdict_status,
        "release_verdict_decision": release_verdict_decision,
        "release_verdict_exit_code": int(release_verdict_exit_code),
        "should_publish_archive": should_publish_archive,
        "should_ship_release": should_ship_release,
        "should_open_incident": should_open_incident,
        "release_run_id": release_archive_report["release_run_id"],
        "release_run_url": str(release_archive_report["release_run_url"]),
        "release_verdict_summary": release_verdict_summary,
        "reason_codes": _unique(reason_codes),
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Verdict Report",
        "",
        f"- Release Verdict Status: **{str(payload['release_verdict_status']).upper()}**",
        f"- Release Verdict Decision: `{payload['release_verdict_decision']}`",
        f"- Should Ship Release: `{payload['should_ship_release']}`",
        f"- Should Open Incident: `{payload['should_open_incident']}`",
        f"- Release Verdict Exit Code: `{payload['release_verdict_exit_code']}`",
        f"- Release Archive Status: `{payload['release_archive_status']}`",
        f"- Release Archive Decision: `{payload['release_archive_decision']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_verdict_summary']}",
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
        "workflow_release_verdict_status": str(payload["release_verdict_status"]),
        "workflow_release_verdict_decision": str(payload["release_verdict_decision"]),
        "workflow_release_verdict_should_ship_release": (
            "true" if payload["should_ship_release"] else "false"
        ),
        "workflow_release_verdict_should_open_incident": (
            "true" if payload["should_open_incident"] else "false"
        ),
        "workflow_release_verdict_exit_code": str(payload["release_verdict_exit_code"]),
        "workflow_release_verdict_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_verdict_run_url": str(payload["release_run_url"]),
        "workflow_release_verdict_missing_artifacts": json.dumps(
            payload["missing_artifacts"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_verdict_report_json": str(output_json),
        "workflow_release_verdict_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release verdict contract from P2-37 release archive report"
        )
    )
    parser.add_argument(
        "--release-archive-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_archive.json",
        help="P2-37 release archive report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_verdict.json",
        help="Output release verdict JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_verdict.md",
        help="Output release verdict markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release verdict JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    release_archive_report_path = Path(args.release_archive_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        release_archive_report = load_release_archive_report(release_archive_report_path)
        payload = build_release_verdict_payload(
            release_archive_report,
            source_path=release_archive_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-verdict-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release verdict json: {output_json_path}")
        print(f"release verdict markdown: {output_markdown_path}")

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
        "release verdict summary: "
        f"release_verdict_status={payload['release_verdict_status']} "
        f"release_verdict_decision={payload['release_verdict_decision']} "
        f"release_verdict_exit_code={payload['release_verdict_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_verdict_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
