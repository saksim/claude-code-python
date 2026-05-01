"""Contract tests for P2-39 Linux CI workflow release incident gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_incident_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_incident_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_incident_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_verdict_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_archive_report": "/tmp/ci_workflow_release_archive.json",
        "release_archive_status": "ready",
        "release_archive_decision": "publish",
        "release_archive_exit_code": 0,
        "release_verdict_status": "published",
        "release_verdict_decision": "ship",
        "release_verdict_exit_code": 0,
        "should_publish_archive": True,
        "should_ship_release": True,
        "should_open_incident": False,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "release_verdict_summary": (
            "release_archive_status=ready release_verdict_status=published "
            "release_verdict_decision=ship"
        ),
        "reason_codes": ["release_verdict_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_finalization.json", "exists": True},
        ],
    }


def test_build_release_incident_payload_not_required(tmp_path: Path):
    gate = _load_ci_workflow_release_incident_gate_module()
    payload = _sample_release_verdict_payload()
    report_path = tmp_path / "ci_workflow_release_verdict.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_verdict_report(report_path)
    incident_payload = gate.build_release_incident_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        incident_repo="",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
        incident_command_parts=[],
        dry_run=True,
        command_result=None,
    )

    assert incident_payload["incident_dispatch_status"] == "not_required"
    assert incident_payload["should_dispatch_incident"] is False
    assert incident_payload["incident_dispatch_exit_code"] == 0
    assert incident_payload["should_open_incident"] is False


def test_build_release_incident_payload_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_release_incident_gate_module()
    payload = _sample_release_verdict_payload()
    payload["release_archive_status"] = "failed"
    payload["release_archive_decision"] = "block"
    payload["release_archive_exit_code"] = 1
    payload["release_verdict_status"] = "blocked"
    payload["release_verdict_decision"] = "block"
    payload["release_verdict_exit_code"] = 1
    payload["should_ship_release"] = False
    payload["should_open_incident"] = True
    payload["reason_codes"] = ["release_archive_failed"]
    report_path = tmp_path / "ci_workflow_release_verdict_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_verdict_report(report_path)
    command_parts = gate.build_incident_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        incident_command="",
        incident_repo="acme/demo",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
    )
    incident_payload = gate.build_release_incident_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        incident_repo="acme/demo",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
        incident_command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )

    assert incident_payload["incident_dispatch_status"] == "ready_dry_run"
    assert incident_payload["should_dispatch_incident"] is True
    assert incident_payload["incident_dispatch_exit_code"] == 0
    assert incident_payload["incident_dispatch_attempted"] is False
    assert incident_payload["incident_command_parts"][:3] == ["gh", "issue", "create"]


def test_build_release_incident_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_incident_gate_module()
    payload = _sample_release_verdict_payload()
    payload["release_verdict_status"] = "published"
    payload["release_verdict_decision"] = "ship"
    payload["release_verdict_exit_code"] = 0
    payload["should_ship_release"] = True
    payload["should_open_incident"] = True
    report_path = tmp_path / "ci_workflow_release_verdict_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_verdict_report(report_path)
    incident_payload = gate.build_release_incident_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        incident_repo="",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
        incident_command_parts=[],
        dry_run=True,
        command_result=None,
    )

    assert incident_payload["incident_dispatch_status"] == "contract_failed"
    assert incident_payload["incident_dispatch_exit_code"] == 1
    assert "should_open_incident_mismatch_published" in incident_payload["structural_issues"]


def test_build_release_incident_payload_marks_dispatch_failed(tmp_path: Path):
    gate = _load_ci_workflow_release_incident_gate_module()
    payload = _sample_release_verdict_payload()
    payload["release_archive_status"] = "failed"
    payload["release_archive_decision"] = "block"
    payload["release_archive_exit_code"] = 1
    payload["release_verdict_status"] = "blocked"
    payload["release_verdict_decision"] = "block"
    payload["release_verdict_exit_code"] = 1
    payload["should_ship_release"] = False
    payload["should_open_incident"] = True
    payload["reason_codes"] = ["release_archive_failed"]
    report_path = tmp_path / "ci_workflow_release_verdict_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_verdict_report(report_path)
    command_parts = gate.build_incident_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        incident_command="",
        incident_repo="acme/demo",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
    )
    incident_payload = gate.build_release_incident_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        incident_repo="acme/demo",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
        incident_command_parts=command_parts,
        dry_run=False,
        command_result={
            "attempted": True,
            "returncode": 1,
            "stdout_tail": "",
            "stderr_tail": "issue create failed",
            "error_type": "",
            "error_message": "",
        },
    )

    assert incident_payload["incident_dispatch_status"] == "dispatch_failed"
    assert incident_payload["incident_dispatch_exit_code"] == 1
    assert incident_payload["incident_dispatch_attempted"] is True
    assert "release_incident_command_failed" in incident_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_incident_gate_module()
    payload = _sample_release_verdict_payload()
    payload["release_archive_status"] = "failed"
    payload["release_archive_decision"] = "block"
    payload["release_archive_exit_code"] = 1
    payload["release_verdict_status"] = "blocked"
    payload["release_verdict_decision"] = "block"
    payload["release_verdict_exit_code"] = 1
    payload["should_ship_release"] = False
    payload["should_open_incident"] = True
    payload["reason_codes"] = ["release_archive_failed"]
    report_path = tmp_path / "ci_workflow_release_verdict_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_verdict_report(report_path)
    command_parts = gate.build_incident_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        incident_command="",
        incident_repo="acme/demo",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
    )
    incident_payload = gate.build_release_incident_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        incident_repo="acme/demo",
        incident_label="release-incident",
        incident_title_prefix="[release-incident]",
        incident_command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )
    outputs = gate.build_github_output_values(
        incident_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_incident.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_incident.md"),
    )

    assert outputs["workflow_release_incident_status"] == "ready_dry_run"
    assert outputs["workflow_release_incident_should_dispatch"] == "true"
    assert outputs["workflow_release_incident_attempted"] == "false"
    assert outputs["workflow_release_incident_exit_code"] == "0"
    assert outputs["workflow_release_incident_repo"] == "acme/demo"
    assert outputs["workflow_release_incident_label"] == "release-incident"
    assert outputs["workflow_release_incident_verdict_status"] == "blocked"
    assert outputs["workflow_release_incident_run_id"] == "2233445566"
    assert outputs["workflow_release_incident_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_incident_report_json"].endswith(
        "ci_workflow_release_incident.json"
    )
    assert outputs["workflow_release_incident_report_markdown"].endswith(
        "ci_workflow_release_incident.md"
    )

