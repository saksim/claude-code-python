"""Contract tests for P2-78 Linux CI workflow Linux validation terminal dispatch terminal verdict publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_tverdict_publish_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_terminal_verdict_payload() -> dict:
    return {
        "generated_at": "2026-05-03T00:00:00+00:00",
        "source_linux_validation_terminal_dispatch_final_publish_archive_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json",
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
        "linux_validation_terminal_dispatch_terminal_verdict_status": "ready_for_linux_validation_terminal_dispatch",
        "linux_validation_terminal_dispatch_terminal_verdict_decision": "proceed_linux_validation_terminal_dispatch",
        "linux_validation_terminal_dispatch_terminal_verdict_exit_code": 0,
        "linux_validation_terminal_dispatch_terminal_verdict_should_proceed": True,
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action": False,
        "linux_validation_terminal_dispatch_terminal_verdict_should_page_owner": False,
        "linux_validation_terminal_dispatch_terminal_verdict_channel": "release",
        "linux_validation_terminal_dispatch_terminal_verdict_summary": (
            "linux_validation_terminal_dispatch_final_publish_archive_status=archived "
            "linux_validation_terminal_dispatch_terminal_verdict_status=ready_for_linux_validation_terminal_dispatch "
            "linux_validation_terminal_dispatch_terminal_verdict_decision=proceed_linux_validation_terminal_dispatch"
        ),
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "follow_up_queue_url": "",
        "reason_codes": ["linux_validation_terminal_dispatch_terminal_verdict_ready"],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload_published(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate_module()
    )
    verdict_payload = _sample_linux_validation_terminal_dispatch_terminal_verdict_payload()

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json"
    )
    report_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_verdict_report(
        report_path
    )
    publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"]
        == "published"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
        ]
        == "announce_linux_validation_terminal_dispatch_ready"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"
        ]
        == 0
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_should_notify"
        ]
        is True
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action"
        ]
        is False
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner"
        ]
        is False
    )
    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_channel"]
        == "release"
    )
    assert publish_payload["reason_codes"] == [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_ready"
    ]


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload_published_with_follow_up(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate_module()
    )
    verdict_payload = _sample_linux_validation_terminal_dispatch_terminal_verdict_payload()
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "archived_with_follow_up"
    )
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_validated_with_follow_up"
    )
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 1
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = (
        "follow_up"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = (
        "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "follow_up"
    )
    verdict_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    verdict_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_ready_with_follow_up"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_follow_up.json"
    )
    report_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_verdict_report(
        report_path
    )
    publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"]
        == "published_with_follow_up"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
        ]
        == "announce_linux_validation_terminal_dispatch_ready_with_follow_up"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"
        ]
        == 1
    )
    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_channel"]
        == "follow_up"
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_ready_with_follow_up"
        in publish_payload["reason_codes"]
    )
    assert publish_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload_blocked(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate_module()
    )
    verdict_payload = _sample_linux_validation_terminal_dispatch_terminal_verdict_payload()
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = "blocked"
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_blocker"
    )
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 1
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_should_archive"] = (
        False
    )
    verdict_payload[
        "linux_validation_terminal_dispatch_final_publish_archive_requires_manual_action"
    ] = True
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_should_page_owner"] = (
        True
    )
    verdict_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = (
        "blocker"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = "blocked"
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "halt_linux_validation_terminal_dispatch_blocker"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_should_proceed"] = False
    verdict_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
    ] = True
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"] = (
        True
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = "blocker"
    verdict_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_blocked"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_blocked.json"
    )
    report_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_verdict_report(
        report_path
    )
    publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"]
        == "blocked"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
        ]
        == "announce_linux_validation_terminal_dispatch_blocker"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"
        ]
        == 1
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action"
        ]
        is True
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner"
        ]
        is True
    )
    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_channel"]
        == "blocker"
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_blocked"
        in publish_payload["reason_codes"]
    )


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload_contract_failed_on_mismatch(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate_module()
    )
    verdict_payload = _sample_linux_validation_terminal_dispatch_terminal_verdict_payload()
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = (
        "ready_for_linux_validation_terminal_dispatch"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_should_proceed"] = False
    verdict_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
    ] = True
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"] = (
        True
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "follow_up"
    )

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_mismatch.json"
    )
    report_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_verdict_report(
        report_path
    )
    publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"]
        == "contract_failed"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
        ]
        == "abort_linux_validation_terminal_dispatch_terminal_verdict_publish"
    )
    assert (
        publish_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"
        ]
        == 1
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_decision_mismatch"
        in publish_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_should_proceed_mismatch"
        in publish_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action_mismatch"
        in publish_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_should_page_owner_mismatch"
        in publish_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_channel_mismatch"
        in publish_payload["structural_issues"]
    )


def test_build_github_output_values_contract(tmp_path: Path):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_gate_module()
    )
    verdict_payload = _sample_linux_validation_terminal_dispatch_terminal_verdict_payload()
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = (
        "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    verdict_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "follow_up"
    )
    verdict_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    verdict_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_ready_with_follow_up"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_output.json"
    )
    report_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_verdict_report(
        report_path
    )
    publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_payload(
            report,
            source_path=report_path.resolve(),
        )
    )
    outputs = gate.build_github_output_values(
        publish_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.md"
        ),
    )

    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_status"]
        == "published_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_decision"]
        == "announce_linux_validation_terminal_dispatch_ready_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"]
        == "1"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_should_notify"]
        == "true"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action"
        ]
        == "false"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner"
        ]
        == "false"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_channel"]
        == "follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_terminal_verdict_status"
        ]
        == "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_terminal_verdict_channel"
        ]
        == "follow_up"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_follow_up_queue_url"
    ].endswith("/issues/77")
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_run_id"]
        == "9988776655"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_run_url"
    ].endswith("/actions/runs/9988776655")
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_report_json"
    ].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_report_markdown"
    ].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.md"
    )

