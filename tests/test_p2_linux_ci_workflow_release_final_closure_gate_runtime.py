"""Contract tests for P2-51 Linux CI workflow release final closure gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_closure_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_final_closure_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_closure_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_handoff_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_final_terminal_publish_report": "/tmp/ci_workflow_release_final_terminal_publish.json",
        "source_release_final_outcome_report": "/tmp/ci_workflow_release_final_outcome.json",
        "source_release_delivery_final_verdict_report": "/tmp/ci_workflow_release_delivery_final_verdict.json",
        "source_release_follow_up_final_verdict_report": "/tmp/ci_workflow_release_follow_up_final_verdict.json",
        "release_delivery_final_verdict_status": "completed",
        "release_delivery_final_verdict_decision": "close_release",
        "release_delivery_final_verdict_exit_code": 0,
        "release_follow_up_final_verdict_status": "completed",
        "release_follow_up_final_verdict_decision": "close_follow_up",
        "release_follow_up_final_verdict_exit_code": 0,
        "release_final_outcome_status": "released",
        "release_final_outcome_decision": "ship_and_close",
        "release_final_outcome_exit_code": 0,
        "release_final_terminal_publish_status": "published",
        "release_final_terminal_publish_decision": "announce_release_closure",
        "release_final_terminal_publish_exit_code": 0,
        "release_final_handoff_status": "completed",
        "release_final_handoff_decision": "handoff_release_closure",
        "release_final_handoff_exit_code": 0,
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "final_handoff_should_archive_release": True,
        "final_handoff_keep_follow_up_open": False,
        "final_handoff_should_page_owner": False,
        "final_handoff_target": "release",
        "release_final_handoff_summary": (
            "release_final_terminal_publish_status=published "
            "release_final_handoff_status=completed "
            "release_final_handoff_decision=handoff_release_closure"
        ),
        "reason_codes": ["release_final_handoff_completed"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "terminal_publish",
                "path": "/tmp/ci_workflow_release_final_terminal_publish.json",
                "exists": True,
            },
            {
                "source": "final_outcome",
                "path": "/tmp/ci_workflow_release_final_outcome.json",
                "exists": True,
            },
        ],
    }


def test_build_release_final_closure_payload_closed(tmp_path: Path):
    gate = _load_ci_workflow_release_final_closure_gate_module()
    handoff_payload = _sample_release_final_handoff_payload()

    handoff_path = tmp_path / "ci_workflow_release_final_handoff.json"
    handoff_path.write_text(json.dumps(handoff_payload, indent=2), encoding="utf-8")

    handoff_report = gate.load_release_final_handoff_report(handoff_path)
    closure_payload = gate.build_release_final_closure_payload(
        handoff_report,
        source_path=handoff_path.resolve(),
    )

    assert closure_payload["release_final_closure_status"] == "closed"
    assert closure_payload["release_final_closure_decision"] == "close_release"
    assert closure_payload["release_final_closure_exit_code"] == 0
    assert closure_payload["final_closure_is_closed"] is True
    assert closure_payload["final_closure_has_open_follow_up"] is False
    assert closure_payload["final_closure_should_page_owner"] is False
    assert closure_payload["final_closure_target"] == "release"
    assert "release_final_closure_closed" in closure_payload["reason_codes"]


def test_build_release_final_closure_payload_closed_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_closure_gate_module()
    handoff_payload = _sample_release_final_handoff_payload()
    handoff_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    handoff_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    handoff_payload["release_follow_up_final_verdict_exit_code"] = 1
    handoff_payload["release_final_outcome_status"] = "released_with_follow_up"
    handoff_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    handoff_payload["release_final_outcome_exit_code"] = 1
    handoff_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    handoff_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    handoff_payload["release_final_terminal_publish_exit_code"] = 1
    handoff_payload["release_final_handoff_status"] = "completed_with_follow_up"
    handoff_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    handoff_payload["release_final_handoff_exit_code"] = 1
    handoff_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    handoff_payload["final_handoff_should_archive_release"] = True
    handoff_payload["final_handoff_keep_follow_up_open"] = True
    handoff_payload["final_handoff_should_page_owner"] = False
    handoff_payload["final_handoff_target"] = "follow_up"
    handoff_payload["reason_codes"] = ["release_final_handoff_completed_with_follow_up"]

    handoff_path = tmp_path / "release_final_handoff_with_follow_up.json"
    handoff_path.write_text(json.dumps(handoff_payload, indent=2), encoding="utf-8")

    handoff_report = gate.load_release_final_handoff_report(handoff_path)
    closure_payload = gate.build_release_final_closure_payload(
        handoff_report,
        source_path=handoff_path.resolve(),
    )

    assert closure_payload["release_final_closure_status"] == "closed_with_follow_up"
    assert closure_payload["release_final_closure_decision"] == "close_with_follow_up"
    assert closure_payload["release_final_closure_exit_code"] == 1
    assert closure_payload["final_closure_is_closed"] is True
    assert closure_payload["final_closure_has_open_follow_up"] is True
    assert closure_payload["final_closure_should_page_owner"] is False
    assert closure_payload["final_closure_target"] == "follow_up"
    assert "release_final_closure_closed_with_follow_up" in closure_payload["reason_codes"]


def test_build_release_final_closure_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_closure_gate_module()
    handoff_payload = _sample_release_final_handoff_payload()
    handoff_payload["release_delivery_final_verdict_status"] = "blocked"
    handoff_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    handoff_payload["release_delivery_final_verdict_exit_code"] = 1
    handoff_payload["release_follow_up_final_verdict_status"] = "blocked"
    handoff_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    handoff_payload["release_follow_up_final_verdict_exit_code"] = 1
    handoff_payload["release_final_outcome_status"] = "blocked"
    handoff_payload["release_final_outcome_decision"] = "escalate_blocker"
    handoff_payload["release_final_outcome_exit_code"] = 1
    handoff_payload["release_final_terminal_publish_status"] = "blocked"
    handoff_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    handoff_payload["release_final_terminal_publish_exit_code"] = 1
    handoff_payload["release_final_handoff_status"] = "blocked"
    handoff_payload["release_final_handoff_decision"] = "handoff_blocker"
    handoff_payload["release_final_handoff_exit_code"] = 1
    handoff_payload["final_handoff_should_archive_release"] = False
    handoff_payload["final_handoff_keep_follow_up_open"] = True
    handoff_payload["final_handoff_should_page_owner"] = True
    handoff_payload["final_handoff_target"] = "blocker"
    handoff_payload["reason_codes"] = ["release_final_handoff_blocked"]

    handoff_path = tmp_path / "release_final_handoff_blocked.json"
    handoff_path.write_text(json.dumps(handoff_payload, indent=2), encoding="utf-8")

    handoff_report = gate.load_release_final_handoff_report(handoff_path)
    closure_payload = gate.build_release_final_closure_payload(
        handoff_report,
        source_path=handoff_path.resolve(),
    )

    assert closure_payload["release_final_closure_status"] == "blocked"
    assert closure_payload["release_final_closure_decision"] == "close_blocker"
    assert closure_payload["release_final_closure_exit_code"] == 1
    assert closure_payload["final_closure_is_closed"] is False
    assert closure_payload["final_closure_has_open_follow_up"] is True
    assert closure_payload["final_closure_should_page_owner"] is True
    assert closure_payload["final_closure_target"] == "blocker"
    assert "release_final_closure_blocked" in closure_payload["reason_codes"]


def test_build_release_final_closure_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_final_closure_gate_module()
    handoff_payload = _sample_release_final_handoff_payload()
    handoff_payload["release_final_handoff_status"] = "completed"
    handoff_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    handoff_payload["final_handoff_keep_follow_up_open"] = True
    handoff_payload["final_handoff_target"] = "follow_up"

    handoff_path = tmp_path / "release_final_handoff_mismatch.json"
    handoff_path.write_text(json.dumps(handoff_payload, indent=2), encoding="utf-8")

    handoff_report = gate.load_release_final_handoff_report(handoff_path)
    closure_payload = gate.build_release_final_closure_payload(
        handoff_report,
        source_path=handoff_path.resolve(),
    )

    assert closure_payload["release_final_closure_status"] == "contract_failed"
    assert closure_payload["release_final_closure_decision"] == "abort_close"
    assert closure_payload["release_final_closure_exit_code"] == 1
    assert "final_handoff_decision_mismatch" in closure_payload["structural_issues"]
    assert "final_handoff_keep_follow_up_open_mismatch" in closure_payload["structural_issues"]
    assert "final_handoff_target_mismatch" in closure_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_closure_gate_module()
    handoff_payload = _sample_release_final_handoff_payload()
    handoff_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    handoff_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    handoff_payload["release_follow_up_final_verdict_exit_code"] = 1
    handoff_payload["release_final_outcome_status"] = "released_with_follow_up"
    handoff_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    handoff_payload["release_final_outcome_exit_code"] = 1
    handoff_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    handoff_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    handoff_payload["release_final_terminal_publish_exit_code"] = 1
    handoff_payload["release_final_handoff_status"] = "completed_with_follow_up"
    handoff_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    handoff_payload["release_final_handoff_exit_code"] = 1
    handoff_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    handoff_payload["final_handoff_should_archive_release"] = True
    handoff_payload["final_handoff_keep_follow_up_open"] = True
    handoff_payload["final_handoff_should_page_owner"] = False
    handoff_payload["final_handoff_target"] = "follow_up"
    handoff_payload["reason_codes"] = ["release_final_handoff_completed_with_follow_up"]

    handoff_path = tmp_path / "release_final_handoff_output.json"
    handoff_path.write_text(json.dumps(handoff_payload, indent=2), encoding="utf-8")

    handoff_report = gate.load_release_final_handoff_report(handoff_path)
    closure_payload = gate.build_release_final_closure_payload(
        handoff_report,
        source_path=handoff_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        closure_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_closure.md"),
    )

    assert outputs["workflow_release_final_closure_status"] == "closed_with_follow_up"
    assert outputs["workflow_release_final_closure_decision"] == "close_with_follow_up"
    assert outputs["workflow_release_final_closure_exit_code"] == "1"
    assert outputs["workflow_release_final_closure_is_closed"] == "true"
    assert outputs["workflow_release_final_closure_has_open_follow_up"] == "true"
    assert outputs["workflow_release_final_closure_should_page_owner"] == "false"
    assert outputs["workflow_release_final_closure_target"] == "follow_up"
    assert outputs["workflow_release_final_closure_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_final_closure_run_id"] == "1234567890"
    assert outputs["workflow_release_final_closure_run_url"].endswith("/actions/runs/1234567890")
    assert outputs["workflow_release_final_closure_report_json"].endswith(
        "ci_workflow_release_final_closure.json"
    )
    assert outputs["workflow_release_final_closure_report_markdown"].endswith(
        "ci_workflow_release_final_closure.md"
    )
