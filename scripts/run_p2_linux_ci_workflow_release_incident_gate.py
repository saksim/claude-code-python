"""Phase 2 card P2-39 gate for Linux CI workflow release incident dispatch.

This script consumes the P2-38 release verdict artifact and converges
the release-incident dispatch contract:
1) validate release verdict consistency + evidence contract,
2) build/execute incident dispatch command when incident is required,
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


ALLOWED_RELEASE_VERDICT_STATUSES: set[str] = {
    "published",
    "awaiting_archive",
    "blocked",
    "contract_failed",
}
ALLOWED_RELEASE_VERDICT_DECISIONS: set[str] = {"ship", "hold", "block"}
ALLOWED_INCIDENT_DISPATCH_STATUSES: set[str] = {
    "not_required",
    "ready_dry_run",
    "dispatched",
    "dispatch_failed",
    "contract_failed",
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


def load_release_verdict_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: release verdict report not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{path}: release verdict payload must be object")

    required_fields = (
        "release_archive_status",
        "release_archive_decision",
        "release_archive_exit_code",
        "release_verdict_status",
        "release_verdict_decision",
        "release_verdict_exit_code",
        "should_publish_archive",
        "should_ship_release",
        "should_open_incident",
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
    release_archive_decision = _coerce_str(
        payload["release_archive_decision"],
        field="release_archive_decision",
        path=path,
    )
    release_archive_exit_code = _coerce_int(
        payload["release_archive_exit_code"],
        field="release_archive_exit_code",
        path=path,
    )
    if release_archive_exit_code < 0:
        raise ValueError(f"{path}: field 'release_archive_exit_code' must be >= 0")

    release_verdict_status = _coerce_str(
        payload["release_verdict_status"],
        field="release_verdict_status",
        path=path,
    )
    if release_verdict_status not in ALLOWED_RELEASE_VERDICT_STATUSES:
        raise ValueError(
            f"{path}: field 'release_verdict_status' must be one of "
            f"{sorted(ALLOWED_RELEASE_VERDICT_STATUSES)}"
        )

    release_verdict_decision = _coerce_str(
        payload["release_verdict_decision"],
        field="release_verdict_decision",
        path=path,
    )
    if release_verdict_decision not in ALLOWED_RELEASE_VERDICT_DECISIONS:
        raise ValueError(
            f"{path}: field 'release_verdict_decision' must be one of "
            f"{sorted(ALLOWED_RELEASE_VERDICT_DECISIONS)}"
        )

    release_verdict_exit_code = _coerce_int(
        payload["release_verdict_exit_code"],
        field="release_verdict_exit_code",
        path=path,
    )
    if release_verdict_exit_code < 0:
        raise ValueError(f"{path}: field 'release_verdict_exit_code' must be >= 0")

    should_publish_archive = _coerce_bool(
        payload["should_publish_archive"],
        field="should_publish_archive",
        path=path,
    )
    should_ship_release = _coerce_bool(
        payload["should_ship_release"],
        field="should_ship_release",
        path=path,
    )
    should_open_incident = _coerce_bool(
        payload["should_open_incident"],
        field="should_open_incident",
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
        "source_release_archive_report": _coerce_str(
            payload.get("source_release_archive_report", ""),
            field="source_release_archive_report",
            path=path,
        ),
        "release_archive_status": release_archive_status,
        "release_archive_decision": release_archive_decision,
        "release_archive_exit_code": release_archive_exit_code,
        "release_verdict_status": release_verdict_status,
        "release_verdict_decision": release_verdict_decision,
        "release_verdict_exit_code": release_verdict_exit_code,
        "should_publish_archive": should_publish_archive,
        "should_ship_release": should_ship_release,
        "should_open_incident": should_open_incident,
        "release_run_id": release_run_id,
        "release_run_url": release_run_url,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def build_incident_command_parts(
    verdict_report: dict[str, Any],
    *,
    source_report_path: Path,
    gh_executable: str,
    incident_command: str,
    incident_repo: str,
    incident_label: str,
    incident_title_prefix: str,
) -> list[str]:
    if incident_command.strip():
        try:
            custom_parts = shlex.split(incident_command)
        except ValueError as exc:
            raise ValueError(f"invalid --incident-command ({exc})") from exc
        if not custom_parts:
            raise ValueError("invalid --incident-command (empty command)")
        return custom_parts

    verdict_status = str(verdict_report["release_verdict_status"])
    verdict_decision = str(verdict_report["release_verdict_decision"])
    release_run_url = str(verdict_report["release_run_url"])
    reason_codes = list(verdict_report["reason_codes"])
    reason_codes_text = ", ".join(reason_codes) if reason_codes else "none"
    title = (
        f"{incident_title_prefix} release_verdict_status={verdict_status} "
        f"release_verdict_decision={verdict_decision}"
    )
    body = "\n".join(
        [
            "Automated incident opened by P2-39 release incident gate.",
            "",
            f"- release_verdict_status: {verdict_status}",
            f"- release_verdict_decision: {verdict_decision}",
            f"- release_verdict_exit_code: {verdict_report['release_verdict_exit_code']}",
            f"- release_run_id: {verdict_report['release_run_id']}",
            f"- release_run_url: {release_run_url}",
            f"- source_release_verdict_report: {source_report_path}",
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
    if incident_label.strip():
        parts.extend(["--label", incident_label])
    if incident_repo.strip():
        parts.extend(["--repo", incident_repo])
    return parts


def execute_incident_command(
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
            "error_message": f"incident command timeout after {timeout_seconds}s",
        }

    return {
        "attempted": True,
        "returncode": int(completed.returncode),
        "stdout_tail": _tail_text(completed.stdout or ""),
        "stderr_tail": _tail_text(completed.stderr or ""),
        "error_type": "",
        "error_message": "",
    }


def build_release_incident_payload(
    verdict_report: dict[str, Any],
    *,
    source_path: Path,
    project_root: Path,
    incident_repo: str,
    incident_label: str,
    incident_title_prefix: str,
    incident_command_parts: list[str],
    dry_run: bool,
    command_result: dict[str, Any] | None,
) -> dict[str, Any]:
    verdict_status = str(verdict_report["release_verdict_status"])
    verdict_decision = str(verdict_report["release_verdict_decision"])
    verdict_exit_code = int(verdict_report["release_verdict_exit_code"])
    should_ship_release = bool(verdict_report["should_ship_release"])
    should_open_incident = bool(verdict_report["should_open_incident"])

    reason_codes = list(verdict_report["reason_codes"])
    structural_issues = list(verdict_report["structural_issues"])
    missing_artifacts = list(verdict_report["missing_artifacts"])
    evidence_manifest = list(verdict_report["evidence_manifest"])

    missing_evidence = [str(item["path"]) for item in evidence_manifest if not bool(item["exists"])]
    if missing_evidence:
        missing_artifacts.extend(missing_evidence)
        reason_codes.append("release_incident_evidence_missing")

    if verdict_status == "published":
        if verdict_decision != "ship":
            structural_issues.append("release_verdict_decision_mismatch_published")
        if verdict_exit_code != 0:
            structural_issues.append("release_verdict_exit_code_mismatch_published")
        if not should_ship_release:
            structural_issues.append("should_ship_release_mismatch_published")
        if should_open_incident:
            structural_issues.append("should_open_incident_mismatch_published")
    elif verdict_status == "awaiting_archive":
        if verdict_decision != "hold":
            structural_issues.append("release_verdict_decision_mismatch_awaiting_archive")
        if should_ship_release:
            structural_issues.append("should_ship_release_mismatch_awaiting_archive")
        if should_open_incident:
            structural_issues.append("should_open_incident_mismatch_awaiting_archive")
    elif verdict_status in {"blocked", "contract_failed"}:
        if verdict_decision != "block":
            structural_issues.append("release_verdict_decision_mismatch_blocked")
        if should_ship_release:
            structural_issues.append("should_ship_release_mismatch_blocked")
        if not should_open_incident:
            structural_issues.append("should_open_incident_mismatch_blocked")
        if verdict_exit_code == 0:
            structural_issues.append("release_verdict_exit_code_mismatch_blocked")

    structural_issues = _unique(structural_issues)
    missing_artifacts = _unique(missing_artifacts)
    reason_codes = _unique(reason_codes)

    incident_command = (
        _format_shell_command(incident_command_parts) if incident_command_parts else ""
    )
    should_dispatch_incident = should_open_incident and not structural_issues and not missing_artifacts

    incident_dispatch_attempted = False
    incident_dispatch_status = "not_required"
    incident_dispatch_exit_code = 0
    incident_url = ""
    command_returncode: int | None = None
    command_stdout_tail = ""
    command_stderr_tail = ""
    incident_error_type = ""
    incident_error_message = ""

    if structural_issues or missing_artifacts:
        incident_dispatch_status = "contract_failed"
        incident_dispatch_exit_code = 1
        reason_codes.extend(structural_issues)
    elif not should_dispatch_incident:
        incident_dispatch_status = "not_required"
        incident_dispatch_exit_code = 0
        if verdict_status == "published":
            reason_codes = ["incident_not_required_release_published"]
    elif dry_run:
        incident_dispatch_status = "ready_dry_run"
        incident_dispatch_exit_code = 0
    else:
        incident_dispatch_attempted = True
        if command_result is None:
            incident_dispatch_status = "dispatch_failed"
            incident_dispatch_exit_code = 1
            reason_codes.append("incident_command_result_missing")
        else:
            command_returncode = int(command_result["returncode"])
            command_stdout_tail = str(command_result.get("stdout_tail", ""))
            command_stderr_tail = str(command_result.get("stderr_tail", ""))
            incident_error_type = str(command_result.get("error_type", ""))
            incident_error_message = str(command_result.get("error_message", ""))
            if command_returncode == 0:
                incident_dispatch_status = "dispatched"
                incident_dispatch_exit_code = 0
                incident_url = _extract_url(command_stdout_tail)
                reason_codes = ["release_incident_dispatched"]
            else:
                incident_dispatch_status = "dispatch_failed"
                incident_dispatch_exit_code = 1
                if incident_error_type == "command_not_found":
                    reason_codes.append("release_incident_cli_unavailable")
                elif incident_error_type == "timeout":
                    reason_codes.append("release_incident_timeout")
                else:
                    reason_codes.append("release_incident_command_failed")

    reason_codes = _unique(reason_codes)

    if incident_dispatch_status not in ALLOWED_INCIDENT_DISPATCH_STATUSES:
        raise ValueError("internal: unsupported incident dispatch status computed")

    incident_dispatch_summary = (
        f"release_verdict_status={verdict_status} "
        f"incident_dispatch_status={incident_dispatch_status} "
        f"should_dispatch_incident={should_dispatch_incident}"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_release_verdict_report": str(source_path),
        "project_root": str(project_root),
        "source_release_archive_report": str(verdict_report["source_release_archive_report"]),
        "release_archive_status": str(verdict_report["release_archive_status"]),
        "release_archive_decision": str(verdict_report["release_archive_decision"]),
        "release_archive_exit_code": int(verdict_report["release_archive_exit_code"]),
        "release_verdict_status": verdict_status,
        "release_verdict_decision": verdict_decision,
        "release_verdict_exit_code": verdict_exit_code,
        "should_publish_archive": bool(verdict_report["should_publish_archive"]),
        "should_ship_release": should_ship_release,
        "should_open_incident": should_open_incident,
        "should_dispatch_incident": should_dispatch_incident,
        "incident_dispatch_status": incident_dispatch_status,
        "incident_dispatch_exit_code": int(incident_dispatch_exit_code),
        "incident_dispatch_attempted": incident_dispatch_attempted,
        "incident_command": incident_command,
        "incident_command_parts": list(incident_command_parts),
        "incident_command_returncode": command_returncode,
        "incident_command_stdout_tail": command_stdout_tail,
        "incident_command_stderr_tail": command_stderr_tail,
        "incident_error_type": incident_error_type,
        "incident_error_message": incident_error_message,
        "incident_repo": incident_repo,
        "incident_label": incident_label,
        "incident_title_prefix": incident_title_prefix,
        "incident_url": incident_url,
        "release_run_id": verdict_report["release_run_id"],
        "release_run_url": str(verdict_report["release_run_url"]),
        "incident_dispatch_summary": incident_dispatch_summary,
        "reason_codes": reason_codes,
        "structural_issues": structural_issues,
        "missing_artifacts": missing_artifacts,
        "evidence_manifest": evidence_manifest,
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Linux CI Workflow Release Incident Dispatch Report",
        "",
        f"- Incident Dispatch Status: **{str(payload['incident_dispatch_status']).upper()}**",
        f"- Incident Dispatch Exit Code: `{payload['incident_dispatch_exit_code']}`",
        f"- Should Open Incident: `{payload['should_open_incident']}`",
        f"- Should Dispatch Incident: `{payload['should_dispatch_incident']}`",
        f"- Incident Dispatch Attempted: `{payload['incident_dispatch_attempted']}`",
        f"- Incident URL: `{payload['incident_url']}`",
        f"- Release Verdict Status: `{payload['release_verdict_status']}`",
        f"- Release Verdict Decision: `{payload['release_verdict_decision']}`",
        f"- Release Run ID: `{payload['release_run_id']}`",
        f"- Release Run URL: `{payload['release_run_url']}`",
        f"- Generated At (UTC): `{payload['generated_at']}`",
        "",
        "## Incident Command",
    ]

    incident_command = str(payload["incident_command"])
    if incident_command:
        lines.append(f"- `{incident_command}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Summary", "", f"- {payload['incident_dispatch_summary']}", "", "## Reason Codes"])
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

    lines.extend(["", "## Incident Command Output (tail)"])
    stdout_tail = str(payload["incident_command_stdout_tail"]).strip()
    stderr_tail = str(payload["incident_command_stderr_tail"]).strip()
    if stdout_tail:
        lines.append("- stdout:")
        lines.append("```text")
        lines.append(stdout_tail)
        lines.append("```")
    else:
        lines.append("- stdout: none")
    if stderr_tail:
        lines.append("- stderr:")
        lines.append("```text")
        lines.append(stderr_tail)
        lines.append("```")
    else:
        lines.append("- stderr: none")

    lines.append("")
    return "\n".join(lines)


def build_github_output_values(
    payload: dict[str, Any], *, output_json: Path, output_markdown: Path
) -> dict[str, str]:
    release_run_id = payload["release_run_id"]
    command_returncode = payload["incident_command_returncode"]
    return {
        "workflow_release_incident_status": str(payload["incident_dispatch_status"]),
        "workflow_release_incident_should_dispatch": (
            "true" if payload["should_dispatch_incident"] else "false"
        ),
        "workflow_release_incident_attempted": (
            "true" if payload["incident_dispatch_attempted"] else "false"
        ),
        "workflow_release_incident_exit_code": str(payload["incident_dispatch_exit_code"]),
        "workflow_release_incident_command_returncode": (
            "" if command_returncode is None else str(command_returncode)
        ),
        "workflow_release_incident_url": str(payload["incident_url"]),
        "workflow_release_incident_repo": str(payload["incident_repo"]),
        "workflow_release_incident_label": str(payload["incident_label"]),
        "workflow_release_incident_verdict_status": str(payload["release_verdict_status"]),
        "workflow_release_incident_run_id": (
            "" if release_run_id is None else str(release_run_id)
        ),
        "workflow_release_incident_run_url": str(payload["release_run_url"]),
        "workflow_release_incident_reason_codes": json.dumps(
            payload["reason_codes"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "workflow_release_incident_report_json": str(output_json),
        "workflow_release_incident_report_markdown": str(output_markdown),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Linux CI workflow release incident gate from P2-38 release verdict report"
        )
    )
    parser.add_argument(
        "--release-verdict-report",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_verdict.json",
        help="P2-38 release verdict report JSON path",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root for incident command execution",
    )
    parser.add_argument(
        "--gh-executable",
        default="gh",
        help="GitHub CLI executable used when auto-building incident command",
    )
    parser.add_argument(
        "--incident-command",
        default="",
        help="Optional explicit incident command string (overrides auto command)",
    )
    parser.add_argument(
        "--incident-repo",
        default="",
        help="Optional GitHub repo for incident creation (OWNER/REPO)",
    )
    parser.add_argument(
        "--incident-label",
        default="release-incident",
        help="Incident label forwarded to auto-built command",
    )
    parser.add_argument(
        "--incident-title-prefix",
        default="[release-incident]",
        help="Incident title prefix for auto-built command",
    )
    parser.add_argument(
        "--incident-timeout-seconds",
        type=int,
        default=600,
        help="Incident command timeout in seconds",
    )
    parser.add_argument(
        "--output-json",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_incident.json",
        help="Output release incident JSON path",
    )
    parser.add_argument(
        "--output-markdown",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_incident.md",
        help="Output release incident markdown report path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print release incident JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate contract and skip incident command execution",
    )
    args = parser.parse_args()

    if args.incident_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-release-incident-gate] "
            "--incident-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    release_verdict_report_path = Path(args.release_verdict_report)
    project_root = Path(args.project_root)
    output_json_path = Path(args.output_json)
    output_markdown_path = Path(args.output_markdown)

    try:
        verdict_report = load_release_verdict_report(release_verdict_report_path)
    except ValueError as exc:
        print(f"[p2-linux-ci-workflow-release-incident-gate] {exc}", file=sys.stderr)
        return 2

    incident_command_parts: list[str] = []
    if verdict_report["should_open_incident"]:
        try:
            incident_command_parts = build_incident_command_parts(
                verdict_report,
                source_report_path=release_verdict_report_path.resolve(),
                gh_executable=args.gh_executable,
                incident_command=args.incident_command,
                incident_repo=args.incident_repo,
                incident_label=args.incident_label,
                incident_title_prefix=args.incident_title_prefix,
            )
        except ValueError as exc:
            print(f"[p2-linux-ci-workflow-release-incident-gate] {exc}", file=sys.stderr)
            return 2

    command_result: dict[str, Any] | None = None
    if verdict_report["should_open_incident"] and not args.dry_run:
        command_result = execute_incident_command(
            incident_command_parts,
            cwd=project_root,
            timeout_seconds=args.incident_timeout_seconds,
        )

    payload = build_release_incident_payload(
        verdict_report,
        source_path=release_verdict_report_path.resolve(),
        project_root=project_root.resolve(),
        incident_repo=args.incident_repo,
        incident_label=args.incident_label,
        incident_title_prefix=args.incident_title_prefix,
        incident_command_parts=incident_command_parts,
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
        print(f"release incident json: {output_json_path}")
        print(f"release incident markdown: {output_markdown_path}")

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
        "release incident summary: "
        f"incident_dispatch_status={payload['incident_dispatch_status']} "
        f"should_dispatch_incident={payload['should_dispatch_incident']} "
        f"incident_dispatch_exit_code={payload['incident_dispatch_exit_code']}"
    )
    if args.print_report or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return int(payload["incident_dispatch_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

