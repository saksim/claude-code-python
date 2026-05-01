"""Contract tests for P2-48 Linux CI workflow release final outcome gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_outcome_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_final_outcome_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_outcome_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_delivery_final_verdict_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_delivery_terminal_publish_report": "/tmp/ci_workflow_release_delivery_terminal_publish.json",
        "release_delivery_final_verdict_status": "completed",
        "release_delivery_final_verdict_decision": "close_release",
        "release_delivery_final_verdict_exit_code": 0,
        "final_should_close_release": True,
        "final_should_open_follow_up": False,
        "final_should_page_owner": False,
        "final_announcement_target": "release",
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "reason_codes": ["release_delivery_final_completed"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_delivery_terminal_publish.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_delivery.json", "exists": True},
        ],
    }


def _sample_release_follow_up_final_verdict_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_follow_up_terminal_publish_report": "/tmp/ci_workflow_release_follow_up_terminal_publish.json",
        "release_follow_up_final_verdict_status": "completed",
        "release_follow_up_final_verdict_decision": "close_follow_up",
        "release_follow_up_final_verdict_exit_code": 0,
        "final_should_close_follow_up": True,
        "final_should_open_follow_up": False,
        "final_should_page_owner": False,
        "final_announcement_target": "release",
        "follow_up_queue_url": "",
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "reason_codes": ["release_follow_up_final_completed_closed"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_follow_up_terminal_publish.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_follow_up_closure.json", "exists": True},
        ],
    }


def test_build_release_final_outcome_payload_released(tmp_path: Path):
    gate = _load_ci_workflow_release_final_outcome_gate_module()
    delivery_payload = _sample_release_delivery_final_verdict_payload()
    follow_payload = _sample_release_follow_up_final_verdict_payload()

    delivery_path = tmp_path / "ci_workflow_release_delivery_final_verdict.json"
    follow_path = tmp_path / "ci_workflow_release_follow_up_final_verdict.json"
    delivery_path.write_text(json.dumps(delivery_payload, indent=2), encoding="utf-8")
    follow_path.write_text(json.dumps(follow_payload, indent=2), encoding="utf-8")

    delivery_report = gate.load_release_delivery_final_verdict_report(delivery_path)
    follow_report = gate.load_release_follow_up_final_verdict_report(follow_path)
    final_payload = gate.build_release_final_outcome_payload(
        delivery_report,
        follow_report,
        delivery_source_path=delivery_path.resolve(),
        follow_up_source_path=follow_path.resolve(),
    )

    assert final_payload["release_final_outcome_status"] == "released"
    assert final_payload["release_final_outcome_decision"] == "ship_and_close"
    assert final_payload["release_final_outcome_exit_code"] == 0
    assert final_payload["final_should_ship_release"] is True
    assert final_payload["final_follow_up_open"] is False
    assert final_payload["final_should_page_owner"] is False
    assert final_payload["final_outcome_target"] == "release"
    assert "release_final_outcome_released" in final_payload["reason_codes"]


def test_build_release_final_outcome_payload_released_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_outcome_gate_module()
    delivery_payload = _sample_release_delivery_final_verdict_payload()
    follow_payload = _sample_release_follow_up_final_verdict_payload()
    follow_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    follow_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    follow_payload["release_follow_up_final_verdict_exit_code"] = 1
    follow_payload["final_should_close_follow_up"] = False
    follow_payload["final_should_open_follow_up"] = True
    follow_payload["final_should_page_owner"] = False
    follow_payload["final_announcement_target"] = "follow_up"
    follow_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    follow_payload["reason_codes"] = ["release_follow_up_final_pending_queue"]

    delivery_path = tmp_path / "delivery_requires_follow_up.json"
    follow_path = tmp_path / "follow_up_requires_follow_up.json"
    delivery_path.write_text(json.dumps(delivery_payload, indent=2), encoding="utf-8")
    follow_path.write_text(json.dumps(follow_payload, indent=2), encoding="utf-8")

    delivery_report = gate.load_release_delivery_final_verdict_report(delivery_path)
    follow_report = gate.load_release_follow_up_final_verdict_report(follow_path)
    final_payload = gate.build_release_final_outcome_payload(
        delivery_report,
        follow_report,
        delivery_source_path=delivery_path.resolve(),
        follow_up_source_path=follow_path.resolve(),
    )

    assert final_payload["release_final_outcome_status"] == "released_with_follow_up"
    assert final_payload["release_final_outcome_decision"] == "ship_with_follow_up_open"
    assert final_payload["release_final_outcome_exit_code"] == 1
    assert final_payload["final_should_ship_release"] is True
    assert final_payload["final_follow_up_open"] is True
    assert final_payload["final_should_page_owner"] is False
    assert final_payload["final_outcome_target"] == "follow_up"
    assert "release_final_outcome_released_with_follow_up" in final_payload["reason_codes"]


def test_build_release_final_outcome_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_outcome_gate_module()
    delivery_payload = _sample_release_delivery_final_verdict_payload()
    follow_payload = _sample_release_follow_up_final_verdict_payload()
    delivery_payload["release_delivery_final_verdict_status"] = "blocked"
    delivery_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    delivery_payload["release_delivery_final_verdict_exit_code"] = 1
    delivery_payload["final_should_close_release"] = False
    delivery_payload["final_should_open_follow_up"] = True
    delivery_payload["final_should_page_owner"] = True
    delivery_payload["final_announcement_target"] = "blocker"
    delivery_payload["reason_codes"] = ["release_delivery_final_blocked"]
    follow_payload["release_follow_up_final_verdict_status"] = "blocked"
    follow_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    follow_payload["release_follow_up_final_verdict_exit_code"] = 1
    follow_payload["final_should_close_follow_up"] = False
    follow_payload["final_should_open_follow_up"] = True
    follow_payload["final_should_page_owner"] = True
    follow_payload["final_announcement_target"] = "blocker"
    follow_payload["reason_codes"] = ["release_follow_up_final_queue_failed"]

    delivery_path = tmp_path / "delivery_blocked.json"
    follow_path = tmp_path / "follow_blocked.json"
    delivery_path.write_text(json.dumps(delivery_payload, indent=2), encoding="utf-8")
    follow_path.write_text(json.dumps(follow_payload, indent=2), encoding="utf-8")

    delivery_report = gate.load_release_delivery_final_verdict_report(delivery_path)
    follow_report = gate.load_release_follow_up_final_verdict_report(follow_path)
    final_payload = gate.build_release_final_outcome_payload(
        delivery_report,
        follow_report,
        delivery_source_path=delivery_path.resolve(),
        follow_up_source_path=follow_path.resolve(),
    )

    assert final_payload["release_final_outcome_status"] == "blocked"
    assert final_payload["release_final_outcome_decision"] == "escalate_blocker"
    assert final_payload["release_final_outcome_exit_code"] == 1
    assert final_payload["final_should_ship_release"] is False
    assert final_payload["final_follow_up_open"] is True
    assert final_payload["final_should_page_owner"] is True
    assert final_payload["final_outcome_target"] == "blocker"
    assert "release_final_outcome_blocked" in final_payload["reason_codes"]


def test_build_release_final_outcome_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_final_outcome_gate_module()
    delivery_payload = _sample_release_delivery_final_verdict_payload()
    follow_payload = _sample_release_follow_up_final_verdict_payload()
    delivery_payload["release_delivery_final_verdict_status"] = "completed"
    delivery_payload["release_delivery_final_verdict_decision"] = "open_follow_up"
    delivery_payload["final_should_close_release"] = False
    follow_payload["release_follow_up_final_verdict_status"] = "completed"
    follow_payload["release_follow_up_final_verdict_decision"] = "close_follow_up"
    follow_payload["release_run_id"] = 99887766
    follow_payload["release_run_url"] = "https://github.com/acme/demo/actions/runs/99887766"

    delivery_path = tmp_path / "delivery_mismatch.json"
    follow_path = tmp_path / "follow_mismatch.json"
    delivery_path.write_text(json.dumps(delivery_payload, indent=2), encoding="utf-8")
    follow_path.write_text(json.dumps(follow_payload, indent=2), encoding="utf-8")

    delivery_report = gate.load_release_delivery_final_verdict_report(delivery_path)
    follow_report = gate.load_release_follow_up_final_verdict_report(follow_path)
    final_payload = gate.build_release_final_outcome_payload(
        delivery_report,
        follow_report,
        delivery_source_path=delivery_path.resolve(),
        follow_up_source_path=follow_path.resolve(),
    )

    assert final_payload["release_final_outcome_status"] == "contract_failed"
    assert final_payload["release_final_outcome_decision"] == "abort_outcome"
    assert final_payload["release_final_outcome_exit_code"] == 1
    assert "delivery_decision_mismatch" in final_payload["structural_issues"]
    assert "release_run_id_mismatch" in final_payload["structural_issues"]
    assert "release_run_url_mismatch" in final_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_outcome_gate_module()
    delivery_payload = _sample_release_delivery_final_verdict_payload()
    follow_payload = _sample_release_follow_up_final_verdict_payload()
    follow_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    follow_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    follow_payload["release_follow_up_final_verdict_exit_code"] = 1
    follow_payload["final_should_close_follow_up"] = False
    follow_payload["final_should_open_follow_up"] = True
    follow_payload["final_should_page_owner"] = False
    follow_payload["final_announcement_target"] = "follow_up"
    follow_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    follow_payload["reason_codes"] = ["release_follow_up_final_pending_queue"]

    delivery_path = tmp_path / "delivery_output.json"
    follow_path = tmp_path / "follow_output.json"
    delivery_path.write_text(json.dumps(delivery_payload, indent=2), encoding="utf-8")
    follow_path.write_text(json.dumps(follow_payload, indent=2), encoding="utf-8")

    delivery_report = gate.load_release_delivery_final_verdict_report(delivery_path)
    follow_report = gate.load_release_follow_up_final_verdict_report(follow_path)
    final_payload = gate.build_release_final_outcome_payload(
        delivery_report,
        follow_report,
        delivery_source_path=delivery_path.resolve(),
        follow_up_source_path=follow_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        final_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.md"),
    )

    assert outputs["workflow_release_final_outcome_status"] == "released_with_follow_up"
    assert outputs["workflow_release_final_outcome_decision"] == "ship_with_follow_up_open"
    assert outputs["workflow_release_final_outcome_exit_code"] == "1"
    assert outputs["workflow_release_final_should_ship_release"] == "true"
    assert outputs["workflow_release_final_follow_up_open"] == "true"
    assert outputs["workflow_release_final_should_page_owner"] == "false"
    assert outputs["workflow_release_final_target"] == "follow_up"
    assert outputs["workflow_release_final_delivery_status"] == "completed"
    assert outputs["workflow_release_final_follow_up_status"] == "requires_follow_up"
    assert outputs["workflow_release_final_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_final_run_id"] == "1234567890"
    assert outputs["workflow_release_final_run_url"].endswith("/actions/runs/1234567890")
    assert outputs["workflow_release_final_report_json"].endswith(
        "ci_workflow_release_final_outcome.json"
    )
    assert outputs["workflow_release_final_report_markdown"].endswith(
        "ci_workflow_release_final_outcome.md"
    )
