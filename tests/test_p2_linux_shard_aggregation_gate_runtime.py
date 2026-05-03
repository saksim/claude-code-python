"""Contract tests for P2-12 Linux shard aggregation gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_aggregation_gate_module():
    script_path = Path("scripts") / "run_p2_linux_shard_aggregation_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_shard_aggregation_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discover_summary_files_deduplicates_across_inputs(tmp_path: Path):
    gate = _load_aggregation_gate_module()
    summary = tmp_path / "summary.json"
    summary.write_text("{}", encoding="utf-8")

    nested = tmp_path / "nested"
    nested.mkdir(parents=True, exist_ok=True)
    nested_summary = nested / "summary.json"
    nested_summary.write_text("{}", encoding="utf-8")

    files = gate.discover_summary_files(
        summary_paths=[str(summary)],
        summary_globs=[str(tmp_path / "**" / "summary.json")],
        artifacts_dir=str(tmp_path),
    )

    normalized = {path.resolve() for path in files}
    assert summary.resolve() in normalized
    assert nested_summary.resolve() in normalized


def test_load_shard_summary_validates_required_contract(tmp_path: Path):
    gate = _load_aggregation_gate_module()
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "manifest_total_tests": 6,
                "total_tests": 3,
                "passed": 3,
                "failed": 0,
                "shard_total": 2,
                "shard_index": 1,
                "report_dir": "reports/shard-1",
            }
        ),
        encoding="utf-8",
    )

    loaded = gate.load_shard_summary(summary)
    assert loaded["manifest_total_tests"] == 6
    assert loaded["total_tests"] == 3
    assert loaded["passed"] == 3
    assert loaded["failed"] == 0
    assert loaded["shard_total"] == 2
    assert loaded["shard_index"] == 1


def test_aggregate_shard_summaries_happy_path():
    gate = _load_aggregation_gate_module()
    merged = gate.aggregate_shard_summaries(
        [
            {
                "path": "summary-1.json",
                "manifest_total_tests": 6,
                "total_tests": 3,
                "passed": 3,
                "failed": 0,
                "shard_total": 2,
                "shard_index": 1,
                "report_dir": "report-1",
            },
            {
                "path": "summary-2.json",
                "manifest_total_tests": 6,
                "total_tests": 3,
                "passed": 3,
                "failed": 0,
                "shard_total": 2,
                "shard_index": 2,
                "report_dir": "report-2",
            },
        ]
    )

    assert merged["overall_status"] == "passed"
    assert merged["totals"]["total_tests"] == 6
    assert merged["totals"]["passed"] == 6
    assert merged["totals"]["failed"] == 0
    assert merged["shards_missing"] == []
    assert merged["structural_issues"] == []


def test_aggregate_shard_summaries_detects_missing_shard_and_total_drift():
    gate = _load_aggregation_gate_module()
    merged = gate.aggregate_shard_summaries(
        [
            {
                "path": "summary-1.json",
                "manifest_total_tests": 6,
                "total_tests": 2,
                "passed": 2,
                "failed": 0,
                "shard_total": 3,
                "shard_index": 1,
                "report_dir": "report-1",
            },
            {
                "path": "summary-3.json",
                "manifest_total_tests": 6,
                "total_tests": 2,
                "passed": 2,
                "failed": 0,
                "shard_total": 3,
                "shard_index": 3,
                "report_dir": "report-3",
            },
        ]
    )

    assert merged["overall_status"] == "failed"
    assert merged["shards_missing"] == [2]
    issues = " | ".join(merged["structural_issues"])
    assert "missing shard indexes" in issues
    assert "aggregated total_tests" in issues
