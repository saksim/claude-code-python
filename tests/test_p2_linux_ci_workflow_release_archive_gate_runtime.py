"""Contract tests for P2-37 Linux CI workflow release archive gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_archive_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_archive_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_archive_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_closure_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_finalization_report": "/tmp/ci_workflow_release_finalization.json",
        "source_release_terminal_publish_report": "/tmp/ci_workflow_release_terminal_publish.json",
        "source_release_completion_report": "/tmp/ci_workflow_release_completion.json",
        "source_release_trace_report": "/tmp/ci_workflow_release_trace.json",
        "source_release_trigger_report": "/tmp/ci_workflow_release_trigger.json",
        "source_release_handoff_report": "/tmp/ci_workflow_release_handoff.json",
        "source_terminal_publish_report": "/tmp/ci_workflow_terminal_publish.json",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "release_closure_status": "closed",
        "release_closure_decision": "ship",
        "release_closure_exit_code": 0,
        "should_close_release": True,
        "should_notify": True,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "reason_codes": ["release_closed"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def _materialize_evidence_paths(base_dir: Path, payload: dict) -> None:
    closure_file = base_dir / "ci_workflow_release_closure.json"
    closure_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for field in (
        "source_release_finalization_report",
        "source_release_terminal_publish_report",
        "source_release_completion_report",
        "source_release_trace_report",
        "source_release_trigger_report",
        "source_release_handoff_report",
        "source_terminal_publish_report",
        "source_dispatch_completion_report",
        "source_dispatch_trace_report",
        "source_dispatch_execution_report",
        "source_dispatch_report",
    ):
        evidence_path = base_dir / Path(payload[field]).name
        evidence_path.write_text("{}", encoding="utf-8")
        payload[field] = str(evidence_path)


def test_build_release_archive_payload_marks_ready_when_evidence_complete(tmp_path: Path):
    gate = _load_ci_workflow_release_archive_gate_module()
    payload = _sample_release_closure_payload()
    _materialize_evidence_paths(tmp_path, payload)
    report_path = tmp_path / "ci_workflow_release_closure.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_closure_report(report_path)
    archive_payload = gate.build_release_archive_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert archive_payload["release_archive_status"] == "ready"
    assert archive_payload["release_archive_decision"] == "publish"
    assert archive_payload["should_publish_archive"] is True
    assert archive_payload["release_archive_exit_code"] == 0
    assert archive_payload["reason_codes"] == ["release_archive_ready"]
    assert archive_payload["missing_artifacts"] == []


def test_build_release_archive_payload_pending_hold_path(tmp_path: Path):
    gate = _load_ci_workflow_release_archive_gate_module()
    payload = _sample_release_closure_payload()
    payload["release_closure_status"] = "pending"
    payload["release_closure_decision"] = "hold"
    payload["release_closure_exit_code"] = 1
    payload["should_close_release"] = False
    payload["reason_codes"] = ["release_run_await_timeout"]
    _materialize_evidence_paths(tmp_path, payload)
    report_path = tmp_path / "ci_workflow_release_closure_pending.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_closure_report(report_path)
    archive_payload = gate.build_release_archive_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert archive_payload["release_archive_status"] == "pending"
    assert archive_payload["release_archive_decision"] == "hold"
    assert archive_payload["should_publish_archive"] is False
    assert archive_payload["release_archive_exit_code"] == 1
    assert "release_run_await_timeout" in archive_payload["reason_codes"]


def test_build_release_archive_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_archive_gate_module()
    payload = _sample_release_closure_payload()
    payload["release_closure_status"] = "closed"
    payload["release_closure_decision"] = "hold"
    _materialize_evidence_paths(tmp_path, payload)
    report_path = tmp_path / "ci_workflow_release_closure_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_closure_report(report_path)
    archive_payload = gate.build_release_archive_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert archive_payload["release_archive_status"] == "contract_failed"
    assert archive_payload["release_archive_decision"] == "block"
    assert archive_payload["release_archive_exit_code"] == 1
    assert "release_closure_decision_mismatch_closed" in archive_payload["structural_issues"]


def test_build_release_archive_payload_tracks_missing_evidence(tmp_path: Path):
    gate = _load_ci_workflow_release_archive_gate_module()
    payload = _sample_release_closure_payload()
    _materialize_evidence_paths(tmp_path, payload)
    missing_path = tmp_path / "ci_workflow_release_trace.json"
    if missing_path.exists():
        missing_path.unlink()
    payload["source_release_trace_report"] = str(missing_path)
    report_path = tmp_path / "ci_workflow_release_closure_missing.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_closure_report(report_path)
    archive_payload = gate.build_release_archive_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert archive_payload["release_archive_status"] == "contract_failed"
    assert archive_payload["release_archive_decision"] == "block"
    assert archive_payload["release_archive_exit_code"] == 1
    assert str(missing_path) in archive_payload["missing_artifacts"]
    assert "release_evidence_missing" in archive_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_archive_gate_module()
    payload = _sample_release_closure_payload()
    _materialize_evidence_paths(tmp_path, payload)
    report_path = tmp_path / "ci_workflow_release_closure.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_closure_report(report_path)
    archive_payload = gate.build_release_archive_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        archive_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_archive.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_archive.md"),
    )

    assert outputs["workflow_release_archive_status"] == "ready"
    assert outputs["workflow_release_archive_decision"] == "publish"
    assert outputs["workflow_release_archive_should_publish"] == "true"
    assert outputs["workflow_release_archive_exit_code"] == "0"
    assert outputs["workflow_release_archive_run_id"] == "2233445566"
    assert outputs["workflow_release_archive_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_archive_report_json"].endswith(
        "ci_workflow_release_archive.json"
    )
    assert outputs["workflow_release_archive_report_markdown"].endswith(
        "ci_workflow_release_archive.md"
    )

