"""Contract tests for P2-38 Linux CI workflow release verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_verdict_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_verdict_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_archive_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_closure_report": "/tmp/ci_workflow_release_closure.json",
        "release_closure_status": "closed",
        "release_closure_decision": "ship",
        "release_closure_exit_code": 0,
        "release_archive_status": "ready",
        "release_archive_decision": "publish",
        "release_archive_exit_code": 0,
        "should_close_release": True,
        "should_notify": True,
        "should_publish_archive": True,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "release_archive_summary": "release_closure_status=closed release_archive_status=ready",
        "reason_codes": ["release_archive_ready"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
            {"path": "/tmp/ci_workflow_release_finalization.json", "exists": True},
        ],
    }


def test_build_release_verdict_payload_marks_published(tmp_path: Path):
    gate = _load_ci_workflow_release_verdict_gate_module()
    payload = _sample_release_archive_payload()
    report_path = tmp_path / "ci_workflow_release_archive.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_archive_report(report_path)
    verdict_payload = gate.build_release_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert verdict_payload["release_verdict_status"] == "published"
    assert verdict_payload["release_verdict_decision"] == "ship"
    assert verdict_payload["should_ship_release"] is True
    assert verdict_payload["should_open_incident"] is False
    assert verdict_payload["release_verdict_exit_code"] == 0
    assert verdict_payload["reason_codes"] == ["release_verdict_published"]


def test_build_release_verdict_payload_pending_hold_path(tmp_path: Path):
    gate = _load_ci_workflow_release_verdict_gate_module()
    payload = _sample_release_archive_payload()
    payload["release_archive_status"] = "pending"
    payload["release_archive_decision"] = "hold"
    payload["release_archive_exit_code"] = 1
    payload["should_publish_archive"] = False
    payload["reason_codes"] = ["release_run_await_timeout"]

    report_path = tmp_path / "ci_workflow_release_archive_pending.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_archive_report(report_path)
    verdict_payload = gate.build_release_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert verdict_payload["release_verdict_status"] == "awaiting_archive"
    assert verdict_payload["release_verdict_decision"] == "hold"
    assert verdict_payload["should_ship_release"] is False
    assert verdict_payload["should_open_incident"] is False
    assert verdict_payload["release_verdict_exit_code"] == 1
    assert "release_run_await_timeout" in verdict_payload["reason_codes"]


def test_build_release_verdict_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_verdict_gate_module()
    payload = _sample_release_archive_payload()
    payload["release_archive_status"] = "ready"
    payload["release_archive_decision"] = "hold"

    report_path = tmp_path / "ci_workflow_release_archive_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_archive_report(report_path)
    verdict_payload = gate.build_release_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert verdict_payload["release_verdict_status"] == "contract_failed"
    assert verdict_payload["release_verdict_decision"] == "block"
    assert verdict_payload["release_verdict_exit_code"] == 1
    assert "release_archive_decision_mismatch_ready" in verdict_payload["structural_issues"]


def test_build_release_verdict_payload_tracks_missing_evidence(tmp_path: Path):
    gate = _load_ci_workflow_release_verdict_gate_module()
    payload = _sample_release_archive_payload()
    payload["evidence_manifest"] = [
        {"path": "/tmp/ci_workflow_release_closure.json", "exists": True},
        {"path": "/tmp/ci_workflow_release_finalization.json", "exists": False},
    ]

    report_path = tmp_path / "ci_workflow_release_archive_missing.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_archive_report(report_path)
    verdict_payload = gate.build_release_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert verdict_payload["release_verdict_status"] == "contract_failed"
    assert verdict_payload["release_verdict_decision"] == "block"
    assert verdict_payload["release_verdict_exit_code"] == 1
    assert "/tmp/ci_workflow_release_finalization.json" in verdict_payload["missing_artifacts"]
    assert "release_verdict_evidence_missing" in verdict_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_verdict_gate_module()
    payload = _sample_release_archive_payload()
    report_path = tmp_path / "ci_workflow_release_archive.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_archive_report(report_path)
    verdict_payload = gate.build_release_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        verdict_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_verdict.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_verdict.md"),
    )

    assert outputs["workflow_release_verdict_status"] == "published"
    assert outputs["workflow_release_verdict_decision"] == "ship"
    assert outputs["workflow_release_verdict_should_ship_release"] == "true"
    assert outputs["workflow_release_verdict_should_open_incident"] == "false"
    assert outputs["workflow_release_verdict_exit_code"] == "0"
    assert outputs["workflow_release_verdict_run_id"] == "2233445566"
    assert outputs["workflow_release_verdict_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_verdict_report_json"].endswith(
        "ci_workflow_release_verdict.json"
    )
    assert outputs["workflow_release_verdict_report_markdown"].endswith(
        "ci_workflow_release_verdict.md"
    )
