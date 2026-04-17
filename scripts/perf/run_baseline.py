"""Performance baseline runner for claude-code-python.

The baseline is intentionally deterministic and API-independent:
- Startup import benchmark (import claude_code.main)
- QueryEngine loop benchmark with stubbed API client
- Core file-tool benchmarks (read/grep/glob) on generated dataset
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = int((len(sorted_values) - 1) * p)
    return sorted_values[idx]


def summarize_ms(name: str, durations_sec: list[float]) -> dict[str, Any]:
    ms = [d * 1000.0 for d in durations_sec]
    return {
        "name": name,
        "count": len(ms),
        "mean_ms": statistics.fmean(ms) if ms else 0.0,
        "min_ms": min(ms) if ms else 0.0,
        "max_ms": max(ms) if ms else 0.0,
        "p50_ms": percentile(ms, 0.50),
        "p95_ms": percentile(ms, 0.95),
        "p99_ms": percentile(ms, 0.99),
    }


def run_read_only_syntax_scan(project_root: Path) -> dict[str, Any]:
    files = sorted((project_root / "claude_code").rglob("*.py"))
    errors: list[dict[str, Any]] = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except SyntaxError as exc:
            errors.append(
                {
                    "path": str(path.relative_to(project_root)).replace("\\", "/"),
                    "line": exc.lineno,
                    "message": exc.msg,
                    "type": exc.__class__.__name__,
                }
            )
    return {
        "total_files": len(files),
        "syntax_errors": len(errors),
        "errors": errors,
    }


def benchmark_startup_import(project_root: Path) -> dict[str, Any]:
    command = [sys.executable, "-X", "importtime", "-c", "import claude_code.main"]
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    wall_time_ms = (time.perf_counter() - started) * 1000.0

    # importtime lines are generally emitted to stderr
    text = f"{proc.stdout}\n{proc.stderr}"
    match = re.findall(
        r"import time:\s+\d+\s+\|\s+(\d+)\s+\|\s+claude_code\.main",
        text,
    )
    cumulative_us = int(match[-1]) if match else None

    return {
        "command": command,
        "returncode": proc.returncode,
        "wall_time_ms": wall_time_ms,
        "importtime_claude_code_main_us": cumulative_us,
    }


@dataclass(frozen=True, slots=True)
class FakeStreamEvent:
    type: str
    content: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    error: str | None = None


class FakeAPIClient:
    async def create_message_streaming(
        self,
        messages: list[Any],
        options: Any,
    ) -> AsyncGenerator[FakeStreamEvent, None]:
        yield FakeStreamEvent(type="text", content={"text": "ok"})
        yield FakeStreamEvent(
            type="message",
            content={"content": [{"type": "text", "text": "ok"}]},
            usage={"input_tokens": 1, "output_tokens": 1},
        )

    async def create_message(self, messages: list[Any], options: Any) -> Any:
        class _Response:
            content = [{"type": "text", "text": "ok"}]

        return _Response()


async def benchmark_query_engine(project_root: Path, iterations: int) -> dict[str, Any]:
    from claude_code.engine.query import QueryConfig, QueryEngine
    from claude_code.tools.registry import ToolRegistry

    engine = QueryEngine(
        api_client=FakeAPIClient(),
        config=QueryConfig(),
        tool_registry=ToolRegistry(),
    )

    durations: list[float] = []
    event_counts: list[int] = []

    for i in range(iterations):
        start = time.perf_counter()
        count = 0
        async for _ in engine.query(f"perf-query-{i}"):
            count += 1
        durations.append(time.perf_counter() - start)
        event_counts.append(count)
        engine.clear()

    summary = summarize_ms("query_engine_single_turn_stub", durations)
    summary["avg_events_per_turn"] = statistics.fmean(event_counts) if event_counts else 0.0
    return summary


def _prepare_tool_dataset(root: Path, file_count: int = 400) -> tuple[Path, Path]:
    dataset = root / "dataset"
    dataset.mkdir(parents=True, exist_ok=True)
    target_file = dataset / "target.py"

    # Anchor file for read benchmark.
    target_file.write_text(
        "\n".join(f"line_{i}" for i in range(1, 1001)),
        encoding="utf-8",
    )

    # Mixed files for grep/glob benchmark.
    for i in range(file_count):
        sub = dataset / f"pkg_{i % 20}"
        sub.mkdir(parents=True, exist_ok=True)
        ext = ".py" if i % 3 == 0 else ".txt"
        content = (
            f"# file {i}\n"
            f"VALUE = {i}\n"
            + ("# TODO_BENCHMARK\n" if i % 5 == 0 else "")
        )
        (sub / f"file_{i}{ext}").write_text(content, encoding="utf-8")

    return dataset, target_file


async def benchmark_tools(project_root: Path, iterations: int) -> dict[str, Any]:
    from claude_code.tools.base import ToolContext
    from claude_code.tools.builtin.glob import GlobTool
    from claude_code.tools.builtin.grep import GrepTool
    from claude_code.tools.builtin.read import ReadTool

    temp_root = Path(tempfile.gettempdir())
    run_root = temp_root / f"claude_perf_{uuid.uuid4().hex[:8]}"
    try:
        run_root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Fallback to workspace if system temp is unavailable.
        fallback_root = project_root / "docs" / "perf" / "_tmp"
        fallback_root.mkdir(parents=True, exist_ok=True)
        run_root = fallback_root / f"claude_perf_{uuid.uuid4().hex[:8]}"
        run_root.mkdir(parents=True, exist_ok=True)

    try:
        dataset, target_file = _prepare_tool_dataset(run_root)

        context = ToolContext(working_directory=str(dataset), environment={})

        read_tool = ReadTool()
        grep_tool = GrepTool()
        glob_tool = GlobTool()

        read_durations: list[float] = []
        grep_durations: list[float] = []
        glob_durations: list[float] = []

        for _ in range(iterations):
            t0 = time.perf_counter()
            await read_tool.execute(
                {"file_path": str(target_file), "offset": 100, "limit": 120},
                context,
            )
            read_durations.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            await grep_tool.execute(
                {"pattern": "TODO_BENCHMARK", "path": str(dataset), "include": "*.py"},
                context,
            )
            grep_durations.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            await glob_tool.execute({"pattern": "**/*.py", "path": str(dataset)}, context)
            glob_durations.append(time.perf_counter() - t0)
    finally:
        # Best-effort cleanup. Some locked-down environments can deny deletes.
        shutil.rmtree(run_root, ignore_errors=True)

    return {
        "read": summarize_ms("read_tool", read_durations),
        "grep": summarize_ms("grep_tool", grep_durations),
        "glob": summarize_ms("glob_tool", glob_durations),
    }


async def run(args: argparse.Namespace) -> dict[str, Any]:
    project_root = Path(args.project_root).resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    started = time.perf_counter()

    syntax = run_read_only_syntax_scan(project_root)
    startup = benchmark_startup_import(project_root)
    query_engine = await benchmark_query_engine(project_root, args.iterations)
    tools = await benchmark_tools(project_root, args.iterations)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root).replace("\\", "/"),
        "python_executable": sys.executable.replace("\\", "/"),
        "iterations": args.iterations,
        "total_duration_ms": (time.perf_counter() - started) * 1000.0,
        "syntax": syntax,
        "startup": startup,
        "query_engine": query_engine,
        "tools": tools,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run performance baseline")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Iterations per benchmark (default: 20)",
    )
    parser.add_argument(
        "--output",
        default="docs/perf/baseline_v1.json",
        help="Output JSON path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = asyncio.run(run(args))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"baseline_written={output_path.as_posix()}")
    print(f"syntax_errors={result['syntax']['syntax_errors']}")
    print(f"startup_wall_time_ms={result['startup']['wall_time_ms']:.3f}")
    print(f"query_p95_ms={result['query_engine']['p95_ms']:.3f}")
    print(f"read_p95_ms={result['tools']['read']['p95_ms']:.3f}")
    print(f"grep_p95_ms={result['tools']['grep']['p95_ms']:.3f}")
    print(f"glob_p95_ms={result['tools']['glob']['p95_ms']:.3f}")

    return 1 if result["syntax"]["syntax_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
