"""Contract tests for P2-43 Linux CI workflow release delivery final verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_delivery_final_verdict_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_delivery_final_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_delivery_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_delivery_report": "/tmp/ci_workflow_release_delivery.json",
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
        "release_delivery_terminal_publish_status": "published",
        "release_delivery_terminal_publish_decision": "announce_release",
        "release_delivery_terminal_publish_exit_code": 0,
        "terminal_publish_should_notify": True,
        "terminal_publish_should_create_follow_up": False,
        "terminal_publish_channel": "release",
        "release_run_id": 3344556677,
        "release_run_url": "https://github.com/acme/demo/actions/runs/3344556677",
        "release_delivery_terminal_publish_summary": (
            "release_delivery_status=shipped "
            "release_delivery_terminal_publish_status=published "
            "release_delivery_terminal_publish_decision=announce_release"
        ),
        "reason_codes": ["release_delivery_terminal_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_delivery.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_terminal_verdict.json", "exists": True},
        ],
    }


def test_build_release_delivery_final_verdict_payload_completed(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_final_verdict_gate_module()
    payload = _sample_release_delivery_terminal_publish_payload()
    report_path = tmp_path / "ci_workflow_release_delivery_terminal_publish.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_terminal_publish_report(report_path)
    final_payload = gate.build_release_delivery_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_delivery_final_verdict_status"] == "completed"
    assert final_payload["release_delivery_final_verdict_decision"] == "close_release"
    assert final_payload["release_delivery_final_verdict_exit_code"] == 0
    assert final_payload["final_should_close_release"] is True
    assert final_payload["final_should_open_follow_up"] is False
    assert final_payload["final_should_page_owner"] is False
    assert final_payload["final_announcement_target"] == "release"
    assert final_payload["reason_codes"] == ["release_delivery_final_completed"]


def test_build_release_delivery_final_verdict_payload_requires_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_final_verdict_gate_module()
    payload = _sample_release_delivery_terminal_publish_payload()
    payload["release_archive_status"] = "pending"
    payload["release_archive_decision"] = "hold"
    payload["release_archive_exit_code"] = 1
    payload["should_publish_archive"] = False
    payload["release_verdict_status"] = "awaiting_archive"
    payload["release_verdict_decision"] = "hold"
    payload["release_verdict_exit_code"] = 1
    payload["should_ship_release"] = False
    payload["release_terminal_verdict_status"] = "awaiting_archive"
    payload["release_terminal_verdict_decision"] = "hold"
    payload["release_terminal_verdict_exit_code"] = 1
    payload["terminal_should_ship_release"] = False
    payload["terminal_requires_follow_up"] = True
    payload["release_delivery_status"] = "pending_follow_up"
    payload["release_delivery_decision"] = "hold"
    payload["release_delivery_exit_code"] = 1
    payload["delivery_should_ship_release"] = False
    payload["delivery_requires_human_action"] = True
    payload["delivery_should_announce_blocker"] = True
    payload["release_delivery_terminal_publish_status"] = "pending_follow_up"
    payload["release_delivery_terminal_publish_decision"] = "announce_hold"
    payload["release_delivery_terminal_publish_exit_code"] = 1
    payload["terminal_publish_should_notify"] = True
    payload["terminal_publish_should_create_follow_up"] = True
    payload["terminal_publish_channel"] = "hold"
    payload["reason_codes"] = ["release_delivery_terminal_pending_follow_up"]
    report_path = tmp_path / "ci_workflow_release_delivery_terminal_publish_hold.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_terminal_publish_report(report_path)
    final_payload = gate.build_release_delivery_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_delivery_final_verdict_status"] == "requires_follow_up"
    assert final_payload["release_delivery_final_verdict_decision"] == "open_follow_up"
    assert final_payload["release_delivery_final_verdict_exit_code"] == 1
    assert final_payload["final_should_close_release"] is False
    assert final_payload["final_should_open_follow_up"] is True
    assert final_payload["final_should_page_owner"] is False
    assert final_payload["final_announcement_target"] == "hold"
    assert "release_delivery_final_follow_up_required" in final_payload["reason_codes"]


def test_build_release_delivery_final_verdict_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_final_verdict_gate_module()
    payload = _sample_release_delivery_terminal_publish_payload()
    payload["release_delivery_terminal_publish_status"] = "published"
    payload["release_delivery_terminal_publish_decision"] = "announce_release"
    payload["release_delivery_terminal_publish_exit_code"] = 0
    payload["terminal_publish_should_notify"] = True
    payload["terminal_publish_should_create_follow_up"] = False
    payload["terminal_publish_channel"] = "release"
    payload["release_delivery_status"] = "shipped"
    payload["release_delivery_decision"] = "deliver"
    payload["release_delivery_exit_code"] = 0
    payload["delivery_should_ship_release"] = True
    payload["delivery_requires_human_action"] = False
    payload["incident_dispatch_status"] = "ready_dry_run"
    report_path = tmp_path / "ci_workflow_release_delivery_terminal_publish_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_terminal_publish_report(report_path)
    final_payload = gate.build_release_delivery_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_delivery_final_verdict_status"] == "contract_failed"
    assert final_payload["release_delivery_final_verdict_decision"] == "abort_close"
    assert final_payload["release_delivery_final_verdict_exit_code"] == 1
    assert "incident_status_mismatch_published" in final_payload["structural_issues"]


def test_build_release_delivery_final_verdict_payload_tracks_missing_evidence(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_final_verdict_gate_module()
    payload = _sample_release_delivery_terminal_publish_payload()
    payload["evidence_manifest"] = [
        {"path": "/tmp/ci_workflow_release_delivery.json", "exists": True},
        {"path": "/tmp/ci_workflow_release_terminal_verdict.json", "exists": False},
    ]
    report_path = tmp_path / "ci_workflow_release_delivery_terminal_publish_missing.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_terminal_publish_report(report_path)
    final_payload = gate.build_release_delivery_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_delivery_final_verdict_status"] == "contract_failed"
    assert final_payload["release_delivery_final_verdict_decision"] == "abort_close"
    assert final_payload["release_delivery_final_verdict_exit_code"] == 1
    assert "/tmp/ci_workflow_release_terminal_verdict.json" in final_payload["missing_artifacts"]
    assert "release_delivery_final_evidence_missing" in final_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_delivery_final_verdict_gate_module()
    payload = _sample_release_delivery_terminal_publish_payload()
    payload["release_archive_status"] = "failed"
    payload["release_archive_decision"] = "block"
    payload["release_archive_exit_code"] = 1
    payload["should_publish_archive"] = False
    payload["release_verdict_status"] = "blocked"
    payload["release_verdict_decision"] = "block"
    payload["release_verdict_exit_code"] = 1
    payload["should_ship_release"] = False
    payload["should_open_incident"] = True
    payload["should_dispatch_incident"] = True
    payload["incident_dispatch_status"] = "dispatched"
    payload["incident_dispatch_exit_code"] = 0
    payload["incident_dispatch_attempted"] = True
    payload["incident_url"] = "https://github.com/acme/demo/issues/88"
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
    payload["release_delivery_terminal_publish_status"] = "blocked"
    payload["release_delivery_terminal_publish_decision"] = "announce_blocker"
    payload["release_delivery_terminal_publish_exit_code"] = 1
    payload["terminal_publish_should_notify"] = True
    payload["terminal_publish_should_create_follow_up"] = True
    payload["terminal_publish_channel"] = "blocker"
    payload["reason_codes"] = ["release_delivery_terminal_blocked"]
    report_path = tmp_path / "ci_workflow_release_delivery_terminal_publish_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_delivery_terminal_publish_report(report_path)
    final_payload = gate.build_release_delivery_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        final_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.md"
        ),
    )

    assert outputs["workflow_release_delivery_final_verdict_status"] == "blocked"
    assert outputs["workflow_release_delivery_final_verdict_decision"] == "escalate_blocker"
    assert outputs["workflow_release_delivery_final_verdict_exit_code"] == "1"
    assert outputs["workflow_release_delivery_final_should_close_release"] == "false"
    assert outputs["workflow_release_delivery_final_should_open_follow_up"] == "true"
    assert outputs["workflow_release_delivery_final_should_page_owner"] == "true"
    assert outputs["workflow_release_delivery_final_announcement_target"] == "blocker"
    assert outputs["workflow_release_delivery_final_terminal_publish_status"] == "blocked"
    assert outputs["workflow_release_delivery_final_incident_status"] == "dispatched"
    assert outputs["workflow_release_delivery_final_incident_url"].endswith("/issues/88")
    assert outputs["workflow_release_delivery_final_run_id"] == "3344556677"
    assert outputs["workflow_release_delivery_final_run_url"].endswith(
        "/actions/runs/3344556677"
    )
    assert outputs["workflow_release_delivery_final_report_json"].endswith(
        "ci_workflow_release_delivery_final_verdict.json"
    )
    assert outputs["workflow_release_delivery_final_report_markdown"].endswith(
        "ci_workflow_release_delivery_final_verdict.md"
    )

