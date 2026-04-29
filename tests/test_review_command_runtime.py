"""Runtime tests for /review command and review service behavior."""

from __future__ import annotations

import io
import subprocess
from pathlib import Path

import pytest
from rich.console import Console

from claude_code.commands.base import CommandContext
from claude_code.commands.review import ReviewCommand
from claude_code.services.review_service import ReviewService


def _context(tmp_path: Path) -> CommandContext:
    return CommandContext(
        working_directory=str(tmp_path),
        console=Console(file=io.StringIO(), force_terminal=False, width=120),
        engine=None,
        session=None,
        config=None,
    )


def _run_git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo: Path) -> None:
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "review-test@example.com")
    _run_git(repo, "config", "user.name", "review-test")


@pytest.mark.asyncio
async def test_review_command_reports_no_changes_for_clean_repo(tmp_path):
    _init_git_repo(tmp_path)
    baseline = tmp_path / "sample.py"
    baseline.write_text("def ok():\n    return 1\n", encoding="utf-8")
    _run_git(tmp_path, "add", "sample.py")
    _run_git(tmp_path, "commit", "-m", "baseline")

    result = await ReviewCommand().execute("", _context(tmp_path))

    assert result.success
    assert "No changes found to review." in str(result.content)


@pytest.mark.asyncio
async def test_review_command_returns_error_for_missing_file(tmp_path):
    result = await ReviewCommand().execute("missing.py", _context(tmp_path))

    assert result.success is False
    assert "File not found: missing.py" in str(result.error)


def test_review_service_detects_findings_for_specified_files(tmp_path):
    target = tmp_path / "risk.py"
    target.write_text(
        "\n".join(
            [
                "import subprocess",
                "subprocess.run('echo hello', shell=True)",
                "api_key = 'hardcoded-demo'",
                "print('debug log')",
                "# TODO: remove unsafe code",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = ReviewService().review_files(str(tmp_path), ["risk.py"])

    assert result.files_reviewed == ["risk.py"]
    assert len(result.findings) >= 4
    severities = {finding.severity for finding in result.findings}
    assert "high" in severities
    assert "low" in severities


@pytest.mark.asyncio
async def test_review_command_reviews_current_git_diff(tmp_path):
    _init_git_repo(tmp_path)
    target = tmp_path / "module.py"
    target.write_text("def safe():\n    return 0\n", encoding="utf-8")
    _run_git(tmp_path, "add", "module.py")
    _run_git(tmp_path, "commit", "-m", "baseline")

    target.write_text("def safe():\n    print('debug')\n    return 0\n", encoding="utf-8")

    result = await ReviewCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Files Reviewed: 1" in str(result.content)
    assert "module.py" in str(result.content)
    assert "[LOW]" in str(result.content)


def test_review_service_reviews_only_changed_lines_in_git_diff(tmp_path):
    _init_git_repo(tmp_path)
    target = tmp_path / "script.py"
    target.write_text(
        "\n".join(
            [
                "import subprocess",
                "def run():",
                "    return 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _run_git(tmp_path, "add", "script.py")
    _run_git(tmp_path, "commit", "-m", "baseline")

    target.write_text(
        "\n".join(
            [
                "import subprocess",
                "def run():",
                "    subprocess.run('echo risky', shell=True)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = ReviewService().review_git_changes(str(tmp_path))

    assert "script.py" in result.files_reviewed
    assert any("shell=True" in finding.issue for finding in result.findings)


@pytest.mark.asyncio
async def test_review_command_accepts_quoted_file_path(tmp_path):
    nested = tmp_path / "sub dir"
    nested.mkdir(parents=True, exist_ok=True)
    target = nested / "quoted.py"
    target.write_text("try:\n    pass\nexcept Exception:\n    pass\n", encoding="utf-8")

    result = await ReviewCommand().execute('"sub dir/quoted.py"', _context(tmp_path))

    assert result.success
    assert "sub dir/quoted.py" in str(result.content)
    assert "Findings:" in str(result.content)
