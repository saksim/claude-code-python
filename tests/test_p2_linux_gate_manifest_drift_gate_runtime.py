"""Contract tests for P2-57 Linux gate manifest drift gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_p2_linux_gate_manifest_drift_gate_module():
    script_path = Path("scripts") / "run_p2_linux_gate_manifest_drift_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_gate_manifest_drift_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_gate_script_basenames_includes_new_gate():
    gate = _load_p2_linux_gate_manifest_drift_gate_module()
    scripts = gate.collect_gate_script_basenames(scripts_dir=Path("scripts"))

    assert "run_p2_linux_gate_manifest_drift_gate.py" in scripts
    assert "run_linux_unified_gate.py" not in scripts
    assert all(name.startswith("run_") and name.endswith("_gate.py") for name in scripts)


def test_expected_runtime_test_for_gate_contract():
    gate = _load_p2_linux_gate_manifest_drift_gate_module()
    runtime_test = gate.expected_runtime_test_for_gate("run_p2_linux_ci_matrix_gate.py")
    assert runtime_test == "test_p2_linux_ci_matrix_gate_runtime.py"


def test_build_manifest_drift_report_passes_in_repo_contract():
    gate = _load_p2_linux_gate_manifest_drift_gate_module()
    report = gate.build_manifest_drift_report(project_root=Path("."))

    assert report["status"] == "passed"
    assert report["missing_runtime_tests"] == []
    assert report["missing_manifest_entries"] == []
    assert report["orphan_manifest_entries"] == []
    assert "run_p2_linux_gate_manifest_drift_gate.py" in report["gate_scripts_scanned"]
    assert (
        "test_p2_linux_gate_manifest_drift_gate_runtime.py"
        in report["gate_runtime_tests_expected"]
    )


def test_build_github_output_values_contract():
    gate = _load_p2_linux_gate_manifest_drift_gate_module()
    payload = {
        "status": "failed",
        "missing_runtime_tests": ["test_a.py"],
        "missing_manifest_entries": ["tests/test_a.py"],
        "orphan_manifest_entries": ["tests/test_orphan.py"],
    }
    outputs = gate.build_github_output_values(
        payload=payload,
        output_json=Path(".claude/reports/linux_unified_gate/linux_gate_manifest_drift.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/linux_gate_manifest_drift.md"
        ),
    )

    assert outputs["linux_gate_manifest_drift_status"] == "failed"
    assert outputs["linux_gate_manifest_drift_missing_runtime_tests"] == "1"
    assert outputs["linux_gate_manifest_drift_missing_manifest_entries"] == "1"
    assert outputs["linux_gate_manifest_drift_orphan_manifest_entries"] == "1"
    assert outputs["linux_gate_manifest_drift_report_json"].endswith(
        "linux_gate_manifest_drift.json"
    )
    assert outputs["linux_gate_manifest_drift_report_markdown"].endswith(
        "linux_gate_manifest_drift.md"
    )
