"""Multi-agent supervisor runtime for DAG orchestration."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

from claude_code.services.artifact_bus import (
    ArtifactBus,
    ArtifactConflictError,
    ArtifactSchemaError,
)


class SupervisorConfigError(ValueError):
    """Raised when supervisor workflow configuration is invalid."""


class NodeExecutionStatus(Enum):
    """Execution status for one supervisor node."""

    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class AgentNodeSpec:
    """Specification for one agent node in a workflow DAG."""

    node_id: str
    description: str
    prompt: str
    subagent_type: str = "general-purpose"
    model: Optional[str] = None
    dependencies: tuple[str, ...] = ()
    ownership: tuple[str, ...] = ()
    timeout_seconds: Optional[float] = None
    max_retries: int = 0

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, index: int) -> "AgentNodeSpec":
        """Create node spec from workflow JSON payload."""
        if not isinstance(payload, dict):
            raise SupervisorConfigError(f"workflow.nodes[{index}] must be an object")

        node_id = str(payload.get("id") or f"node-{index}")
        prompt = str(payload.get("prompt") or "").strip()
        if not prompt:
            raise SupervisorConfigError(f"workflow.nodes[{index}] missing required prompt")

        description = str(payload.get("description") or node_id)
        subagent_type = str(payload.get("subagent_type") or "general-purpose")
        model_raw = payload.get("model")
        model = str(model_raw) if isinstance(model_raw, str) and model_raw.strip() else None

        deps_raw = payload.get("depends_on", payload.get("dependencies", []))
        dependencies = _as_string_tuple(deps_raw, field_name=f"workflow.nodes[{index}].depends_on")
        ownership = _as_string_tuple(payload.get("ownership", []), field_name=f"workflow.nodes[{index}].ownership")

        timeout_seconds = _parse_timeout(
            payload.get("timeout_seconds"),
            field_name=f"workflow.nodes[{index}].timeout_seconds",
        )

        max_retries = _parse_non_negative_int(
            payload.get("max_retries", 0),
            field_name=f"workflow.nodes[{index}].max_retries",
        )

        return cls(
            node_id=node_id,
            description=description,
            prompt=prompt,
            subagent_type=subagent_type,
            model=model,
            dependencies=dependencies,
            ownership=ownership,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )


@dataclass(frozen=True, slots=True)
class SupervisorBudget:
    """Supervisor execution budget controls."""

    max_parallelism: int = 2
    max_total_agents: Optional[int] = None
    max_failures: Optional[int] = None

    @classmethod
    def from_dict(cls, payload: Any) -> "SupervisorBudget":
        """Build budget from optional JSON payload."""
        if payload is None:
            return cls()
        if not isinstance(payload, dict):
            raise SupervisorConfigError("workflow.budget must be an object")

        max_parallelism = _parse_positive_int(
            payload.get("max_parallelism", 2),
            field_name="workflow.budget.max_parallelism",
        )

        max_total_agents = payload.get("max_total_agents")
        if max_total_agents is not None:
            max_total_agents = _parse_positive_int(
                max_total_agents,
                field_name="workflow.budget.max_total_agents",
            )

        max_failures = payload.get("max_failures")
        if max_failures is not None:
            max_failures = _parse_non_negative_int(
                max_failures,
                field_name="workflow.budget.max_failures",
            )

        return cls(
            max_parallelism=max_parallelism,
            max_total_agents=max_total_agents,
            max_failures=max_failures,
        )


@dataclass(frozen=True, slots=True)
class NodeExecutionResult:
    """Execution result for one node."""

    node_id: str
    description: str
    status: NodeExecutionStatus
    attempts: int
    duration_ms: float
    output: str = ""
    error: Optional[str] = None
    ownership: tuple[str, ...] = ()
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SupervisorRunResult:
    """Final workflow result."""

    workflow_id: str
    success: bool
    duration_ms: float
    results: tuple[NodeExecutionResult, ...]
    artifacts_by_node: dict[str, dict[str, Any]]

    @property
    def status(self) -> str:
        """Return high-level workflow status."""
        return "completed" if self.success else "failed"


AgentNodeExecutor = Callable[
    [AgentNodeSpec, str, dict[str, dict[str, Any]]],
    Awaitable[Any],
]


class MultiAgentSupervisor:
    """DAG supervisor for spawning and aggregating sub-agent execution."""

    def __init__(
        self,
        *,
        executor: AgentNodeExecutor,
        budget: Optional[SupervisorBudget] = None,
        workflow_timeout_seconds: Optional[float] = None,
    ) -> None:
        self._executor = executor
        self._budget = budget or SupervisorBudget()
        self._workflow_timeout_seconds = workflow_timeout_seconds

    async def run(
        self,
        *,
        workflow_id: str,
        nodes: list[AgentNodeSpec],
    ) -> SupervisorRunResult:
        """Execute workflow DAG with parallel scheduling and retries."""
        if not nodes:
            raise SupervisorConfigError("workflow.nodes must not be empty")
        self._validate(nodes)

        start_time = time.perf_counter()
        node_map = {node.node_id: node for node in nodes}
        topo_order = _topological_sort(nodes)
        dependents = _build_dependents(nodes)
        remaining = {
            node.node_id: set(node.dependencies)
            for node in nodes
        }
        artifact_bus = ArtifactBus()

        ready: list[str] = [node_id for node_id in topo_order if not remaining[node_id]]
        running: dict[str, asyncio.Task[NodeExecutionResult]] = {}
        results: dict[str, NodeExecutionResult] = {}
        artifacts_by_node: dict[str, dict[str, Any]] = {}
        failures = 0

        while ready or running:
            workflow_timeout_triggered = False
            if (
                self._workflow_timeout_seconds is not None
                and (time.perf_counter() - start_time) >= self._workflow_timeout_seconds
            ):
                workflow_timeout_triggered = True

            while ready and len(running) < self._budget.max_parallelism and not workflow_timeout_triggered:
                node_id = ready.pop(0)
                node = node_map[node_id]

                if _has_non_success_dependency(node, results):
                    skip_result = _build_skipped_result(
                        node,
                        error="skipped due to failed dependency",
                    )
                    results[node_id] = skip_result
                    artifacts_by_node[node_id] = artifact_bus.build_node_bundle(node_id)
                    for child_id in dependents[node_id]:
                        remaining[child_id].discard(node_id)
                        if not remaining[child_id]:
                            ready.append(child_id)
                    continue

                if self._is_budget_exhausted(failures):
                    skip_result = _build_skipped_result(
                        node,
                        error="skipped due to budget.max_failures",
                    )
                    results[node_id] = skip_result
                    artifacts_by_node[node_id] = artifact_bus.build_node_bundle(node_id)
                    for child_id in dependents[node_id]:
                        remaining[child_id].discard(node_id)
                        if not remaining[child_id]:
                            ready.append(child_id)
                    continue

                dependency_artifacts = artifact_bus.build_dependency_view(node.dependencies)
                running[node_id] = asyncio.create_task(
                    self._execute_node(
                        node,
                        dependency_artifacts,
                        artifact_bus=artifact_bus,
                    )
                )

            if workflow_timeout_triggered:
                for node_id, task in list(running.items()):
                    task.cancel()
                    results[node_id] = _build_timeout_result(node_map[node_id], "workflow timeout")
                    artifacts_by_node[node_id] = artifact_bus.build_node_bundle(node_id)
                running.clear()
                break

            if not running:
                continue

            wait_timeout = None
            if self._workflow_timeout_seconds is not None:
                elapsed = time.perf_counter() - start_time
                wait_timeout = max(self._workflow_timeout_seconds - elapsed, 0.0)

            done, _ = await asyncio.wait(
                running.values(),
                timeout=wait_timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if not done:
                # Workflow timeout while waiting.
                for node_id, task in list(running.items()):
                    task.cancel()
                    results[node_id] = _build_timeout_result(node_map[node_id], "workflow timeout")
                    artifacts_by_node[node_id] = artifact_bus.build_node_bundle(node_id)
                running.clear()
                break

            finished_ids = [node_id for node_id, task in running.items() if task in done]
            for node_id in finished_ids:
                task = running.pop(node_id)
                try:
                    node_result = task.result()
                except asyncio.CancelledError:
                    node_result = _build_timeout_result(node_map[node_id], "node cancelled")
                except Exception as exc:
                    node_result = _build_failed_result(
                        node_map[node_id],
                        error=f"node execution error: {exc}",
                        attempts=1,
                    )

                results[node_id] = node_result
                artifacts_by_node[node_id] = artifact_bus.build_node_bundle(node_id)
                if node_result.status in (NodeExecutionStatus.FAILED, NodeExecutionStatus.TIMEOUT):
                    failures += 1

                for child_id in dependents[node_id]:
                    remaining[child_id].discard(node_id)
                    if not remaining[child_id]:
                        ready.append(child_id)

        for node_id in topo_order:
            if node_id in results:
                continue
            fallback = _build_skipped_result(
                node_map[node_id],
                error="skipped due to unresolved scheduling state",
            )
            results[node_id] = fallback
            artifacts_by_node[node_id] = artifact_bus.build_node_bundle(node_id)

        artifacts_by_node["__bus__"] = artifact_bus.snapshot()

        ordered_results = tuple(results[node_id] for node_id in topo_order)
        success = all(item.status == NodeExecutionStatus.COMPLETED for item in ordered_results)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SupervisorRunResult(
            workflow_id=workflow_id,
            success=success,
            duration_ms=duration_ms,
            results=ordered_results,
            artifacts_by_node=artifacts_by_node,
        )

    def _validate(self, nodes: list[AgentNodeSpec]) -> None:
        """Validate node graph and budget limits."""
        if self._budget.max_total_agents is not None and len(nodes) > self._budget.max_total_agents:
            raise SupervisorConfigError(
                f"workflow node count {len(nodes)} exceeds budget.max_total_agents={self._budget.max_total_agents}"
            )

        node_ids = [node.node_id for node in nodes]
        seen: set[str] = set()
        duplicates: set[str] = set()
        for node_id in node_ids:
            if node_id in seen:
                duplicates.add(node_id)
            seen.add(node_id)
        if duplicates:
            duplicate_list = ", ".join(sorted(duplicates))
            raise SupervisorConfigError(f"duplicate workflow node ids: {duplicate_list}")

        node_set = set(node_ids)
        for node in nodes:
            missing = [dep for dep in node.dependencies if dep not in node_set]
            if missing:
                missing_list = ", ".join(missing)
                raise SupervisorConfigError(
                    f"workflow node '{node.node_id}' depends on unknown nodes: {missing_list}"
                )

        _topological_sort(nodes)

    def _is_budget_exhausted(self, failures: int) -> bool:
        if self._budget.max_failures is None:
            return False
        return failures > self._budget.max_failures

    async def _execute_node(
        self,
        node: AgentNodeSpec,
        dependency_artifacts: dict[str, dict[str, Any]],
        *,
        artifact_bus: ArtifactBus,
    ) -> NodeExecutionResult:
        """Execute one node with retry and timeout policy."""
        attempts = 0
        start_time = time.perf_counter()
        last_error: Optional[str] = None
        last_status = NodeExecutionStatus.FAILED

        while attempts <= node.max_retries:
            attempts += 1
            prompt = self._build_node_prompt(node, dependency_artifacts)
            try:
                if node.timeout_seconds is not None:
                    output = await asyncio.wait_for(
                        self._executor(node, prompt, dependency_artifacts),
                        timeout=node.timeout_seconds,
                    )
                else:
                    output = await self._executor(node, prompt, dependency_artifacts)

                artifact_records = artifact_bus.publish_from_output(
                    node_id=node.node_id,
                    output=output,
                    ownership=node.ownership,
                )
                output_text = str(output or "")
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                artifacts = {
                    "output": output_text,
                    "status": NodeExecutionStatus.COMPLETED.value,
                    "owner": list(node.ownership),
                    "artifact_count": len(artifact_records),
                    "artifacts": [record.to_dict() for record in artifact_records],
                }
                return NodeExecutionResult(
                    node_id=node.node_id,
                    description=node.description,
                    status=NodeExecutionStatus.COMPLETED,
                    attempts=attempts,
                    duration_ms=duration_ms,
                    output=output_text,
                    ownership=node.ownership,
                    artifacts=artifacts,
                )
            except asyncio.TimeoutError:
                last_status = NodeExecutionStatus.TIMEOUT
                last_error = f"node timeout after {node.timeout_seconds}s"
            except (ArtifactSchemaError, ArtifactConflictError) as exc:
                last_status = NodeExecutionStatus.FAILED
                last_error = f"artifact bus error: {exc}"
            except Exception as exc:
                last_status = NodeExecutionStatus.FAILED
                last_error = str(exc) or exc.__class__.__name__

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        artifacts = {
            "output": "",
            "status": last_status.value,
            "error": last_error or "unknown node failure",
            "owner": list(node.ownership),
        }
        return NodeExecutionResult(
            node_id=node.node_id,
            description=node.description,
            status=last_status,
            attempts=attempts,
            duration_ms=duration_ms,
            output="",
            error=last_error or "unknown node failure",
            ownership=node.ownership,
            artifacts=artifacts,
        )

    def _build_node_prompt(
        self,
        node: AgentNodeSpec,
        dependency_artifacts: dict[str, dict[str, Any]],
    ) -> str:
        """Build node prompt with ownership and inherited artifacts."""
        parts = [node.prompt]
        if node.ownership:
            ownership_line = ", ".join(node.ownership)
            parts.append(
                "Ownership scope for this node: "
                f"{ownership_line}. Do not revert edits made by other workers."
            )
        if dependency_artifacts:
            payload = json.dumps(dependency_artifacts, ensure_ascii=True, indent=2, sort_keys=True)
            parts.append(f"Artifacts from dependencies:\n{payload}")
        return "\n\n".join(parts)


def _has_non_success_dependency(
    node: AgentNodeSpec,
    results: dict[str, NodeExecutionResult],
) -> bool:
    for dep in node.dependencies:
        dep_result = results.get(dep)
        if dep_result is None:
            return False
        if dep_result.status != NodeExecutionStatus.COMPLETED:
            return True
    return False


def _build_dependents(nodes: list[AgentNodeSpec]) -> dict[str, list[str]]:
    dependents: dict[str, list[str]] = {node.node_id: [] for node in nodes}
    for node in nodes:
        for dep in node.dependencies:
            dependents[dep].append(node.node_id)
    return dependents


def _topological_sort(nodes: list[AgentNodeSpec]) -> list[str]:
    """Return topological order or raise if cycle exists."""
    node_ids = [node.node_id for node in nodes]
    indegree = {node.node_id: len(node.dependencies) for node in nodes}
    dependents = _build_dependents(nodes)

    ready = [node_id for node_id in node_ids if indegree[node_id] == 0]
    ordered: list[str] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(node_id)
        for child_id in dependents[node_id]:
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                ready.append(child_id)

    if len(ordered) != len(nodes):
        unresolved = sorted({node.node_id for node in nodes} - set(ordered))
        raise SupervisorConfigError(
            "workflow graph contains a cycle: " + ", ".join(unresolved)
        )
    return ordered


def _build_skipped_result(node: AgentNodeSpec, *, error: str) -> NodeExecutionResult:
    return NodeExecutionResult(
        node_id=node.node_id,
        description=node.description,
        status=NodeExecutionStatus.SKIPPED,
        attempts=0,
        duration_ms=0.0,
        output="",
        error=error,
        ownership=node.ownership,
        artifacts={
            "output": "",
            "status": NodeExecutionStatus.SKIPPED.value,
            "error": error,
            "owner": list(node.ownership),
        },
    )


def _build_timeout_result(node: AgentNodeSpec, error: str) -> NodeExecutionResult:
    return NodeExecutionResult(
        node_id=node.node_id,
        description=node.description,
        status=NodeExecutionStatus.TIMEOUT,
        attempts=1,
        duration_ms=0.0,
        output="",
        error=error,
        ownership=node.ownership,
        artifacts={
            "output": "",
            "status": NodeExecutionStatus.TIMEOUT.value,
            "error": error,
            "owner": list(node.ownership),
        },
    )


def _build_failed_result(node: AgentNodeSpec, *, error: str, attempts: int) -> NodeExecutionResult:
    return NodeExecutionResult(
        node_id=node.node_id,
        description=node.description,
        status=NodeExecutionStatus.FAILED,
        attempts=attempts,
        duration_ms=0.0,
        output="",
        error=error,
        ownership=node.ownership,
        artifacts={
            "output": "",
            "status": NodeExecutionStatus.FAILED.value,
            "error": error,
            "owner": list(node.ownership),
        },
    )


def _as_string_tuple(raw: Any, *, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        value = raw.strip()
        return (value,) if value else ()
    if not isinstance(raw, list):
        raise SupervisorConfigError(f"{field_name} must be a string or list of strings")

    values: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            values.append(text)
    return tuple(values)


def _parse_positive_int(value: Any, *, field_name: str) -> int:
    try:
        parsed = int(value)
    except Exception as exc:  # pragma: no cover - defensive parse guard
        raise SupervisorConfigError(f"{field_name} must be an integer") from exc
    if parsed <= 0:
        raise SupervisorConfigError(f"{field_name} must be > 0")
    return parsed


def _parse_non_negative_int(value: Any, *, field_name: str) -> int:
    try:
        parsed = int(value)
    except Exception as exc:  # pragma: no cover - defensive parse guard
        raise SupervisorConfigError(f"{field_name} must be an integer") from exc
    if parsed < 0:
        raise SupervisorConfigError(f"{field_name} must be >= 0")
    return parsed


def _parse_timeout(value: Any, *, field_name: str) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except Exception as exc:  # pragma: no cover - defensive parse guard
        raise SupervisorConfigError(f"{field_name} must be a number") from exc
    if parsed <= 0:
        raise SupervisorConfigError(f"{field_name} must be > 0")
    return parsed


__all__ = [
    "SupervisorConfigError",
    "NodeExecutionStatus",
    "AgentNodeSpec",
    "SupervisorBudget",
    "NodeExecutionResult",
    "SupervisorRunResult",
    "MultiAgentSupervisor",
]
