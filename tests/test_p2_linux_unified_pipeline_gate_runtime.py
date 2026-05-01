"""Contract tests for P2-14 Linux unified pipeline gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_pipeline_gate_module():
    script_path = Path("scripts") / "run_p2_linux_unified_pipeline_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_unified_pipeline_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_pipeline_commands_default_chain_includes_execution_summary_feed():
    gate = _load_pipeline_gate_module()
    commands = gate.build_pipeline_commands(
        python_executable="python",
        execution_report_dir=Path(".claude/reports/linux_unified_gate"),
        shard_total=3,
        shard_index=2,
        continue_on_failure=True,
        skip_execution=False,
        skip_aggregation=False,
        skip_publish=False,
        summary_paths=[],
        summary_globs=[],
        artifacts_dir=None,
        merged_summary_output=Path(".claude/reports/linux_unified_gate/merged_summary.json"),
        final_report_json=Path(".claude/reports/linux_unified_gate/final_report.json"),
        final_report_markdown=Path(".claude/reports/linux_unified_gate/final_report.md"),
        pytest_args=["-k", "daemon"],
    )

    assert [stage for stage, _ in commands] == ["execution", "aggregation", "publish"]

    execution_cmd = commands[0][1]
    assert execution_cmd[:2] == ["python", "scripts/run_p2_linux_unified_execution_gate.py"]
    assert "--continue-on-failure" in execution_cmd
    assert "--" in execution_cmd
    assert execution_cmd[-2:] == ["-k", "daemon"]

    aggregation_cmd = commands[1][1]
    assert aggregation_cmd[:2] == ["python", "scripts/run_p2_linux_shard_aggregation_gate.py"]
    assert "--summary" in aggregation_cmd
    summary_index = aggregation_cmd.index("--summary") + 1
    assert aggregation_cmd[summary_index].endswith("/summary.json")

    publish_cmd = commands[2][1]
    assert publish_cmd[:2] == ["python", "scripts/run_p2_linux_report_publish_gate.py"]
    assert "--merged-summary" in publish_cmd


def test_build_pipeline_commands_skip_execution_uses_external_summary_inputs():
    gate = _load_pipeline_gate_module()
    commands = gate.build_pipeline_commands(
        python_executable="python3",
        execution_report_dir=Path("ignored/report-dir"),
        shard_total=1,
        shard_index=1,
        continue_on_failure=False,
        skip_execution=True,
        skip_aggregation=False,
        skip_publish=True,
        summary_paths=["artifacts/job1/summary.json"],
        summary_globs=["artifacts/**/summary.json"],
        artifacts_dir="artifacts",
        merged_summary_output=Path("out/merged_summary.json"),
        final_report_json=Path("out/final_report.json"),
        final_report_markdown=Path("out/final_report.md"),
        pytest_args=None,
    )

    assert [stage for stage, _ in commands] == ["aggregation"]
    aggregation_cmd = commands[0][1]
    assert aggregation_cmd[0] == "python3"
    assert "--summary" in aggregation_cmd
    assert "artifacts/job1/summary.json" in aggregation_cmd
    assert "--summary-glob" in aggregation_cmd
    assert "artifacts/**/summary.json" in aggregation_cmd
    assert "--artifacts-dir" in aggregation_cmd
    assert "artifacts" in aggregation_cmd
    assert "ignored/report-dir/summary.json" not in aggregation_cmd


def test_build_pipeline_commands_skip_all_returns_empty_plan():
    gate = _load_pipeline_gate_module()
    commands = gate.build_pipeline_commands(
        python_executable="python",
        execution_report_dir=Path("tmp"),
        shard_total=1,
        shard_index=1,
        continue_on_failure=False,
        skip_execution=True,
        skip_aggregation=True,
        skip_publish=True,
        summary_paths=[],
        summary_globs=[],
        artifacts_dir=None,
        merged_summary_output=Path("tmp/merged_summary.json"),
        final_report_json=Path("tmp/final_report.json"),
        final_report_markdown=Path("tmp/final_report.md"),
        pytest_args=[],
    )

    assert commands == []
