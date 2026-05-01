"""Contract tests for P2-46 Linux CI workflow release follow-up terminal publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_follow_up_terminal_publish_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_follow_up_terminal_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_follow_up_closure_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_follow_up_dispatch_report": (
            "/tmp/ci_workflow_release_follow_up_dispatch.json"
        ),
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
        "release_run_id": 7788990011,
        "release_run_url": "https://github.com/acme/demo/actions/runs/7788990011",
        "reason_codes": ["release_follow_up_closed_no_action"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_follow_up_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_follow_up_dispatch.json", "exists": True},
        ],
    }


def test_build_release_follow_up_terminal_publish_payload_closed(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_terminal_publish_gate_module()
    payload = _sample_release_follow_up_closure_payload()
    report_path = tmp_path / "ci_workflow_release_follow_up_closure.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_closure_report(report_path)
    terminal_payload = gate.build_release_follow_up_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_follow_up_terminal_publish_status"] == "published"
    assert terminal_payload["release_follow_up_terminal_publish_decision"] == "announce_closed"
    assert terminal_payload["release_follow_up_terminal_publish_exit_code"] == 0
    assert terminal_payload["follow_up_terminal_publish_should_notify"] is True
    assert terminal_payload["follow_up_terminal_requires_manual_action"] is False
    assert terminal_payload["follow_up_terminal_publish_channel"] == "release"
    assert terminal_payload["reason_codes"] == ["release_follow_up_terminal_closed"]


def test_build_release_follow_up_terminal_publish_payload_pending_queue(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_terminal_publish_gate_module()
    payload = _sample_release_follow_up_closure_payload()
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
    payload["follow_up_queue_url"] = ""
    payload["reason_codes"] = ["release_follow_up_dispatch_required"]
    report_path = tmp_path / "ci_workflow_release_follow_up_closure_pending.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_closure_report(report_path)
    terminal_payload = gate.build_release_follow_up_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_follow_up_terminal_publish_status"] == "pending_queue"
    assert (
        terminal_payload["release_follow_up_terminal_publish_decision"]
        == "announce_pending_queue"
    )
    assert terminal_payload["release_follow_up_terminal_publish_exit_code"] == 1
    assert terminal_payload["follow_up_terminal_publish_should_notify"] is True
    assert terminal_payload["follow_up_terminal_requires_manual_action"] is True
    assert terminal_payload["follow_up_terminal_publish_channel"] == "follow_up"
    assert "release_follow_up_terminal_pending_queue" in terminal_payload["reason_codes"]


def test_build_release_follow_up_terminal_publish_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_release_follow_up_terminal_publish_gate_module()
    payload = _sample_release_follow_up_closure_payload()
    payload["release_follow_up_closure_status"] = "closed"
    payload["release_follow_up_closure_decision"] = "no_action"
    payload["release_follow_up_closure_exit_code"] = 0
    payload["dispatch_target"] = "follow_up_queue"
    payload["follow_up_required"] = False
    report_path = tmp_path / "ci_workflow_release_follow_up_closure_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_closure_report(report_path)
    terminal_payload = gate.build_release_follow_up_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_follow_up_terminal_publish_status"] == "contract_failed"
    assert terminal_payload["release_follow_up_terminal_publish_decision"] == "abort_publish"
    assert terminal_payload["release_follow_up_terminal_publish_exit_code"] == 1
    assert "dispatch_target_mismatch_closed" in terminal_payload["structural_issues"]


def test_build_release_follow_up_terminal_publish_payload_queue_failed(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_terminal_publish_gate_module()
    payload = _sample_release_follow_up_closure_payload()
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
    payload["follow_up_error_type"] = ""
    payload["follow_up_error_message"] = ""
    payload["follow_up_repo"] = "acme/demo"
    payload["follow_up_queue_url"] = ""
    payload["reason_codes"] = ["release_follow_up_command_failed"]
    report_path = tmp_path / "ci_workflow_release_follow_up_closure_queue_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_closure_report(report_path)
    terminal_payload = gate.build_release_follow_up_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert terminal_payload["release_follow_up_terminal_publish_status"] == "queue_failed"
    assert (
        terminal_payload["release_follow_up_terminal_publish_decision"]
        == "announce_queue_failure"
    )
    assert terminal_payload["release_follow_up_terminal_publish_exit_code"] == 1
    assert terminal_payload["follow_up_terminal_publish_should_notify"] is True
    assert terminal_payload["follow_up_terminal_requires_manual_action"] is True
    assert terminal_payload["follow_up_terminal_publish_channel"] == "blocker"
    assert "release_follow_up_terminal_queue_failed" in terminal_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_follow_up_terminal_publish_gate_module()
    payload = _sample_release_follow_up_closure_payload()
    payload["release_follow_up_dispatch_status"] = "follow_up_required"
    payload["release_follow_up_dispatch_decision"] = "dispatch_follow_up"
    payload["release_follow_up_dispatch_exit_code"] = 1
    payload["follow_up_required"] = True
    payload["escalation_required"] = False
    payload["dispatch_target"] = "follow_up_queue"
    payload["should_queue_follow_up"] = True
    payload["release_follow_up_closure_status"] = "queued"
    payload["release_follow_up_closure_decision"] = "queue_follow_up"
    payload["release_follow_up_closure_exit_code"] = 0
    payload["follow_up_queue_attempted"] = True
    payload["follow_up_task_queued"] = True
    payload["escalation_task_queued"] = False
    payload["follow_up_command"] = "gh issue create --repo acme/demo"
    payload["follow_up_command_parts"] = ["gh", "issue", "create", "--repo", "acme/demo"]
    payload["follow_up_command_returncode"] = 0
    payload["follow_up_command_stdout_tail"] = "created https://github.com/acme/demo/issues/123"
    payload["follow_up_repo"] = "acme/demo"
    payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/123"
    payload["reason_codes"] = ["release_follow_up_queued"]
    report_path = tmp_path / "ci_workflow_release_follow_up_closure_queued.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_follow_up_closure_report(report_path)
    terminal_payload = gate.build_release_follow_up_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        terminal_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.md"
        ),
    )

    assert outputs["workflow_release_follow_up_terminal_publish_status"] == "published"
    assert outputs["workflow_release_follow_up_terminal_publish_decision"] == "announce_queued"
    assert outputs["workflow_release_follow_up_terminal_publish_exit_code"] == "0"
    assert outputs["workflow_release_follow_up_terminal_publish_should_notify"] == "true"
    assert outputs["workflow_release_follow_up_terminal_publish_manual_action"] == "false"
    assert outputs["workflow_release_follow_up_terminal_publish_channel"] == "follow_up"
    assert outputs["workflow_release_follow_up_terminal_publish_closure_status"] == "queued"
    assert outputs["workflow_release_follow_up_terminal_publish_queue_url"].endswith(
        "/issues/123"
    )
    assert outputs["workflow_release_follow_up_terminal_publish_run_id"] == "7788990011"
    assert outputs["workflow_release_follow_up_terminal_publish_run_url"].endswith(
        "/actions/runs/7788990011"
    )
    assert outputs["workflow_release_follow_up_terminal_publish_report_json"].endswith(
        "ci_workflow_release_follow_up_terminal_publish.json"
    )
    assert outputs["workflow_release_follow_up_terminal_publish_report_markdown"].endswith(
        "ci_workflow_release_follow_up_terminal_publish.md"
    )
