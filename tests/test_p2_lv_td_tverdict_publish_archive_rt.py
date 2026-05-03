"""Contract tests for P2-79 Linux CI workflow Linux validation terminal dispatch terminal verdict publish archive gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_tverdict_publish_archive_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-03T00:00:00+00:00",
        "source_linux_validation_terminal_dispatch_terminal_verdict_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json",
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
        "linux_validation_terminal_dispatch_terminal_verdict_publish_status": "published",
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision": "announce_linux_validation_terminal_dispatch_ready",
        "linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code": 0,
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_notify": True,
        "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action": False,
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner": False,
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel": "release",
        "linux_validation_terminal_dispatch_terminal_verdict_publish_summary": (
            "linux_validation_terminal_dispatch_terminal_verdict_status=ready_for_linux_validation_terminal_dispatch "
            "linux_validation_terminal_dispatch_terminal_verdict_publish_status=published "
            "linux_validation_terminal_dispatch_terminal_verdict_publish_decision=announce_linux_validation_terminal_dispatch_ready"
        ),
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "follow_up_queue_url": "",
        "reason_codes": ["linux_validation_terminal_dispatch_terminal_verdict_publish_ready"],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload_archived(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "archived"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "archive_linux_validation_terminal_dispatch_ready"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == 0
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_archive"
        ]
        is True
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_requires_manual_action"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_page_owner"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_channel"
        ]
        == "release"
    )
    assert archive_payload["reason_codes"] == [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_archived"
    ]


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload_archived_with_follow_up(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )
    publish_payload["linux_validation_terminal_dispatch_final_publish_archive_status"] = (
        "archived_with_follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_final_publish_archive_decision"] = (
        "archive_linux_validation_terminal_dispatch_validated_with_follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_final_publish_archive_exit_code"] = 1
    publish_payload["linux_validation_terminal_dispatch_final_publish_archive_channel"] = (
        "follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = (
        "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"] = (
        "published_with_follow_up"
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_ready_with_follow_up"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"] = (
        1
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel"
    ] = "follow_up"
    publish_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_ready_with_follow_up"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_follow_up.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "archived_with_follow_up"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "archive_linux_validation_terminal_dispatch_ready_with_follow_up"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == 1
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_archive"
        ]
        is True
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_requires_manual_action"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_page_owner"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_channel"
        ]
        == "follow_up"
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_archived_with_follow_up"
        in archive_payload["reason_codes"]
    )
    assert archive_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload_in_progress(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = (
        "in_progress"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "hold_linux_validation_terminal_dispatch_in_progress"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_should_proceed"] = (
        False
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
    ] = False
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"] = (
        False
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"] = (
        "in_progress"
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_in_progress"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"] = (
        0
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel"
    ] = "follow_up"
    publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_in_progress"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_in_progress.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "in_progress"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "archive_linux_validation_terminal_dispatch_in_progress"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == 0
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_archive"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_requires_manual_action"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_page_owner"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_channel"
        ]
        == "follow_up"
    )


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload_blocked(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = "blocked"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "halt_linux_validation_terminal_dispatch_blocker"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_should_proceed"] = (
        False
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
    ] = True
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"] = (
        True
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "blocker"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"] = (
        "blocked"
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_blocker"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"] = (
        1
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action"
    ] = True
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner"
    ] = True
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel"
    ] = "blocker"
    publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_blocked"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_blocked.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "blocked"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "archive_linux_validation_terminal_dispatch_blocker"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == 1
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_archive"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_requires_manual_action"
        ]
        is True
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_page_owner"
        ]
        is True
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_channel"
        ]
        == "blocker"
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_blocked"
        in archive_payload["reason_codes"]
    )


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload_failed(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = "failed"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "halt_linux_validation_terminal_dispatch_failure"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_should_proceed"] = (
        False
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_requires_manual_action"
    ] = True
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_should_page_owner"] = (
        True
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "blocker"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"] = (
        "failed"
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_failure"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"] = (
        1
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action"
    ] = True
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner"
    ] = True
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel"
    ] = "blocker"
    publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_failed"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_failed.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "failed"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "archive_linux_validation_terminal_dispatch_failure"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == 1
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_archive"
        ]
        is False
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_requires_manual_action"
        ]
        is True
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_page_owner"
        ]
        is True
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_channel"
        ]
        == "blocker"
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_failed"
        in archive_payload["reason_codes"]
    )


def test_build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload_contract_failed_on_mismatch(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"] = (
        "published"
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_ready_with_follow_up"
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_notify"
    ] = False
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action"
    ] = True
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner"
    ] = True
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel"
    ] = "follow_up"

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_mismatch.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )

    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "contract_failed"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "abort_linux_validation_terminal_dispatch_terminal_verdict_publish_archive"
    )
    assert (
        archive_payload[
            "linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == 1
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision_mismatch"
        in archive_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_notify_mismatch"
        in archive_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_requires_manual_action_mismatch"
        in archive_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_should_page_owner_mismatch"
        in archive_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel_mismatch"
        in archive_payload["structural_issues"]
    )


def test_build_github_output_values_contract(tmp_path: Path):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_gate_module()
    )
    publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_verdict_publish_payload()
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_status"] = (
        "ready_with_follow_up_for_linux_validation_terminal_dispatch"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_decision"] = (
        "proceed_linux_validation_terminal_dispatch_with_follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_exit_code"] = 1
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_channel"] = (
        "follow_up"
    )
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_status"] = (
        "published_with_follow_up"
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_ready_with_follow_up"
    publish_payload["linux_validation_terminal_dispatch_terminal_verdict_publish_exit_code"] = (
        1
    )
    publish_payload[
        "linux_validation_terminal_dispatch_terminal_verdict_publish_channel"
    ] = "follow_up"
    publish_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_verdict_publish_ready_with_follow_up"
    ]

    report_path = (
        tmp_path
        / "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_output.json"
    )
    report_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    report = (
        gate.load_linux_validation_terminal_dispatch_terminal_verdict_publish_report(
            report_path
        )
    )
    archive_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_payload(
            report,
            source_path=report_path.resolve(),
        )
    )
    outputs = gate.build_github_output_values(
        archive_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.md"
        ),
    )

    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_status"
        ]
        == "archived_with_follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_decision"
        ]
        == "archive_linux_validation_terminal_dispatch_ready_with_follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_exit_code"
        ]
        == "1"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_archive"
        ]
        == "true"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_requires_manual_action"
        ]
        == "false"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_should_page_owner"
        ]
        == "false"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_channel"
        ]
        == "follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_publish_status"
        ]
        == "published_with_follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_publish_channel"
        ]
        == "follow_up"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_follow_up_queue_url"
    ].endswith("/issues/77")
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_run_id"
        ]
        == "9988776655"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_run_url"
    ].endswith("/actions/runs/9988776655")
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_report_json"
    ].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.json"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive_report_markdown"
    ].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.md"
    )
