"""
Shell task executor for Claude Code Python.

Executes shell commands as background tasks.
"""

import asyncio
import os
import shlex
from typing import Optional, Callable, Any
from dataclasses import dataclass

from claude_code.tasks.types import Task, BashTask, TaskResult, TaskStatus
from claude_code.tasks.manager import get_task_manager


class ShellTaskExecutor:
    """
    Executes shell commands as tasks.
    
    Runs shell commands in the background with proper
    environment and timeout handling.
    """
    
    def __init__(self, task_manager=None):
        self.task_manager = task_manager or get_task_manager()
        self._output_handlers: dict[str, Callable[[str], None]] = {}
    
    async def execute_bash(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
        background: bool = True,
        description: Optional[str] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> BashTask:
        """
        Execute a bash command.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            background: Run in background
            description: Task description
            on_output: Callback for output
            
        Returns:
            The created BashTask
        """
        task = await self.task_manager.create_bash_task(
            command=command,
            cwd=cwd,
            env=env,
            timeout=timeout,
            background=background,
            description=description,
        )
        
        if on_output:
            self._output_handlers[task.id] = on_output
        
        if background:
            await self.task_manager.start_task(
                task.id,
                executor=lambda t: self._execute_command(t),
            )
        else:
            result = await self._execute_command(task)
            task.status = TaskStatus.COMPLETED
            task.result = result
        
        return task
    
    async def _execute_command(self, task: BashTask) -> TaskResult:
        """Execute a bash command."""
        if not isinstance(task, BashTask):
            raise TypeError("Task must be a BashTask")
        
        try:
            if os.name == 'nt':
                cmd = ["cmd", "/c", task.command]
            else:
                cmd = shlex.split(task.command)
            
            env = {**os.environ, **(task.env or {})}
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task.cwd,
                env=env,
            )
            
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=task.timeout,
            )
            
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            
            task.result = TaskResult(
                code=process.returncode or 0,
                stdout=stdout,
                stderr=stderr,
            )
            
            return task.result
            
        except asyncio.TimeoutError:
            task.error = f"Command timed out after {task.timeout} seconds"
            return TaskResult(
                code=-1,
                error=task.error,
            )
            
        except Exception as e:
            task.error = str(e)
            return TaskResult(
                code=-1,
                error=str(e),
            )
    
    async def execute_and_stream(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
        on_line: Optional[Callable[[str], None]] = None,
    ) -> TaskResult:
        """
        Execute a command and stream output line by line.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            on_line: Callback for each line of output
            
        Returns:
            The task result
        """
        if os.name == 'nt':
            cmd = ["cmd", "/c", command]
        else:
            cmd = shlex.split(command)
        
        full_env = {**os.environ, **(env or {})}
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env=full_env,
            )
            
            stdout_lines = []
            
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    line_str = line.decode('utf-8', errors='replace').rstrip()
                    stdout_lines.append(line_str)
                    
                    if on_line:
                        on_line(line_str)
            
            await process.wait()
            
            return TaskResult(
                code=process.returncode or 0,
                stdout="\n".join(stdout_lines),
            )
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            return TaskResult(code=-1, error=f"Timeout after {timeout}s")
            
        except Exception as e:
            return TaskResult(code=-1, error=str(e))


async def run_background_bash(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    timeout: Optional[float] = None,
) -> BashTask:
    """Run a bash command in the background."""
    executor = ShellTaskExecutor()
    return await executor.execute_bash(
        command=command,
        cwd=cwd,
        env=env,
        timeout=timeout,
        background=True,
    )


async def run_bash(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    timeout: Optional[float] = None,
) -> TaskResult:
    """Run a bash command and wait for result."""
    executor = ShellTaskExecutor()
    task = await executor.execute_bash(
        command=command,
        cwd=cwd,
        env=env,
        timeout=timeout,
        background=False,
    )
    return task.result or TaskResult(code=-1, error="No result")
