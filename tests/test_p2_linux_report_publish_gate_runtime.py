"""Contract tests for P2-13 Linux report publish gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_publish_gate_module():
    script_path = Path("scripts") / "run_p2_linux_report_publish_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_report_publish_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _valid_merged_summary() -> dict:
    return {
        "manifest_total_tests": 6,
        "shard_total": 2,
        "shards_present": [1, 2],
        "shards_missing": [],
        "totals": {
            "total_tests": 6,
            "passed": 6,
            "failed": 0,
        },
        "structural_issues": [],
        "overall_status": "passed",
    }


def test_load_merged_summary_validates_required_contract(tmp_path: Path):
    gate = _load_publish_gate_module()
    summary_path = tmp_path / "merged_summary.json"
    summary_path.write_text(
        (
            "{"
            '"manifest_total_tests": 6,'
            '"shard_total": 2,'
            '"shards_present": [1, 2],'
            '"shards_missing": [],'
            '"totals": {"total_tests": 6, "passed": 6, "failed": 0},'
            '"structural_issues": [],'
            '"overall_status": "passed"'
            "}"
        ),
        encoding="utf-8",
    )

    payload = gate.load_merged_summary(summary_path)
    assert payload["manifest_total_tests"] == 6
    assert payload["totals"]["passed"] == 6
    assert payload["overall_status"] == "passed"


def test_build_publish_payload_happy_path_status_passed():
    gate = _load_publish_gate_module()
    payload = gate.build_publish_payload(
        _valid_merged_summary(),
        source_path=Path("merged_summary.json"),
    )

    assert payload["overall_status"] == "passed"
    assert payload["totals"]["total_tests"] == 6
    assert payload["notes"] == []


def test_build_publish_payload_marks_failed_when_status_mismatch():
    gate = _load_publish_gate_module()
    merged = _valid_merged_summary()
    merged["overall_status"] = "failed"
    payload = gate.build_publish_payload(
        merged,
        source_path=Path("merged_summary.json"),
    )

    assert payload["overall_status"] == "failed"
    assert payload["notes"]
    assert "overall_status mismatch" in payload["notes"][0]


def test_render_markdown_report_contains_required_sections():
    gate = _load_publish_gate_module()
    payload = gate.build_publish_payload(
        _valid_merged_summary(),
        source_path=Path("merged_summary.json"),
    )
    report = gate.render_markdown_report(payload)

    assert "Linux Unified Gate Final Report" in report
    assert "## Totals" in report
    assert "## Shards" in report
    assert "## Structural Issues" in report
    assert "## Notes" in report
