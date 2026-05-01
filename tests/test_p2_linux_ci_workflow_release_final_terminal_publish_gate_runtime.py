"""Contract tests for P2-49 Linux CI workflow release final terminal publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_terminal_publish_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_terminal_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_outcome_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_delivery_final_verdict_report": "/tmp/ci_workflow_release_delivery_final_verdict.json",
        "source_release_follow_up_final_verdict_report": "/tmp/ci_workflow_release_follow_up_final_verdict.json",
        "release_delivery_final_verdict_status": "completed",
        "release_delivery_final_verdict_decision": "close_release",
        "release_delivery_final_verdict_exit_code": 0,
        "release_follow_up_final_verdict_status": "completed",
        "release_follow_up_final_verdict_decision": "close_follow_up",
        "release_follow_up_final_verdict_exit_code": 0,
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "release_final_outcome_status": "released",
        "release_final_outcome_decision": "ship_and_close",
        "release_final_outcome_exit_code": 0,
        "final_should_ship_release": True,
        "final_follow_up_open": False,
        "final_should_page_owner": False,
        "final_outcome_target": "release",
        "release_final_outcome_summary": (
            "release_delivery_final_verdict_status=completed "
            "release_follow_up_final_verdict_status=completed "
            "release_final_outcome_status=released "
            "release_final_outcome_decision=ship_and_close"
        ),
        "reason_codes": ["release_final_outcome_released"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"source": "delivery", "path": "/tmp/ci_workflow_release_delivery_final_verdict.json", "exists": True},
            {"source": "follow_up", "path": "/tmp/ci_workflow_release_follow_up_final_verdict.json", "exists": True},
        ],
    }


def test_build_release_final_terminal_publish_payload_published(tmp_path: Path):
    gate = _load_ci_workflow_release_final_terminal_publish_gate_module()
    outcome_payload = _sample_release_final_outcome_payload()

    outcome_path = tmp_path / "ci_workflow_release_final_outcome.json"
    outcome_path.write_text(json.dumps(outcome_payload, indent=2), encoding="utf-8")

    outcome_report = gate.load_release_final_outcome_report(outcome_path)
    final_payload = gate.build_release_final_terminal_publish_payload(
        outcome_report,
        source_path=outcome_path.resolve(),
    )

    assert final_payload["release_final_terminal_publish_status"] == "published"
    assert final_payload["release_final_terminal_publish_decision"] == "announce_release_closure"
    assert final_payload["release_final_terminal_publish_exit_code"] == 0
    assert final_payload["final_terminal_should_notify"] is True
    assert final_payload["final_terminal_requires_manual_action"] is False
    assert final_payload["final_terminal_channel"] == "release"
    assert "release_final_terminal_published" in final_payload["reason_codes"]


def test_build_release_final_terminal_publish_payload_published_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_terminal_publish_gate_module()
    outcome_payload = _sample_release_final_outcome_payload()
    outcome_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    outcome_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    outcome_payload["release_follow_up_final_verdict_exit_code"] = 1
    outcome_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    outcome_payload["release_final_outcome_status"] = "released_with_follow_up"
    outcome_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    outcome_payload["release_final_outcome_exit_code"] = 1
    outcome_payload["final_should_ship_release"] = True
    outcome_payload["final_follow_up_open"] = True
    outcome_payload["final_should_page_owner"] = False
    outcome_payload["final_outcome_target"] = "follow_up"
    outcome_payload["reason_codes"] = ["release_final_outcome_released_with_follow_up"]

    outcome_path = tmp_path / "release_final_outcome_with_follow_up.json"
    outcome_path.write_text(json.dumps(outcome_payload, indent=2), encoding="utf-8")

    outcome_report = gate.load_release_final_outcome_report(outcome_path)
    final_payload = gate.build_release_final_terminal_publish_payload(
        outcome_report,
        source_path=outcome_path.resolve(),
    )

    assert final_payload["release_final_terminal_publish_status"] == "published_with_follow_up"
    assert (
        final_payload["release_final_terminal_publish_decision"]
        == "announce_release_with_follow_up"
    )
    assert final_payload["release_final_terminal_publish_exit_code"] == 1
    assert final_payload["final_terminal_should_notify"] is True
    assert final_payload["final_terminal_requires_manual_action"] is False
    assert final_payload["final_terminal_channel"] == "follow_up"
    assert "release_final_terminal_published_with_follow_up" in final_payload["reason_codes"]


def test_build_release_final_terminal_publish_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_terminal_publish_gate_module()
    outcome_payload = _sample_release_final_outcome_payload()
    outcome_payload["release_delivery_final_verdict_status"] = "blocked"
    outcome_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    outcome_payload["release_delivery_final_verdict_exit_code"] = 1
    outcome_payload["release_follow_up_final_verdict_status"] = "blocked"
    outcome_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    outcome_payload["release_follow_up_final_verdict_exit_code"] = 1
    outcome_payload["release_final_outcome_status"] = "blocked"
    outcome_payload["release_final_outcome_decision"] = "escalate_blocker"
    outcome_payload["release_final_outcome_exit_code"] = 1
    outcome_payload["final_should_ship_release"] = False
    outcome_payload["final_follow_up_open"] = True
    outcome_payload["final_should_page_owner"] = True
    outcome_payload["final_outcome_target"] = "blocker"
    outcome_payload["reason_codes"] = ["release_final_outcome_blocked"]

    outcome_path = tmp_path / "release_final_outcome_blocked.json"
    outcome_path.write_text(json.dumps(outcome_payload, indent=2), encoding="utf-8")

    outcome_report = gate.load_release_final_outcome_report(outcome_path)
    final_payload = gate.build_release_final_terminal_publish_payload(
        outcome_report,
        source_path=outcome_path.resolve(),
    )

    assert final_payload["release_final_terminal_publish_status"] == "blocked"
    assert final_payload["release_final_terminal_publish_decision"] == "announce_blocker"
    assert final_payload["release_final_terminal_publish_exit_code"] == 1
    assert final_payload["final_terminal_should_notify"] is True
    assert final_payload["final_terminal_requires_manual_action"] is True
    assert final_payload["final_terminal_channel"] == "blocker"
    assert "release_final_terminal_blocked" in final_payload["reason_codes"]


def test_build_release_final_terminal_publish_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_release_final_terminal_publish_gate_module()
    outcome_payload = _sample_release_final_outcome_payload()
    outcome_payload["release_final_outcome_status"] = "released"
    outcome_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    outcome_payload["final_follow_up_open"] = True
    outcome_payload["final_outcome_target"] = "follow_up"

    outcome_path = tmp_path / "release_final_outcome_mismatch.json"
    outcome_path.write_text(json.dumps(outcome_payload, indent=2), encoding="utf-8")

    outcome_report = gate.load_release_final_outcome_report(outcome_path)
    final_payload = gate.build_release_final_terminal_publish_payload(
        outcome_report,
        source_path=outcome_path.resolve(),
    )

    assert final_payload["release_final_terminal_publish_status"] == "contract_failed"
    assert final_payload["release_final_terminal_publish_decision"] == "abort_publish"
    assert final_payload["release_final_terminal_publish_exit_code"] == 1
    assert "final_outcome_decision_mismatch" in final_payload["structural_issues"]
    assert "final_follow_up_open_mismatch" in final_payload["structural_issues"]
    assert "final_outcome_target_mismatch" in final_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_terminal_publish_gate_module()
    outcome_payload = _sample_release_final_outcome_payload()
    outcome_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    outcome_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    outcome_payload["release_follow_up_final_verdict_exit_code"] = 1
    outcome_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    outcome_payload["release_final_outcome_status"] = "released_with_follow_up"
    outcome_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    outcome_payload["release_final_outcome_exit_code"] = 1
    outcome_payload["final_should_ship_release"] = True
    outcome_payload["final_follow_up_open"] = True
    outcome_payload["final_should_page_owner"] = False
    outcome_payload["final_outcome_target"] = "follow_up"
    outcome_payload["reason_codes"] = ["release_final_outcome_released_with_follow_up"]

    outcome_path = tmp_path / "release_final_outcome_output.json"
    outcome_path.write_text(json.dumps(outcome_payload, indent=2), encoding="utf-8")

    outcome_report = gate.load_release_final_outcome_report(outcome_path)
    final_payload = gate.build_release_final_terminal_publish_payload(
        outcome_report,
        source_path=outcome_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        final_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.md"
        ),
    )

    assert outputs["workflow_release_final_terminal_publish_status"] == "published_with_follow_up"
    assert (
        outputs["workflow_release_final_terminal_publish_decision"]
        == "announce_release_with_follow_up"
    )
    assert outputs["workflow_release_final_terminal_publish_exit_code"] == "1"
    assert outputs["workflow_release_final_terminal_should_notify"] == "true"
    assert outputs["workflow_release_final_terminal_requires_manual_action"] == "false"
    assert outputs["workflow_release_final_terminal_channel"] == "follow_up"
    assert outputs["workflow_release_final_terminal_outcome_status"] == "released_with_follow_up"
    assert outputs["workflow_release_final_terminal_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_final_terminal_run_id"] == "1234567890"
    assert outputs["workflow_release_final_terminal_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_release_final_terminal_report_json"].endswith(
        "ci_workflow_release_final_terminal_publish.json"
    )
    assert outputs["workflow_release_final_terminal_report_markdown"].endswith(
        "ci_workflow_release_final_terminal_publish.md"
    )
