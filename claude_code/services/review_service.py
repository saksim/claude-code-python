"""Review service for command-level diff and file risk inspection."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


_HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_SHELL_TRUE_PATTERN = re.compile(r"subprocess\.(?:run|Popen|call|check_call|check_output)\(.*shell\s*=\s*True")
_TODO_PATTERN = re.compile(r"#\s*(?:TODO|FIXME)\b", re.IGNORECASE)
_HARD_CODED_SECRET_PATTERN = re.compile(
    r"\b(?:api_key|token|password|secret)\b\s*=\s*['\"][^'\"]+['\"]",
    re.IGNORECASE,
)
_BARE_EXCEPT_PATTERN = re.compile(r"^\s*except\s*:\s*$")
_BROAD_EXCEPT_PATTERN = re.compile(r"^\s*except\s+Exception\b")
_DEBUG_PRINT_PATTERN = re.compile(r"\bprint\(")


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    """A structured finding produced by static review rules."""

    file_path: str
    line: int
    severity: str
    issue: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class ReviewResult:
    """Review result for a specific scope."""

    scope: str
    files_reviewed: list[str]
    findings: list[ReviewFinding]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _ChangedFile:
    path: str
    full_scan: bool = False


class ReviewServiceError(RuntimeError):
    """Raised when review cannot be executed for the requested scope."""


class ReviewService:
    """Review service with lightweight risk heuristics."""

    def review_git_changes(self, working_directory: str) -> ReviewResult:
        """Review current git working tree changes."""
        changed_files = self._collect_changed_files(working_directory)
        if not changed_files:
            return ReviewResult(scope="git_diff", files_reviewed=[], findings=[], warnings=[])

        findings: list[ReviewFinding] = []
        warnings: list[str] = []
        files_reviewed: list[str] = []

        for changed in changed_files:
            file_path = Path(working_directory) / changed.path
            if not file_path.exists():
                warnings.append(f"Skipped missing file: {changed.path}")
                continue

            line_filter = None
            if not changed.full_scan:
                line_filter = self._collect_changed_line_numbers(working_directory, changed.path)
                if not line_filter:
                    continue

            files_reviewed.append(changed.path)
            findings.extend(self._analyze_file(file_path, changed.path, line_filter))

        return ReviewResult(
            scope="git_diff",
            files_reviewed=files_reviewed,
            findings=self._sort_findings(findings),
            warnings=warnings,
        )

    def review_files(self, working_directory: str, file_paths: list[str]) -> ReviewResult:
        """Review specific files provided by user input."""
        findings: list[ReviewFinding] = []
        warnings: list[str] = []
        files_reviewed: list[str] = []

        for file_path_text in file_paths:
            normalized = file_path_text.strip()
            if not normalized:
                continue
            absolute_path = Path(working_directory) / normalized
            if not absolute_path.exists():
                raise ReviewServiceError(f"File not found: {normalized}")
            if absolute_path.is_dir():
                raise ReviewServiceError(f"Expected file but got directory: {normalized}")

            files_reviewed.append(normalized)
            findings.extend(self._analyze_file(absolute_path, normalized, None))

        return ReviewResult(
            scope="files",
            files_reviewed=files_reviewed,
            findings=self._sort_findings(findings),
            warnings=warnings,
        )

    def _collect_changed_files(self, working_directory: str) -> list[_ChangedFile]:
        """Collect changed files from git status porcelain output."""
        result = self._run_git(
            ["git", "status", "--porcelain=v1", "-uall"],
            working_directory,
        )
        if result.returncode != 0:
            error = result.stderr.strip() or "Unknown git status error"
            raise ReviewServiceError(f"Git review unavailable: {error}")

        changed_files: list[_ChangedFile] = []
        seen: set[str] = set()
        for raw_line in result.stdout.splitlines():
            line = raw_line.rstrip()
            if len(line) < 4:
                continue
            status = line[:2]
            path_part = self._normalize_path_token(line[3:])
            if " -> " in path_part:
                path_part = path_part.split(" -> ", 1)[1].strip()

            if not path_part or path_part in seen:
                continue

            # Deletions cannot be scanned from workspace files.
            if "D" in status:
                continue

            changed_files.append(_ChangedFile(path=path_part, full_scan=status == "??"))
            seen.add(path_part)

        return changed_files

    def _collect_changed_line_numbers(self, working_directory: str, file_path: str) -> set[int]:
        """Collect added/modified line numbers from staged and unstaged diffs."""
        line_numbers: set[int] = set()
        for cmd in (
            ["git", "diff", "-U0", "--", file_path],
            ["git", "diff", "--cached", "-U0", "--", file_path],
        ):
            result = self._run_git(cmd, working_directory)
            if result.returncode != 0:
                continue
            for line in result.stdout.splitlines():
                match = _HUNK_PATTERN.match(line)
                if not match:
                    continue
                start = int(match.group(1))
                count_group = match.group(2)
                count = int(count_group) if count_group is not None else 1
                for line_number in range(start, start + count):
                    line_numbers.add(line_number)
        return line_numbers

    def _analyze_file(
        self,
        absolute_path: Path,
        display_path: str,
        line_filter: set[int] | None,
    ) -> list[ReviewFinding]:
        """Analyze a file and return findings."""
        try:
            text = absolute_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = absolute_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            return [
                ReviewFinding(
                    file_path=display_path,
                    line=1,
                    severity="medium",
                    issue=f"Unable to read file for review: {exc}",
                    recommendation="Check file permissions and encoding.",
                )
            ]

        findings: list[ReviewFinding] = []
        for index, line in enumerate(text.splitlines(), start=1):
            if line_filter is not None and index not in line_filter:
                continue
            findings.extend(self._analyze_line(display_path, index, line))
        return findings

    def _analyze_line(self, file_path: str, line_number: int, line: str) -> list[ReviewFinding]:
        """Apply heuristic checks to a single line."""
        findings: list[ReviewFinding] = []
        stripped = line.strip()

        if _SHELL_TRUE_PATTERN.search(line):
            findings.append(
                ReviewFinding(
                    file_path=file_path,
                    line=line_number,
                    severity="high",
                    issue="subprocess call uses shell=True, which can lead to command injection.",
                    recommendation="Use argument lists and keep shell=False unless strictly required.",
                )
            )

        if _HARD_CODED_SECRET_PATTERN.search(line):
            findings.append(
                ReviewFinding(
                    file_path=file_path,
                    line=line_number,
                    severity="high",
                    issue="Potential hard-coded secret detected.",
                    recommendation="Load secrets from environment/config vault instead of source code.",
                )
            )

        if _BARE_EXCEPT_PATTERN.match(stripped):
            findings.append(
                ReviewFinding(
                    file_path=file_path,
                    line=line_number,
                    severity="high",
                    issue="Bare except swallows all exceptions.",
                    recommendation="Catch specific exception types and log failure context.",
                )
            )
        elif _BROAD_EXCEPT_PATTERN.match(stripped):
            findings.append(
                ReviewFinding(
                    file_path=file_path,
                    line=line_number,
                    severity="medium",
                    issue="Broad `except Exception` may hide actionable failures.",
                    recommendation="Handle expected exceptions explicitly and fail closed for unknown errors.",
                )
            )

        if _TODO_PATTERN.search(line):
            findings.append(
                ReviewFinding(
                    file_path=file_path,
                    line=line_number,
                    severity="low",
                    issue="TODO/FIXME marker in reviewed code path.",
                    recommendation="Resolve or track it with a linked task before merge.",
                )
            )

        if _DEBUG_PRINT_PATTERN.search(line) and not stripped.startswith("#"):
            findings.append(
                ReviewFinding(
                    file_path=file_path,
                    line=line_number,
                    severity="low",
                    issue="Debug print statement detected.",
                    recommendation="Use structured logging or remove debug output before shipping.",
                )
            )

        return findings

    @staticmethod
    def _sort_findings(findings: list[ReviewFinding]) -> list[ReviewFinding]:
        """Sort findings by severity and location."""
        severity_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            findings,
            key=lambda item: (
                severity_order.get(item.severity, 99),
                item.file_path,
                item.line,
                item.issue,
            ),
        )

    @staticmethod
    def _normalize_path_token(path_token: str) -> str:
        """Normalize git porcelain path token."""
        candidate = path_token.strip()
        if len(candidate) >= 2 and candidate.startswith('"') and candidate.endswith('"'):
            return candidate[1:-1].encode("utf-8").decode("unicode_escape")
        return candidate

    @staticmethod
    def _run_git(cmd: list[str], working_directory: str) -> subprocess.CompletedProcess[str]:
        """Run git command with shared subprocess defaults."""
        return subprocess.run(
            cmd,
            cwd=working_directory,
            capture_output=True,
            text=True,
        )


__all__ = [
    "ReviewFinding",
    "ReviewResult",
    "ReviewService",
    "ReviewServiceError",
]
