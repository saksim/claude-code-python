"""Contract tests for P2-45 Linux CI workflow release follow-up closure gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_follow_up_closure_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_release_follow_up_closure_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_follow_up_closure_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_follow_up_dispatch_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_delivery_final_verdict_report": (
            "/tmp/ci_workflow_release_delivery_final_verdict.json"
        ),
        "source_release_delivery_terminal_publish_report": (
            "/tmp/ci_workflow_release_delivery_terminal_publish.json"
        ),
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
        "release_delivery_final_verdict_status": "completed",
        "release_delivery_final_verdict_decision": "close_release",
        "release_delivery_final_verdict_exit_code": 0,
        "final_should_close_release": True,
        "final_should_open_follow_up": False,
        "final_should_page_owner": False,
        "final_announcement_target": "release",
        "release_follow_up_dispatch_status": "closed",
        "release_follow_up_dispatch_decision": "no_action",
        "release_follow_up_dispatch_exit_code": 0,
        "follow_up_required": False,
        "escalation_required": False,
        "dispatch_target": "none",
        "release_run_id": 5566778899,
        "release_run_url": "https://github.com/acme/demo/actions/runs/5566778899",
        "reason_codes": ["release_follow_up_dispatch_closed"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_follow_up_dispatch.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_delivery_final_verdict.json", "exists": True},
        ],
    }


def test_build_release_follow_up_closure_payload_closed(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_closure_gate_module()
    payload = _sample_release_follow_up_dispatch_payload()
    report_path = tmp_path / "ci_workflow_release_follow_up_dispatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_dispatch_report(report_path)
    closure_payload = gate.build_release_follow_up_closure_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        follow_up_repo="",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
        follow_up_command_parts=[],
        dry_run=True,
        command_result=None,
    )

    assert closure_payload["release_follow_up_closure_status"] == "closed"
    assert closure_payload["release_follow_up_closure_decision"] == "no_action"
    assert closure_payload["release_follow_up_closure_exit_code"] == 0
    assert closure_payload["should_queue_follow_up"] is False
    assert closure_payload["follow_up_queue_attempted"] is False
    assert closure_payload["follow_up_task_queued"] is False
    assert closure_payload["escalation_task_queued"] is False
    assert closure_payload["reason_codes"] == ["release_follow_up_closed_no_action"]


def test_build_release_follow_up_closure_payload_queued_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_closure_gate_module()
    payload = _sample_release_follow_up_dispatch_payload()
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
    payload["release_delivery_final_verdict_status"] = "requires_follow_up"
    payload["release_delivery_final_verdict_decision"] = "open_follow_up"
    payload["release_delivery_final_verdict_exit_code"] = 1
    payload["final_should_close_release"] = False
    payload["final_should_open_follow_up"] = True
    payload["final_should_page_owner"] = False
    payload["final_announcement_target"] = "hold"
    payload["release_follow_up_dispatch_status"] = "follow_up_required"
    payload["release_follow_up_dispatch_decision"] = "dispatch_follow_up"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["escalation_required"] = False
    payload["dispatch_target"] = "follow_up_queue"
    payload["reason_codes"] = ["release_follow_up_dispatch_required"]
    report_path = tmp_path / "ci_workflow_release_follow_up_dispatch_follow_up.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_dispatch_report(report_path)
    command_parts = gate.build_follow_up_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        follow_up_command="",
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
    )
    closure_payload = gate.build_release_follow_up_closure_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
        follow_up_command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )

    assert closure_payload["release_follow_up_closure_status"] == "queued_dry_run"
    assert closure_payload["release_follow_up_closure_decision"] == "queue_follow_up"
    assert closure_payload["release_follow_up_closure_exit_code"] == 0
    assert closure_payload["should_queue_follow_up"] is True
    assert closure_payload["follow_up_queue_attempted"] is False
    assert closure_payload["follow_up_task_queued"] is False
    assert closure_payload["escalation_task_queued"] is False
    assert closure_payload["follow_up_command_parts"][:3] == ["gh", "issue", "create"]


def test_build_release_follow_up_closure_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_closure_gate_module()
    payload = _sample_release_follow_up_dispatch_payload()
    payload["release_follow_up_dispatch_status"] = "closed"
    payload["release_follow_up_dispatch_decision"] = "no_action"
    payload["release_follow_up_dispatch_exit_code"] = 0
    payload["follow_up_required"] = True
    payload["escalation_required"] = False
    payload["dispatch_target"] = "none"
    report_path = tmp_path / "ci_workflow_release_follow_up_dispatch_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_dispatch_report(report_path)
    closure_payload = gate.build_release_follow_up_closure_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        follow_up_repo="",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
        follow_up_command_parts=[],
        dry_run=True,
        command_result=None,
    )

    assert closure_payload["release_follow_up_closure_status"] == "contract_failed"
    assert closure_payload["release_follow_up_closure_decision"] == "abort_queue"
    assert closure_payload["release_follow_up_closure_exit_code"] == 1
    assert "follow_up_required_mismatch_closed" in closure_payload["structural_issues"]


def test_build_release_follow_up_closure_payload_marks_queue_failed(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_closure_gate_module()
    payload = _sample_release_follow_up_dispatch_payload()
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
    payload["incident_url"] = "https://github.com/acme/demo/issues/101"
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
    payload["release_delivery_final_verdict_status"] = "blocked"
    payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    payload["release_delivery_final_verdict_exit_code"] = 1
    payload["final_should_close_release"] = False
    payload["final_should_open_follow_up"] = True
    payload["final_should_page_owner"] = True
    payload["final_announcement_target"] = "blocker"
    payload["release_follow_up_dispatch_status"] = "escalated"
    payload["release_follow_up_dispatch_decision"] = "dispatch_escalation"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["escalation_required"] = True
    payload["dispatch_target"] = "incident_commander"
    payload["reason_codes"] = ["release_follow_up_dispatch_escalated"]
    report_path = tmp_path / "ci_workflow_release_follow_up_dispatch_escalated.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_dispatch_report(report_path)
    command_parts = gate.build_follow_up_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        follow_up_command="",
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
    )
    closure_payload = gate.build_release_follow_up_closure_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
        follow_up_command_parts=command_parts,
        dry_run=False,
        command_result={
            "attempted": True,
            "returncode": 1,
            "stdout_tail": "",
            "stderr_tail": "follow-up create failed",
            "error_type": "",
            "error_message": "",
        },
    )

    assert closure_payload["release_follow_up_closure_status"] == "queue_failed"
    assert closure_payload["release_follow_up_closure_decision"] == "abort_queue"
    assert closure_payload["release_follow_up_closure_exit_code"] == 1
    assert closure_payload["should_queue_follow_up"] is True
    assert closure_payload["follow_up_queue_attempted"] is True
    assert "release_follow_up_command_failed" in closure_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_closure_gate_module()
    payload = _sample_release_follow_up_dispatch_payload()
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
    payload["release_delivery_final_verdict_status"] = "requires_follow_up"
    payload["release_delivery_final_verdict_decision"] = "open_follow_up"
    payload["release_delivery_final_verdict_exit_code"] = 1
    payload["final_should_close_release"] = False
    payload["final_should_open_follow_up"] = True
    payload["final_should_page_owner"] = False
    payload["final_announcement_target"] = "hold"
    payload["release_follow_up_dispatch_status"] = "follow_up_required"
    payload["release_follow_up_dispatch_decision"] = "dispatch_follow_up"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["escalation_required"] = False
    payload["dispatch_target"] = "follow_up_queue"
    payload["reason_codes"] = ["release_follow_up_dispatch_required"]
    report_path = tmp_path / "ci_workflow_release_follow_up_dispatch_follow_up.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_dispatch_report(report_path)
    command_parts = gate.build_follow_up_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        follow_up_command="",
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
    )
    closure_payload = gate.build_release_follow_up_closure_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up",
        follow_up_title_prefix="[release-follow-up]",
        follow_up_command_parts=command_parts,
        dry_run=False,
        command_result={
            "attempted": True,
            "returncode": 0,
            "stdout_tail": "created https://github.com/acme/demo/issues/77",
            "stderr_tail": "",
            "error_type": "",
            "error_message": "",
        },
    )
    outputs = gate.build_github_output_values(
        closure_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.md"
        ),
    )

    assert outputs["workflow_release_follow_up_closure_status"] == "queued"
    assert outputs["workflow_release_follow_up_closure_decision"] == "queue_follow_up"
    assert outputs["workflow_release_follow_up_closure_exit_code"] == "0"
    assert outputs["workflow_release_follow_up_closure_should_queue"] == "true"
    assert outputs["workflow_release_follow_up_closure_attempted"] == "true"
    assert outputs["workflow_release_follow_up_closure_follow_up_queued"] == "true"
    assert outputs["workflow_release_follow_up_closure_escalation_queued"] == "false"
    assert outputs["workflow_release_follow_up_closure_target"] == "follow_up_queue"
    assert outputs["workflow_release_follow_up_closure_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_follow_up_closure_dispatch_status"] == "follow_up_required"
    assert outputs["workflow_release_follow_up_closure_run_id"] == "5566778899"
    assert outputs["workflow_release_follow_up_closure_run_url"].endswith(
        "/actions/runs/5566778899"
    )
    assert outputs["workflow_release_follow_up_closure_report_json"].endswith(
        "ci_workflow_release_follow_up_closure.json"
    )
    assert outputs["workflow_release_follow_up_closure_report_markdown"].endswith(
        "ci_workflow_release_follow_up_closure.md"
    )
