"""GitHub/CI workflow service for issue->plan->code->test->review->PR automation."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class GitHubCIWorkflowError(RuntimeError):
    """Raised when workflow execution fails with structured metadata."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "workflow_failed",
        status_code: int = 500,
        details: Any = None,
        step: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        self.step = step


class WorkflowStepStatus(Enum):
    """Step state in workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class WorkflowStepRecord:
    """Runtime state for one workflow step."""

    name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    message: str = ""
    commands: list[str] = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "commands": list(self.commands),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass(slots=True)
class _WorkflowState:
    """Mutable workflow state accumulator."""

    workflow_id: str
    working_directory: str
    headless_ci: bool
    steps: list[WorkflowStepRecord] = field(
        default_factory=lambda: [
            WorkflowStepRecord(name="issue"),
            WorkflowStepRecord(name="plan"),
            WorkflowStepRecord(name="code"),
            WorkflowStepRecord(name="test"),
            WorkflowStepRecord(name="review"),
            WorkflowStepRecord(name="pr"),
        ]
    )
    branch_name: str | None = None
    pull_request_url: str | None = None
    started_at: str = field(default_factory=lambda: _utc_now_iso())
    finished_at: str | None = None

    def get_step(self, name: str) -> WorkflowStepRecord:
        for step in self.steps:
            if step.name == name:
                return step
        raise KeyError(f"unknown workflow step: {name}")

    def start(self, name: str) -> WorkflowStepRecord:
        step = self.get_step(name)
        step.status = WorkflowStepStatus.RUNNING
        step.started_at = _utc_now_iso()
        return step

    def complete(self, name: str, message: str = "") -> WorkflowStepRecord:
        step = self.get_step(name)
        step.status = WorkflowStepStatus.COMPLETED
        step.message = message
        step.finished_at = _utc_now_iso()
        if step.started_at is None:
            step.started_at = step.finished_at
        return step

    def fail(self, name: str, message: str) -> WorkflowStepRecord:
        step = self.get_step(name)
        step.status = WorkflowStepStatus.FAILED
        step.message = message
        step.finished_at = _utc_now_iso()
        if step.started_at is None:
            step.started_at = step.finished_at
        return step

    def skip_pending_after(self, name: str, message: str) -> None:
        target_seen = False
        for step in self.steps:
            if step.name == name:
                target_seen = True
                continue
            if not target_seen:
                continue
            if step.status != WorkflowStepStatus.PENDING:
                continue
            step.status = WorkflowStepStatus.SKIPPED
            step.message = message
            step.started_at = _utc_now_iso()
            step.finished_at = step.started_at

    def to_dict(self, *, status: str) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "status": status,
            "working_directory": self.working_directory,
            "headless_ci": self.headless_ci,
            "branch_name": self.branch_name,
            "pull_request_url": self.pull_request_url,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [step.to_dict() for step in self.steps],
        }


CommandRunner = Callable[[list[str], str], subprocess.CompletedProcess[str]]


class GitHubCIWorkflowService:
    """Execute workflow card P2-04 with pluggable command runner."""

    def __init__(self, *, command_runner: Optional[CommandRunner] = None) -> None:
        self._command_runner = command_runner or _default_command_runner

    def run_workflow(
        self,
        *,
        working_directory: str,
        issue_reference: str | None = None,
        plan_summary: str | None = None,
        branch_name: str | None = None,
        base_branch: str = "main",
        commit_message: str | None = None,
        pr_title: str | None = None,
        pr_body: str | None = None,
        ci_commands: list[str] | None = None,
        headless_ci: bool = True,
        allow_dirty_repo: bool = False,
        push_remote: bool = True,
        create_pull_request: bool = True,
    ) -> dict[str, Any]:
        ci_commands = [cmd.strip() for cmd in (ci_commands or []) if str(cmd).strip()]
        workflow_id = f"ghci-{int(time.time() * 1000)}"
        state = _WorkflowState(
            workflow_id=workflow_id,
            working_directory=working_directory,
            headless_ci=headless_ci,
        )

        try:
            self._run_issue_step(state, issue_reference)
            self._run_plan_step(state, plan_summary)

            active_branch = self._run_code_step(
                state,
                issue_reference=issue_reference,
                plan_summary=plan_summary,
                branch_name=branch_name,
                base_branch=base_branch,
                commit_message=commit_message,
                allow_dirty_repo=allow_dirty_repo,
            )
            state.branch_name = active_branch

            self._run_test_step(state, ci_commands=ci_commands, headless_ci=headless_ci)
            self._run_review_step(state, base_branch=base_branch)
            self._run_pr_step(
                state,
                issue_reference=issue_reference,
                plan_summary=plan_summary,
                branch_name=active_branch,
                base_branch=base_branch,
                pr_title=pr_title,
                pr_body=pr_body,
                push_remote=push_remote,
                create_pull_request=create_pull_request,
            )
        except GitHubCIWorkflowError as exc:
            failed_step = exc.step or "code"
            state.fail(failed_step, exc.message)
            state.skip_pending_after(failed_step, "skipped due to previous failure")
            state.finished_at = _utc_now_iso()
            details = dict(exc.details or {})
            details["workflow"] = state.to_dict(status="failed")
            raise GitHubCIWorkflowError(
                exc.message,
                code=exc.code,
                status_code=exc.status_code,
                details=details,
                step=failed_step,
            ) from exc

        state.finished_at = _utc_now_iso()
        return state.to_dict(status="completed")

    def _run_issue_step(self, state: _WorkflowState, issue_reference: str | None) -> None:
        state.start("issue")
        state.complete("issue", issue_reference or "no issue reference provided")

    def _run_plan_step(self, state: _WorkflowState, plan_summary: str | None) -> None:
        state.start("plan")
        state.complete("plan", plan_summary or "no plan summary provided")

    def _run_code_step(
        self,
        state: _WorkflowState,
        *,
        issue_reference: str | None,
        plan_summary: str | None,
        branch_name: str | None,
        base_branch: str,
        commit_message: str | None,
        allow_dirty_repo: bool,
    ) -> str:
        step = state.start("code")
        self._expect_success(
            ["git", "rev-parse", "--is-inside-work-tree"],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )

        status_result = self._expect_success(
            ["git", "status", "--porcelain"],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )
        is_dirty = bool(status_result.stdout.strip())
        if is_dirty and not allow_dirty_repo:
            raise GitHubCIWorkflowError(
                "Repository working tree is not clean; set allow_dirty_repo=true to continue.",
                code="repo_dirty",
                status_code=409,
                step=step.name,
                details={"status_output": status_result.stdout},
            )

        target_branch = branch_name or _build_branch_name(issue_reference)
        self._expect_success(
            ["git", "checkout", "-B", target_branch],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )
        self._expect_success(
            ["git", "add", "-A"],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )

        staged_result = self._expect_success(
            ["git", "diff", "--cached", "--name-only"],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )
        staged_files = [line.strip() for line in staged_result.stdout.splitlines() if line.strip()]
        if staged_files:
            resolved_message = commit_message or _build_default_commit_message(
                issue_reference=issue_reference,
                plan_summary=plan_summary,
            )
            self._expect_success(
                ["git", "commit", "-m", resolved_message],
                working_directory=state.working_directory,
                step=step.name,
                record=step,
            )
            summary = (
                f"checked out {target_branch} from {base_branch}; "
                f"committed {len(staged_files)} staged file(s)"
            )
        else:
            summary = f"checked out {target_branch}; no staged changes to commit"

        state.complete(step.name, summary)
        return target_branch

    def _run_test_step(
        self,
        state: _WorkflowState,
        *,
        ci_commands: list[str],
        headless_ci: bool,
    ) -> None:
        step = state.start("test")
        if not headless_ci:
            state.complete(step.name, "headless CI disabled by request")
            return
        if not ci_commands:
            state.complete(step.name, "headless CI enabled; no ci_commands configured")
            return

        for command_line in ci_commands:
            command = _split_command(command_line)
            self._expect_success(
                command,
                working_directory=state.working_directory,
                step=step.name,
                record=step,
            )
        state.complete(step.name, f"executed {len(ci_commands)} headless CI command(s)")

    def _run_review_step(self, state: _WorkflowState, *, base_branch: str) -> None:
        step = state.start("review")
        review_command = ["git", "diff", "--name-only", f"{base_branch}...HEAD"]
        result = self._run_command(review_command, state.working_directory, record=step)
        changed_files: list[str]
        if result.returncode == 0:
            changed_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            state.complete(step.name, f"review snapshot contains {len(changed_files)} changed file(s)")
            return

        fallback_result = self._expect_success(
            ["git", "diff", "--name-only"],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )
        changed_files = [line.strip() for line in fallback_result.stdout.splitlines() if line.strip()]
        state.complete(
            step.name,
            (
                f"review fallback used (base branch unavailable: {base_branch}); "
                f"changed file(s)={len(changed_files)}"
            ),
        )

    def _run_pr_step(
        self,
        state: _WorkflowState,
        *,
        issue_reference: str | None,
        plan_summary: str | None,
        branch_name: str,
        base_branch: str,
        pr_title: str | None,
        pr_body: str | None,
        push_remote: bool,
        create_pull_request: bool,
    ) -> None:
        step = state.start("pr")
        if not create_pull_request:
            state.complete(step.name, "pull request creation skipped by request")
            return

        if push_remote:
            self._expect_success(
                ["git", "push", "-u", "origin", branch_name],
                working_directory=state.working_directory,
                step=step.name,
                record=step,
            )

        resolved_title = pr_title or _build_default_pr_title(issue_reference, plan_summary)
        resolved_body = pr_body or _build_default_pr_body(issue_reference, plan_summary, headless_ci=state.headless_ci)
        pr_result = self._expect_success(
            [
                "gh",
                "pr",
                "create",
                "--base",
                base_branch,
                "--head",
                branch_name,
                "--title",
                resolved_title,
                "--body",
                resolved_body,
            ],
            working_directory=state.working_directory,
            step=step.name,
            record=step,
        )

        pr_url = _extract_first_url(pr_result.stdout) or _extract_first_url(pr_result.stderr)
        state.pull_request_url = pr_url
        if pr_url:
            state.complete(step.name, f"pull request created: {pr_url}")
        else:
            state.complete(step.name, "pull request created (URL not detected in command output)")

    def _expect_success(
        self,
        command: list[str],
        *,
        working_directory: str,
        step: str,
        record: WorkflowStepRecord,
    ) -> subprocess.CompletedProcess[str]:
        result = self._run_command(command, working_directory, record=record)
        if result.returncode == 0:
            return result
        raise _command_failure_to_error(
            command=command,
            result=result,
            step=step,
        )

    def _run_command(
        self,
        command: list[str],
        working_directory: str,
        *,
        record: WorkflowStepRecord,
    ) -> subprocess.CompletedProcess[str]:
        command_text = _join_command(command)
        record.commands.append(command_text)
        return self._command_runner(command, working_directory)


def _default_command_runner(command: list[str], working_directory: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=working_directory,
        capture_output=True,
        text=True,
    )


def _command_failure_to_error(
    *,
    command: list[str],
    result: subprocess.CompletedProcess[str],
    step: str,
) -> GitHubCIWorkflowError:
    stderr_text = (result.stderr or "").strip()
    stdout_text = (result.stdout or "").strip()
    output_text = f"{stderr_text}\n{stdout_text}".strip().lower()
    if _contains_any(
        output_text,
        [
            "permission denied",
            "resource not accessible",
            "forbidden",
            "403",
            "authentication failed",
            "not authorized",
            "requires authentication",
        ],
    ):
        code = "permission_denied"
        status_code = 403
    elif _contains_any(
        output_text,
        [
            "could not resolve host",
            "network is unreachable",
            "connection timed out",
            "timed out",
            "failed to connect",
            "connection reset",
        ],
    ):
        code = "network_failure"
        status_code = 503
    elif _contains_any(
        output_text,
        [
            "not a git repository",
            "unknown revision",
        ],
    ):
        code = "repo_error"
        status_code = 400
    elif _contains_any(
        output_text,
        [
            "not recognized as an internal or external command",
            "command not found",
            "no such file or directory",
        ],
    ):
        code = "command_unavailable"
        status_code = 503
    else:
        code = "workflow_command_failed"
        status_code = 500

    message = (
        f"Command failed at step '{step}': {_join_command(command)} "
        f"(exit={result.returncode})"
    )
    details = {
        "command": command,
        "return_code": result.returncode,
        "stderr": stderr_text,
        "stdout": stdout_text,
    }
    return GitHubCIWorkflowError(
        message,
        code=code,
        status_code=status_code,
        details=details,
        step=step,
    )


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def _build_branch_name(issue_reference: str | None) -> str:
    issue = (issue_reference or "").strip().replace("#", "")
    if issue:
        normalized = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in issue).strip("-")
        if normalized:
            return f"codex/p2-04-{normalized}"
    return f"codex/p2-04-{int(time.time())}"


def _build_default_commit_message(*, issue_reference: str | None, plan_summary: str | None) -> str:
    if issue_reference:
        return f"feat(workflow): progress {issue_reference}"
    if plan_summary:
        compact = " ".join(plan_summary.split())
        if compact:
            return f"feat(workflow): {compact[:72]}"
    return "feat(workflow): progress github ci workflow"


def _build_default_pr_title(issue_reference: str | None, plan_summary: str | None) -> str:
    if issue_reference and plan_summary:
        return f"{issue_reference}: {plan_summary[:80]}"
    if issue_reference:
        return f"{issue_reference}: workflow delivery"
    if plan_summary:
        return f"Workflow delivery: {plan_summary[:80]}"
    return "Workflow delivery update"


def _build_default_pr_body(issue_reference: str | None, plan_summary: str | None, *, headless_ci: bool) -> str:
    lines = [
        "Automated issue->plan->code->test->review->PR workflow execution.",
    ]
    if issue_reference:
        lines.append(f"Issue: {issue_reference}")
    if plan_summary:
        lines.append(f"Plan: {plan_summary}")
    lines.append(f"Headless CI mode: {'enabled' if headless_ci else 'disabled'}")
    return "\n".join(lines)


def _split_command(command_line: str) -> list[str]:
    parsed = shlex.split(command_line, posix=os.name != "nt")
    if not parsed:
        raise GitHubCIWorkflowError(
            f"Invalid empty CI command: {command_line!r}",
            code="validation_error",
            status_code=400,
            step="test",
        )
    return parsed


def _join_command(command: list[str]) -> str:
    return " ".join(command)


def _extract_first_url(text: str) -> str | None:
    if not text:
        return None
    for token in text.replace("\r", " ").replace("\n", " ").split():
        normalized = token.strip()
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "GitHubCIWorkflowError",
    "WorkflowStepStatus",
    "WorkflowStepRecord",
    "GitHubCIWorkflowService",
]
