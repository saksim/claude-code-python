"""Linux-stage unified verification gate for Phase 0 -> Phase 2 cards.

This script only defines Linux-stage test command list and does not run tests.
"""

from __future__ import annotations

from pathlib import Path


LINUX_UNIFIED_TEST_FILES: tuple[str, ...] = (
    # Phase 0
    "tests/test_runtime_bootstrap.py",
    "tests/test_main_runtime.py",
    "tests/test_resume_runtime.py",
    "tests/test_commands_auth_runtime.py",
    "tests/test_features_runtime.py",
    "tests/test_review_command_runtime.py",
    "tests/test_session_history_memory_runtime.py",
    "tests/test_context_builder_runtime.py",
    "tests/test_hooks_runtime.py",
    "tests/test_doctor_runtime.py",
    "tests/test_plugins_runtime.py",
    "tests/test_phase0_regression_contract.py",
    "tests/test_phase0_gate_runtime.py",
    # Phase 1
    "tests/test_server_runtime.py",
    "tests/test_event_journal_runtime.py",
    "tests/test_tasks_backend_contract.py",
    "tests/test_tasks_factory_runtime.py",
    "tests/test_tasks_manager_runtime.py",
    "tests/test_tasks_middleware_runtime.py",
    "tests/test_sqlite_runtime_state_backend.py",
    "tests/test_memory_scope_runtime.py",
    "tests/test_active_memory_runtime.py",
    "tests/test_permissions_unified.py",
    "tests/test_query_engine_runtime.py",
    "tests/test_services_mcp_runtime.py",
    "tests/test_hook_permission_audit_runtime.py",
    "tests/test_cli_daemon_thin_client_runtime.py",
    "tests/test_p1_control_plane_gate_runtime.py",
    "tests/test_p1_event_journal_gate_runtime.py",
    "tests/test_p1_sqlite_state_backend_gate_runtime.py",
    "tests/test_p1_active_memory_gate_runtime.py",
    "tests/test_p1_hook_permission_audit_gate_runtime.py",
    "tests/test_p1_cli_thin_client_gate_runtime.py",
    # Phase 2
    "tests/test_multi_agent_supervisor_runtime.py",
    "tests/test_artifact_bus_runtime.py",
    "tests/test_ide_integration_runtime.py",
    "tests/test_github_ci_workflow_runtime.py",
    "tests/test_org_policy_audit_runtime.py",
    "tests/test_tools_registry_runtime.py",
    "tests/test_agent_background_context_runtime.py",
    "tests/test_custom_agents_loader_runtime.py",
    "tests/test_p2_jetbrains_ide_integration_runtime.py",
    "tests/test_p2_linux_unified_execution_gate_runtime.py",
    "tests/test_p2_linux_shard_aggregation_gate_runtime.py",
    "tests/test_p2_linux_report_publish_gate_runtime.py",
    "tests/test_p2_linux_unified_pipeline_gate_runtime.py",
    "tests/test_p2_linux_shard_plan_gate_runtime.py",
    "tests/test_p2_linux_ci_matrix_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_plan_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_yaml_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_sync_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_command_guard_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_governance_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_governance_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_decision_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_dispatch_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_dispatch_execution_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_dispatch_trace_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_dispatch_completion_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_terminal_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_handoff_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_trigger_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_trace_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_completion_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_terminal_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_finalization_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_closure_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_archive_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_verdict_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_incident_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_terminal_verdict_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_delivery_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_delivery_terminal_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_delivery_final_verdict_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_follow_up_dispatch_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_follow_up_closure_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_follow_up_final_verdict_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_outcome_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_terminal_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_handoff_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_closure_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_closure_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_archive_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_verdict_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_verdict_publish_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_release_final_publish_archive_gate_runtime.py",
    # gate contract coverage closure
    "tests/test_linux_unified_gate_runtime.py",
    "tests/test_p2_linux_gate_manifest_drift_gate_runtime.py",
    "tests/test_p2_linux_ci_workflow_terminal_verdict_gate_runtime.py",
    "tests/test_p2_lv_dispatch_rt.py",
    "tests/test_p2_lv_verdict_rt.py",
    "tests/test_p2_lv_verdict_publish_rt.py",
    "tests/test_p2_lv_terminal_publish_rt.py",
    "tests/test_p2_lv_final_verdict_rt.py",
    "tests/test_p2_lv_final_verdict_publish_rt.py",
    "tests/test_p2_lv_final_publish_archive_rt.py",
    "tests/test_p2_lv_terminal_verdict_rt.py",
    "tests/test_p2_lv_terminal_verdict_publish_rt.py",
    "tests/test_p2_lv_td_dispatch_rt.py",
    "tests/test_p2_lv_td_execution_rt.py",
    "tests/test_p2_lv_td_trace_rt.py",
    "tests/test_p2_lv_td_completion_rt.py",
    "tests/test_p2_lv_td_terminal_publish_rt.py",
    "tests/test_p2_lv_td_final_verdict_rt.py",
    "tests/test_p2_lv_td_final_verdict_publish_rt.py",
    "tests/test_p2_lv_td_final_publish_archive_rt.py",
    "tests/test_p2_lv_td_terminal_verdict_rt.py",
    "tests/test_p2_lv_td_tverdict_publish_rt.py",
    "tests/test_p2_lv_td_tverdict_publish_archive_rt.py",
    "tests/test_p2_multi_agent_supervisor_gate_runtime.py",
    "tests/test_p2_artifact_bus_gate_runtime.py",
    "tests/test_p2_ide_integration_gate_runtime.py",
    "tests/test_p2_github_ci_workflow_gate_runtime.py",
    "tests/test_p2_org_policy_audit_gate_runtime.py",
    "tests/test_p2_agent_runtime_parity_gate_runtime.py",
    "tests/test_p2_custom_agents_loader_gate_runtime.py",
    "tests/test_p2_jetbrains_ide_integration_gate_runtime.py",
)


def build_gate_commands(project_root: Path) -> list[str]:
    _ = project_root
    return [
        f"python -m pytest -q -c pytest.ini {test_file}"
        for test_file in LINUX_UNIFIED_TEST_FILES
    ]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    commands = build_gate_commands(root)
    print("Phase 0-2 Linux unified gate commands (execution in Linux stage):")
    for idx, command in enumerate(commands, start=1):
        print(f"{idx}. {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


