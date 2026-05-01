"""Contract tests for P2-47 Linux CI workflow release follow-up final verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_follow_up_final_verdict_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_follow_up_final_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_follow_up_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_follow_up_closure_report": "/tmp/ci_workflow_release_follow_up_closure.json",
        "source_release_follow_up_dispatch_report": "/tmp/ci_workflow_release_follow_up_dispatch.json",
        "project_root": "/tmp/project",
        "release_follow_up_dispatch_status": "closed",
        "release_follow_up_dispatch_decision": "no_action",
        "release_follow_up_dispatch_exit_code": 0,
        "follow_up_required": False,
        "escalation_required": False,
        "dispatch_target": "none",
        "should_queue_follow_up": False,
        "release_follow_up_closure_status": "closed",
        "release_follow_up_closure_decision": "no_action",
        "release_follow_up_closure_exit_code": 0,
        "follow_up_queue_attempted": False,
        "follow_up_task_queued": False,
        "escalation_task_queued": False,
        "follow_up_command": "",
        "follow_up_command_parts": [],
        "follow_up_command_returncode": None,
        "follow_up_command_stdout_tail": "",
        "follow_up_command_stderr_tail": "",
        "follow_up_error_type": "",
        "follow_up_error_message": "",
        "follow_up_repo": "",
        "follow_up_label": "release-follow-up",
        "follow_up_title_prefix": "[release-follow-up]",
        "follow_up_queue_url": "",
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "release_follow_up_terminal_publish_status": "published",
        "release_follow_up_terminal_publish_decision": "announce_closed",
        "release_follow_up_terminal_publish_exit_code": 0,
        "follow_up_terminal_publish_should_notify": True,
        "follow_up_terminal_requires_manual_action": False,
        "follow_up_terminal_publish_channel": "release",
        "release_follow_up_terminal_publish_summary": (
            "release_follow_up_closure_status=closed "
            "release_follow_up_terminal_publish_status=published "
            "release_follow_up_terminal_publish_decision=announce_closed"
        ),
        "reason_codes": ["release_follow_up_terminal_closed"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_follow_up_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_follow_up_dispatch.json", "exists": True},
        ],
    }


def test_build_release_follow_up_final_verdict_payload_completed(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_final_verdict_gate_module()
    payload = _sample_release_follow_up_terminal_publish_payload()
    report_path = tmp_path / "ci_workflow_release_follow_up_terminal_publish.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_terminal_publish_report(report_path)
    final_payload = gate.build_release_follow_up_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_follow_up_final_verdict_status"] == "completed"
    assert final_payload["release_follow_up_final_verdict_decision"] == "close_follow_up"
    assert final_payload["release_follow_up_final_verdict_exit_code"] == 0
    assert final_payload["final_should_close_follow_up"] is True
    assert final_payload["final_should_open_follow_up"] is False
    assert final_payload["final_should_page_owner"] is False
    assert final_payload["final_announcement_target"] == "release"
    assert final_payload["reason_codes"] == ["release_follow_up_final_completed_closed"]


def test_build_release_follow_up_final_verdict_payload_requires_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_final_verdict_gate_module()
    payload = _sample_release_follow_up_terminal_publish_payload()
    payload["release_follow_up_dispatch_status"] = "follow_up_required"
    payload["release_follow_up_dispatch_decision"] = "dispatch_follow_up"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["escalation_required"] = False
    payload["dispatch_target"] = "follow_up_queue"
    payload["should_queue_follow_up"] = True
    payload["release_follow_up_closure_status"] = "queued_dry_run"
    payload["release_follow_up_closure_decision"] = "queue_follow_up"
    payload["release_follow_up_closure_exit_code"] = 0
    payload["follow_up_queue_attempted"] = False
    payload["follow_up_task_queued"] = False
    payload["escalation_task_queued"] = False
    payload["follow_up_command"] = "gh issue create --repo acme/demo"
    payload["follow_up_command_parts"] = ["gh", "issue", "create", "--repo", "acme/demo"]
    payload["follow_up_repo"] = "acme/demo"
    payload["release_follow_up_terminal_publish_status"] = "pending_queue"
    payload["release_follow_up_terminal_publish_decision"] = "announce_pending_queue"
    payload["release_follow_up_terminal_publish_exit_code"] = 1
    payload["follow_up_terminal_publish_should_notify"] = True
    payload["follow_up_terminal_requires_manual_action"] = True
    payload["follow_up_terminal_publish_channel"] = "follow_up"
    payload["reason_codes"] = ["release_follow_up_terminal_pending_queue"]
    report_path = tmp_path / "ci_workflow_release_follow_up_terminal_publish_pending.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_terminal_publish_report(report_path)
    final_payload = gate.build_release_follow_up_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_follow_up_final_verdict_status"] == "requires_follow_up"
    assert final_payload["release_follow_up_final_verdict_decision"] == "keep_follow_up_open"
    assert final_payload["release_follow_up_final_verdict_exit_code"] == 1
    assert final_payload["final_should_close_follow_up"] is False
    assert final_payload["final_should_open_follow_up"] is True
    assert final_payload["final_should_page_owner"] is False
    assert final_payload["final_announcement_target"] == "follow_up"
    assert "release_follow_up_final_pending_queue" in final_payload["reason_codes"]


def test_build_release_follow_up_final_verdict_payload_queue_failed_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_final_verdict_gate_module()
    payload = _sample_release_follow_up_terminal_publish_payload()
    payload["release_follow_up_dispatch_status"] = "escalated"
    payload["release_follow_up_dispatch_decision"] = "dispatch_escalation"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["escalation_required"] = True
    payload["dispatch_target"] = "incident_commander"
    payload["should_queue_follow_up"] = True
    payload["release_follow_up_closure_status"] = "queue_failed"
    payload["release_follow_up_closure_decision"] = "abort_queue"
    payload["release_follow_up_closure_exit_code"] = 1
    payload["follow_up_queue_attempted"] = True
    payload["follow_up_task_queued"] = False
    payload["escalation_task_queued"] = False
    payload["follow_up_command"] = "gh issue create --repo acme/demo"
    payload["follow_up_command_parts"] = ["gh", "issue", "create", "--repo", "acme/demo"]
    payload["follow_up_command_returncode"] = 1
    payload["follow_up_command_stderr_tail"] = "create failed"
    payload["follow_up_repo"] = "acme/demo"
    payload["release_follow_up_terminal_publish_status"] = "queue_failed"
    payload["release_follow_up_terminal_publish_decision"] = "announce_queue_failure"
    payload["release_follow_up_terminal_publish_exit_code"] = 1
    payload["follow_up_terminal_publish_should_notify"] = True
    payload["follow_up_terminal_requires_manual_action"] = True
    payload["follow_up_terminal_publish_channel"] = "blocker"
    payload["reason_codes"] = ["release_follow_up_terminal_queue_failed"]
    report_path = tmp_path / "ci_workflow_release_follow_up_terminal_publish_queue_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_terminal_publish_report(report_path)
    final_payload = gate.build_release_follow_up_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_follow_up_final_verdict_status"] == "blocked"
    assert final_payload["release_follow_up_final_verdict_decision"] == "escalate_queue_failure"
    assert final_payload["release_follow_up_final_verdict_exit_code"] == 1
    assert final_payload["final_should_close_follow_up"] is False
    assert final_payload["final_should_open_follow_up"] is True
    assert final_payload["final_should_page_owner"] is True
    assert final_payload["final_announcement_target"] == "blocker"
    assert "release_follow_up_final_queue_failed" in final_payload["reason_codes"]


def test_build_release_follow_up_final_verdict_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_release_follow_up_final_verdict_gate_module()
    payload = _sample_release_follow_up_terminal_publish_payload()
    payload["release_follow_up_terminal_publish_status"] = "published"
    payload["release_follow_up_terminal_publish_decision"] = "announce_closed"
    payload["release_follow_up_terminal_publish_exit_code"] = 0
    payload["follow_up_terminal_publish_should_notify"] = True
    payload["follow_up_terminal_requires_manual_action"] = False
    payload["follow_up_terminal_publish_channel"] = "release"
    payload["release_follow_up_closure_status"] = "closed"
    payload["release_follow_up_closure_decision"] = "no_action"
    payload["dispatch_target"] = "follow_up_queue"
    report_path = tmp_path / "ci_workflow_release_follow_up_terminal_publish_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_terminal_publish_report(report_path)
    final_payload = gate.build_release_follow_up_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["release_follow_up_final_verdict_status"] == "contract_failed"
    assert final_payload["release_follow_up_final_verdict_decision"] == "abort_close"
    assert final_payload["release_follow_up_final_verdict_exit_code"] == 1
    assert "dispatch_target_mismatch_closed" in final_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_final_verdict_gate_module()
    payload = _sample_release_follow_up_terminal_publish_payload()
    payload["release_follow_up_dispatch_status"] = "follow_up_required"
    payload["release_follow_up_dispatch_decision"] = "dispatch_follow_up"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["dispatch_target"] = "follow_up_queue"
    payload["should_queue_follow_up"] = True
    payload["release_follow_up_closure_status"] = "queued"
    payload["release_follow_up_closure_decision"] = "queue_follow_up"
    payload["release_follow_up_closure_exit_code"] = 0
    payload["follow_up_queue_attempted"] = True
    payload["follow_up_task_queued"] = True
    payload["follow_up_command"] = "gh issue create --repo acme/demo"
    payload["follow_up_command_parts"] = ["gh", "issue", "create", "--repo", "acme/demo"]
    payload["follow_up_command_returncode"] = 0
    payload["follow_up_command_stdout_tail"] = "created https://github.com/acme/demo/issues/123"
    payload["follow_up_repo"] = "acme/demo"
    payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/123"
    payload["release_follow_up_terminal_publish_status"] = "published"
    payload["release_follow_up_terminal_publish_decision"] = "announce_queued"
    payload["release_follow_up_terminal_publish_exit_code"] = 0
    payload["follow_up_terminal_publish_channel"] = "follow_up"
    payload["reason_codes"] = ["release_follow_up_terminal_queued"]
    report_path = tmp_path / "ci_workflow_release_follow_up_terminal_publish_queued.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_terminal_publish_report(report_path)
    final_payload = gate.build_release_follow_up_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        final_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.md"
        ),
    )

    assert outputs["workflow_release_follow_up_final_verdict_status"] == "completed"
    assert outputs["workflow_release_follow_up_final_verdict_decision"] == "close_follow_up"
    assert outputs["workflow_release_follow_up_final_verdict_exit_code"] == "0"
    assert outputs["workflow_release_follow_up_final_should_close_follow_up"] == "true"
    assert outputs["workflow_release_follow_up_final_should_open_follow_up"] == "false"
    assert outputs["workflow_release_follow_up_final_should_page_owner"] == "false"
    assert outputs["workflow_release_follow_up_final_announcement_target"] == "follow_up"
    assert outputs["workflow_release_follow_up_final_terminal_publish_status"] == "published"
    assert outputs["workflow_release_follow_up_final_terminal_publish_channel"] == "follow_up"
    assert outputs["workflow_release_follow_up_final_queue_url"].endswith("/issues/123")
    assert outputs["workflow_release_follow_up_final_run_id"] == "9988776655"
    assert outputs["workflow_release_follow_up_final_run_url"].endswith(
        "/actions/runs/9988776655"
    )
    assert outputs["workflow_release_follow_up_final_report_json"].endswith(
        "ci_workflow_release_follow_up_final_verdict.json"
    )
    assert outputs["workflow_release_follow_up_final_report_markdown"].endswith(
        "ci_workflow_release_follow_up_final_verdict.md"
    )
