"""Runtime tests for P2-04 GitHub/CI workflow state machine."""

from __future__ import annotations

import subprocess

import pytest

from claude_code.services.github_ci_workflow import (
    GitHubCIWorkflowError,
    GitHubCIWorkflowService,
)


def _cp(command: list[str], *, returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)


def test_workflow_state_machine_success_with_fake_repo_and_pr_chain():
    working_directory = "/tmp/fake-repo"
    branch_name = "codex/p2-04-123"
    ci_command = "python -m pytest -q"

    command_map: dict[tuple[str, ...], subprocess.CompletedProcess[str]] = {
        ("git", "rev-parse", "--is-inside-work-tree"): _cp(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout="true\n",
        ),
        ("git", "status", "--porcelain"): _cp(["git", "status", "--porcelain"], stdout=""),
        ("git", "checkout", "-B", branch_name): _cp(["git", "checkout", "-B", branch_name]),
        ("git", "add", "-A"): _cp(["git", "add", "-A"]),
        ("git", "diff", "--cached", "--name-only"): _cp(
            ["git", "diff", "--cached", "--name-only"],
            stdout="claude_code/main.py\n",
        ),
        ("git", "commit", "-m", "feat: workflow"): _cp(["git", "commit", "-m", "feat: workflow"]),
        ("python", "-m", "pytest", "-q"): _cp(["python", "-m", "pytest", "-q"], stdout="ok\n"),
        ("git", "diff", "--name-only", "main...HEAD"): _cp(
            ["git", "diff", "--name-only", "main...HEAD"],
            stdout="claude_code/main.py\n",
        ),
        ("git", "push", "-u", "origin", branch_name): _cp(
            ["git", "push", "-u", "origin", branch_name],
            stdout="pushed\n",
        ),
        (
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            branch_name,
            "--title",
            "Workflow PR",
            "--body",
            "PR body",
        ): _cp(
            [
                "gh",
                "pr",
                "create",
                "--base",
                "main",
                "--head",
                branch_name,
                "--title",
                "Workflow PR",
                "--body",
                "PR body",
            ],
            stdout="https://github.com/example/repo/pull/1\n",
        ),
    }

    calls: list[tuple[list[str], str]] = []

    def _runner(command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
        calls.append((list(command), cwd))
        key = tuple(command)
        return command_map.get(key, _cp(command))

    service = GitHubCIWorkflowService(command_runner=_runner)
    payload = service.run_workflow(
        working_directory=working_directory,
        issue_reference="#123",
        plan_summary="deliver workflow",
        branch_name=branch_name,
        base_branch="main",
        commit_message="feat: workflow",
        pr_title="Workflow PR",
        pr_body="PR body",
        ci_commands=[ci_command],
        headless_ci=True,
        push_remote=True,
        create_pull_request=True,
    )

    assert payload["status"] == "completed"
    assert payload["branch_name"] == branch_name
    assert payload["pull_request_url"] == "https://github.com/example/repo/pull/1"
    step_status = {item["name"]: item["status"] for item in payload["steps"]}
    assert step_status == {
        "issue": "completed",
        "plan": "completed",
        "code": "completed",
        "test": "completed",
        "review": "completed",
        "pr": "completed",
    }
    assert all(cwd == working_directory for _, cwd in calls)
    assert any(command[:3] == ["gh", "pr", "create"] for command, _ in calls)


def test_workflow_fails_on_dirty_repo_when_not_allowed():
    def _runner(command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["git", "status", "--porcelain"]:
            return _cp(command, stdout=" M claude_code/main.py\n")
        return _cp(command, stdout="true\n")

    service = GitHubCIWorkflowService(command_runner=_runner)
    with pytest.raises(GitHubCIWorkflowError) as exc_info:
        service.run_workflow(
            working_directory="D:/repo",
            issue_reference="#dirty",
            ci_commands=[],
            create_pull_request=False,
            push_remote=False,
        )

    exc = exc_info.value
    assert exc.code == "repo_dirty"
    assert exc.status_code == 409
    assert isinstance(exc.details, dict)
    workflow = exc.details["workflow"]
    assert workflow["status"] == "failed"
    steps = {item["name"]: item["status"] for item in workflow["steps"]}
    assert steps["code"] == "failed"
    assert steps["test"] == "skipped"


def test_workflow_failure_classifies_permission_and_network_errors():
    branch_name = "codex/p2-04-403"

    def _permission_runner(command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["git", "status", "--porcelain"]:
            return _cp(command, stdout="")
        if command[:3] == ["gh", "pr", "create"]:
            return _cp(command, returncode=1, stderr="HTTP 403 Forbidden")
        if command[:3] == ["git", "diff", "--cached"]:
            return _cp(command, stdout="claude_code/main.py\n")
        return _cp(command, stdout="true\n")

    permission_service = GitHubCIWorkflowService(command_runner=_permission_runner)
    with pytest.raises(GitHubCIWorkflowError) as permission_exc:
        permission_service.run_workflow(
            working_directory="D:/repo",
            issue_reference="#403",
            branch_name=branch_name,
            commit_message="feat: pr",
            pr_title="permission",
            pr_body="permission",
            create_pull_request=True,
            push_remote=False,
        )
    assert permission_exc.value.code == "permission_denied"
    assert permission_exc.value.status_code == 403
    assert permission_exc.value.step == "pr"

    def _network_runner(command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["git", "status", "--porcelain"]:
            return _cp(command, stdout="")
        if command[:4] == ["git", "push", "-u", "origin"]:
            return _cp(command, returncode=128, stderr="Could not resolve host: github.com")
        if command[:3] == ["git", "diff", "--cached"]:
            return _cp(command, stdout="claude_code/main.py\n")
        return _cp(command, stdout="true\n")

    network_service = GitHubCIWorkflowService(command_runner=_network_runner)
    with pytest.raises(GitHubCIWorkflowError) as network_exc:
        network_service.run_workflow(
            working_directory="D:/repo",
            issue_reference="#net",
            branch_name="codex/p2-04-net",
            commit_message="feat: net",
            pr_title="network",
            pr_body="network",
            push_remote=True,
            create_pull_request=True,
        )
    assert network_exc.value.code == "network_failure"
    assert network_exc.value.status_code == 503
    assert network_exc.value.step == "pr"
