"""Phase 2 card P2-37 gate for Linux CI workflow release evidence archive.

This script consumes the P2-36 release closure artifact and converges
the terminal release archive contract:
1) validate release closure contract consistency,
2) collect release evidence manifest from upstream source reports,
3) emit JSON/Markdown report + optional GitHub outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RELEASE_CLOSURE_STATUSES: set[str] = {"closed", "pending", "failed", "contract_failed"}
ALLOWED_RELEASE_CLOSURE_DECISIONS: set[str] = {"ship", "hold", "rollback"}
ALLOWED_RELEASE_ARCHIVE_STATUSES: set[str] = {"ready", "pending", "failed", "contract_failed"}
ALLOWED_RELEASE_ARCHIVE_DECISIONS: set[str] = {"publish", "hold", "block"}

SOURCE_FIELDS: tuple[str, ...] = (
    "source_release_finalization_report",
    "source_release_terminal_publish_report",
    "source_release_completion_report",
    "source_release_trace_report",
    "source_release_trigger_report",
    "source_release_handoff_report",
    "source_terminal_publish_report",
    "source_dispatch_completion_report",
    "source_dispatch_trace_report",
    "source_dispatch_execution_report",
    "source_dispatch_report",
)


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


def load_release_closure_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release closure report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release closure payload must be object")

    required_fields = (
        "release_closure_status",
        "release_closure_decision",
        "release_closure_exit_code",
        "should_close_release",
        "should_notify",
        "release_run_id",
        "release_run_url",
        "reason_codes",
        "structural_issues",
        "missing_artifacts",
        *SOURCE_FIELDS,
    )
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    release_closure_status = _coerce_str(
        payload["release_closure_status"],
        field="release_closure_status",
        path=path,
    )
    if release_closure_status not in ALLOWED_RELEASE_CLOSURE_STATUSES:
        raise ValueError(
            f"{path}: field 'release_closure_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_CLOSURE_STATUSES)}"
        )

    release_closure_decision = _coerce_str(
        payload["release_closure_decision"],
        field="release_closure_decision",
        path=path,
    )
    if release_closure_decision not in ALLOWED_RELEASE_CLOSURE_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_closure_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_CLOSURE_DECISIONS)}"
        )

    release_closure_exit_code = _coerce_int(
        payload["release_closure_exit_code"],
        field="release_closure_exit_code",
        path=path,
    )
    if release_closure_exit_code < 0:
        raise ValueError(f"{path}: field 'release_closure_exit_code' must be >= 0")

    should_close_release = _coerce_bool(
        payload["should_close_release"],
        field="should_close_release",
        path=path,
    )
    should_notify = _coerce_bool(
        payload["should_notify"],
        field="should_notify",
        path=path,
    )

    release_run_id_raw = payload["release_run_id"]
    if release_run_id_raw is None:
        release_run_id = None
    else:
        release_run_id = _coerce_int(release_run_id_raw, field="release_run_id", path=path)
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

    source_paths = {
        field: _coerce_str(payload[field], field=field, path=path)
        for field in SOURCE_FIELDS
    }

    return {
        "generated_at": payload.get("generated_at"),
        "release_closure_status": release_closure_status,
        "release_closure_decision": release_closure_decision,
        "release_closure_exit_code": release_closure_exit_code,
        "should_close_release": should_close_release,
        "should_notify": should_notify,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        **source_paths,
    }


def _build_evidence_manifest(release_closure_report: dict[str, Any], source_path: Path) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    seen: set[str] = set()

    evidence_paths = [str(source_path)] + [str(release_closure_report[field]) for field in SOURCE_FIELDS]
    for evidence_path in evidence_paths:
        if evidence_path in seen:
            continue
        seen.add(evidence_path)
        evidence_file = Path(evidence_path)
        manifest.append(
            {
                "path": evidence_path,
                "exists": evidence_file.is_file(),
            }
        )
    return manifest


def build_release_archive_payload(
    release_closure_report: dict[str, Any], *, source_path: Path
) -> dict[str, Any]:
    release_closure_status = str(release_closure_report["release_closure_status"])
    release_closure_decision = str(release_closure_report["release_closure_decision"])
    release_closure_exit_code = int(release_closure_report["release_closure_exit_code"])
    should_close_release = bool(release_closure_report["should_close_release"])
    should_notify = bool(release_closure_report["should_notify"])

    reason_codes = list(release_closure_report["reason_codes"])
    structural_issues = list(release_closure_report["structural_issues"])
    missing_artifacts = list(release_closure_report["missing_artifacts"])

    if release_closure_status == "closed":
        if release_closure_decision != "ship":
            structural_issues.append("release_closure_decision_mismatch_closed")
        if release_closure_exit_code != 0:
            structural_issues.append("release_closure_exit_code_mismatch_closed")
        if not should_close_release:
            structural_issues.append("should_close_release_mismatch_closed")
    elif release_closure_status == "pending":
        if release_closure_decision != "hold":
            structural_issues.append("release_closure_decision_mismatch_pending")
        if should_close_release:
            structural_issues.append("should_close_release_mismatch_pending")
    elif release_closure_status in {"failed", "contract_failed"}:
        if release_closure_decision != "rollback":
            structural_issues.append("release_closure_decision_mismatch_failed")
        if should_close_release:
            structural_issues.append("should_close_release_mismatch_failed")
        if release_closure_exit_code == 0:
            structural_issues.append("release_closure_exit_code_mismatch_failed")

    evidence_manifest = _build_evidence_manifest(release_closure_report, source_path)
    manifest_missing_paths = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if manifest_missing_paths:
        missing_artifacts.extend(manifest_missing_paths)
        reason_codes.append("release_evidence_missing")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)

    if structural_issues or missing_artifacts:
        release_archive_status = "contract_failed"
        release_archive_decision = "block"
        release_archive_exit_code = 1
        should_publish_archive = False
        reason_codes.extend(structural_issues)
    elif release_closure_status == "closed":
        release_archive_status = "ready"
        release_archive_decision = "publish"
        release_archive_exit_code = 0
        should_publish_archive = True
        reason_codes = ["release_archive_ready"]
    elif release_closure_status == "pending":
        release_archive_status = "pending"
        release_archive_decision = "hold"
        release_archive_exit_code = max(1, release_closure_exit_code)
        should_publish_archive = False
    elif release_closure_status == "failed":
        release_archive_status = "failed"
        release_archive_decision = "block"
        release_archive_exit_code = max(1, release_closure_exit_code)
        should_publish_archive = False
    else:
        release_archive_status = "contract_failed"
        release_archive_decision = "block"
        release_archive_exit_code = 1
        should_publish_archive = False

    if release_archive_status not in ALLOWED_RELEASE_ARCHIVE_STATUSES:
        raise ValueError("internal: unsupported release_archive_status computed")
    if release_archive_decision not in ALLOWED_RELEASE_ARCHIVE_DECISIONS:
        raise ValueError("internal: unsupported release_archive_decision computed")

    release_archive_summary = (
        f"release_closure_status={release_closure_status} "
        f"release_archive_status={release_archive_status} "
        f"release_archive_decision={release_archive_decision}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_closure_report": str(source_path),
        "release_closure_status": release_closure_status,
        "release_closure_decision": release_closure_decision,
        "release_closure_exit_code": release_closure_exit_code,
        "release_archive_status": release_archive_status,
        "release_archive_decision": release_archive_decision,
        "release_archive_exit_code": int(release_archive_exit_code),
        "should_close_release": should_close_release,
        "should_notify": should_notify,
        "should_publish_archive": should_publish_archive,
        "release_run_id": release_closure_report["release_run_id"],
        "release_run_url": str(release_closure_report["release_run_url"]),
        "release_archive_summary": release_archive_summary,
        "reason_codes": _unique(reason_codes),
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Archive Report",
        "",
        f"- Release Archive Status: **{str(payload['release_archive_status']).upper()}**",
        f"- Release Archive Decision: `{payload['release_archive_decision']}`",
        f"- Should Publish Archive: `{payload['should_publish_archive']}`",
        f"- Release Archive Exit Code: `{payload['release_archive_exit_code']}`",
        f"- Release Closure Status: `{payload['release_closure_status']}`",
        f"- Release Closure Decision: `{payload['release_closure_decision']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- {payload['release_archive_summary']}",
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

    lines.extend(["", "## Evidence Manifest"])
    for item in payload["evidence_manifest"]:
        exists = "yes" if bool(item["exists"]) else "no"
        lines.append(f"- exists={exists} path=`{item['path']}`")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    return {
        "workflow_release_archive_status": str(payload["release_archive_status"]),
        "workflow_release_archive_decision": str(payload["release_archive_decision"]),
        "workflow_release_archive_should_publish": (
            "true" if payload["should_publish_archive"] else "false"
        ),
        "workflow_release_archive_exit_code": str(payload["release_archive_exit_code"]),
        "workflow_release_archive_run_id": "" if release_run_id is None else str(release_run_id),
        "workflow_release_archive_run_url": str(payload["release_run_url"]),
        "workflow_release_archive_missing_artifacts": json.dumps(
            payload["missing_artifacts"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_archive_report_json": str(output_json),
        "workflow_release_archive_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Linux CI workflow release archive contract from P2-36 release closure report"
        )
    )
    parser.add_argument(
        "--release-closure-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_closure.json",
        help="P2-36 release closure report JSON path",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_archive.json",
        help="Output release archive JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_archive.md",
        help="Output release archive markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release archive JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print summary without writing output files",
    )
    args = parser.parse_args()

    release_closure_report_path = Path(args.release_closure_report)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        release_closure_report = load_release_closure_report(release_closure_report_path)
        payload = build_release_archive_payload(
            release_closure_report,
            source_path=release_closure_report_path.resolve(),
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-archive-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
        output_markdown_path.write_text(render_markdown_report(payload), encoding="utf-8")
        print(f"release archive json: {output_json_path}")
        print(f"release archive markdown: {output_markdown_path}")

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
        "release archive summary: "
        f"release_archive_status={payload['release_archive_status']} "
        f"release_archive_decision={payload['release_archive_decision']} "
        f"release_archive_exit_code={payload['release_archive_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["release_archive_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

