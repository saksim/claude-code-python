"""
Shell command utilities for Claude Code Python.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
- Async/await patterns
- Proper error handling
"""

from __future__ import annotations

import asyncio
import os
import shlex
import shutil
import time
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum


class ShellType(Enum):
    """Shell types for different platforms.
    
    Attributes:
        BASH: Bash shell (Linux/macOS)
        ZSH: Zsh shell (macOS/Linux)
        SH: POSIX shell
        CMD: Windows Command Prompt
        POWERSHELL: Windows PowerShell
    """
    BASH = "bash"
    ZSH = "zsh"
    SH = "sh"
    CMD = "cmd"
    POWERSHELL = "powershell"


@dataclass
class ExecResult:
    """Result from executing a shell command.
    
    Contains all information about command execution including
    return code, output, and timing.
    
    Attributes:
        returncode: Exit code from the command
        stdout: Standard output
        stderr: Standard error
        command: The command that was executed
        duration_ms: Execution time in milliseconds
    """
    returncode: int
    stdout: str
    stderr: str
    command: str
    duration_ms: float = 0
    
    @property
    def success(self) -> bool:
        """Check if command succeeded (returncode == 0)."""
        return self.returncode == 0
    
    @property
    def output(self) -> str:
        """Get combined output (stdout + stderr)."""
        if self.stderr:
            return f"{self.stdout}\n{self.stderr}"
        return self.stdout


def get_shell_type() -> ShellType:
    """Detect the current shell type based on OS and environment.
    
    Returns:
        ShellType for the current platform/shell
    """
    if os.name == 'nt':
        return ShellType.CMD
    
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        return ShellType.ZSH
    if 'bash' in shell:
        return ShellType.BASH
    
    return ShellType.SH


def quote_shell_arg(arg: str) -> str:
    """Quote a shell argument safely.
    
    Args:
        arg: Argument to quote
        
    Returns:
        Safely quoted argument string
    """
    return shlex.quote(arg)


def build_env(env: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Build environment for subprocess.
    
    Merges current environment with provided overrides.
    
    Args:
        env: Optional environment overrides
        
    Returns:
        Complete environment dictionary
    """
    return {**os.environ, **(env or {})}


async def run_command(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[float] = None,
    shell: bool = True,
) -> ExecResult:
    """Run a shell command asynchronously.
    
    Executes a command and returns the result including
    output and timing information.
    
    Args:
        command: Command to run
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        shell: Run through shell
        
    Returns:
        ExecResult with execution details
    """
    start = time.time()
    
    try:
        if os.name == 'nt':
            cmd_parts = ["cmd", "/c", command] if shell else command.split()
        else:
            cmd_parts = command if shell else shlex.split(command)
        
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=build_env(env),
        )
        
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        duration_ms = (time.time() - start) * 1000
        
        return ExecResult(
            returncode=process.returncode or 0,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
            command=command,
            duration_ms=duration_ms,
        )
        
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return ExecResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            command=command,
            duration_ms=(time.time() - start) * 1000,
        )
    except OSError as e:
        return ExecResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            command=command,
            duration_ms=(time.time() - start) * 1000,
        )


def run_command_sync(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[float] = None,
    shell: bool = True,
) -> ExecResult:
    """Run a shell command synchronously.
    
    Args:
        command: Command to run
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        shell: Run through shell
        
    Returns:
        ExecResult with execution details
    """
    start = time.time()
    
    try:
        result = subprocess.run(
            command if shell else shlex.split(command),
            capture_output=True,
            text=True,
            cwd=cwd,
            env=build_env(env),
            timeout=timeout,
            shell=shell,
        )
        
        duration_ms = (time.time() - start) * 1000
        
        return ExecResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            command=command,
            duration_ms=duration_ms,
        )
        
    except subprocess.TimeoutExpired:
        return ExecResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            command=command,
            duration_ms=(time.time() - start) * 1000,
        )
    except OSError as e:
        return ExecResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            command=command,
            duration_ms=(time.time() - start) * 1000,
        )


async def run_command_stream(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
) -> AsyncIterator[str]:
    """Run a command and yield output lines as they come.
    
    Useful for long-running commands where you want to
    process output in real-time.
    
    Args:
        command: Command to run
        cwd: Working directory
        env: Environment variables
        
    Yields:
        Lines of command output
    """
    if os.name == 'nt':
        cmd_parts = ["cmd", "/c", command]
    else:
        cmd_parts = shlex.split(command)
    
    process = await asyncio.create_subprocess_exec(
        *cmd_parts,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd,
        env=build_env(env),
    )
    
    if process.stdout:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line.decode("utf-8", errors="replace").rstrip()
    
    await process.wait()


def which(command: str) -> Optional[str]:
    """Find the path to an executable.
    
    Uses shutil.which to locate command in PATH.
    
    Args:
        command: Name of the executable
        
    Returns:
        Full path to executable, or None if not found
    """
    return shutil.which(command)
