"""Contract tests for P2-61 Linux CI workflow Linux validation verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_verdict_gate_module():
    script_path = Path("scripts") / "run_p2_lv_verdict_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_dispatch_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_terminal_verdict_report": "/tmp/ci_workflow_terminal_verdict.json",
        "project_root": "/tmp",
        "source_release_final_publish_archive_report": "/tmp/ci_workflow_release_final_publish_archive.json",
        "source_gate_manifest_drift_report": "/tmp/linux_gate_manifest_drift.json",
        "release_final_publish_archive_status": "archived",
        "gate_manifest_drift_status": "passed",
        "gate_manifest_drift_missing_runtime_tests": [],
        "gate_manifest_drift_missing_manifest_entries": [],
        "gate_manifest_drift_orphan_manifest_entries": [],
        "terminal_verdict_status": "ready_for_linux_validation",
        "terminal_verdict_decision": "proceed_linux_validation",
        "terminal_verdict_exit_code": 0,
        "terminal_verdict_should_proceed": True,
        "terminal_verdict_requires_manual_action": False,
        "terminal_verdict_channel": "release",
        "linux_validation_should_dispatch": True,
        "linux_validation_requires_manual_action": False,
        "linux_validation_channel": "release",
        "linux_validation_dispatch_status": "ready_dry_run",
        "linux_validation_dispatch_decision": "dispatch_linux_validation",
        "linux_validation_dispatch_exit_code": 0,
        "linux_validation_dispatch_attempted": False,
        "linux_validation_timeout_seconds": 7200,
        "linux_validation_command": "python scripts/run_p2_linux_unified_pipeline_gate.py --continue-on-failure",
        "linux_validation_command_parts": [
            "python",
            "scripts/run_p2_linux_unified_pipeline_gate.py",
            "--continue-on-failure",
        ],
        "dry_run": True,
        "command_returncode": None,
        "command_stdout_tail": "",
        "command_stderr_tail": "",
        "dispatch_error_type": "",
        "dispatch_error_message": "",
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "linux_validation_dispatch_summary": (
            "terminal_verdict_status=ready_for_linux_validation "
            "terminal_verdict_decision=proceed_linux_validation "
            "linux_validation_dispatch_status=ready_dry_run "
            "linux_validation_dispatch_decision=dispatch_linux_validation"
        ),
        "reason_codes": ["linux_validation_dispatch_ready_dry_run"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "final_publish_archive",
                "path": "/tmp/ci_workflow_release_final_publish_archive.json",
                "exists": True,
            },
            {
                "source": "manifest_drift",
                "path": "/tmp/linux_gate_manifest_drift.json",
                "exists": True,
            },
            {
                "source": "terminal_verdict",
                "path": "/tmp/ci_workflow_terminal_verdict.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_verdict_payload_validated_from_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_verdict_gate_module()
    dispatch_payload = _sample_linux_validation_dispatch_payload()
    dispatch_path = tmp_path / "ci_workflow_linux_validation_dispatch.json"
    dispatch_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_dispatch_report(dispatch_path)
    payload = gate.build_linux_validation_verdict_payload(
        dispatch_report,
        source_path=dispatch_path.resolve(),
    )

    assert payload["linux_validation_verdict_status"] == "validated"
    assert payload["linux_validation_verdict_decision"] == "accept_linux_validation"
    assert payload["linux_validation_verdict_exit_code"] == 0
    assert payload["linux_validation_verdict_should_accept"] is True
    assert payload["linux_validation_verdict_requires_manual_action"] is False
    assert payload["linux_validation_verdict_channel"] == "release"
    assert payload["linux_validation_dispatch_status"] == "ready_dry_run"
    assert payload["linux_validation_dispatch_attempted"] is False


def test_build_linux_validation_verdict_payload_validated_with_follow_up_from_dry_run(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_verdict_gate_module()
    dispatch_payload = _sample_linux_validation_dispatch_payload()
    dispatch_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    dispatch_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    dispatch_payload["terminal_verdict_exit_code"] = 1
    dispatch_payload["terminal_verdict_channel"] = "follow_up"
    dispatch_payload["linux_validation_channel"] = "follow_up"
    dispatch_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    dispatch_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    dispatch_payload["reason_codes"] = ["linux_validation_dispatch_ready_with_follow_up_dry_run"]

    dispatch_path = tmp_path / "ci_workflow_linux_validation_dispatch_follow_up.json"
    dispatch_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_dispatch_report(dispatch_path)
    payload = gate.build_linux_validation_verdict_payload(
        dispatch_report,
        source_path=dispatch_path.resolve(),
    )

    assert payload["linux_validation_verdict_status"] == "validated_with_follow_up"
    assert (
        payload["linux_validation_verdict_decision"]
        == "accept_linux_validation_with_follow_up"
    )
    assert payload["linux_validation_verdict_exit_code"] == 1
    assert payload["linux_validation_verdict_should_accept"] is True
    assert payload["linux_validation_verdict_requires_manual_action"] is False
    assert payload["linux_validation_verdict_channel"] == "follow_up"
    assert payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_verdict_payload_validation_failed_from_dispatch_failed(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_verdict_gate_module()
    dispatch_payload = _sample_linux_validation_dispatch_payload()
    dispatch_payload["dry_run"] = False
    dispatch_payload["linux_validation_dispatch_status"] = "dispatch_failed"
    dispatch_payload["linux_validation_dispatch_decision"] = "dispatch_linux_validation"
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_dispatch_attempted"] = True
    dispatch_payload["command_returncode"] = 124
    dispatch_payload["dispatch_error_type"] = "timeout"
    dispatch_payload["dispatch_error_message"] = "linux validation command timeout after 7200s"
    dispatch_payload["reason_codes"] = ["linux_validation_dispatch_timeout"]

    dispatch_path = tmp_path / "ci_workflow_linux_validation_dispatch_failed.json"
    dispatch_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_dispatch_report(dispatch_path)
    payload = gate.build_linux_validation_verdict_payload(
        dispatch_report,
        source_path=dispatch_path.resolve(),
    )

    assert payload["linux_validation_verdict_status"] == "validation_failed"
    assert payload["linux_validation_verdict_decision"] == "escalate_linux_validation_failure"
    assert payload["linux_validation_verdict_exit_code"] == 1
    assert payload["linux_validation_verdict_should_accept"] is False
    assert payload["linux_validation_verdict_requires_manual_action"] is True
    assert payload["linux_validation_verdict_channel"] == "blocker"
    assert "linux_validation_verdict_dispatch_timeout" in payload["reason_codes"]


def test_build_linux_validation_verdict_payload_blocked_from_dispatch_blocked(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_verdict_gate_module()
    dispatch_payload = _sample_linux_validation_dispatch_payload()
    dispatch_payload["terminal_verdict_status"] = "blocked"
    dispatch_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    dispatch_payload["terminal_verdict_exit_code"] = 1
    dispatch_payload["terminal_verdict_should_proceed"] = False
    dispatch_payload["terminal_verdict_requires_manual_action"] = True
    dispatch_payload["terminal_verdict_channel"] = "blocker"
    dispatch_payload["linux_validation_should_dispatch"] = False
    dispatch_payload["linux_validation_requires_manual_action"] = True
    dispatch_payload["linux_validation_channel"] = "blocker"
    dispatch_payload["linux_validation_dispatch_status"] = "blocked"
    dispatch_payload["linux_validation_dispatch_decision"] = "hold_linux_validation_blocker"
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_dispatch_attempted"] = False
    dispatch_payload["reason_codes"] = ["linux_validation_dispatch_blocked"]

    dispatch_path = tmp_path / "ci_workflow_linux_validation_dispatch_blocked.json"
    dispatch_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_dispatch_report(dispatch_path)
    payload = gate.build_linux_validation_verdict_payload(
        dispatch_report,
        source_path=dispatch_path.resolve(),
    )

    assert payload["linux_validation_verdict_status"] == "blocked"
    assert payload["linux_validation_verdict_decision"] == "hold_linux_validation_blocker"
    assert payload["linux_validation_verdict_exit_code"] == 1
    assert payload["linux_validation_verdict_should_accept"] is False
    assert payload["linux_validation_verdict_requires_manual_action"] is True
    assert payload["linux_validation_verdict_channel"] == "blocker"
    assert "linux_validation_verdict_blocked" in payload["reason_codes"]


def test_build_linux_validation_verdict_payload_rejects_dispatch_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_verdict_gate_module()
    dispatch_payload = _sample_linux_validation_dispatch_payload()
    dispatch_payload["linux_validation_dispatch_status"] = "dispatched"
    dispatch_payload["linux_validation_dispatch_decision"] = "dispatch_linux_validation_with_follow_up"
    dispatch_payload["linux_validation_channel"] = "release"
    dispatch_payload["linux_validation_dispatch_attempted"] = False
    dispatch_payload["command_returncode"] = None
    dispatch_payload["evidence_manifest"][0]["exists"] = False

    dispatch_path = tmp_path / "ci_workflow_linux_validation_dispatch_mismatch.json"
    dispatch_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_dispatch_report(dispatch_path)
    payload = gate.build_linux_validation_verdict_payload(
        dispatch_report,
        source_path=dispatch_path.resolve(),
    )

    assert payload["linux_validation_verdict_status"] == "contract_failed"
    assert payload["linux_validation_verdict_decision"] == "abort_linux_validation_verdict"
    assert payload["linux_validation_verdict_exit_code"] == 1
    assert payload["linux_validation_verdict_should_accept"] is False
    assert payload["linux_validation_verdict_requires_manual_action"] is True
    assert payload["linux_validation_verdict_channel"] == "blocker"
    assert "linux_validation_dispatch_decision_mismatch" in payload["structural_issues"]
    assert "linux_validation_dispatch_attempted_mismatch" in payload["structural_issues"]
    assert "linux_validation_dispatch_evidence_missing" in payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_verdict_gate_module()
    dispatch_payload = _sample_linux_validation_dispatch_payload()
    dispatch_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    dispatch_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    dispatch_payload["terminal_verdict_exit_code"] = 1
    dispatch_payload["terminal_verdict_channel"] = "follow_up"
    dispatch_payload["linux_validation_channel"] = "follow_up"
    dispatch_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    dispatch_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    dispatch_payload["reason_codes"] = ["linux_validation_dispatch_ready_with_follow_up_dry_run"]

    dispatch_path = tmp_path / "ci_workflow_linux_validation_dispatch_outputs.json"
    dispatch_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_dispatch_report(dispatch_path)
    payload = gate.build_linux_validation_verdict_payload(
        dispatch_report,
        source_path=dispatch_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.md"
        ),
    )

    assert outputs["workflow_linux_validation_verdict_status"] == "validated_with_follow_up"
    assert (
        outputs["workflow_linux_validation_verdict_decision"]
        == "accept_linux_validation_with_follow_up"
    )
    assert outputs["workflow_linux_validation_verdict_exit_code"] == "1"
    assert outputs["workflow_linux_validation_verdict_should_accept"] == "true"
    assert outputs["workflow_linux_validation_verdict_requires_manual_action"] == "false"
    assert outputs["workflow_linux_validation_verdict_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_verdict_dispatch_status"] == "ready_with_follow_up_dry_run"
    assert outputs["workflow_linux_validation_verdict_dispatch_attempted"] == "false"
    assert outputs["workflow_linux_validation_verdict_command_returncode"] == ""
    assert (
        outputs["workflow_linux_validation_verdict_terminal_status"]
        == "ready_with_follow_up_for_linux_validation"
    )
    assert outputs["workflow_linux_validation_verdict_gate_manifest_drift_status"] == "passed"
    assert outputs["workflow_linux_validation_verdict_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_linux_validation_verdict_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_verdict_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_verdict_report_json"].endswith(
        "ci_workflow_linux_validation_verdict.json"
    )
    assert outputs["workflow_linux_validation_verdict_report_markdown"].endswith(
        "ci_workflow_linux_validation_verdict.md"
    )
