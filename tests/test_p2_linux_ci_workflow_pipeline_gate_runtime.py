"""Contract tests for P2-26 Linux CI workflow pipeline gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_ci_workflow_pipeline_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_pipeline_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_pipeline_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_commands(**overrides):
    gate = _load_ci_workflow_pipeline_gate_module()
    kwargs = {
        "python_executable": "python",
        "ci_matrix_path": Path(".claude/reports/linux_unified_gate/ci_matrix.json"),
        "workflow_plan_output": Path(".claude/reports/linux_unified_gate/ci_workflow_plan.json"),
        "workflow_path": Path(".github/workflows/linux_unified_gate.yml"),
        "metadata_path": Path(".claude/reports/linux_unified_gate/ci_workflow_render.json"),
        "command_guard_output": Path(".claude/reports/linux_unified_gate/ci_workflow_command_guard.json"),
        "governance_report_output": Path(".claude/reports/linux_unified_gate/ci_workflow_governance.json"),
        "governance_publish_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_governance_publish.json"
        ),
        "governance_publish_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_governance_publish.md"
        ),
        "execution_decision_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_execution_decision.json"
        ),
        "execution_decision_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_execution_decision.md"
        ),
        "dispatch_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch.json"),
        "dispatch_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch.md"),
        "dispatch_execution_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json"
        ),
        "dispatch_execution_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.md"
        ),
        "dispatch_trace_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json"
        ),
        "dispatch_trace_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.md"
        ),
        "dispatch_completion_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json"
        ),
        "dispatch_completion_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.md"
        ),
        "terminal_publish_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json"
        ),
        "terminal_publish_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.md"
        ),
        "release_handoff_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_handoff.json"
        ),
        "release_handoff_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_handoff.md"
        ),
        "release_trigger_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_trigger.json"
        ),
        "release_trigger_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_trigger.md"
        ),
        "release_trace_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_trace.json"
        ),
        "release_trace_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_trace.md"
        ),
        "release_completion_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_completion.json"
        ),
        "release_completion_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_completion.md"
        ),
        "release_terminal_publish_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json"
        ),
        "release_terminal_publish_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.md"
        ),
        "release_finalization_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_finalization.json"
        ),
        "release_finalization_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_finalization.md"
        ),
        "release_closure_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_closure.json"
        ),
        "release_closure_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_closure.md"
        ),
        "release_archive_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_archive.json"
        ),
        "release_archive_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_archive.md"
        ),
        "release_verdict_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_verdict.json"
        ),
        "release_verdict_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_verdict.md"
        ),
        "release_incident_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_incident.json"
        ),
        "release_incident_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_incident.md"
        ),
        "release_terminal_verdict_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json"
        ),
        "release_terminal_verdict_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.md"
        ),
        "release_delivery_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery.json"
        ),
        "release_delivery_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery.md"
        ),
        "release_delivery_terminal_publish_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json"
        ),
        "release_delivery_terminal_publish_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.md"
        ),
        "release_delivery_final_verdict_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json"
        ),
        "release_delivery_final_verdict_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.md"
        ),
        "release_follow_up_dispatch_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json"
        ),
        "release_follow_up_dispatch_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.md"
        ),
        "release_follow_up_closure_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json"
        ),
        "release_follow_up_closure_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.md"
        ),
        "release_follow_up_terminal_publish_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json"
        ),
        "release_follow_up_terminal_publish_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.md"
        ),
        "release_follow_up_final_verdict_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json"
        ),
        "release_follow_up_final_verdict_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.md"
        ),
        "release_final_outcome_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json"
        ),
        "release_final_outcome_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.md"
        ),
        "release_final_terminal_publish_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json"
        ),
        "release_final_terminal_publish_markdown_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.md"
        ),
        "release_final_handoff_json_output": Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json"
        ),
        "release_final_handoff_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.md"),
        "release_final_closure_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json"),
        "release_final_closure_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_closure.md"),
        "release_final_closure_publish_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json"),
        "release_final_closure_publish_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.md"),
        "release_final_archive_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json"),
        "release_final_archive_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.md"),
        "release_final_verdict_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json"),
        "release_final_verdict_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.md"),
        "release_final_verdict_publish_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json"),
        "release_final_verdict_publish_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.md"),
        "release_final_publish_archive_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json"),
        "release_final_publish_archive_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.md"),
        "gate_manifest_drift_json_output": Path(".claude/reports/linux_unified_gate/linux_gate_manifest_drift.json"),
        "gate_manifest_drift_markdown_output": Path(".claude/reports/linux_unified_gate/linux_gate_manifest_drift.md"),
        "terminal_verdict_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json"),
        "terminal_verdict_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.md"),
        "linux_validation_dispatch_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json"),
        "linux_validation_dispatch_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.md"),
        "linux_validation_verdict_json_output": Path(".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json"),
        "linux_validation_verdict_markdown_output": Path(".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.md"),
        "workflow_name": "Linux Unified Gate",
        "python_version": "3.11",
        "artifact_prefix": "linux-unified-summary",
        "target_environment": "production",
        "release_channel": "stable",
        "workflow_ref": "main",
        "release_workflow_path": ".github/workflows/release.yml",
        "release_workflow_ref": "main",
        "release_timeout_seconds": 900,
        "release_command": "",
        "release_trace_poll_timeout_seconds": 600,
        "release_completion_poll_interval_seconds": 30,
        "release_completion_max_polls": 20,
        "release_completion_poll_timeout_seconds": 600,
        "incident_timeout_seconds": 600,
        "incident_command": "",
        "incident_repo": "",
        "incident_label": "release-incident",
        "incident_title_prefix": "[release-incident]",
        "follow_up_timeout_seconds": 600,
        "follow_up_command": "",
        "follow_up_repo": "",
        "follow_up_label": "release-follow-up",
        "follow_up_title_prefix": "[release-follow-up]",
        "on_block_policy": "fail",
        "dispatch_timeout_seconds": 300,
        "trace_poll_timeout_seconds": 600,
        "completion_poll_interval_seconds": 30,
        "completion_max_polls": 20,
        "completion_poll_timeout_seconds": 600,
        "linux_validation_timeout_seconds": 7200,
        "strict_generated_at": False,
        "sync_write": False,
        "command_guard_write": False,
        "dispatch_trace_poll_now": False,
        "release_trace_poll_now": False,
        "completion_allow_in_progress": False,
        "release_completion_allow_in_progress": False,
        "on_release_hold_policy": "pass",
        "skip_plan": False,
        "skip_yaml": False,
        "skip_sync": False,
        "skip_command_guard": False,
        "skip_governance": False,
        "skip_governance_publish": False,
        "skip_decision": False,
        "skip_dispatch": False,
        "skip_dispatch_execution": False,
        "skip_dispatch_trace": False,
        "skip_dispatch_completion": False,
        "skip_dispatch_terminal_publish": False,
        "skip_dispatch_release_handoff": False,
        "skip_release_trigger": False,
        "skip_release_trace": False,
        "skip_release_completion": False,
        "skip_release_terminal_publish": False,
        "skip_release_finalization": False,
        "skip_release_closure": False,
        "skip_release_archive": False,
        "skip_release_verdict": False,
        "skip_release_incident": False,
        "skip_release_terminal_verdict": False,
        "skip_release_delivery": False,
        "skip_release_delivery_terminal_publish": False,
        "skip_release_delivery_final_verdict": False,
        "skip_release_follow_up_dispatch": False,
        "skip_release_follow_up_closure": False,
        "skip_release_follow_up_terminal_publish": False,
        "skip_release_follow_up_final_verdict": False,
        "skip_release_final_outcome": False,
        "skip_release_final_terminal_publish": False,
        "skip_release_final_handoff": False,
        "skip_release_final_closure": False,
        "skip_release_final_closure_publish": False,
        "skip_release_final_archive": False,
        "skip_release_final_verdict": False,
        "skip_release_final_verdict_publish": False,
        "skip_release_final_publish_archive": False,
        "skip_gate_manifest_drift": False,
        "skip_terminal_verdict": False,
        "skip_linux_validation_dispatch": False,
        "skip_linux_validation_verdict": False,
    }
    kwargs.update(overrides)
    if "skip_terminal_verdict" not in overrides:
        kwargs["skip_terminal_verdict"] = bool(
            kwargs["skip_gate_manifest_drift"]
            or kwargs["skip_release_final_publish_archive"]
        )
    if "skip_linux_validation_dispatch" not in overrides:
        kwargs["skip_linux_validation_dispatch"] = bool(kwargs["skip_terminal_verdict"])
    if "skip_linux_validation_verdict" not in overrides:
        kwargs["skip_linux_validation_verdict"] = bool(
            kwargs["skip_linux_validation_dispatch"]
        )
    return gate.build_ci_workflow_pipeline_commands(**kwargs)


def test_build_ci_workflow_pipeline_commands_default_stage_chain():
    commands = _build_commands()
    assert [stage for stage, _ in commands] == [
        "workflow_plan",
        "workflow_yaml",
        "workflow_sync",
        "workflow_command_guard",
        "workflow_governance",
        "workflow_governance_publish",
        "workflow_decision",
        "workflow_dispatch",
        "workflow_dispatch_execution",
        "workflow_dispatch_trace",
        "workflow_dispatch_completion",
        "workflow_terminal_publish",
        "workflow_release_handoff",
        "workflow_release_trigger",
        "workflow_release_trace",
        "workflow_release_completion",
        "workflow_release_terminal_publish",
        "workflow_release_finalization",
        "workflow_release_closure",
        "workflow_release_archive",
        "workflow_release_verdict",
        "workflow_release_incident",
        "workflow_release_terminal_verdict",
        "workflow_release_delivery",
        "workflow_release_delivery_terminal_publish",
        "workflow_release_delivery_final_verdict",
        "workflow_release_follow_up_dispatch",
        "workflow_release_follow_up_closure",
        "workflow_release_follow_up_terminal_publish",
        "workflow_release_follow_up_final_verdict",
        "workflow_release_final_outcome",
        "workflow_release_final_terminal_publish",
        "workflow_release_final_handoff",
        "workflow_release_final_closure",
        "workflow_release_final_closure_publish",
        "workflow_release_final_archive",
        "workflow_release_final_verdict",
        "workflow_release_final_verdict_publish",
        "workflow_release_final_publish_archive",
        "workflow_gate_manifest_drift",
        "workflow_terminal_verdict",
        "workflow_linux_validation_dispatch",
        "workflow_linux_validation_verdict",
    ]

    assert commands[0][1][:2] == ["python", "scripts/run_p2_linux_ci_workflow_plan_gate.py"]
    assert commands[1][1][:2] == ["python", "scripts/run_p2_linux_ci_workflow_yaml_gate.py"]
    assert commands[2][1][:2] == ["python", "scripts/run_p2_linux_ci_workflow_sync_gate.py"]
    assert commands[3][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_command_guard_gate.py",
    ]
    assert commands[4][1][:2] == ["python", "scripts/run_p2_linux_ci_workflow_governance_gate.py"]
    assert commands[5][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_governance_publish_gate.py",
    ]
    assert commands[6][1][:2] == ["python", "scripts/run_p2_linux_ci_workflow_decision_gate.py"]
    assert commands[7][1][:2] == ["python", "scripts/run_p2_linux_ci_workflow_dispatch_gate.py"]
    assert commands[8][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py",
    ]
    assert commands[9][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py",
    ]
    assert commands[10][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py",
    ]
    assert commands[11][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py",
    ]
    assert commands[12][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_handoff_gate.py",
    ]
    assert commands[13][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_trigger_gate.py",
    ]
    assert commands[14][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_trace_gate.py",
    ]
    assert commands[15][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_completion_gate.py",
    ]
    assert commands[16][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py",
    ]
    assert commands[17][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_finalization_gate.py",
    ]
    assert commands[18][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_closure_gate.py",
    ]
    assert commands[19][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_archive_gate.py",
    ]
    assert commands[20][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_verdict_gate.py",
    ]
    assert commands[21][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_incident_gate.py",
    ]
    assert commands[22][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py",
    ]
    assert commands[23][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_delivery_gate.py",
    ]
    assert commands[24][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py",
    ]
    assert commands[25][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py",
    ]
    assert commands[26][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py",
    ]
    assert commands[27][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py",
    ]
    assert commands[28][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py",
    ]
    assert commands[29][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py",
    ]
    assert commands[30][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py",
    ]
    assert commands[31][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py",
    ]
    assert commands[32][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py",
    ]
    assert commands[33][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py",
    ]
    assert commands[34][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py",
    ]
    assert commands[35][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py",
    ]
    assert commands[36][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py",
    ]
    assert commands[37][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py",
    ]
    assert commands[38][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py",
    ]
    assert commands[39][1][:2] == [
        "python",
        "scripts/run_p2_linux_gate_manifest_drift_gate.py",
    ]
    assert commands[40][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py",
    ]
    assert commands[41][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py",
    ]
    assert commands[42][1][:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_linux_validation_verdict_gate.py",
    ]


def test_build_ci_workflow_pipeline_commands_propagates_optional_flags():
    commands = _build_commands(
        strict_generated_at=True,
        sync_write=True,
        command_guard_write=True,
        dispatch_trace_poll_now=True,
        on_block_policy="skip",
        workflow_ref="release",
        dispatch_timeout_seconds=120,
        trace_poll_timeout_seconds=240,
        completion_poll_interval_seconds=15,
        completion_max_polls=8,
        completion_poll_timeout_seconds=180,
        completion_allow_in_progress=True,
        target_environment="staging",
        release_channel="canary",
        release_workflow_path=".github/workflows/release-prod.yml",
        release_workflow_ref="release",
        release_timeout_seconds=1200,
        release_trace_poll_timeout_seconds=480,
        release_completion_poll_interval_seconds=12,
        release_completion_max_polls=7,
        release_completion_poll_timeout_seconds=150,
        release_command=(
            "gh workflow run .github/workflows/release-prod.yml "
            "--ref release --raw-field mode=promote"
        ),
        incident_timeout_seconds=300,
        incident_command=(
            "gh issue create --repo acme/demo --title "
            "\"[release-incident] auto\" --body \"incident\""
        ),
        incident_repo="acme/demo",
        incident_label="sev-1",
        incident_title_prefix="[release-incident][sev1]",
        follow_up_timeout_seconds=450,
        follow_up_command=(
            "gh issue create --repo acme/demo --title "
            "\"[release-follow-up] auto\" --body \"follow-up\""
        ),
        follow_up_repo="acme/demo",
        follow_up_label="release-follow-up-sev1",
        follow_up_title_prefix="[release-follow-up][sev1]",
        release_trace_poll_now=True,
        release_completion_allow_in_progress=True,
        on_release_hold_policy="fail",
    )
    command_map = {stage: command for stage, command in commands}

    sync_command = command_map["workflow_sync"]
    assert "--strict-generated-at" in sync_command
    assert "--write" in sync_command

    command_guard_command = command_map["workflow_command_guard"]
    assert "--write" in command_guard_command

    governance_command = command_map["workflow_governance"]
    assert "--strict-generated-at" in governance_command

    decision_command = command_map["workflow_decision"]
    on_block_index = decision_command.index("--on-block") + 1
    assert decision_command[on_block_index] == "skip"

    dispatch_command = command_map["workflow_dispatch"]
    workflow_ref_index = dispatch_command.index("--workflow-ref") + 1
    assert dispatch_command[workflow_ref_index] == "release"

    dispatch_execution_command = command_map["workflow_dispatch_execution"]
    timeout_index = dispatch_execution_command.index("--dispatch-timeout-seconds") + 1
    assert dispatch_execution_command[timeout_index] == "120"

    dispatch_trace_command = command_map["workflow_dispatch_trace"]
    assert "--poll-now" in dispatch_trace_command
    trace_timeout_index = dispatch_trace_command.index("--poll-timeout-seconds") + 1
    assert dispatch_trace_command[trace_timeout_index] == "240"

    dispatch_completion_command = command_map["workflow_dispatch_completion"]
    interval_index = dispatch_completion_command.index("--poll-interval-seconds") + 1
    assert dispatch_completion_command[interval_index] == "15"
    max_polls_index = dispatch_completion_command.index("--max-polls") + 1
    assert dispatch_completion_command[max_polls_index] == "8"
    completion_timeout_index = dispatch_completion_command.index("--poll-timeout-seconds") + 1
    assert dispatch_completion_command[completion_timeout_index] == "180"
    assert "--allow-in-progress" in dispatch_completion_command

    release_handoff_command = command_map["workflow_release_handoff"]
    environment_index = release_handoff_command.index("--target-environment") + 1
    assert release_handoff_command[environment_index] == "staging"
    channel_index = release_handoff_command.index("--release-channel") + 1
    assert release_handoff_command[channel_index] == "canary"

    release_trigger_command = command_map["workflow_release_trigger"]
    workflow_path_index = release_trigger_command.index("--release-workflow-path") + 1
    assert release_trigger_command[workflow_path_index] == ".github/workflows/release-prod.yml"
    workflow_ref_index = release_trigger_command.index("--release-workflow-ref") + 1
    assert release_trigger_command[workflow_ref_index] == "release"
    timeout_index = release_trigger_command.index("--release-timeout-seconds") + 1
    assert release_trigger_command[timeout_index] == "1200"
    release_command_index = release_trigger_command.index("--release-command") + 1
    assert release_trigger_command[release_command_index].startswith("gh workflow run")

    release_trace_command = command_map["workflow_release_trace"]
    trace_timeout_index = release_trace_command.index("--poll-timeout-seconds") + 1
    assert release_trace_command[trace_timeout_index] == "480"
    assert "--poll-now" in release_trace_command

    release_completion_command = command_map["workflow_release_completion"]
    interval_index = release_completion_command.index("--poll-interval-seconds") + 1
    assert release_completion_command[interval_index] == "12"
    max_polls_index = release_completion_command.index("--max-polls") + 1
    assert release_completion_command[max_polls_index] == "7"
    timeout_index = release_completion_command.index("--poll-timeout-seconds") + 1
    assert release_completion_command[timeout_index] == "150"
    assert "--allow-in-progress" in release_completion_command

    release_finalization_command = command_map["workflow_release_finalization"]
    hold_policy_index = release_finalization_command.index("--on-hold") + 1
    assert release_finalization_command[hold_policy_index] == "fail"

    release_incident_command = command_map["workflow_release_incident"]
    timeout_index = release_incident_command.index("--incident-timeout-seconds") + 1
    assert release_incident_command[timeout_index] == "300"
    repo_index = release_incident_command.index("--incident-repo") + 1
    assert release_incident_command[repo_index] == "acme/demo"
    label_index = release_incident_command.index("--incident-label") + 1
    assert release_incident_command[label_index] == "sev-1"
    title_prefix_index = release_incident_command.index("--incident-title-prefix") + 1
    assert release_incident_command[title_prefix_index] == "[release-incident][sev1]"
    incident_command_index = release_incident_command.index("--incident-command") + 1
    assert release_incident_command[incident_command_index].startswith("gh issue create")

    release_terminal_verdict_command = command_map["workflow_release_terminal_verdict"]
    assert release_terminal_verdict_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py",
    ]
    incident_report_index = (
        release_terminal_verdict_command.index("--release-incident-report") + 1
    )
    assert release_terminal_verdict_command[incident_report_index].endswith(
        "ci_workflow_release_incident.json"
    )
    release_delivery_command = command_map["workflow_release_delivery"]
    assert release_delivery_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_delivery_gate.py",
    ]
    terminal_verdict_report_index = (
        release_delivery_command.index("--release-terminal-verdict-report") + 1
    )
    assert release_delivery_command[terminal_verdict_report_index].endswith(
        "ci_workflow_release_terminal_verdict.json"
    )
    release_delivery_terminal_publish_command = command_map["workflow_release_delivery_terminal_publish"]
    assert release_delivery_terminal_publish_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py",
    ]
    release_delivery_report_index = (
        release_delivery_terminal_publish_command.index("--release-delivery-report") + 1
    )
    assert release_delivery_terminal_publish_command[release_delivery_report_index].endswith(
        "ci_workflow_release_delivery.json"
    )
    release_delivery_final_verdict_command = command_map["workflow_release_delivery_final_verdict"]
    assert release_delivery_final_verdict_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py",
    ]
    release_delivery_terminal_publish_report_index = (
        release_delivery_final_verdict_command.index(
            "--release-delivery-terminal-publish-report"
        )
        + 1
    )
    assert release_delivery_final_verdict_command[
        release_delivery_terminal_publish_report_index
    ].endswith("ci_workflow_release_delivery_terminal_publish.json")
    release_follow_up_dispatch_command = command_map["workflow_release_follow_up_dispatch"]
    assert release_follow_up_dispatch_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py",
    ]
    release_delivery_final_verdict_report_index = (
        release_follow_up_dispatch_command.index("--release-delivery-final-verdict-report") + 1
    )
    assert release_follow_up_dispatch_command[
        release_delivery_final_verdict_report_index
    ].endswith("ci_workflow_release_delivery_final_verdict.json")
    release_follow_up_closure_command = command_map["workflow_release_follow_up_closure"]
    assert release_follow_up_closure_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py",
    ]
    release_follow_up_dispatch_report_index = (
        release_follow_up_closure_command.index("--release-follow-up-dispatch-report") + 1
    )
    assert release_follow_up_closure_command[
        release_follow_up_dispatch_report_index
    ].endswith("ci_workflow_release_follow_up_dispatch.json")
    follow_up_timeout_index = (
        release_follow_up_closure_command.index("--follow-up-timeout-seconds") + 1
    )
    assert release_follow_up_closure_command[follow_up_timeout_index] == "450"
    follow_up_repo_index = release_follow_up_closure_command.index("--follow-up-repo") + 1
    assert release_follow_up_closure_command[follow_up_repo_index] == "acme/demo"
    follow_up_label_index = release_follow_up_closure_command.index("--follow-up-label") + 1
    assert release_follow_up_closure_command[follow_up_label_index] == "release-follow-up-sev1"
    follow_up_title_prefix_index = (
        release_follow_up_closure_command.index("--follow-up-title-prefix") + 1
    )
    assert (
        release_follow_up_closure_command[follow_up_title_prefix_index]
        == "[release-follow-up][sev1]"
    )
    follow_up_command_index = (
        release_follow_up_closure_command.index("--follow-up-command") + 1
    )
    assert release_follow_up_closure_command[follow_up_command_index].startswith(
        "gh issue create"
    )
    release_follow_up_terminal_publish_command = command_map[
        "workflow_release_follow_up_terminal_publish"
    ]
    assert release_follow_up_terminal_publish_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py",
    ]
    release_follow_up_closure_report_index = (
        release_follow_up_terminal_publish_command.index("--release-follow-up-closure-report") + 1
    )
    assert release_follow_up_terminal_publish_command[
        release_follow_up_closure_report_index
    ].endswith("ci_workflow_release_follow_up_closure.json")
    release_follow_up_final_verdict_command = command_map[
        "workflow_release_follow_up_final_verdict"
    ]
    assert release_follow_up_final_verdict_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py",
    ]
    release_follow_up_terminal_publish_report_index = (
        release_follow_up_final_verdict_command.index(
            "--release-follow-up-terminal-publish-report"
        )
        + 1
    )
    assert release_follow_up_final_verdict_command[
        release_follow_up_terminal_publish_report_index
    ].endswith("ci_workflow_release_follow_up_terminal_publish.json")
    release_final_outcome_command = command_map["workflow_release_final_outcome"]
    assert release_final_outcome_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py",
    ]
    release_final_outcome_report_index = (
        release_final_outcome_command.index("--release-delivery-final-verdict-report") + 1
    )
    assert release_final_outcome_command[release_final_outcome_report_index].endswith(
        "ci_workflow_release_delivery_final_verdict.json"
    )
    release_final_terminal_publish_command = command_map[
        "workflow_release_final_terminal_publish"
    ]
    assert release_final_terminal_publish_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py",
    ]
    release_final_terminal_publish_report_index = (
        release_final_terminal_publish_command.index("--release-final-outcome-report") + 1
    )
    assert release_final_terminal_publish_command[
        release_final_terminal_publish_report_index
    ].endswith("ci_workflow_release_final_outcome.json")
    release_final_handoff_command = command_map["workflow_release_final_handoff"]
    assert release_final_handoff_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py",
    ]
    release_final_handoff_report_index = (
        release_final_handoff_command.index("--release-final-terminal-publish-report") + 1
    )
    assert release_final_handoff_command[release_final_handoff_report_index].endswith(
        "ci_workflow_release_final_terminal_publish.json"
    )
    release_final_closure_command = command_map["workflow_release_final_closure"]
    assert release_final_closure_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py",
    ]
    release_final_closure_report_index = (
        release_final_closure_command.index("--release-final-handoff-report") + 1
    )
    assert release_final_closure_command[release_final_closure_report_index].endswith(
        "ci_workflow_release_final_handoff.json"
    )
    release_final_closure_publish_command = command_map["workflow_release_final_closure_publish"]
    assert release_final_closure_publish_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py",
    ]
    release_final_closure_publish_report_index = (
        release_final_closure_publish_command.index("--release-final-closure-report") + 1
    )
    assert release_final_closure_publish_command[
        release_final_closure_publish_report_index
    ].endswith("ci_workflow_release_final_closure.json")
    release_final_archive_command = command_map["workflow_release_final_archive"]
    assert release_final_archive_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py",
    ]
    release_final_archive_report_index = (
        release_final_archive_command.index("--release-final-closure-publish-report") + 1
    )
    assert release_final_archive_command[release_final_archive_report_index].endswith(
        "ci_workflow_release_final_closure_publish.json"
    )
    release_final_verdict_command = command_map["workflow_release_final_verdict"]
    assert release_final_verdict_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py",
    ]
    release_final_verdict_report_index = (
        release_final_verdict_command.index("--release-final-archive-report") + 1
    )
    assert release_final_verdict_command[release_final_verdict_report_index].endswith(
        "ci_workflow_release_final_archive.json"
    )
    release_final_verdict_publish_command = command_map[
        "workflow_release_final_verdict_publish"
    ]
    assert release_final_verdict_publish_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py",
    ]
    release_final_verdict_publish_report_index = (
        release_final_verdict_publish_command.index("--release-final-verdict-report") + 1
    )
    assert release_final_verdict_publish_command[
        release_final_verdict_publish_report_index
    ].endswith("ci_workflow_release_final_verdict.json")
    release_final_publish_archive_command = command_map[
        "workflow_release_final_publish_archive"
    ]
    assert release_final_publish_archive_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py",
    ]
    release_final_publish_archive_report_index = (
        release_final_publish_archive_command.index("--release-final-verdict-publish-report")
        + 1
    )
    assert release_final_publish_archive_command[
        release_final_publish_archive_report_index
    ].endswith("ci_workflow_release_final_verdict_publish.json")
    gate_manifest_drift_command = command_map["workflow_gate_manifest_drift"]
    assert gate_manifest_drift_command[:2] == [
        "python",
        "scripts/run_p2_linux_gate_manifest_drift_gate.py",
    ]
    gate_manifest_drift_json_index = gate_manifest_drift_command.index("--output-json") + 1
    assert gate_manifest_drift_command[gate_manifest_drift_json_index].endswith(
        "linux_gate_manifest_drift.json"
    )
    gate_manifest_drift_markdown_index = (
        gate_manifest_drift_command.index("--output-markdown") + 1
    )
    assert gate_manifest_drift_command[gate_manifest_drift_markdown_index].endswith(
        "linux_gate_manifest_drift.md"
    )
    terminal_verdict_command = command_map["workflow_terminal_verdict"]
    assert terminal_verdict_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py",
    ]
    terminal_verdict_release_report_index = (
        terminal_verdict_command.index("--release-final-publish-archive-report") + 1
    )
    assert terminal_verdict_command[terminal_verdict_release_report_index].endswith(
        "ci_workflow_release_final_publish_archive.json"
    )
    terminal_verdict_drift_report_index = (
        terminal_verdict_command.index("--gate-manifest-drift-report") + 1
    )
    assert terminal_verdict_command[terminal_verdict_drift_report_index].endswith(
        "linux_gate_manifest_drift.json"
    )
    terminal_verdict_json_index = terminal_verdict_command.index("--output-json") + 1
    assert terminal_verdict_command[terminal_verdict_json_index].endswith(
        "ci_workflow_terminal_verdict.json"
    )
    terminal_verdict_markdown_index = terminal_verdict_command.index("--output-markdown") + 1
    assert terminal_verdict_command[terminal_verdict_markdown_index].endswith(
        "ci_workflow_terminal_verdict.md"
    )
    linux_validation_dispatch_command = command_map["workflow_linux_validation_dispatch"]
    assert linux_validation_dispatch_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py",
    ]
    linux_validation_terminal_verdict_report_index = (
        linux_validation_dispatch_command.index("--terminal-verdict-report") + 1
    )
    assert linux_validation_dispatch_command[
        linux_validation_terminal_verdict_report_index
    ].endswith("ci_workflow_terminal_verdict.json")
    linux_validation_project_root_index = (
        linux_validation_dispatch_command.index("--project-root") + 1
    )
    assert linux_validation_dispatch_command[linux_validation_project_root_index] == "."
    linux_validation_python_index = (
        linux_validation_dispatch_command.index("--python-executable") + 1
    )
    assert linux_validation_dispatch_command[linux_validation_python_index] == "python"
    linux_validation_timeout_index = (
        linux_validation_dispatch_command.index("--linux-validation-timeout-seconds") + 1
    )
    assert linux_validation_dispatch_command[linux_validation_timeout_index] == "7200"
    linux_validation_json_index = (
        linux_validation_dispatch_command.index("--output-json") + 1
    )
    assert linux_validation_dispatch_command[linux_validation_json_index].endswith(
        "ci_workflow_linux_validation_dispatch.json"
    )
    linux_validation_markdown_index = (
        linux_validation_dispatch_command.index("--output-markdown") + 1
    )
    assert linux_validation_dispatch_command[linux_validation_markdown_index].endswith(
        "ci_workflow_linux_validation_dispatch.md"
    )
    linux_validation_verdict_command = command_map["workflow_linux_validation_verdict"]
    assert linux_validation_verdict_command[:2] == [
        "python",
        "scripts/run_p2_linux_ci_workflow_linux_validation_verdict_gate.py",
    ]
    linux_validation_verdict_dispatch_report_index = (
        linux_validation_verdict_command.index("--linux-validation-dispatch-report") + 1
    )
    assert linux_validation_verdict_command[
        linux_validation_verdict_dispatch_report_index
    ].endswith("ci_workflow_linux_validation_dispatch.json")
    linux_validation_verdict_json_index = (
        linux_validation_verdict_command.index("--output-json") + 1
    )
    assert linux_validation_verdict_command[linux_validation_verdict_json_index].endswith(
        "ci_workflow_linux_validation_verdict.json"
    )
    linux_validation_verdict_markdown_index = (
        linux_validation_verdict_command.index("--output-markdown") + 1
    )
    assert linux_validation_verdict_command[
        linux_validation_verdict_markdown_index
    ].endswith("ci_workflow_linux_validation_verdict.md")


def test_build_ci_workflow_pipeline_commands_supports_partial_skip():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
    )
    assert [stage for stage, _ in commands] == [
        "workflow_governance_publish",
        "workflow_decision",
        "workflow_dispatch",
        "workflow_dispatch_execution",
        "workflow_dispatch_trace",
        "workflow_dispatch_completion",
        "workflow_terminal_publish",
        "workflow_release_handoff",
        "workflow_release_trigger",
        "workflow_release_trace",
        "workflow_release_completion",
        "workflow_release_terminal_publish",
        "workflow_release_finalization",
        "workflow_release_closure",
        "workflow_release_archive",
        "workflow_release_verdict",
        "workflow_release_incident",
        "workflow_release_terminal_verdict",
        "workflow_release_delivery",
        "workflow_release_delivery_terminal_publish",
        "workflow_release_delivery_final_verdict",
        "workflow_release_follow_up_dispatch",
        "workflow_release_follow_up_closure",
        "workflow_release_follow_up_terminal_publish",
        "workflow_release_follow_up_final_verdict",
        "workflow_release_final_outcome",
        "workflow_release_final_terminal_publish",
        "workflow_release_final_handoff",
        "workflow_release_final_closure",
        "workflow_release_final_closure_publish",
        "workflow_release_final_archive",
        "workflow_release_final_verdict",
        "workflow_release_final_verdict_publish",
        "workflow_release_final_publish_archive",
        "workflow_gate_manifest_drift",
        "workflow_terminal_verdict",
        "workflow_linux_validation_dispatch",
        "workflow_linux_validation_verdict",
    ]


def test_build_ci_workflow_pipeline_commands_skip_all_returns_empty_plan():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert commands == []


def test_build_ci_workflow_pipeline_commands_supports_completion_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=False,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_dispatch_completion"]


def test_build_ci_workflow_pipeline_commands_supports_terminal_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=False,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_terminal_publish"]


def test_build_ci_workflow_pipeline_commands_supports_release_handoff_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=False,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_handoff"]


def test_build_ci_workflow_pipeline_commands_supports_release_trigger_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=False,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_trigger"]


def test_build_ci_workflow_pipeline_commands_supports_release_trace_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=False,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_trace"]


def test_build_ci_workflow_pipeline_commands_supports_release_completion_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=False,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_completion"]


def test_build_ci_workflow_pipeline_commands_supports_release_terminal_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=False,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_terminal_publish"]




def test_build_ci_workflow_pipeline_commands_supports_release_finalization_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=False,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_finalization"]


def test_build_ci_workflow_pipeline_commands_supports_release_closure_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=False,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_closure"]


def test_build_ci_workflow_pipeline_commands_supports_release_archive_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=False,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_archive"]


def test_build_ci_workflow_pipeline_commands_supports_release_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=False,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_verdict"]


def test_build_ci_workflow_pipeline_commands_supports_release_incident_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=False,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_incident"]


def test_build_ci_workflow_pipeline_commands_supports_release_terminal_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=False,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_terminal_verdict"]



def test_build_ci_workflow_pipeline_commands_supports_release_delivery_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=False,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_delivery"]





def test_build_ci_workflow_pipeline_commands_supports_release_delivery_terminal_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=False,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_delivery_terminal_publish"]


def test_build_ci_workflow_pipeline_commands_supports_release_delivery_final_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=False,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_delivery_final_verdict"]



def test_build_ci_workflow_pipeline_commands_supports_release_follow_up_dispatch_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=False,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_follow_up_dispatch"]


def test_build_ci_workflow_pipeline_commands_supports_release_follow_up_closure_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=False,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_follow_up_closure"]






def test_build_ci_workflow_pipeline_commands_supports_release_follow_up_terminal_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=False,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_follow_up_terminal_publish"]


def test_build_ci_workflow_pipeline_commands_supports_release_follow_up_final_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=False,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_follow_up_final_verdict"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_outcome_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=False,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_outcome"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_terminal_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=False,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_terminal_publish"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_handoff_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=False,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_handoff"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_closure_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=False,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_closure"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_closure_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=False,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_closure_publish"]










def test_build_ci_workflow_pipeline_commands_supports_release_final_archive_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=False,
        skip_release_final_verdict=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_archive"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=False,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_verdict"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_verdict_publish_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=False,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_verdict_publish"]


def test_build_ci_workflow_pipeline_commands_supports_release_final_publish_archive_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=False,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_release_final_publish_archive"]


def test_build_ci_workflow_pipeline_commands_supports_gate_manifest_drift_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=False,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_gate_manifest_drift"]


def test_build_ci_workflow_pipeline_commands_supports_terminal_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=False,
        skip_linux_validation_dispatch=True,
        skip_linux_validation_verdict=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_terminal_verdict"]


def test_build_ci_workflow_pipeline_commands_supports_linux_validation_dispatch_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=False,
        skip_linux_validation_verdict=True,
    )
    assert [stage for stage, _ in commands] == ["workflow_linux_validation_dispatch"]


def test_build_ci_workflow_pipeline_commands_supports_linux_validation_verdict_only_stage():
    commands = _build_commands(
        skip_plan=True,
        skip_yaml=True,
        skip_sync=True,
        skip_command_guard=True,
        skip_governance=True,
        skip_governance_publish=True,
        skip_decision=True,
        skip_dispatch=True,
        skip_dispatch_execution=True,
        skip_dispatch_trace=True,
        skip_dispatch_completion=True,
        skip_dispatch_terminal_publish=True,
        skip_dispatch_release_handoff=True,
        skip_release_trigger=True,
        skip_release_trace=True,
        skip_release_completion=True,
        skip_release_terminal_publish=True,
        skip_release_finalization=True,
        skip_release_closure=True,
        skip_release_archive=True,
        skip_release_verdict=True,
        skip_release_incident=True,
        skip_release_terminal_verdict=True,
        skip_release_delivery=True,
        skip_release_delivery_terminal_publish=True,
        skip_release_delivery_final_verdict=True,
        skip_release_follow_up_dispatch=True,
        skip_release_follow_up_closure=True,
        skip_release_follow_up_terminal_publish=True,
        skip_release_follow_up_final_verdict=True,
        skip_release_final_outcome=True,
        skip_release_final_terminal_publish=True,
        skip_release_final_handoff=True,
        skip_release_final_closure=True,
        skip_release_final_closure_publish=True,
        skip_release_final_archive=True,
        skip_release_final_verdict=True,
        skip_release_final_verdict_publish=True,
        skip_release_final_publish_archive=True,
        skip_gate_manifest_drift=True,
        skip_terminal_verdict=True,
        skip_linux_validation_dispatch=True,
        skip_linux_validation_verdict=False,
    )
    assert [stage for stage, _ in commands] == ["workflow_linux_validation_verdict"]








