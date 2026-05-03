"""Contract tests for P2-42 Linux CI workflow release delivery terminal publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_delivery_terminal_publish_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_delivery_terminal_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_delivery_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_terminal_verdict_report": "/tmp/ci_workflow_release_terminal_verdict.json",
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
        "release_delivery_status": "shipped",
        "release_delivery_decision": "deliver",
        "release_delivery_exit_code": 0,
        "delivery_should_ship_release": True,
        "delivery_requires_human_action": False,
        "delivery_should_announce_blocker": False,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "release_delivery_summary": (
            "release_terminal_verdict_status=released "
            "release_delivery_status=shipped "
            "release_delivery_decision=deliver"
        ),
        "reason_codes": ["release_delivery_shipped"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_finalization.json", "exists": True},
        ],
    }


def test_build_release_delivery_terminal_publish_payload_published(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_terminal_publish_gate_module()
    payload = _sample_release_delivery_payload()
    report_path = tmp_path / "ci_workflow_release_delivery.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_report(report_path)
    terminal_payload = gate.build_release_delivery_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_delivery_terminal_publish_status"] == "published"
    assert terminal_payload["release_delivery_terminal_publish_decision"] == "announce_release"
    assert terminal_payload["release_delivery_terminal_publish_exit_code"] == 0
    assert terminal_payload["terminal_publish_should_notify"] is True
    assert terminal_payload["terminal_publish_should_create_follow_up"] is False
    assert terminal_payload["terminal_publish_channel"] == "release"
    assert terminal_payload["reason_codes"] == ["release_delivery_terminal_published"]


def test_build_release_delivery_terminal_publish_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_terminal_publish_gate_module()
    payload = _sample_release_delivery_payload()
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
    payload["release_terminal_verdict_status"] = "blocked_incident_ready_dry_run"
    payload["release_terminal_verdict_decision"] = "escalate"
    payload["release_terminal_verdict_exit_code"] = 1
    payload["terminal_should_ship_release"] = False
    payload["terminal_requires_follow_up"] = True
    payload["terminal_incident_linked"] = True
    payload["release_delivery_status"] = "blocked_incident"
    payload["release_delivery_decision"] = "escalate"
    payload["release_delivery_exit_code"] = 1
    payload["delivery_should_ship_release"] = False
    payload["delivery_requires_human_action"] = True
    payload["delivery_should_announce_blocker"] = True
    payload["reason_codes"] = ["release_delivery_incident_escalation_required"]
    report_path = tmp_path / "ci_workflow_release_delivery_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_report(report_path)
    terminal_payload = gate.build_release_delivery_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_delivery_terminal_publish_status"] == "blocked"
    assert terminal_payload["release_delivery_terminal_publish_decision"] == "announce_blocker"
    assert terminal_payload["release_delivery_terminal_publish_exit_code"] == 1
    assert terminal_payload["terminal_publish_should_notify"] is True
    assert terminal_payload["terminal_publish_should_create_follow_up"] is True
    assert terminal_payload["terminal_publish_channel"] == "blocker"
    assert "release_delivery_terminal_blocked" in terminal_payload["reason_codes"]


def test_build_release_delivery_terminal_publish_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_terminal_publish_gate_module()
    payload = _sample_release_delivery_payload()
    payload["release_delivery_status"] = "shipped"
    payload["release_delivery_decision"] = "deliver"
    payload["release_delivery_exit_code"] = 0
    payload["delivery_should_ship_release"] = True
    payload["delivery_requires_human_action"] = False
    payload["delivery_should_announce_blocker"] = False
    payload["incident_dispatch_status"] = "ready_dry_run"
    payload["should_dispatch_incident"] = True
    report_path = tmp_path / "ci_workflow_release_delivery_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_report(report_path)
    terminal_payload = gate.build_release_delivery_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_delivery_terminal_publish_status"] == "contract_failed"
    assert terminal_payload["release_delivery_terminal_publish_decision"] == "abort_publish"
    assert terminal_payload["release_delivery_terminal_publish_exit_code"] == 1
    assert "incident_status_mismatch_shipped" in terminal_payload["structural_issues"]


def test_build_release_delivery_terminal_publish_payload_tracks_missing_evidence(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_terminal_publish_gate_module()
    payload = _sample_release_delivery_payload()
    payload["evidence_manifest"] = [
        {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
        {"path": "/tmp/ci_workflow_release_finalization.json", "exists": False},
    ]
    report_path = tmp_path / "ci_workflow_release_delivery_missing.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_report(report_path)
    terminal_payload = gate.build_release_delivery_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_delivery_terminal_publish_status"] == "contract_failed"
    assert terminal_payload["release_delivery_terminal_publish_decision"] == "abort_publish"
    assert terminal_payload["release_delivery_terminal_publish_exit_code"] == 1
    assert "/tmp/ci_workflow_release_finalization.json" in terminal_payload["missing_artifacts"]
    assert "release_delivery_terminal_evidence_missing" in terminal_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_terminal_publish_gate_module()
    payload = _sample_release_delivery_payload()
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
    payload["release_delivery_status"] = "blocked_incident"
    payload["release_delivery_decision"] = "escalate"
    payload["release_delivery_exit_code"] = 1
    payload["delivery_should_ship_release"] = False
    payload["delivery_requires_human_action"] = True
    payload["delivery_should_announce_blocker"] = True
    payload["reason_codes"] = ["release_delivery_incident_escalation_required"]
    report_path = tmp_path / "ci_workflow_release_delivery_incident.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_report(report_path)
    terminal_payload = gate.build_release_delivery_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        terminal_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.md"
        ),
    )

    assert outputs["workflow_release_delivery_terminal_publish_status"] == "blocked"
    assert outputs["workflow_release_delivery_terminal_publish_decision"] == "announce_blocker"
    assert outputs["workflow_release_delivery_terminal_publish_exit_code"] == "1"
    assert outputs["workflow_release_delivery_terminal_publish_should_notify"] == "true"
    assert outputs["workflow_release_delivery_terminal_publish_should_create_follow_up"] == "true"
    assert outputs["workflow_release_delivery_terminal_publish_channel"] == "blocker"
    assert outputs["workflow_release_delivery_terminal_publish_delivery_status"] == "blocked_incident"
    assert outputs["workflow_release_delivery_terminal_publish_incident_status"] == "dispatched"
    assert outputs["workflow_release_delivery_terminal_publish_incident_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_release_delivery_terminal_publish_run_id"] == "2233445566"
    assert outputs["workflow_release_delivery_terminal_publish_run_url"].endswith(
        "/actions/runs/2233445566"
    )
    assert outputs["workflow_release_delivery_terminal_publish_report_json"].endswith(
        "ci_workflow_release_delivery_terminal_publish.json"
    )
    assert outputs["workflow_release_delivery_terminal_publish_report_markdown"].endswith(
        "ci_workflow_release_delivery_terminal_publish.md"
    )

