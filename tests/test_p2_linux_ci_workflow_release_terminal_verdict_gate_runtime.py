"""Contract tests for P2-40 Linux CI workflow release terminal verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_terminal_verdict_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_terminal_verdict_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_terminal_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_incident_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_verdict_report": "/tmp/ci_workflow_release_verdict.json",
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
        "should_dispatch_incident": False,
        "incident_dispatch_status": "not_required",
        "incident_dispatch_exit_code": 0,
        "incident_dispatch_attempted": False,
        "incident_command": "",
        "incident_command_parts": [],
        "incident_command_returncode": None,
        "incident_command_stdout_tail": "",
        "incident_command_stderr_tail": "",
        "incident_error_type": "",
        "incident_error_message": "",
        "incident_repo": "",
        "incident_label": "release-incident",
        "incident_title_prefix": "[release-incident]",
        "incident_url": "",
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "incident_dispatch_summary": (
            "release_verdict_status=published incident_dispatch_status=not_required "
            "should_dispatch_incident=False"
        ),
        "reason_codes": ["incident_not_required_release_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_finalization.json", "exists": True},
        ],
    }


def test_build_release_terminal_verdict_payload_released(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_verdict_gate_module()
    payload = _sample_release_incident_payload()
    report_path = tmp_path / "ci_workflow_release_incident.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_incident_report(report_path)
    terminal_payload = gate.build_release_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_terminal_verdict_status"] == "released"
    assert terminal_payload["release_terminal_verdict_decision"] == "ship"
    assert terminal_payload["release_terminal_verdict_exit_code"] == 0
    assert terminal_payload["terminal_should_ship_release"] is True
    assert terminal_payload["terminal_requires_follow_up"] is False
    assert terminal_payload["reason_codes"] == ["release_terminal_released"]


def test_build_release_terminal_verdict_payload_blocked_incident_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_verdict_gate_module()
    payload = _sample_release_incident_payload()
    payload["release_archive_status"] = "failed"
    payload["release_archive_decision"] = "block"
    payload["release_archive_exit_code"] = 1
    payload["release_verdict_status"] = "blocked"
    payload["release_verdict_decision"] = "block"
    payload["release_verdict_exit_code"] = 1
    payload["should_publish_archive"] = False
    payload["should_ship_release"] = False
    payload["should_open_incident"] = True
    payload["should_dispatch_incident"] = True
    payload["incident_dispatch_status"] = "ready_dry_run"
    payload["incident_dispatch_exit_code"] = 0
    payload["reason_codes"] = ["release_archive_failed"]
    report_path = tmp_path / "ci_workflow_release_incident_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_incident_report(report_path)
    terminal_payload = gate.build_release_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_terminal_verdict_status"] == "blocked_incident_ready_dry_run"
    assert terminal_payload["release_terminal_verdict_decision"] == "escalate"
    assert terminal_payload["release_terminal_verdict_exit_code"] == 1
    assert terminal_payload["terminal_should_ship_release"] is False
    assert terminal_payload["terminal_requires_follow_up"] is True
    assert "release_terminal_blocked_incident_ready_dry_run" in terminal_payload["reason_codes"]


def test_build_release_terminal_verdict_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_verdict_gate_module()
    payload = _sample_release_incident_payload()
    payload["release_verdict_status"] = "published"
    payload["release_verdict_decision"] = "ship"
    payload["release_verdict_exit_code"] = 0
    payload["should_ship_release"] = True
    payload["should_open_incident"] = True
    payload["should_dispatch_incident"] = True
    payload["incident_dispatch_status"] = "ready_dry_run"
    report_path = tmp_path / "ci_workflow_release_incident_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_incident_report(report_path)
    terminal_payload = gate.build_release_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_terminal_verdict_status"] == "contract_failed"
    assert terminal_payload["release_terminal_verdict_decision"] == "block"
    assert terminal_payload["release_terminal_verdict_exit_code"] == 1
    assert "should_open_incident_mismatch_published" in terminal_payload["structural_issues"]


def test_build_release_terminal_verdict_payload_tracks_missing_evidence(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_verdict_gate_module()
    payload = _sample_release_incident_payload()
    payload["evidence_manifest"] = [
        {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
        {"path": "/tmp/ci_workflow_release_finalization.json", "exists": False},
    ]
    report_path = tmp_path / "ci_workflow_release_incident_missing_evidence.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_incident_report(report_path)
    terminal_payload = gate.build_release_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_terminal_verdict_status"] == "contract_failed"
    assert terminal_payload["release_terminal_verdict_decision"] == "block"
    assert terminal_payload["release_terminal_verdict_exit_code"] == 1
    assert "/tmp/ci_workflow_release_finalization.json" in terminal_payload["missing_artifacts"]
    assert "release_terminal_evidence_missing" in terminal_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_verdict_gate_module()
    payload = _sample_release_incident_payload()
    payload["release_archive_status"] = "failed"
    payload["release_archive_decision"] = "block"
    payload["release_archive_exit_code"] = 1
    payload["release_verdict_status"] = "blocked"
    payload["release_verdict_decision"] = "block"
    payload["release_verdict_exit_code"] = 1
    payload["should_publish_archive"] = False
    payload["should_ship_release"] = False
    payload["should_open_incident"] = True
    payload["should_dispatch_incident"] = True
    payload["incident_dispatch_status"] = "dispatched"
    payload["incident_dispatch_exit_code"] = 0
    payload["incident_dispatch_attempted"] = True
    payload["incident_url"] = "https://github.com/acme/demo/issues/77"
    payload["reason_codes"] = ["release_incident_dispatched"]
    report_path = tmp_path / "ci_workflow_release_incident_dispatched.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_incident_report(report_path)
    terminal_payload = gate.build_release_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        terminal_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.md"
        ),
    )

    assert outputs["workflow_release_terminal_verdict_status"] == "blocked_incident_dispatched"
    assert outputs["workflow_release_terminal_verdict_decision"] == "escalate"
    assert outputs["workflow_release_terminal_verdict_exit_code"] == "1"
    assert outputs["workflow_release_terminal_verdict_should_ship_release"] == "false"
    assert outputs["workflow_release_terminal_verdict_requires_follow_up"] == "true"
    assert outputs["workflow_release_terminal_verdict_incident_status"] == "dispatched"
    assert outputs["workflow_release_terminal_verdict_incident_url"].endswith("/issues/77")
    assert outputs["workflow_release_terminal_verdict_run_id"] == "2233445566"
    assert outputs["workflow_release_terminal_verdict_run_url"].endswith(
        "/actions/runs/2233445566"
    )
    assert outputs["workflow_release_terminal_verdict_report_json"].endswith(
        "ci_workflow_release_terminal_verdict.json"
    )
    assert outputs["workflow_release_terminal_verdict_report_markdown"].endswith(
        "ci_workflow_release_terminal_verdict.md"
    )
