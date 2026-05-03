"""Contract tests for P2-41 Linux CI workflow release delivery gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_delivery_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_delivery_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_delivery_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_terminal_verdict_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_incident_report": "/tmp/ci_workflow_release_incident.json",
        "source_release_verdict_report": "/tmp/ci_workflow_release_verdict.json",
        "source_release_archive_report": "/tmp/ci_workflow_release_archive.json",
        "release_archive_status": "ready",
        "release_archive_decision": "publish",
        "release_archive_exit_code": 0,
        "should_publish_archive": True,
        "release_verdict_status": "published",
        "release_verdict_decision": "ship",
        "release_verdict_exit_code": 0,
        "should_ship_release": True,
        "should_open_incident": False,
        "should_dispatch_incident": False,
        "incident_dispatch_status": "not_required",
        "incident_dispatch_exit_code": 0,
        "incident_dispatch_attempted": False,
        "incident_url": "",
        "release_terminal_verdict_status": "released",
        "release_terminal_verdict_decision": "ship",
        "release_terminal_verdict_exit_code": 0,
        "terminal_should_ship_release": True,
        "terminal_requires_follow_up": False,
        "terminal_incident_linked": False,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "release_terminal_verdict_summary": (
            "release_verdict_status=published incident_dispatch_status=not_required "
            "release_terminal_verdict_status=released release_terminal_verdict_decision=ship"
        ),
        "reason_codes": ["release_terminal_released"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_finalization.json", "exists": True},
        ],
    }


def test_build_release_delivery_payload_shipped(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_gate_module()
    payload = _sample_release_terminal_verdict_payload()
    report_path = tmp_path / "ci_workflow_release_terminal_verdict.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_verdict_report(report_path)
    delivery_payload = gate.build_release_delivery_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert delivery_payload["release_delivery_status"] == "shipped"
    assert delivery_payload["release_delivery_decision"] == "deliver"
    assert delivery_payload["release_delivery_exit_code"] == 0
    assert delivery_payload["delivery_should_ship_release"] is True
    assert delivery_payload["delivery_requires_human_action"] is False
    assert delivery_payload["reason_codes"] == ["release_delivery_shipped"]


def test_build_release_delivery_payload_blocked_incident(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_gate_module()
    payload = _sample_release_terminal_verdict_payload()
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
    payload["incident_dispatch_attempted"] = False
    payload["release_terminal_verdict_status"] = "blocked_incident_ready_dry_run"
    payload["release_terminal_verdict_decision"] = "escalate"
    payload["release_terminal_verdict_exit_code"] = 1
    payload["terminal_should_ship_release"] = False
    payload["terminal_requires_follow_up"] = True
    payload["terminal_incident_linked"] = True
    payload["reason_codes"] = ["release_terminal_blocked_incident_ready_dry_run"]
    report_path = tmp_path / "ci_workflow_release_terminal_verdict_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_verdict_report(report_path)
    delivery_payload = gate.build_release_delivery_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert delivery_payload["release_delivery_status"] == "blocked_incident"
    assert delivery_payload["release_delivery_decision"] == "escalate"
    assert delivery_payload["release_delivery_exit_code"] == 1
    assert delivery_payload["delivery_should_ship_release"] is False
    assert delivery_payload["delivery_requires_human_action"] is True
    assert "release_delivery_incident_escalation_required" in delivery_payload["reason_codes"]


def test_build_release_delivery_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_gate_module()
    payload = _sample_release_terminal_verdict_payload()
    payload["release_terminal_verdict_status"] = "released"
    payload["release_terminal_verdict_decision"] = "ship"
    payload["release_terminal_verdict_exit_code"] = 0
    payload["terminal_should_ship_release"] = True
    payload["terminal_requires_follow_up"] = False
    payload["incident_dispatch_status"] = "ready_dry_run"
    payload["should_dispatch_incident"] = True
    report_path = tmp_path / "ci_workflow_release_terminal_verdict_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_verdict_report(report_path)
    delivery_payload = gate.build_release_delivery_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert delivery_payload["release_delivery_status"] == "contract_failed"
    assert delivery_payload["release_delivery_decision"] == "block"
    assert delivery_payload["release_delivery_exit_code"] == 1
    assert "incident_status_mismatch_released" in delivery_payload["structural_issues"]


def test_build_release_delivery_payload_tracks_missing_evidence(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_gate_module()
    payload = _sample_release_terminal_verdict_payload()
    payload["evidence_manifest"] = [
        {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
        {"path": "/tmp/ci_workflow_release_finalization.json", "exists": False},
    ]
    report_path = tmp_path / "ci_workflow_release_terminal_verdict_missing.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_verdict_report(report_path)
    delivery_payload = gate.build_release_delivery_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert delivery_payload["release_delivery_status"] == "contract_failed"
    assert delivery_payload["release_delivery_decision"] == "block"
    assert delivery_payload["release_delivery_exit_code"] == 1
    assert "/tmp/ci_workflow_release_finalization.json" in delivery_payload["missing_artifacts"]
    assert "release_delivery_evidence_missing" in delivery_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_gate_module()
    payload = _sample_release_terminal_verdict_payload()
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
    payload["release_terminal_verdict_status"] = "blocked_incident_dispatched"
    payload["release_terminal_verdict_decision"] = "escalate"
    payload["release_terminal_verdict_exit_code"] = 1
    payload["terminal_should_ship_release"] = False
    payload["terminal_requires_follow_up"] = True
    payload["terminal_incident_linked"] = True
    payload["reason_codes"] = ["release_terminal_blocked_incident_dispatched"]
    report_path = tmp_path / "ci_workflow_release_terminal_verdict_dispatched.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_verdict_report(report_path)
    delivery_payload = gate.build_release_delivery_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        delivery_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_delivery.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_delivery.md"),
    )

    assert outputs["workflow_release_delivery_status"] == "blocked_incident"
    assert outputs["workflow_release_delivery_decision"] == "escalate"
    assert outputs["workflow_release_delivery_exit_code"] == "1"
    assert outputs["workflow_release_delivery_should_ship_release"] == "false"
    assert outputs["workflow_release_delivery_requires_human_action"] == "true"
    assert outputs["workflow_release_delivery_should_announce_blocker"] == "true"
    assert outputs["workflow_release_delivery_terminal_verdict_status"] == "blocked_incident_dispatched"
    assert outputs["workflow_release_delivery_incident_status"] == "dispatched"
    assert outputs["workflow_release_delivery_incident_url"].endswith("/issues/77")
    assert outputs["workflow_release_delivery_run_id"] == "2233445566"
    assert outputs["workflow_release_delivery_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_delivery_report_json"].endswith(
        "ci_workflow_release_delivery.json"
    )
    assert outputs["workflow_release_delivery_report_markdown"].endswith(
        "ci_workflow_release_delivery.md"
    )

