"""Phase 2 card P2-26 gate for Linux CI workflow full-pipeline orchestration.

This script composes P2-17 -> P2-79 into one CI-entry pipeline:
1) workflow plan generation,
2) workflow YAML rendering,
3) render drift sync,
4) command guard,
5) governance convergence,
6) governance publish,
7) execution decision,
8) dispatch readiness,
9) dispatch execution,
10) dispatch traceability,
11) dispatch completion await,
12) dispatch terminal publish,
13) release handoff,
14) release trigger,
15) release traceability,
16) release completion await,
17) release terminal publish,
18) release finalization,
19) release closure publish,
20) release archive publish,
21) release verdict publish,
22) release incident dispatch,
23) release terminal verdict publish,
24) release delivery closure publish,
25) release delivery terminal publish,
26) release delivery final verdict publish,
27) release follow-up dispatch publish,
28) release follow-up closure publish,
29) release follow-up terminal publish,
30) release follow-up final verdict,
31) release final outcome,
32) release final terminal publish,
33) release final handoff,
34) release final closure,
35) release final closure publish,
36) release final archive,
37) release final verdict,
38) release final verdict publish,
39) release final publish archive,
40) gate manifest drift closure,
41) terminal verdict closure,
42) Linux validation dispatch,
43) Linux validation verdict,
44) Linux validation verdict publish,
45) Linux validation terminal publish,
46) Linux validation final verdict,
47) Linux validation final verdict publish,
48) Linux validation final publish archive,
49) Linux validation terminal verdict,
50) Linux validation terminal verdict publish,
51) Linux validation terminal dispatch,
52) Linux validation terminal dispatch execution,
53) Linux validation terminal dispatch traceability (poll-ready run tracking contract).
54) Linux validation terminal dispatch completion await.
55) Linux validation terminal dispatch terminal publish.
56) Linux validation terminal dispatch final verdict.
57) Linux validation terminal dispatch final publish archive.
58) Linux validation terminal dispatch terminal verdict.
59) Linux validation terminal dispatch terminal verdict publish.
60) Linux validation terminal dispatch terminal verdict publish archive.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _format_shell_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def build_ci_workflow_pipeline_commands(
    *,
    python_executable: str,
    ci_matrix_path: Path,
    workflow_plan_output: Path,
    workflow_path: Path,
    metadata_path: Path,
    command_guard_output: Path,
    governance_report_output: Path,
    governance_publish_json_output: Path,
    governance_publish_markdown_output: Path,
    execution_decision_json_output: Path,
    execution_decision_markdown_output: Path,
    dispatch_json_output: Path,
    dispatch_markdown_output: Path,
    dispatch_execution_json_output: Path,
    dispatch_execution_markdown_output: Path,
    dispatch_trace_json_output: Path,
    dispatch_trace_markdown_output: Path,
    dispatch_completion_json_output: Path,
    dispatch_completion_markdown_output: Path,
    terminal_publish_json_output: Path,
    terminal_publish_markdown_output: Path,
    release_handoff_json_output: Path,
    release_handoff_markdown_output: Path,
    release_trigger_json_output: Path,
    release_trigger_markdown_output: Path,
    release_trace_json_output: Path,
    release_trace_markdown_output: Path,
    release_completion_json_output: Path,
    release_completion_markdown_output: Path,
    release_terminal_publish_json_output: Path,
    release_terminal_publish_markdown_output: Path,
    release_finalization_json_output: Path,
    release_finalization_markdown_output: Path,
    release_closure_json_output: Path,
    release_closure_markdown_output: Path,
    release_archive_json_output: Path,
    release_archive_markdown_output: Path,
    release_verdict_json_output: Path,
    release_verdict_markdown_output: Path,
    release_incident_json_output: Path,
    release_incident_markdown_output: Path,
    release_terminal_verdict_json_output: Path,
    release_terminal_verdict_markdown_output: Path,
    release_delivery_json_output: Path,
    release_delivery_markdown_output: Path,
    release_delivery_terminal_publish_json_output: Path,
    release_delivery_terminal_publish_markdown_output: Path,
    release_delivery_final_verdict_json_output: Path,
    release_delivery_final_verdict_markdown_output: Path,
    release_follow_up_dispatch_json_output: Path,
    release_follow_up_dispatch_markdown_output: Path,
    release_follow_up_closure_json_output: Path,
    release_follow_up_closure_markdown_output: Path,
    release_follow_up_terminal_publish_json_output: Path,
    release_follow_up_terminal_publish_markdown_output: Path,
    release_follow_up_final_verdict_json_output: Path,
    release_follow_up_final_verdict_markdown_output: Path,
    release_final_outcome_json_output: Path,
    release_final_outcome_markdown_output: Path,
    release_final_terminal_publish_json_output: Path,
    release_final_terminal_publish_markdown_output: Path,
    release_final_handoff_json_output: Path,
    release_final_handoff_markdown_output: Path,
    release_final_closure_json_output: Path,
    release_final_closure_markdown_output: Path,
    release_final_closure_publish_json_output: Path,
    release_final_closure_publish_markdown_output: Path,
    release_final_archive_json_output: Path,
    release_final_archive_markdown_output: Path,
    release_final_verdict_json_output: Path,
    release_final_verdict_markdown_output: Path,
    release_final_verdict_publish_json_output: Path,
    release_final_verdict_publish_markdown_output: Path,
    release_final_publish_archive_json_output: Path,
    release_final_publish_archive_markdown_output: Path,
    gate_manifest_drift_json_output: Path,
    gate_manifest_drift_markdown_output: Path,
    terminal_verdict_json_output: Path,
    terminal_verdict_markdown_output: Path,
    linux_validation_dispatch_json_output: Path,
    linux_validation_dispatch_markdown_output: Path,
    linux_validation_verdict_json_output: Path,
    linux_validation_verdict_markdown_output: Path,
    linux_validation_verdict_publish_json_output: Path,
    linux_validation_verdict_publish_markdown_output: Path,
    linux_validation_terminal_publish_json_output: Path,
    linux_validation_terminal_publish_markdown_output: Path,
    linux_validation_final_verdict_json_output: Path,
    linux_validation_final_verdict_markdown_output: Path,
    linux_validation_final_verdict_publish_json_output: Path,
    linux_validation_final_verdict_publish_markdown_output: Path,
    linux_validation_final_publish_archive_json_output: Path,
    linux_validation_final_publish_archive_markdown_output: Path,
    linux_validation_terminal_verdict_json_output: Path,
    linux_validation_terminal_verdict_markdown_output: Path,
    linux_validation_terminal_verdict_publish_json_output: Path,
    linux_validation_terminal_verdict_publish_markdown_output: Path,
    linux_validation_terminal_dispatch_json_output: Path,
    linux_validation_terminal_dispatch_markdown_output: Path,
    linux_validation_terminal_dispatch_execution_json_output: Path,
    linux_validation_terminal_dispatch_execution_markdown_output: Path,
    linux_validation_terminal_dispatch_trace_json_output: Path,
    linux_validation_terminal_dispatch_trace_markdown_output: Path,
    linux_validation_terminal_dispatch_completion_json_output: Path,
    linux_validation_terminal_dispatch_completion_markdown_output: Path,
    linux_validation_terminal_dispatch_terminal_publish_json_output: Path,
    linux_validation_terminal_dispatch_terminal_publish_markdown_output: Path,
    linux_validation_terminal_dispatch_final_verdict_json_output: Path,
    linux_validation_terminal_dispatch_final_verdict_markdown_output: Path,
    linux_validation_terminal_dispatch_final_verdict_publish_json_output: Path,
    linux_validation_terminal_dispatch_final_verdict_publish_markdown_output: Path,
    linux_validation_terminal_dispatch_final_publish_archive_json_output: Path,
    linux_validation_terminal_dispatch_final_publish_archive_markdown_output: Path,
    linux_validation_terminal_dispatch_terminal_verdict_json_output: Path,
    linux_validation_terminal_dispatch_terminal_verdict_markdown_output: Path,
    linux_validation_terminal_dispatch_terminal_verdict_publish_json_output: Path,
    linux_validation_terminal_dispatch_terminal_verdict_publish_markdown_output: Path,
    linux_validation_terminal_dispatch_terminal_verdict_publish_archive_json_output: Path,
    linux_validation_terminal_dispatch_terminal_verdict_publish_archive_markdown_output: Path,
    workflow_name: str,
    python_version: str,
    artifact_prefix: str,
    target_environment: str,
    release_channel: str,
    workflow_ref: str,
    release_workflow_path: str,
    release_workflow_ref: str,
    release_timeout_seconds: int,
    release_command: str,
    release_trace_poll_timeout_seconds: int,
    release_completion_poll_interval_seconds: int,
    release_completion_max_polls: int,
    release_completion_poll_timeout_seconds: int,
    incident_timeout_seconds: int,
    incident_command: str,
    incident_repo: str,
    incident_label: str,
    incident_title_prefix: str,
    follow_up_timeout_seconds: int,
    follow_up_command: str,
    follow_up_repo: str,
    follow_up_label: str,
    follow_up_title_prefix: str,
    on_block_policy: str,
    dispatch_timeout_seconds: int,
    trace_poll_timeout_seconds: int,
    completion_poll_interval_seconds: int,
    completion_max_polls: int,
    completion_poll_timeout_seconds: int,
    linux_validation_timeout_seconds: int,
    strict_generated_at: bool,
    sync_write: bool,
    command_guard_write: bool,
    dispatch_trace_poll_now: bool,
    release_trace_poll_now: bool,
    completion_allow_in_progress: bool,
    release_completion_allow_in_progress: bool,
    on_release_hold_policy: str,
    skip_plan: bool,
    skip_yaml: bool,
    skip_sync: bool,
    skip_command_guard: bool,
    skip_governance: bool,
    skip_governance_publish: bool,
    skip_decision: bool,
    skip_dispatch: bool,
    skip_dispatch_execution: bool,
    skip_dispatch_trace: bool,
    skip_dispatch_completion: bool,
    skip_dispatch_terminal_publish: bool,
    skip_dispatch_release_handoff: bool,
    skip_release_trigger: bool,
    skip_release_trace: bool,
    skip_release_completion: bool,
    skip_release_terminal_publish: bool,
    skip_release_finalization: bool,
    skip_release_closure: bool,
    skip_release_archive: bool,
    skip_release_verdict: bool,
    skip_release_incident: bool,
    skip_release_terminal_verdict: bool,
    skip_release_delivery: bool,
    skip_release_delivery_terminal_publish: bool,
    skip_release_delivery_final_verdict: bool,
    skip_release_follow_up_dispatch: bool,
    skip_release_follow_up_closure: bool,
    skip_release_follow_up_terminal_publish: bool,
    skip_release_follow_up_final_verdict: bool,
    skip_release_final_outcome: bool,
    skip_release_final_terminal_publish: bool,
    skip_release_final_handoff: bool,
    skip_release_final_closure: bool,
    skip_release_final_closure_publish: bool,
    skip_release_final_archive: bool,
    skip_release_final_verdict: bool,
    skip_release_final_verdict_publish: bool,
    skip_release_final_publish_archive: bool,
    skip_gate_manifest_drift: bool,
    skip_terminal_verdict: bool,
    skip_linux_validation_dispatch: bool,
    skip_linux_validation_verdict: bool,
    skip_linux_validation_verdict_publish: bool,
    skip_linux_validation_terminal_publish: bool,
    skip_linux_validation_final_verdict: bool,
    skip_linux_validation_final_verdict_publish: bool,
    skip_linux_validation_final_publish_archive: bool,
    skip_linux_validation_terminal_verdict: bool,
    skip_linux_validation_terminal_verdict_publish: bool,
    skip_linux_validation_terminal_dispatch: bool,
    skip_linux_validation_terminal_dispatch_execution: bool,
    skip_linux_validation_terminal_dispatch_trace: bool,
    skip_linux_validation_terminal_dispatch_completion: bool,
    skip_linux_validation_terminal_dispatch_terminal_publish: bool,
    skip_linux_validation_terminal_dispatch_final_verdict: bool,
    skip_linux_validation_terminal_dispatch_final_verdict_publish: bool,
    skip_linux_validation_terminal_dispatch_final_publish_archive: bool,
    skip_linux_validation_terminal_dispatch_terminal_verdict: bool,
    skip_linux_validation_terminal_dispatch_terminal_verdict_publish: bool,
    skip_linux_validation_terminal_dispatch_terminal_verdict_publish_archive: bool,
) -> list[tuple[str, list[str]]]:
    pipeline: list[tuple[str, list[str]]] = []

    if not skip_plan:
        pipeline.append(
            (
                "workflow_plan",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_plan_gate.py",
                    "--ci-matrix",
                    str(ci_matrix_path),
                    "--output",
                    str(workflow_plan_output),
                ],
            )
        )

    if not skip_yaml:
        pipeline.append(
            (
                "workflow_yaml",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_yaml_gate.py",
                    "--ci-workflow-plan",
                    str(workflow_plan_output),
                    "--output-workflow",
                    str(workflow_path),
                    "--output-metadata",
                    str(metadata_path),
                    "--workflow-name",
                    workflow_name,
                    "--python-version",
                    python_version,
                    "--artifact-prefix",
                    artifact_prefix,
                ],
            )
        )

    if not skip_sync:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_sync_gate.py",
            "--ci-workflow-plan",
            str(workflow_plan_output),
            "--workflow-path",
            str(workflow_path),
            "--metadata-path",
            str(metadata_path),
            "--workflow-name",
            workflow_name,
            "--python-version",
            python_version,
            "--artifact-prefix",
            artifact_prefix,
        ]
        if strict_generated_at:
            command.append("--strict-generated-at")
        if sync_write:
            command.append("--write")
        pipeline.append(("workflow_sync", command))

    if not skip_command_guard:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_command_guard_gate.py",
            "--ci-workflow-plan",
            str(workflow_plan_output),
            "--output",
            str(command_guard_output),
        ]
        if command_guard_write:
            command.append("--write")
        pipeline.append(("workflow_command_guard", command))

    if not skip_governance:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_governance_gate.py",
            "--ci-workflow-plan",
            str(workflow_plan_output),
            "--workflow-path",
            str(workflow_path),
            "--metadata-path",
            str(metadata_path),
            "--workflow-name",
            workflow_name,
            "--python-version",
            python_version,
            "--artifact-prefix",
            artifact_prefix,
            "--output",
            str(governance_report_output),
        ]
        if strict_generated_at:
            command.append("--strict-generated-at")
        pipeline.append(("workflow_governance", command))

    if not skip_governance_publish:
        pipeline.append(
            (
                "workflow_governance_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_governance_publish_gate.py",
                    "--governance-report",
                    str(governance_report_output),
                    "--output-json",
                    str(governance_publish_json_output),
                    "--output-markdown",
                    str(governance_publish_markdown_output),
                ],
            )
        )

    if not skip_decision:
        pipeline.append(
            (
                "workflow_decision",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_decision_gate.py",
                    "--governance-publish",
                    str(governance_publish_json_output),
                    "--workflow-plan",
                    str(workflow_plan_output),
                    "--workflow-path",
                    str(workflow_path),
                    "--on-block",
                    on_block_policy,
                    "--output-json",
                    str(execution_decision_json_output),
                    "--output-markdown",
                    str(execution_decision_markdown_output),
                ],
            )
        )

    if not skip_dispatch:
        pipeline.append(
            (
                "workflow_dispatch",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_dispatch_gate.py",
                    "--execution-decision",
                    str(execution_decision_json_output),
                    "--workflow-ref",
                    workflow_ref,
                    "--output-json",
                    str(dispatch_json_output),
                    "--output-markdown",
                    str(dispatch_markdown_output),
                ],
            )
        )

    if not skip_dispatch_execution:
        pipeline.append(
            (
                "workflow_dispatch_execution",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py",
                    "--dispatch-report",
                    str(dispatch_json_output),
                    "--project-root",
                    ".",
                    "--dispatch-timeout-seconds",
                    str(dispatch_timeout_seconds),
                    "--output-json",
                    str(dispatch_execution_json_output),
                    "--output-markdown",
                    str(dispatch_execution_markdown_output),
                ],
            )
        )

    if not skip_dispatch_trace:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py",
            "--dispatch-execution-report",
            str(dispatch_execution_json_output),
            "--project-root",
            ".",
            "--poll-timeout-seconds",
            str(trace_poll_timeout_seconds),
            "--output-json",
            str(dispatch_trace_json_output),
            "--output-markdown",
            str(dispatch_trace_markdown_output),
        ]
        if dispatch_trace_poll_now:
            command.append("--poll-now")
        pipeline.append(("workflow_dispatch_trace", command))

    if not skip_dispatch_completion:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py",
            "--dispatch-trace-report",
            str(dispatch_trace_json_output),
            "--project-root",
            ".",
            "--poll-interval-seconds",
            str(completion_poll_interval_seconds),
            "--max-polls",
            str(completion_max_polls),
            "--poll-timeout-seconds",
            str(completion_poll_timeout_seconds),
            "--output-json",
            str(dispatch_completion_json_output),
            "--output-markdown",
            str(dispatch_completion_markdown_output),
        ]
        if completion_allow_in_progress:
            command.append("--allow-in-progress")
        pipeline.append(("workflow_dispatch_completion", command))

    if not skip_dispatch_terminal_publish:
        pipeline.append(
            (
                "workflow_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py",
                    "--dispatch-completion-report",
                    str(dispatch_completion_json_output),
                    "--output-json",
                    str(terminal_publish_json_output),
                    "--output-markdown",
                    str(terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_dispatch_release_handoff:
        pipeline.append(
            (
                "workflow_release_handoff",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_handoff_gate.py",
                    "--terminal-publish-report",
                    str(terminal_publish_json_output),
                    "--target-environment",
                    target_environment,
                    "--release-channel",
                    release_channel,
                    "--output-json",
                    str(release_handoff_json_output),
                    "--output-markdown",
                    str(release_handoff_markdown_output),
                ],
            )
        )

    if not skip_release_trigger:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_release_trigger_gate.py",
            "--release-handoff-report",
            str(release_handoff_json_output),
            "--project-root",
            ".",
            "--release-workflow-path",
            release_workflow_path,
            "--release-workflow-ref",
            release_workflow_ref,
            "--release-timeout-seconds",
            str(release_timeout_seconds),
            "--output-json",
            str(release_trigger_json_output),
            "--output-markdown",
            str(release_trigger_markdown_output),
        ]
        if release_command.strip():
            command.extend(["--release-command", release_command])
        pipeline.append(("workflow_release_trigger", command))

    if not skip_release_trace:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_release_trace_gate.py",
            "--release-trigger-report",
            str(release_trigger_json_output),
            "--project-root",
            ".",
            "--poll-timeout-seconds",
            str(release_trace_poll_timeout_seconds),
            "--output-json",
            str(release_trace_json_output),
            "--output-markdown",
            str(release_trace_markdown_output),
        ]
        if release_trace_poll_now:
            command.append("--poll-now")
        pipeline.append(("workflow_release_trace", command))

    if not skip_release_completion:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_release_completion_gate.py",
            "--release-trace-report",
            str(release_trace_json_output),
            "--project-root",
            ".",
            "--poll-interval-seconds",
            str(release_completion_poll_interval_seconds),
            "--max-polls",
            str(release_completion_max_polls),
            "--poll-timeout-seconds",
            str(release_completion_poll_timeout_seconds),
            "--output-json",
            str(release_completion_json_output),
            "--output-markdown",
            str(release_completion_markdown_output),
        ]
        if release_completion_allow_in_progress:
            command.append("--allow-in-progress")
        pipeline.append(("workflow_release_completion", command))

    if not skip_release_terminal_publish:
        pipeline.append(
            (
                "workflow_release_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py",
                    "--release-completion-report",
                    str(release_completion_json_output),
                    "--output-json",
                    str(release_terminal_publish_json_output),
                    "--output-markdown",
                    str(release_terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_release_finalization:
        pipeline.append(
            (
                "workflow_release_finalization",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_finalization_gate.py",
                    "--release-terminal-publish-report",
                    str(release_terminal_publish_json_output),
                    "--on-hold",
                    on_release_hold_policy,
                    "--output-json",
                    str(release_finalization_json_output),
                    "--output-markdown",
                    str(release_finalization_markdown_output),
                ],
            )
        )

    if not skip_release_closure:
        pipeline.append(
            (
                "workflow_release_closure",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_closure_gate.py",
                    "--release-finalization-report",
                    str(release_finalization_json_output),
                    "--output-json",
                    str(release_closure_json_output),
                    "--output-markdown",
                    str(release_closure_markdown_output),
                ],
            )
        )

    if not skip_release_archive:
        pipeline.append(
            (
                "workflow_release_archive",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_archive_gate.py",
                    "--release-closure-report",
                    str(release_closure_json_output),
                    "--output-json",
                    str(release_archive_json_output),
                    "--output-markdown",
                    str(release_archive_markdown_output),
                ],
            )
        )

    if not skip_release_verdict:
        pipeline.append(
            (
                "workflow_release_verdict",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_verdict_gate.py",
                    "--release-archive-report",
                    str(release_archive_json_output),
                    "--output-json",
                    str(release_verdict_json_output),
                    "--output-markdown",
                    str(release_verdict_markdown_output),
                ],
            )
        )

    if not skip_release_incident:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_release_incident_gate.py",
            "--release-verdict-report",
            str(release_verdict_json_output),
            "--project-root",
            ".",
            "--incident-timeout-seconds",
            str(incident_timeout_seconds),
            "--incident-repo",
            incident_repo,
            "--incident-label",
            incident_label,
            "--incident-title-prefix",
            incident_title_prefix,
            "--output-json",
            str(release_incident_json_output),
            "--output-markdown",
            str(release_incident_markdown_output),
        ]
        if incident_command.strip():
            command.extend(["--incident-command", incident_command])
        pipeline.append(("workflow_release_incident", command))

    if not skip_release_terminal_verdict:
        pipeline.append(
            (
                "workflow_release_terminal_verdict",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py",
                    "--release-incident-report",
                    str(release_incident_json_output),
                    "--output-json",
                    str(release_terminal_verdict_json_output),
                    "--output-markdown",
                    str(release_terminal_verdict_markdown_output),
                ],
            )
        )

    if not skip_release_delivery:
        pipeline.append(
            (
                "workflow_release_delivery",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_delivery_gate.py",
                    "--release-terminal-verdict-report",
                    str(release_terminal_verdict_json_output),
                    "--output-json",
                    str(release_delivery_json_output),
                    "--output-markdown",
                    str(release_delivery_markdown_output),
                ],
            )
        )

    if not skip_release_delivery_terminal_publish:
        pipeline.append(
            (
                "workflow_release_delivery_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py",
                    "--release-delivery-report",
                    str(release_delivery_json_output),
                    "--output-json",
                    str(release_delivery_terminal_publish_json_output),
                    "--output-markdown",
                    str(release_delivery_terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_release_delivery_final_verdict:
        pipeline.append(
            (
                "workflow_release_delivery_final_verdict",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py",
                    "--release-delivery-terminal-publish-report",
                    str(release_delivery_terminal_publish_json_output),
                    "--output-json",
                    str(release_delivery_final_verdict_json_output),
                    "--output-markdown",
                    str(release_delivery_final_verdict_markdown_output),
                ],
            )
        )

    if not skip_release_follow_up_dispatch:
        pipeline.append(
            (
                "workflow_release_follow_up_dispatch",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py",
                    "--release-delivery-final-verdict-report",
                    str(release_delivery_final_verdict_json_output),
                    "--output-json",
                    str(release_follow_up_dispatch_json_output),
                    "--output-markdown",
                    str(release_follow_up_dispatch_markdown_output),
                ],
            )
        )

    if not skip_release_follow_up_closure:
        command = [
            python_executable,
            "scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py",
            "--release-follow-up-dispatch-report",
            str(release_follow_up_dispatch_json_output),
            "--project-root",
            ".",
            "--follow-up-timeout-seconds",
            str(follow_up_timeout_seconds),
            "--follow-up-repo",
            follow_up_repo,
            "--follow-up-label",
            follow_up_label,
            "--follow-up-title-prefix",
            follow_up_title_prefix,
            "--output-json",
            str(release_follow_up_closure_json_output),
            "--output-markdown",
            str(release_follow_up_closure_markdown_output),
        ]
        if follow_up_command.strip():
            command.extend(["--follow-up-command", follow_up_command])
        pipeline.append(("workflow_release_follow_up_closure", command))

    if not skip_release_follow_up_terminal_publish:
        pipeline.append(
            (
                "workflow_release_follow_up_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py",
                    "--release-follow-up-closure-report",
                    str(release_follow_up_closure_json_output),
                    "--output-json",
                    str(release_follow_up_terminal_publish_json_output),
                    "--output-markdown",
                    str(release_follow_up_terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_release_follow_up_final_verdict:
        pipeline.append(
            (
                "workflow_release_follow_up_final_verdict",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py",
                    "--release-follow-up-terminal-publish-report",
                    str(release_follow_up_terminal_publish_json_output),
                    "--output-json",
                    str(release_follow_up_final_verdict_json_output),
                    "--output-markdown",
                    str(release_follow_up_final_verdict_markdown_output),
                ],
            )
        )

    if not skip_release_final_outcome:
        pipeline.append(
            (
                "workflow_release_final_outcome",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py",
                    "--release-delivery-final-verdict-report",
                    str(release_delivery_final_verdict_json_output),
                    "--release-follow-up-final-verdict-report",
                    str(release_follow_up_final_verdict_json_output),
                    "--output-json",
                    str(release_final_outcome_json_output),
                    "--output-markdown",
                    str(release_final_outcome_markdown_output),
                ],
            )
        )

    if not skip_release_final_terminal_publish:
        pipeline.append(
            (
                "workflow_release_final_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py",
                    "--release-final-outcome-report",
                    str(release_final_outcome_json_output),
                    "--output-json",
                    str(release_final_terminal_publish_json_output),
                    "--output-markdown",
                    str(release_final_terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_release_final_handoff:
        pipeline.append(
            (
                "workflow_release_final_handoff",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py",
                    "--release-final-terminal-publish-report",
                    str(release_final_terminal_publish_json_output),
                    "--output-json",
                    str(release_final_handoff_json_output),
                    "--output-markdown",
                    str(release_final_handoff_markdown_output),
                ],
            )
        )

    if not skip_release_final_closure:
        pipeline.append(
            (
                "workflow_release_final_closure",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py",
                    "--release-final-handoff-report",
                    str(release_final_handoff_json_output),
                    "--output-json",
                    str(release_final_closure_json_output),
                    "--output-markdown",
                    str(release_final_closure_markdown_output),
                ],
            )
        )

    if not skip_release_final_closure_publish:
        pipeline.append(
            (
                "workflow_release_final_closure_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py",
                    "--release-final-closure-report",
                    str(release_final_closure_json_output),
                    "--output-json",
                    str(release_final_closure_publish_json_output),
                    "--output-markdown",
                    str(release_final_closure_publish_markdown_output),
                ],
            )
        )

    if not skip_release_final_archive:
        pipeline.append(
            (
                "workflow_release_final_archive",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py",
                    "--release-final-closure-publish-report",
                    str(release_final_closure_publish_json_output),
                    "--output-json",
                    str(release_final_archive_json_output),
                    "--output-markdown",
                    str(release_final_archive_markdown_output),
                ],
            )
        )

    if not skip_release_final_verdict:
        pipeline.append(
            (
                "workflow_release_final_verdict",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py",
                    "--release-final-archive-report",
                    str(release_final_archive_json_output),
                    "--output-json",
                    str(release_final_verdict_json_output),
                    "--output-markdown",
                    str(release_final_verdict_markdown_output),
                ],
            )
        )

    if not skip_release_final_verdict_publish:
        pipeline.append(
            (
                "workflow_release_final_verdict_publish",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py",
                    "--release-final-verdict-report",
                    str(release_final_verdict_json_output),
                    "--output-json",
                    str(release_final_verdict_publish_json_output),
                    "--output-markdown",
                    str(release_final_verdict_publish_markdown_output),
                ],
            )
        )

    if not skip_release_final_publish_archive:
        pipeline.append(
            (
                "workflow_release_final_publish_archive",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py",
                    "--release-final-verdict-publish-report",
                    str(release_final_verdict_publish_json_output),
                    "--output-json",
                    str(release_final_publish_archive_json_output),
                    "--output-markdown",
                    str(release_final_publish_archive_markdown_output),
                ],
            )
        )

    if not skip_gate_manifest_drift:
        pipeline.append(
            (
                "workflow_gate_manifest_drift",
                [
                    python_executable,
                    "scripts/run_p2_linux_gate_manifest_drift_gate.py",
                    "--output-json",
                    str(gate_manifest_drift_json_output),
                    "--output-markdown",
                    str(gate_manifest_drift_markdown_output),
                ],
            )
        )

    if not skip_terminal_verdict:
        pipeline.append(
            (
                "workflow_terminal_verdict",
                [
                    python_executable,
                    "scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py",
                    "--release-final-publish-archive-report",
                    str(release_final_publish_archive_json_output),
                    "--gate-manifest-drift-report",
                    str(gate_manifest_drift_json_output),
                    "--output-json",
                    str(terminal_verdict_json_output),
                    "--output-markdown",
                    str(terminal_verdict_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_dispatch:
        pipeline.append(
            (
                "workflow_linux_validation_dispatch",
                [
                    python_executable,
                    "scripts/run_p2_lv_dispatch_gate.py",
                    "--terminal-verdict-report",
                    str(terminal_verdict_json_output),
                    "--project-root",
                    ".",
                    "--python-executable",
                    python_executable,
                    "--linux-validation-timeout-seconds",
                    str(linux_validation_timeout_seconds),
                    "--output-json",
                    str(linux_validation_dispatch_json_output),
                    "--output-markdown",
                    str(linux_validation_dispatch_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_verdict:
        pipeline.append(
            (
                "workflow_linux_validation_verdict",
                [
                    python_executable,
                    "scripts/run_p2_lv_verdict_gate.py",
                    "--linux-validation-dispatch-report",
                    str(linux_validation_dispatch_json_output),
                    "--output-json",
                    str(linux_validation_verdict_json_output),
                    "--output-markdown",
                    str(linux_validation_verdict_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_verdict_publish:
        pipeline.append(
            (
                "workflow_linux_validation_verdict_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_verdict_publish_gate.py",
                    "--linux-validation-verdict-report",
                    str(linux_validation_verdict_json_output),
                    "--output-json",
                    str(linux_validation_verdict_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_verdict_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_publish:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_terminal_publish_gate.py",
                    "--linux-validation-verdict-publish-report",
                    str(linux_validation_verdict_publish_json_output),
                    "--output-json",
                    str(linux_validation_terminal_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_final_verdict:
        pipeline.append(
            (
                "workflow_linux_validation_final_verdict",
                [
                    python_executable,
                    "scripts/run_p2_lv_final_verdict_gate.py",
                    "--linux-validation-terminal-publish-report",
                    str(linux_validation_terminal_publish_json_output),
                    "--output-json",
                    str(linux_validation_final_verdict_json_output),
                    "--output-markdown",
                    str(linux_validation_final_verdict_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_final_verdict_publish:
        pipeline.append(
            (
                "workflow_linux_validation_final_verdict_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_final_verdict_publish_gate.py",
                    "--linux-validation-final-verdict-report",
                    str(linux_validation_final_verdict_json_output),
                    "--output-json",
                    str(linux_validation_final_verdict_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_final_verdict_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_final_publish_archive:
        pipeline.append(
            (
                "workflow_linux_validation_final_publish_archive",
                [
                    python_executable,
                    "scripts/run_p2_lv_final_publish_archive_gate.py",
                    "--linux-validation-final-verdict-publish-report",
                    str(linux_validation_final_verdict_publish_json_output),
                    "--output-json",
                    str(linux_validation_final_publish_archive_json_output),
                    "--output-markdown",
                    str(linux_validation_final_publish_archive_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_verdict:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_verdict",
                [
                    python_executable,
                    "scripts/run_p2_lv_terminal_verdict_gate.py",
                    "--linux-validation-final-publish-archive-report",
                    str(linux_validation_final_publish_archive_json_output),
                    "--output-json",
                    str(linux_validation_terminal_verdict_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_verdict_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_verdict_publish:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_verdict_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_terminal_verdict_publish_gate.py",
                    "--linux-validation-terminal-verdict-report",
                    str(linux_validation_terminal_verdict_json_output),
                    "--output-json",
                    str(linux_validation_terminal_verdict_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_verdict_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_dispatch_gate.py",
                    "--linux-validation-terminal-verdict-publish-report",
                    str(linux_validation_terminal_verdict_publish_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_execution:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_execution",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_execution_gate.py",
                    "--linux-validation-terminal-dispatch-report",
                    str(linux_validation_terminal_dispatch_json_output),
                    "--project-root",
                    ".",
                    "--python-executable",
                    python_executable,
                    "--linux-validation-terminal-timeout-seconds",
                    str(linux_validation_timeout_seconds),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_execution_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_execution_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_trace:
        command = [
            python_executable,
            "scripts/run_p2_lv_td_trace_gate.py",
            "--linux-validation-terminal-dispatch-execution-report",
            str(linux_validation_terminal_dispatch_execution_json_output),
            "--project-root",
            ".",
            "--poll-timeout-seconds",
            str(trace_poll_timeout_seconds),
            "--output-json",
            str(linux_validation_terminal_dispatch_trace_json_output),
            "--output-markdown",
            str(linux_validation_terminal_dispatch_trace_markdown_output),
        ]
        if dispatch_trace_poll_now:
            command.append("--poll-now")
        pipeline.append(("workflow_linux_validation_terminal_dispatch_trace", command))

    if not skip_linux_validation_terminal_dispatch_completion:
        command = [
            python_executable,
            "scripts/run_p2_lv_td_completion_gate.py",
            "--linux-validation-terminal-dispatch-trace-report",
            str(linux_validation_terminal_dispatch_trace_json_output),
            "--project-root",
            ".",
            "--poll-interval-seconds",
            str(completion_poll_interval_seconds),
            "--max-polls",
            str(completion_max_polls),
            "--poll-timeout-seconds",
            str(completion_poll_timeout_seconds),
            "--output-json",
            str(linux_validation_terminal_dispatch_completion_json_output),
            "--output-markdown",
            str(linux_validation_terminal_dispatch_completion_markdown_output),
        ]
        if completion_allow_in_progress:
            command.append("--allow-in-progress")
        pipeline.append(("workflow_linux_validation_terminal_dispatch_completion", command))

    if not skip_linux_validation_terminal_dispatch_terminal_publish:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_terminal_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_terminal_publish_gate.py",
                    "--linux-validation-terminal-dispatch-completion-report",
                    str(linux_validation_terminal_dispatch_completion_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_terminal_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_terminal_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_final_verdict:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_final_verdict",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_final_verdict_gate.py",
                    "--linux-validation-terminal-dispatch-terminal-publish-report",
                    str(linux_validation_terminal_dispatch_terminal_publish_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_final_verdict_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_final_verdict_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_final_verdict_publish:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_final_verdict_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_final_verdict_publish_gate.py",
                    "--linux-validation-terminal-dispatch-final-verdict-report",
                    str(linux_validation_terminal_dispatch_final_verdict_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_final_verdict_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_final_verdict_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_final_publish_archive:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_final_publish_archive",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_final_publish_archive_gate.py",
                    "--linux-validation-terminal-dispatch-final-verdict-publish-report",
                    str(linux_validation_terminal_dispatch_final_verdict_publish_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_final_publish_archive_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_final_publish_archive_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_terminal_verdict:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_terminal_verdict",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_terminal_verdict_gate.py",
                    "--linux-validation-terminal-dispatch-final-publish-archive-report",
                    str(linux_validation_terminal_dispatch_final_publish_archive_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_terminal_verdict_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_terminal_verdict_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_terminal_verdict_publish:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_tverdict_publish_gate.py",
                    "--linux-validation-terminal-dispatch-terminal-verdict-report",
                    str(linux_validation_terminal_dispatch_terminal_verdict_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_terminal_verdict_publish_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_terminal_verdict_publish_markdown_output),
                ],
            )
        )

    if not skip_linux_validation_terminal_dispatch_terminal_verdict_publish_archive:
        pipeline.append(
            (
                "workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive",
                [
                    python_executable,
                    "scripts/run_p2_lv_td_tverdict_publish_archive_gate.py",
                    "--linux-validation-terminal-dispatch-terminal-verdict-publish-report",
                    str(linux_validation_terminal_dispatch_terminal_verdict_publish_json_output),
                    "--output-json",
                    str(linux_validation_terminal_dispatch_terminal_verdict_publish_archive_json_output),
                    "--output-markdown",
                    str(linux_validation_terminal_dispatch_terminal_verdict_publish_archive_markdown_output),
                ],
            )
        )

    return pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Linux CI workflow full pipeline: P2-17 -> P2-79"
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
        help="Python executable for all sub-commands (default: current interpreter)",
    )
    parser.add_argument(
        "--ci-matrix",
        default=".claude/reports/linux_unified_gate/ci_matrix.json",
        help="P2-16 CI matrix JSON path",
    )
    parser.add_argument(
        "--workflow-plan-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        help="P2-17 workflow plan output path",
    )
    parser.add_argument(
        "--workflow-path",
        default=".github/workflows/linux_unified_gate.yml",
        help="P2-18 rendered workflow YAML path",
    )
    parser.add_argument(
        "--metadata-path",
        default=".claude/reports/linux_unified_gate/ci_workflow_render.json",
        help="P2-18 rendered metadata JSON path",
    )
    parser.add_argument(
        "--command-guard-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_command_guard.json",
        help="P2-20 command guard report JSON path",
    )
    parser.add_argument(
        "--governance-report-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance.json",
        help="P2-21 governance report JSON path",
    )
    parser.add_argument(
        "--governance-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance_publish.json",
        help="P2-22 governance publish JSON path",
    )
    parser.add_argument(
        "--governance-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_governance_publish.md",
        help="P2-22 governance publish markdown path",
    )
    parser.add_argument(
        "--execution-decision-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_execution_decision.json",
        help="P2-23 execution decision JSON path",
    )
    parser.add_argument(
        "--execution-decision-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_execution_decision.md",
        help="P2-23 execution decision markdown path",
    )
    parser.add_argument(
        "--dispatch-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch.json",
        help="P2-24 dispatch JSON path",
    )
    parser.add_argument(
        "--dispatch-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch.md",
        help="P2-24 dispatch markdown path",
    )
    parser.add_argument(
        "--dispatch-execution-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json",
        help="P2-25 dispatch execution JSON path",
    )
    parser.add_argument(
        "--dispatch-execution-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.md",
        help="P2-25 dispatch execution markdown path",
    )
    parser.add_argument(
        "--dispatch-trace-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json",
        help="P2-27 dispatch trace JSON path",
    )
    parser.add_argument(
        "--dispatch-trace-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.md",
        help="P2-27 dispatch trace markdown path",
    )
    parser.add_argument(
        "--dispatch-completion-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json",
        help="P2-28 dispatch completion JSON path",
    )
    parser.add_argument(
        "--dispatch-completion-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.md",
        help="P2-28 dispatch completion markdown path",
    )
    parser.add_argument(
        "--dispatch-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json",
        help="P2-29 terminal publish JSON path",
    )
    parser.add_argument(
        "--dispatch-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.md",
        help="P2-29 terminal publish markdown path",
    )
    parser.add_argument(
        "--dispatch-release-handoff-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_handoff.json",
        help="P2-30 release handoff JSON path",
    )
    parser.add_argument(
        "--dispatch-release-handoff-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_handoff.md",
        help="P2-30 release handoff markdown path",
    )
    parser.add_argument(
        "--release-trigger-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trigger.json",
        help="P2-31 release trigger JSON path",
    )
    parser.add_argument(
        "--release-trigger-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trigger.md",
        help="P2-31 release trigger markdown path",
    )
    parser.add_argument(
        "--release-trace-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trace.json",
        help="P2-32 release trace JSON path",
    )
    parser.add_argument(
        "--release-trace-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_trace.md",
        help="P2-32 release trace markdown path",
    )
    parser.add_argument(
        "--release-completion-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_completion.json",
        help="P2-33 release completion JSON path",
    )
    parser.add_argument(
        "--release-completion-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_completion.md",
        help="P2-33 release completion markdown path",
    )
    parser.add_argument(
        "--release-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json",
        help="P2-34 release terminal publish JSON path",
    )
    parser.add_argument(
        "--release-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.md",
        help="P2-34 release terminal publish markdown path",
    )
    parser.add_argument(
        "--release-finalization-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_finalization.json",
        help="P2-35 release finalization JSON path",
    )
    parser.add_argument(
        "--release-finalization-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_finalization.md",
        help="P2-35 release finalization markdown path",
    )
    parser.add_argument(
        "--release-closure-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_closure.json",
        help="P2-36 release closure JSON path",
    )
    parser.add_argument(
        "--release-closure-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_closure.md",
        help="P2-36 release closure markdown path",
    )
    parser.add_argument(
        "--release-archive-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_archive.json",
        help="P2-37 release archive JSON path",
    )
    parser.add_argument(
        "--release-archive-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_archive.md",
        help="P2-37 release archive markdown path",
    )
    parser.add_argument(
        "--release-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_verdict.json",
        help="P2-38 release verdict JSON path",
    )
    parser.add_argument(
        "--release-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_verdict.md",
        help="P2-38 release verdict markdown path",
    )
    parser.add_argument(
        "--release-incident-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_incident.json",
        help="P2-39 release incident JSON path",
    )
    parser.add_argument(
        "--release-incident-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_incident.md",
        help="P2-39 release incident markdown path",
    )
    parser.add_argument(
        "--release-terminal-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json",
        help="P2-40 release terminal verdict JSON path",
    )
    parser.add_argument(
        "--release-terminal-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.md",
        help="P2-40 release terminal verdict markdown path",
    )
    parser.add_argument(
        "--release-delivery-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery.json",
        help="P2-41 release delivery JSON path",
    )
    parser.add_argument(
        "--release-delivery-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery.md",
        help="P2-41 release delivery markdown path",
    )
    parser.add_argument(
        "--release-delivery-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json",
        help="P2-42 release delivery terminal publish JSON path",
    )
    parser.add_argument(
        "--release-delivery-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.md",
        help="P2-42 release delivery terminal publish markdown path",
    )
    parser.add_argument(
        "--release-delivery-final-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json",
        help="P2-43 release delivery final verdict JSON path",
    )
    parser.add_argument(
        "--release-delivery-final-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.md",
        help="P2-43 release delivery final verdict markdown path",
    )
    parser.add_argument(
        "--release-follow-up-dispatch-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json",
        help="P2-44 release follow-up dispatch JSON path",
    )
    parser.add_argument(
        "--release-follow-up-dispatch-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.md",
        help="P2-44 release follow-up dispatch markdown path",
    )
    parser.add_argument(
        "--release-follow-up-closure-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json",
        help="P2-45 release follow-up closure JSON path",
    )
    parser.add_argument(
        "--release-follow-up-closure-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.md",
        help="P2-45 release follow-up closure markdown path",
    )
    parser.add_argument(
        "--release-follow-up-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json",
        help="P2-46 release follow-up terminal publish JSON path",
    )
    parser.add_argument(
        "--release-follow-up-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.md",
        help="P2-46 release follow-up terminal publish markdown path",
    )
    parser.add_argument(
        "--release-follow-up-final-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json",
        help="P2-47 release follow-up final verdict JSON path",
    )
    parser.add_argument(
        "--release-follow-up-final-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.md",
        help="P2-47 release follow-up final verdict markdown path",
    )
    parser.add_argument(
        "--release-final-outcome-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json",
        help="P2-48 release final outcome JSON path",
    )
    parser.add_argument(
        "--release-final-outcome-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.md",
        help="P2-48 release final outcome markdown path",
    )
    parser.add_argument(
        "--release-final-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json",
        help="P2-49 release final terminal publish JSON path",
    )
    parser.add_argument(
        "--release-final-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.md",
        help="P2-49 release final terminal publish markdown path",
    )
    parser.add_argument(
        "--release-final-handoff-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json",
        help="P2-50 release final handoff JSON path",
    )
    parser.add_argument(
        "--release-final-handoff-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.md",
        help="P2-50 release final handoff markdown path",
    )
    parser.add_argument(
        "--release-final-closure-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json",
        help="P2-51 release final closure JSON path",
    )
    parser.add_argument(
        "--release-final-closure-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_closure.md",
        help="P2-51 release final closure markdown path",
    )
    parser.add_argument(
        "--release-final-closure-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json",
        help="P2-52 release final closure publish JSON path",
    )
    parser.add_argument(
        "--release-final-closure-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.md",
        help="P2-52 release final closure publish markdown path",
    )
    parser.add_argument(
        "--release-final-archive-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json",
        help="P2-53 release final archive JSON path",
    )
    parser.add_argument(
        "--release-final-archive-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.md",
        help="P2-53 release final archive markdown path",
    )
    parser.add_argument(
        "--release-final-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json",
        help="P2-54 release final verdict JSON path",
    )
    parser.add_argument(
        "--release-final-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.md",
        help="P2-54 release final verdict markdown path",
    )
    parser.add_argument(
        "--release-final-verdict-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json",
        help="P2-55 release final verdict publish JSON path",
    )
    parser.add_argument(
        "--release-final-verdict-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.md",
        help="P2-55 release final verdict publish markdown path",
    )
    parser.add_argument(
        "--release-final-publish-archive-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json",
        help="P2-56 release final publish archive JSON path",
    )
    parser.add_argument(
        "--release-final-publish-archive-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.md",
        help="P2-56 release final publish archive markdown path",
    )
    parser.add_argument(
        "--gate-manifest-drift-json-output",
        default=".claude/reports/linux_unified_gate/linux_gate_manifest_drift.json",
        help="P2-57 gate manifest drift closure JSON path",
    )
    parser.add_argument(
        "--gate-manifest-drift-markdown-output",
        default=".claude/reports/linux_unified_gate/linux_gate_manifest_drift.md",
        help="P2-57 gate manifest drift closure markdown path",
    )
    parser.add_argument(
        "--terminal-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json",
        help="P2-59 terminal verdict closure JSON path",
    )
    parser.add_argument(
        "--terminal-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.md",
        help="P2-59 terminal verdict closure markdown path",
    )
    parser.add_argument(
        "--linux-validation-dispatch-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json",
        help="P2-60 Linux validation dispatch JSON path",
    )
    parser.add_argument(
        "--linux-validation-dispatch-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.md",
        help="P2-60 Linux validation dispatch markdown path",
    )
    parser.add_argument(
        "--linux-validation-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json",
        help="P2-61 Linux validation verdict JSON path",
    )
    parser.add_argument(
        "--linux-validation-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.md",
        help="P2-61 Linux validation verdict markdown path",
    )
    parser.add_argument(
        "--linux-validation-verdict-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict_publish.json",
        help="P2-62 Linux validation verdict publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-verdict-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict_publish.md",
        help="P2-62 Linux validation verdict publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_publish.json",
        help="P2-63 Linux validation terminal publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_publish.md",
        help="P2-63 Linux validation terminal publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-final-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.json",
        help="P2-64 Linux validation final verdict JSON path",
    )
    parser.add_argument(
        "--linux-validation-final-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.md",
        help="P2-64 Linux validation final verdict markdown path",
    )
    parser.add_argument(
        "--linux-validation-final-verdict-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict_publish.json",
        help="P2-65 Linux validation final verdict publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-final-verdict-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict_publish.md",
        help="P2-65 Linux validation final verdict publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-final-publish-archive-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.json",
        help="P2-66 Linux validation final publish archive JSON path",
    )
    parser.add_argument(
        "--linux-validation-final-publish-archive-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.md",
        help="P2-66 Linux validation final publish archive markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.json",
        help="P2-67 Linux validation terminal verdict JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.md",
        help="P2-67 Linux validation terminal verdict markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-verdict-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict_publish.json",
        help="P2-68 Linux validation terminal verdict publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-verdict-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict_publish.md",
        help="P2-68 Linux validation terminal verdict publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.json",
        help="P2-69 Linux validation terminal dispatch JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.md",
        help="P2-69 Linux validation terminal dispatch markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-execution-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json",
        help="P2-70 Linux validation terminal dispatch execution JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-execution-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.md",
        help="P2-70 Linux validation terminal dispatch execution markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-trace-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json",
        help="P2-71 Linux validation terminal dispatch trace JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-trace-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.md",
        help="P2-71 Linux validation terminal dispatch trace markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-completion-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.json",
        help="P2-72 Linux validation terminal dispatch completion JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-completion-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.md",
        help="P2-72 Linux validation terminal dispatch completion markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json",
        help="P2-73 Linux validation terminal dispatch terminal publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.md",
        help="P2-73 Linux validation terminal dispatch terminal publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json",
        help="P2-74 Linux validation terminal dispatch final verdict JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.md",
        help="P2-74 Linux validation terminal dispatch final verdict markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-verdict-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.json",
        help="P2-75 Linux validation terminal dispatch final verdict publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-verdict-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.md",
        help="P2-75 Linux validation terminal dispatch final verdict publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-publish-archive-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json",
        help="P2-76 Linux validation terminal dispatch final publish archive JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-final-publish-archive-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.md",
        help="P2-76 Linux validation terminal dispatch final publish archive markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-verdict-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json",
        help="P2-77 Linux validation terminal dispatch terminal verdict JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-verdict-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.md",
        help="P2-77 Linux validation terminal dispatch terminal verdict markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-verdict-publish-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json",
        help="P2-78 Linux validation terminal dispatch terminal verdict publish JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-verdict-publish-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.md",
        help="P2-78 Linux validation terminal dispatch terminal verdict publish markdown path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-verdict-publish-archive-json-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.json",
        help="P2-79 Linux validation terminal dispatch terminal verdict publish archive JSON path",
    )
    parser.add_argument(
        "--linux-validation-terminal-dispatch-terminal-verdict-publish-archive-markdown-output",
        default=".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.md",
        help="P2-79 Linux validation terminal dispatch terminal verdict publish archive markdown path",
    )
    parser.add_argument(
        "--workflow-name",
        default="Linux Unified Gate",
        help="Workflow name forwarded to P2-18/P2-19/P2-21",
    )
    parser.add_argument(
        "--python-version",
        default="3.11",
        help="Python version forwarded to P2-18/P2-19/P2-21",
    )
    parser.add_argument(
        "--artifact-prefix",
        default="linux-unified-summary",
        help="Artifact prefix forwarded to P2-18/P2-19/P2-21",
    )
    parser.add_argument(
        "--target-environment",
        default="production",
        help="P2-30 release target environment",
    )
    parser.add_argument(
        "--release-channel",
        default="stable",
        help="P2-30 release channel",
    )
    parser.add_argument(
        "--workflow-ref",
        default="main",
        help="Workflow ref used in P2-24 dispatch command generation",
    )
    parser.add_argument(
        "--release-workflow-path",
        default=".github/workflows/release.yml",
        help="Release workflow path used in P2-31 release trigger gate",
    )
    parser.add_argument(
        "--release-workflow-ref",
        default="main",
        help="Release workflow ref used in P2-31 release trigger gate",
    )
    parser.add_argument(
        "--release-timeout-seconds",
        type=int,
        default=900,
        help="P2-31 release trigger command timeout in seconds",
    )
    parser.add_argument(
        "--release-command",
        default="",
        help="Optional explicit release trigger command string for P2-31",
    )
    parser.add_argument(
        "--release-trace-poll-timeout-seconds",
        type=int,
        default=600,
        help="P2-32 release run poll command timeout in seconds",
    )
    parser.add_argument(
        "--release-completion-poll-interval-seconds",
        type=int,
        default=30,
        help="P2-33 release completion poll loop sleep interval in seconds",
    )
    parser.add_argument(
        "--release-completion-max-polls",
        type=int,
        default=20,
        help="P2-33 release completion maximum poll attempts",
    )
    parser.add_argument(
        "--release-completion-poll-timeout-seconds",
        type=int,
        default=600,
        help="P2-33 per-poll command timeout in seconds",
    )
    parser.add_argument(
        "--incident-timeout-seconds",
        type=int,
        default=600,
        help="P2-39 incident command timeout in seconds",
    )
    parser.add_argument(
        "--incident-command",
        default="",
        help="Optional explicit incident command string for P2-39",
    )
    parser.add_argument(
        "--incident-repo",
        default="",
        help="Optional incident target repo (OWNER/REPO) for P2-39",
    )
    parser.add_argument(
        "--incident-label",
        default="release-incident",
        help="Incident label for P2-39 auto-built command",
    )
    parser.add_argument(
        "--incident-title-prefix",
        default="[release-incident]",
        help="Incident title prefix for P2-39 auto-built command",
    )
    parser.add_argument(
        "--follow-up-timeout-seconds",
        type=int,
        default=600,
        help="P2-45 follow-up command timeout in seconds",
    )
    parser.add_argument(
        "--follow-up-command",
        default="",
        help="Optional explicit follow-up command string for P2-45",
    )
    parser.add_argument(
        "--follow-up-repo",
        default="",
        help="Optional follow-up target repo (OWNER/REPO) for P2-45",
    )
    parser.add_argument(
        "--follow-up-label",
        default="release-follow-up",
        help="Follow-up label for P2-45 auto-built command",
    )
    parser.add_argument(
        "--follow-up-title-prefix",
        default="[release-follow-up]",
        help="Follow-up title prefix for P2-45 auto-built command",
    )
    parser.add_argument(
        "--on-block",
        choices=("fail", "skip"),
        default="fail",
        help="P2-23 blocked policy: fail or skip",
    )
    parser.add_argument(
        "--dispatch-timeout-seconds",
        type=int,
        default=300,
        help="P2-25 dispatch command timeout in seconds",
    )
    parser.add_argument(
        "--trace-poll-timeout-seconds",
        type=int,
        default=600,
        help="P2-27 run poll command timeout in seconds",
    )
    parser.add_argument(
        "--completion-poll-interval-seconds",
        type=int,
        default=30,
        help="P2-28 poll loop sleep interval in seconds",
    )
    parser.add_argument(
        "--completion-max-polls",
        type=int,
        default=20,
        help="P2-28 maximum poll attempts",
    )
    parser.add_argument(
        "--completion-poll-timeout-seconds",
        type=int,
        default=600,
        help="P2-28 per-poll command timeout in seconds",
    )
    parser.add_argument(
        "--linux-validation-timeout-seconds",
        type=int,
        default=7200,
        help="P2-60 Linux validation dispatch command timeout in seconds",
    )
    parser.add_argument(
        "--strict-generated-at",
        action="store_true",
        help="Forward strict generated_at drift check into P2-19/P2-21",
    )
    parser.add_argument(
        "--sync-write",
        action="store_true",
        help="Forward --write into P2-19 sync gate",
    )
    parser.add_argument(
        "--command-guard-write",
        action="store_true",
        help="Forward --write into P2-20 command guard gate",
    )
    parser.add_argument(
        "--dispatch-trace-poll-now",
        action="store_true",
        help="Forward --poll-now into P2-27 dispatch trace gate",
    )
    parser.add_argument(
        "--release-trace-poll-now",
        action="store_true",
        help="Forward --poll-now into P2-32 release trace gate",
    )
    parser.add_argument(
        "--completion-allow-in-progress",
        action="store_true",
        help="Forward --allow-in-progress into P2-28 dispatch completion gate",
    )
    parser.add_argument(
        "--release-completion-allow-in-progress",
        action="store_true",
        help="Forward --allow-in-progress into P2-33 release completion gate",
    )
    parser.add_argument(
        "--on-release-hold",
        choices=("pass", "fail"),
        default="pass",
        help="P2-35 hold policy for blocked/in_progress finalization paths",
    )
    parser.add_argument(
        "--skip-plan",
        action="store_true",
        help="Skip P2-17 workflow plan stage",
    )
    parser.add_argument(
        "--skip-yaml",
        action="store_true",
        help="Skip P2-18 workflow YAML stage",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip P2-19 sync stage",
    )
    parser.add_argument(
        "--skip-command-guard",
        action="store_true",
        help="Skip P2-20 command guard stage",
    )
    parser.add_argument(
        "--skip-governance",
        action="store_true",
        help="Skip P2-21 governance stage",
    )
    parser.add_argument(
        "--skip-governance-publish",
        action="store_true",
        help="Skip P2-22 governance publish stage",
    )
    parser.add_argument(
        "--skip-decision",
        action="store_true",
        help="Skip P2-23 execution decision stage",
    )
    parser.add_argument(
        "--skip-dispatch",
        action="store_true",
        help="Skip P2-24 dispatch stage",
    )
    parser.add_argument(
        "--skip-dispatch-execution",
        action="store_true",
        help="Skip P2-25 dispatch execution stage",
    )
    parser.add_argument(
        "--skip-dispatch-trace",
        action="store_true",
        help="Skip P2-27 dispatch traceability stage",
    )
    parser.add_argument(
        "--skip-dispatch-completion",
        action="store_true",
        help="Skip P2-28 dispatch completion await stage",
    )
    parser.add_argument(
        "--skip-dispatch-terminal-publish",
        action="store_true",
        help="Skip P2-29 terminal publish stage",
    )
    parser.add_argument(
        "--skip-dispatch-release-handoff",
        action="store_true",
        help="Skip P2-30 release handoff stage",
    )
    parser.add_argument(
        "--skip-release-trigger",
        action="store_true",
        help="Skip P2-31 release trigger stage",
    )
    parser.add_argument(
        "--skip-release-trace",
        action="store_true",
        help="Skip P2-32 release trace stage",
    )
    parser.add_argument(
        "--skip-release-completion",
        action="store_true",
        help="Skip P2-33 release completion stage",
    )
    parser.add_argument(
        "--skip-release-terminal-publish",
        action="store_true",
        help="Skip P2-34 release terminal publish stage",
    )
    parser.add_argument(
        "--skip-release-finalization",
        action="store_true",
        help="Skip P2-35 release finalization stage",
    )
    parser.add_argument(
        "--skip-release-closure",
        action="store_true",
        help="Skip P2-36 release closure stage",
    )
    parser.add_argument(
        "--skip-release-archive",
        action="store_true",
        help="Skip P2-37 release archive stage",
    )
    parser.add_argument(
        "--skip-release-verdict",
        action="store_true",
        help="Skip P2-38 release verdict stage",
    )
    parser.add_argument(
        "--skip-release-incident",
        action="store_true",
        help="Skip P2-39 release incident stage",
    )
    parser.add_argument(
        "--skip-release-terminal-verdict",
        action="store_true",
        help="Skip P2-40 release terminal verdict stage",
    )
    parser.add_argument(
        "--skip-release-delivery",
        action="store_true",
        help="Skip P2-41 release delivery stage",
    )
    parser.add_argument(
        "--skip-release-delivery-terminal-publish",
        action="store_true",
        help="Skip P2-42 release delivery terminal publish stage",
    )
    parser.add_argument(
        "--skip-release-delivery-final-verdict",
        action="store_true",
        help="Skip P2-43 release delivery final verdict stage",
    )
    parser.add_argument(
        "--skip-release-follow-up-dispatch",
        action="store_true",
        help="Skip P2-44 release follow-up dispatch stage",
    )
    parser.add_argument(
        "--skip-release-follow-up-closure",
        action="store_true",
        help="Skip P2-45 release follow-up closure stage",
    )
    parser.add_argument(
        "--skip-release-follow-up-terminal-publish",
        action="store_true",
        help="Skip P2-46 release follow-up terminal publish stage",
    )
    parser.add_argument(
        "--skip-release-follow-up-final-verdict",
        action="store_true",
        help="Skip P2-47 release follow-up final verdict stage",
    )
    parser.add_argument(
        "--skip-release-final-outcome",
        action="store_true",
        help="Skip P2-48 release final outcome stage",
    )
    parser.add_argument(
        "--skip-release-final-terminal-publish",
        action="store_true",
        help="Skip P2-49 release final terminal publish stage",
    )
    parser.add_argument(
        "--skip-release-final-handoff",
        action="store_true",
        help="Skip P2-50 release final handoff stage",
    )
    parser.add_argument(
        "--skip-release-final-closure",
        action="store_true",
        help="Skip P2-51 release final closure stage",
    )
    parser.add_argument(
        "--skip-release-final-closure-publish",
        action="store_true",
        help="Skip P2-52 release final closure publish stage",
    )
    parser.add_argument(
        "--skip-release-final-archive",
        action="store_true",
        help="Skip P2-53 release final archive stage",
    )
    parser.add_argument(
        "--skip-release-final-verdict",
        action="store_true",
        help="Skip P2-54 release final verdict stage",
    )
    parser.add_argument(
        "--skip-release-final-verdict-publish",
        action="store_true",
        help="Skip P2-55 release final verdict publish stage",
    )
    parser.add_argument(
        "--skip-release-final-publish-archive",
        action="store_true",
        help="Skip P2-56 release final publish archive stage",
    )
    parser.add_argument(
        "--skip-gate-manifest-drift",
        action="store_true",
        help="Skip P2-57 gate manifest drift closure stage",
    )
    parser.add_argument(
        "--skip-terminal-verdict",
        action="store_true",
        help="Skip P2-59 terminal verdict closure stage",
    )
    parser.add_argument(
        "--skip-linux-validation-dispatch",
        action="store_true",
        help="Skip P2-60 Linux validation dispatch stage",
    )
    parser.add_argument(
        "--skip-linux-validation-verdict",
        action="store_true",
        help="Skip P2-61 Linux validation verdict stage",
    )
    parser.add_argument(
        "--skip-linux-validation-verdict-publish",
        action="store_true",
        help="Skip P2-62 Linux validation verdict publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-publish",
        action="store_true",
        help="Skip P2-63 Linux validation terminal publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-final-verdict",
        action="store_true",
        help="Skip P2-64 Linux validation final verdict stage",
    )
    parser.add_argument(
        "--skip-linux-validation-final-verdict-publish",
        action="store_true",
        help="Skip P2-65 Linux validation final verdict publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-final-publish-archive",
        action="store_true",
        help="Skip P2-66 Linux validation final publish archive stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-verdict",
        action="store_true",
        help="Skip P2-67 Linux validation terminal verdict stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-verdict-publish",
        action="store_true",
        help="Skip P2-68 Linux validation terminal verdict publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch",
        action="store_true",
        help="Skip P2-69 Linux validation terminal dispatch stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-execution",
        action="store_true",
        help="Skip P2-70 Linux validation terminal dispatch execution stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-trace",
        action="store_true",
        help="Skip P2-71 Linux validation terminal dispatch trace stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-completion",
        action="store_true",
        help="Skip P2-72 Linux validation terminal dispatch completion stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-terminal-publish",
        action="store_true",
        help="Skip P2-73 Linux validation terminal dispatch terminal publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-final-verdict",
        action="store_true",
        help="Skip P2-74 Linux validation terminal dispatch final verdict stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-final-verdict-publish",
        action="store_true",
        help="Skip P2-75 Linux validation terminal dispatch final verdict publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-final-publish-archive",
        action="store_true",
        help="Skip P2-76 Linux validation terminal dispatch final publish archive stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-terminal-verdict",
        action="store_true",
        help="Skip P2-77 Linux validation terminal dispatch terminal verdict stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-terminal-verdict-publish",
        action="store_true",
        help="Skip P2-78 Linux validation terminal dispatch terminal verdict publish stage",
    )
    parser.add_argument(
        "--skip-linux-validation-terminal-dispatch-terminal-verdict-publish-archive",
        action="store_true",
        help="Skip P2-79 Linux validation terminal dispatch terminal verdict publish archive stage",
    )
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="Print planned commands",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands and exit",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at first non-zero stage exit code",
    )
    args = parser.parse_args()

    if not args.skip_linux_validation_terminal_verdict:
        args.skip_linux_validation_terminal_verdict = bool(
            args.skip_linux_validation_final_publish_archive
        )
    if not args.skip_linux_validation_terminal_verdict_publish:
        args.skip_linux_validation_terminal_verdict_publish = bool(
            args.skip_linux_validation_terminal_verdict
        )
    if not args.skip_linux_validation_terminal_dispatch:
        args.skip_linux_validation_terminal_dispatch = bool(
            args.skip_linux_validation_terminal_verdict_publish
        )
    if not args.skip_linux_validation_terminal_dispatch_execution:
        args.skip_linux_validation_terminal_dispatch_execution = bool(
            args.skip_linux_validation_terminal_dispatch
        )
    if not args.skip_linux_validation_terminal_dispatch_trace:
        args.skip_linux_validation_terminal_dispatch_trace = bool(
            args.skip_linux_validation_terminal_dispatch_execution
        )
    if not args.skip_linux_validation_terminal_dispatch_completion:
        args.skip_linux_validation_terminal_dispatch_completion = bool(
            args.skip_linux_validation_terminal_dispatch_trace
        )
    if not args.skip_linux_validation_terminal_dispatch_terminal_publish:
        args.skip_linux_validation_terminal_dispatch_terminal_publish = bool(
            args.skip_linux_validation_terminal_dispatch_completion
        )
    if not args.skip_linux_validation_terminal_dispatch_final_verdict:
        args.skip_linux_validation_terminal_dispatch_final_verdict = bool(
            args.skip_linux_validation_terminal_dispatch_terminal_publish
        )
    if not args.skip_linux_validation_terminal_dispatch_final_verdict_publish:
        args.skip_linux_validation_terminal_dispatch_final_verdict_publish = bool(
            args.skip_linux_validation_terminal_dispatch_final_verdict
        )
    if not args.skip_linux_validation_terminal_dispatch_final_publish_archive:
        args.skip_linux_validation_terminal_dispatch_final_publish_archive = bool(
            args.skip_linux_validation_terminal_dispatch_final_verdict_publish
        )
    if not args.skip_linux_validation_terminal_dispatch_terminal_verdict:
        args.skip_linux_validation_terminal_dispatch_terminal_verdict = bool(
            args.skip_linux_validation_terminal_dispatch_final_publish_archive
        )
    if not args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish:
        args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish = bool(
            args.skip_linux_validation_terminal_dispatch_terminal_verdict
        )
    if not args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish_archive:
        args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish_archive = bool(
            args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish
        )

    if args.dispatch_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] --dispatch-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.release_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] --release-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.release_trace_poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--release-trace-poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.trace_poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] --trace-poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.completion_poll_interval_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] --completion-poll-interval-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.completion_max_polls < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] --completion-max-polls must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.completion_poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] --completion-poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.release_completion_poll_interval_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--release-completion-poll-interval-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.release_completion_max_polls < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--release-completion-max-polls must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.release_completion_poll_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--release-completion-poll-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.incident_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--incident-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.follow_up_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--follow-up-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2
    if args.linux_validation_timeout_seconds < 1:
        print(
            "[p2-linux-ci-workflow-pipeline-gate] "
            "--linux-validation-timeout-seconds must be >= 1",
            file=sys.stderr,
        )
        return 2

    pipeline = build_ci_workflow_pipeline_commands(
        python_executable=args.python_executable,
        ci_matrix_path=Path(args.ci_matrix),
        workflow_plan_output=Path(args.workflow_plan_output),
        workflow_path=Path(args.workflow_path),
        metadata_path=Path(args.metadata_path),
        command_guard_output=Path(args.command_guard_output),
        governance_report_output=Path(args.governance_report_output),
        governance_publish_json_output=Path(args.governance_publish_json_output),
        governance_publish_markdown_output=Path(args.governance_publish_markdown_output),
        execution_decision_json_output=Path(args.execution_decision_json_output),
        execution_decision_markdown_output=Path(args.execution_decision_markdown_output),
        dispatch_json_output=Path(args.dispatch_json_output),
        dispatch_markdown_output=Path(args.dispatch_markdown_output),
        dispatch_execution_json_output=Path(args.dispatch_execution_json_output),
        dispatch_execution_markdown_output=Path(args.dispatch_execution_markdown_output),
        dispatch_trace_json_output=Path(args.dispatch_trace_json_output),
        dispatch_trace_markdown_output=Path(args.dispatch_trace_markdown_output),
        dispatch_completion_json_output=Path(args.dispatch_completion_json_output),
        dispatch_completion_markdown_output=Path(args.dispatch_completion_markdown_output),
        terminal_publish_json_output=Path(args.dispatch_terminal_publish_json_output),
        terminal_publish_markdown_output=Path(args.dispatch_terminal_publish_markdown_output),
        release_handoff_json_output=Path(args.dispatch_release_handoff_json_output),
        release_handoff_markdown_output=Path(args.dispatch_release_handoff_markdown_output),
        release_trigger_json_output=Path(args.release_trigger_json_output),
        release_trigger_markdown_output=Path(args.release_trigger_markdown_output),
        release_trace_json_output=Path(args.release_trace_json_output),
        release_trace_markdown_output=Path(args.release_trace_markdown_output),
        release_completion_json_output=Path(args.release_completion_json_output),
        release_completion_markdown_output=Path(args.release_completion_markdown_output),
        release_terminal_publish_json_output=Path(args.release_terminal_publish_json_output),
        release_terminal_publish_markdown_output=Path(
            args.release_terminal_publish_markdown_output
        ),
        release_finalization_json_output=Path(args.release_finalization_json_output),
        release_finalization_markdown_output=Path(args.release_finalization_markdown_output),
        release_closure_json_output=Path(args.release_closure_json_output),
        release_closure_markdown_output=Path(args.release_closure_markdown_output),
        release_archive_json_output=Path(args.release_archive_json_output),
        release_archive_markdown_output=Path(args.release_archive_markdown_output),
        release_verdict_json_output=Path(args.release_verdict_json_output),
        release_verdict_markdown_output=Path(args.release_verdict_markdown_output),
        release_incident_json_output=Path(args.release_incident_json_output),
        release_incident_markdown_output=Path(args.release_incident_markdown_output),
        release_terminal_verdict_json_output=Path(args.release_terminal_verdict_json_output),
        release_terminal_verdict_markdown_output=Path(
            args.release_terminal_verdict_markdown_output
        ),
        release_delivery_json_output=Path(args.release_delivery_json_output),
        release_delivery_markdown_output=Path(args.release_delivery_markdown_output),
        release_delivery_terminal_publish_json_output=Path(
            args.release_delivery_terminal_publish_json_output
        ),
        release_delivery_terminal_publish_markdown_output=Path(
            args.release_delivery_terminal_publish_markdown_output
        ),
        release_delivery_final_verdict_json_output=Path(
            args.release_delivery_final_verdict_json_output
        ),
        release_delivery_final_verdict_markdown_output=Path(
            args.release_delivery_final_verdict_markdown_output
        ),
        release_follow_up_dispatch_json_output=Path(
            args.release_follow_up_dispatch_json_output
        ),
        release_follow_up_dispatch_markdown_output=Path(
            args.release_follow_up_dispatch_markdown_output
        ),
        release_follow_up_closure_json_output=Path(
            args.release_follow_up_closure_json_output
        ),
        release_follow_up_closure_markdown_output=Path(
            args.release_follow_up_closure_markdown_output
        ),
        release_follow_up_terminal_publish_json_output=Path(
            args.release_follow_up_terminal_publish_json_output
        ),
        release_follow_up_terminal_publish_markdown_output=Path(
            args.release_follow_up_terminal_publish_markdown_output
        ),
        release_follow_up_final_verdict_json_output=Path(
            args.release_follow_up_final_verdict_json_output
        ),
        release_follow_up_final_verdict_markdown_output=Path(
            args.release_follow_up_final_verdict_markdown_output
        ),
        release_final_outcome_json_output=Path(args.release_final_outcome_json_output),
        release_final_outcome_markdown_output=Path(args.release_final_outcome_markdown_output),
        release_final_terminal_publish_json_output=Path(
            args.release_final_terminal_publish_json_output
        ),
        release_final_terminal_publish_markdown_output=Path(
            args.release_final_terminal_publish_markdown_output
        ),
        release_final_handoff_json_output=Path(args.release_final_handoff_json_output),
        release_final_handoff_markdown_output=Path(args.release_final_handoff_markdown_output),
        release_final_closure_json_output=Path(args.release_final_closure_json_output),
        release_final_closure_markdown_output=Path(args.release_final_closure_markdown_output),
        release_final_closure_publish_json_output=Path(
            args.release_final_closure_publish_json_output
        ),
        release_final_closure_publish_markdown_output=Path(
            args.release_final_closure_publish_markdown_output
        ),
        release_final_archive_json_output=Path(args.release_final_archive_json_output),
        release_final_archive_markdown_output=Path(args.release_final_archive_markdown_output),
        release_final_verdict_json_output=Path(args.release_final_verdict_json_output),
        release_final_verdict_markdown_output=Path(args.release_final_verdict_markdown_output),
        release_final_verdict_publish_json_output=Path(
            args.release_final_verdict_publish_json_output
        ),
        release_final_verdict_publish_markdown_output=Path(
            args.release_final_verdict_publish_markdown_output
        ),
        release_final_publish_archive_json_output=Path(
            args.release_final_publish_archive_json_output
        ),
        release_final_publish_archive_markdown_output=Path(
            args.release_final_publish_archive_markdown_output
        ),
        gate_manifest_drift_json_output=Path(args.gate_manifest_drift_json_output),
        gate_manifest_drift_markdown_output=Path(args.gate_manifest_drift_markdown_output),
        terminal_verdict_json_output=Path(args.terminal_verdict_json_output),
        terminal_verdict_markdown_output=Path(args.terminal_verdict_markdown_output),
        linux_validation_dispatch_json_output=Path(
            args.linux_validation_dispatch_json_output
        ),
        linux_validation_dispatch_markdown_output=Path(
            args.linux_validation_dispatch_markdown_output
        ),
        linux_validation_verdict_json_output=Path(
            args.linux_validation_verdict_json_output
        ),
        linux_validation_verdict_markdown_output=Path(
            args.linux_validation_verdict_markdown_output
        ),
        linux_validation_verdict_publish_json_output=Path(
            args.linux_validation_verdict_publish_json_output
        ),
        linux_validation_verdict_publish_markdown_output=Path(
            args.linux_validation_verdict_publish_markdown_output
        ),
        linux_validation_terminal_publish_json_output=Path(
            args.linux_validation_terminal_publish_json_output
        ),
        linux_validation_terminal_publish_markdown_output=Path(
            args.linux_validation_terminal_publish_markdown_output
        ),
        linux_validation_final_verdict_json_output=Path(
            args.linux_validation_final_verdict_json_output
        ),
        linux_validation_final_verdict_markdown_output=Path(
            args.linux_validation_final_verdict_markdown_output
        ),
        linux_validation_final_verdict_publish_json_output=Path(
            args.linux_validation_final_verdict_publish_json_output
        ),
        linux_validation_final_verdict_publish_markdown_output=Path(
            args.linux_validation_final_verdict_publish_markdown_output
        ),
        linux_validation_final_publish_archive_json_output=Path(
            args.linux_validation_final_publish_archive_json_output
        ),
        linux_validation_final_publish_archive_markdown_output=Path(
            args.linux_validation_final_publish_archive_markdown_output
        ),
        linux_validation_terminal_verdict_json_output=Path(
            args.linux_validation_terminal_verdict_json_output
        ),
        linux_validation_terminal_verdict_markdown_output=Path(
            args.linux_validation_terminal_verdict_markdown_output
        ),
        linux_validation_terminal_verdict_publish_json_output=Path(
            args.linux_validation_terminal_verdict_publish_json_output
        ),
        linux_validation_terminal_verdict_publish_markdown_output=Path(
            args.linux_validation_terminal_verdict_publish_markdown_output
        ),
        linux_validation_terminal_dispatch_json_output=Path(
            args.linux_validation_terminal_dispatch_json_output
        ),
        linux_validation_terminal_dispatch_markdown_output=Path(
            args.linux_validation_terminal_dispatch_markdown_output
        ),
        linux_validation_terminal_dispatch_execution_json_output=Path(
            args.linux_validation_terminal_dispatch_execution_json_output
        ),
        linux_validation_terminal_dispatch_execution_markdown_output=Path(
            args.linux_validation_terminal_dispatch_execution_markdown_output
        ),
        linux_validation_terminal_dispatch_trace_json_output=Path(
            args.linux_validation_terminal_dispatch_trace_json_output
        ),
        linux_validation_terminal_dispatch_trace_markdown_output=Path(
            args.linux_validation_terminal_dispatch_trace_markdown_output
        ),
        linux_validation_terminal_dispatch_completion_json_output=Path(
            args.linux_validation_terminal_dispatch_completion_json_output
        ),
        linux_validation_terminal_dispatch_completion_markdown_output=Path(
            args.linux_validation_terminal_dispatch_completion_markdown_output
        ),
        linux_validation_terminal_dispatch_terminal_publish_json_output=Path(
            args.linux_validation_terminal_dispatch_terminal_publish_json_output
        ),
        linux_validation_terminal_dispatch_terminal_publish_markdown_output=Path(
            args.linux_validation_terminal_dispatch_terminal_publish_markdown_output
        ),
        linux_validation_terminal_dispatch_final_verdict_json_output=Path(
            args.linux_validation_terminal_dispatch_final_verdict_json_output
        ),
        linux_validation_terminal_dispatch_final_verdict_markdown_output=Path(
            args.linux_validation_terminal_dispatch_final_verdict_markdown_output
        ),
        linux_validation_terminal_dispatch_final_verdict_publish_json_output=Path(
            args.linux_validation_terminal_dispatch_final_verdict_publish_json_output
        ),
        linux_validation_terminal_dispatch_final_verdict_publish_markdown_output=Path(
            args.linux_validation_terminal_dispatch_final_verdict_publish_markdown_output
        ),
        linux_validation_terminal_dispatch_final_publish_archive_json_output=Path(
            args.linux_validation_terminal_dispatch_final_publish_archive_json_output
        ),
        linux_validation_terminal_dispatch_final_publish_archive_markdown_output=Path(
            args.linux_validation_terminal_dispatch_final_publish_archive_markdown_output
        ),
        workflow_name=args.workflow_name,
        linux_validation_terminal_dispatch_terminal_verdict_json_output=Path(
            args.linux_validation_terminal_dispatch_terminal_verdict_json_output
        ),
        linux_validation_terminal_dispatch_terminal_verdict_markdown_output=Path(
            args.linux_validation_terminal_dispatch_terminal_verdict_markdown_output
        ),
        linux_validation_terminal_dispatch_terminal_verdict_publish_json_output=Path(
            args.linux_validation_terminal_dispatch_terminal_verdict_publish_json_output
        ),
        linux_validation_terminal_dispatch_terminal_verdict_publish_markdown_output=Path(
            args.linux_validation_terminal_dispatch_terminal_verdict_publish_markdown_output
        ),
        linux_validation_terminal_dispatch_terminal_verdict_publish_archive_json_output=Path(
            args.linux_validation_terminal_dispatch_terminal_verdict_publish_archive_json_output
        ),
        linux_validation_terminal_dispatch_terminal_verdict_publish_archive_markdown_output=Path(
            args.linux_validation_terminal_dispatch_terminal_verdict_publish_archive_markdown_output
        ),
        python_version=args.python_version,
        artifact_prefix=args.artifact_prefix,
        target_environment=args.target_environment,
        release_channel=args.release_channel,
        workflow_ref=args.workflow_ref,
        release_workflow_path=args.release_workflow_path,
        release_workflow_ref=args.release_workflow_ref,
        release_timeout_seconds=args.release_timeout_seconds,
        release_command=args.release_command,
        release_trace_poll_timeout_seconds=args.release_trace_poll_timeout_seconds,
        release_completion_poll_interval_seconds=args.release_completion_poll_interval_seconds,
        release_completion_max_polls=args.release_completion_max_polls,
        release_completion_poll_timeout_seconds=args.release_completion_poll_timeout_seconds,
        incident_timeout_seconds=args.incident_timeout_seconds,
        incident_command=args.incident_command,
        incident_repo=args.incident_repo,
        incident_label=args.incident_label,
        incident_title_prefix=args.incident_title_prefix,
        follow_up_timeout_seconds=args.follow_up_timeout_seconds,
        follow_up_command=args.follow_up_command,
        follow_up_repo=args.follow_up_repo,
        follow_up_label=args.follow_up_label,
        follow_up_title_prefix=args.follow_up_title_prefix,
        on_block_policy=args.on_block,
        dispatch_timeout_seconds=args.dispatch_timeout_seconds,
        trace_poll_timeout_seconds=args.trace_poll_timeout_seconds,
        completion_poll_interval_seconds=args.completion_poll_interval_seconds,
        completion_max_polls=args.completion_max_polls,
        completion_poll_timeout_seconds=args.completion_poll_timeout_seconds,
        linux_validation_timeout_seconds=args.linux_validation_timeout_seconds,
        strict_generated_at=args.strict_generated_at,
        sync_write=args.sync_write,
        command_guard_write=args.command_guard_write,
        dispatch_trace_poll_now=args.dispatch_trace_poll_now,
        release_trace_poll_now=args.release_trace_poll_now,
        completion_allow_in_progress=args.completion_allow_in_progress,
        release_completion_allow_in_progress=args.release_completion_allow_in_progress,
        on_release_hold_policy=args.on_release_hold,
        skip_plan=args.skip_plan,
        skip_yaml=args.skip_yaml,
        skip_sync=args.skip_sync,
        skip_command_guard=args.skip_command_guard,
        skip_governance=args.skip_governance,
        skip_governance_publish=args.skip_governance_publish,
        skip_decision=args.skip_decision,
        skip_dispatch=args.skip_dispatch,
        skip_dispatch_execution=args.skip_dispatch_execution,
        skip_dispatch_trace=args.skip_dispatch_trace,
        skip_dispatch_completion=args.skip_dispatch_completion,
        skip_dispatch_terminal_publish=args.skip_dispatch_terminal_publish,
        skip_dispatch_release_handoff=args.skip_dispatch_release_handoff,
        skip_release_trigger=args.skip_release_trigger,
        skip_release_trace=args.skip_release_trace,
        skip_release_completion=args.skip_release_completion,
        skip_release_terminal_publish=args.skip_release_terminal_publish,
        skip_release_finalization=args.skip_release_finalization,
        skip_release_closure=args.skip_release_closure,
        skip_release_archive=args.skip_release_archive,
        skip_release_verdict=args.skip_release_verdict,
        skip_release_incident=args.skip_release_incident,
        skip_release_terminal_verdict=args.skip_release_terminal_verdict,
        skip_release_delivery=args.skip_release_delivery,
        skip_release_delivery_terminal_publish=args.skip_release_delivery_terminal_publish,
        skip_release_delivery_final_verdict=args.skip_release_delivery_final_verdict,
        skip_release_follow_up_dispatch=args.skip_release_follow_up_dispatch,
        skip_release_follow_up_closure=args.skip_release_follow_up_closure,
        skip_release_follow_up_terminal_publish=args.skip_release_follow_up_terminal_publish,
        skip_release_follow_up_final_verdict=args.skip_release_follow_up_final_verdict,
        skip_release_final_outcome=args.skip_release_final_outcome,
        skip_release_final_terminal_publish=args.skip_release_final_terminal_publish,
        skip_release_final_handoff=args.skip_release_final_handoff,
        skip_release_final_closure=args.skip_release_final_closure,
        skip_release_final_closure_publish=args.skip_release_final_closure_publish,
        skip_release_final_archive=args.skip_release_final_archive,
        skip_release_final_verdict=args.skip_release_final_verdict,
        skip_release_final_verdict_publish=args.skip_release_final_verdict_publish,
        skip_release_final_publish_archive=args.skip_release_final_publish_archive,
        skip_gate_manifest_drift=args.skip_gate_manifest_drift,
        skip_terminal_verdict=args.skip_terminal_verdict,
        skip_linux_validation_dispatch=args.skip_linux_validation_dispatch,
        skip_linux_validation_verdict=args.skip_linux_validation_verdict,
        skip_linux_validation_verdict_publish=args.skip_linux_validation_verdict_publish,
        skip_linux_validation_terminal_publish=args.skip_linux_validation_terminal_publish,
        skip_linux_validation_final_verdict=args.skip_linux_validation_final_verdict,
        skip_linux_validation_final_verdict_publish=args.skip_linux_validation_final_verdict_publish,
        skip_linux_validation_final_publish_archive=args.skip_linux_validation_final_publish_archive,
        skip_linux_validation_terminal_verdict=args.skip_linux_validation_terminal_verdict,
        skip_linux_validation_terminal_verdict_publish=args.skip_linux_validation_terminal_verdict_publish,
        skip_linux_validation_terminal_dispatch=args.skip_linux_validation_terminal_dispatch,
        skip_linux_validation_terminal_dispatch_execution=args.skip_linux_validation_terminal_dispatch_execution,
        skip_linux_validation_terminal_dispatch_trace=args.skip_linux_validation_terminal_dispatch_trace,
        skip_linux_validation_terminal_dispatch_completion=args.skip_linux_validation_terminal_dispatch_completion,
        skip_linux_validation_terminal_dispatch_terminal_publish=args.skip_linux_validation_terminal_dispatch_terminal_publish,
        skip_linux_validation_terminal_dispatch_final_verdict=args.skip_linux_validation_terminal_dispatch_final_verdict,
        skip_linux_validation_terminal_dispatch_final_verdict_publish=args.skip_linux_validation_terminal_dispatch_final_verdict_publish,
        skip_linux_validation_terminal_dispatch_final_publish_archive=args.skip_linux_validation_terminal_dispatch_final_publish_archive,
        skip_linux_validation_terminal_dispatch_terminal_verdict=args.skip_linux_validation_terminal_dispatch_terminal_verdict,
        skip_linux_validation_terminal_dispatch_terminal_verdict_publish=args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish,
        skip_linux_validation_terminal_dispatch_terminal_verdict_publish_archive=args.skip_linux_validation_terminal_dispatch_terminal_verdict_publish_archive,
    )

    if not pipeline:
        print("[p2-linux-ci-workflow-pipeline-gate] no stages selected")
        return 0

    if args.print_commands or args.dry_run:
        for idx, (stage, command) in enumerate(pipeline, start=1):
            print(f"{idx}. [{stage}] {_format_shell_command(command)}")
        if args.dry_run:
            return 0

    project_root = Path(__file__).resolve().parents[1]
    overall_exit = 0
    for idx, (stage, command) in enumerate(pipeline, start=1):
        print(f"[{idx}/{len(pipeline)}] stage={stage} {_format_shell_command(command)}")
        exit_code = subprocess.call(command, cwd=project_root)
        if exit_code != 0:
            if overall_exit == 0:
                overall_exit = exit_code
            if args.fail_fast:
                return exit_code
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())










