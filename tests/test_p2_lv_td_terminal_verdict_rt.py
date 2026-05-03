"""Contract tests for P2-77 Linux CI workflow Linux validation terminal dispatch terminal verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_terminal_verdict_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_final_publish_archive_payload() -> dict:
    return {
        "generated_at": "2026-05-03T00:00:00+00:00",
        "source_linux_validation_terminal_dispatch_final_verdict_publish_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.json",
        "source_linux_validation_terminal_dispatch_final_verdict_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json",
        "source_linux_validation_terminal_dispatch_terminal_publish_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json",
        "source_linux_validation_terminal_dispatch_completion_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_completion.json",
        "source_linux_validation_terminal_dispatch_trace_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_trace.json",
        "source_linux_validation_terminal_dispatch_execution_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_execution.json",
        "source_linux_validation_terminal_dispatch_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch.json",
        "linux_validation_terminal_dispatch_final_publish_archive_status": "archived",
        "linux_validation_terminal_dispatch_final_publish_archive_decision": "archive_linux_validation_terminal_dispatch_validated",
        "linux_validation_terminal_dispatch_final_publish_archive_exit_code": 0,
        "linux_validation_terminal_dispatch_final_publish_archive_should_archive": True,
        "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action": False,
        "linux_validation_terminal_dispatch_final_publish_archive_should_page_owner": False,
        "linux_validation_terminal_dispatch_final_publish_archive_channel": "release",
        "linux_validation_terminal_dispatch_final_publish_archive_summary": (
            "linux_validation_terminal_dispatch_final_verdict_publish_status=published "
            "linux_validation_terminal_dispatch_final_publish_archive_status=archived "
            "linux_validation_terminal_dispatch_final_publish_archive_decision=archive_linux_validation_terminal_dispatch_validated"
        ),
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "follow_up_queue_url": "",
        "reason_codes": ["linux_validation_terminal_dispatch_final_publish_archive_archived"],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_linux_validation_terminal_dispatch_terminal_verdict_payload_ready(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_terminal_dispatch_final_publish_archive_payload()

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json"
    )
    report_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_final_publish_archive_report(
        report_path
    )
    verdict_payload = gate.build_linux_validation_terminal_dispatch_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"]
        == "ready_for_linux_validation_terminal_dispatch"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"]
        == "proceed_linux_validation_terminal_dispatch"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] == 0
    )
    assert (
        verdict_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_should_proceed"
        ]
        is True
    )
    assert (
        verdict_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
        ]
        is False
    )
    assert (
        verdict_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"
        ]
        is False
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"]
        == "release"
    )
    assert verdict_payload["reason_codes"] == [
        "linux_validation_terminal_dispatch_terminal_verdict_ready"
    ]


def test_build_linux_validation_terminal_dispatch_terminal_verdict_payload_follow_up(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_terminal_dispatch_final_publish_archive_payload()
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "archived_with_follow_up"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_validated_with_follow_up"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 1
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = "follow_up"
    archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    archive_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_final_publish_archive_archived_with_follow_up"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_final_publish_archive_follow_up.json"
    )
    report_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_final_publish_archive_report(
        report_path
    )
    verdict_payload = gate.build_linux_validation_terminal_dispatch_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"]
        == "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"]
        == "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] == 1
    )
    assert (
        verdict_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_should_proceed"
        ]
        is True
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"]
        == "follow_up"
    )
    assert verdict_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_terminal_dispatch_terminal_verdict_payload_in_progress(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_terminal_dispatch_final_publish_archive_payload()
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "in_progress"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_in_progress"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 0
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_should_archive"] = (
        False
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = (
        "follow_up"
    )

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_final_publish_archive_in_progress.json"
    )
    report_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_final_publish_archive_report(
        report_path
    )
    verdict_payload = gate.build_linux_validation_terminal_dispatch_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"]
        == "in_progress"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"]
        == "hold_linux_validation_terminal_dispatch_in_progress"
    )
    assert (
        verdict_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_should_proceed"
        ]
        is False
    )


def test_build_linux_validation_terminal_dispatch_terminal_verdict_payload_blocked(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_terminal_dispatch_final_publish_archive_payload()
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "blocked"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_blocker"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 1
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_should_archive"] = (
        False
    )
    archive_payload[
        "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action"
    ] = True
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_should_page_owner"] = (
        True
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = (
        "blocker"
    )

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_final_publish_archive_blocked.json"
    )
    report_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_final_publish_archive_report(
        report_path
    )
    verdict_payload = gate.build_linux_validation_terminal_dispatch_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"]
        == "blocked"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"]
        == "halt_linux_validation_terminal_dispatch_blocker"
    )
    assert (
        verdict_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
        ]
        is True
    )


def test_build_linux_validation_terminal_dispatch_terminal_verdict_payload_contract_failed_on_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_terminal_dispatch_final_publish_archive_payload()
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "archived"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_validated_with_follow_up"
    )

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_final_publish_archive_mismatch.json"
    )
    report_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_final_publish_archive_report(
        report_path
    )
    verdict_payload = gate.build_linux_validation_terminal_dispatch_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"]
        == "contract_failed"
    )
    assert (
        verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"]
        == "abort_linux_validation_terminal_dispatch_terminal_verdict"
    )
    assert (
        "linux_validation_terminal_dispatch_final_publish_archive_decision_mismatch"
        in verdict_payload["structural_issues"]
    )


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_terminal_dispatch_final_publish_archive_payload()
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "archived_with_follow_up"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_validated_with_follow_up"
    )
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 1
    archive_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = (
        "follow_up"
    )
    archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_final_publish_archive_output.json"
    )
    report_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_final_publish_archive_report(
        report_path
    )
    verdict_payload = gate.build_linux_validation_terminal_dispatch_terminal_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        verdict_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.md"
        ),
    )

    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_status"]
        == "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_decision"]
        == "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_exit_code"]
        == "1"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_should_proceed"
        ]
        == "true"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_follow_up_queue_url"
        ].endswith("/issues/77")
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_report_json"].endswith(
            "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json"
        )
    )
