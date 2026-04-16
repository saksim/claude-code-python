"""Claude Code Python - Command and Tool Dependency Graph."""

from __future__ import annotations

import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass(frozen=True, slots=True)
class GraphNode:
    """Node in the dependency graph."""

    name: str
    node_type: str  # command/tool
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """Directed edge in the dependency graph."""

    from_node: str
    to_node: str
    edge_type: str = "depends_on"


class DependencyGraph:
    """Directed dependency graph for commands/tools."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self._reverse_adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(
        self,
        name: str,
        node_type: str,
        depends_on: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add or replace a graph node."""
        deps = depends_on or []
        node = GraphNode(name=name, node_type=node_type, depends_on=deps, metadata=metadata or {})
        self._nodes[name] = node

        self._adjacency[name] = list(deps)
        for dep in deps:
            self._edges.append(GraphEdge(from_node=name, to_node=dep))
            self._reverse_adjacency[dep].append(name)

    def get_dependencies(self, name: str) -> list[str]:
        """Get direct dependencies for a node."""
        node = self._nodes.get(name)
        return list(node.depends_on) if node else []

    def get_dependents(self, name: str) -> list[str]:
        """Get nodes that depend on this node."""
        return list(self._reverse_adjacency.get(name, []))

    def topological_sort(self) -> list[str]:
        """Topological sort (dependencies before dependents)."""
        in_degree: dict[str, int] = {
            name: len(node.depends_on) for name, node in self._nodes.items()
        }
        queue: deque[str] = deque([name for name, deg in in_degree.items() if deg == 0])
        result: list[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for dependent in self._reverse_adjacency.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If cycle exists, append remaining nodes in stable order.
        if len(result) < len(self._nodes):
            remaining = [name for name in self._nodes if name not in set(result)]
            result.extend(remaining)

        return result

    def find_cycles(self) -> list[list[str]]:
        """Detect cycles using DFS recursion stack."""
        visited: set[str] = set()
        in_stack: set[str] = set()
        path: list[str] = []
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            visited.add(node)
            in_stack.add(node)
            path.append(node)

            for dep in self._adjacency.get(node, []):
                if dep not in visited:
                    dfs(dep)
                elif dep in in_stack and dep in path:
                    start = path.index(dep)
                    cycles.append(path[start:].copy())

            in_stack.remove(node)
            path.pop()

        for node in self._nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def get_roots(self) -> list[str]:
        """Return nodes with no dependencies."""
        return [name for name, node in self._nodes.items() if not node.depends_on]

    def get_leaves(self) -> list[str]:
        """Return nodes with no dependents."""
        return [name for name in self._nodes if not self._reverse_adjacency.get(name)]


def build_command_graph() -> DependencyGraph:
    """Build command dependency graph from registry."""
    from claude_code.commands.registry import get_all_commands

    graph = DependencyGraph()
    commands = get_all_commands()

    for name, cmd in commands.items():
        depends: list[str] = []
        command_type = getattr(cmd, "command_type", None)
        if command_type is not None and getattr(command_type, "value", "") == "local":
            depends = ["config", "permissions"]

        graph.add_node(
            name=name,
            node_type="command",
            depends_on=depends,
            metadata={"description": getattr(cmd, "description", "")},
        )

    return graph


def build_tool_graph() -> DependencyGraph:
    """Build tool dependency graph from default registry."""
    from claude_code.tools.registry import create_default_registry

    graph = DependencyGraph()
    registry = create_default_registry()
    tools = registry.list_all()

    for tool in tools:
        depends: list[str] = []
        tool_name = tool.name.lower()

        if "mcp" in tool_name:
            depends = ["mcp"]
        elif tool_name in {"ask_user_question"}:
            depends = ["read"]
        elif tool_name in {"edit", "write"}:
            depends = ["read"]

        graph.add_node(
            name=tool.name,
            node_type="tool",
            depends_on=depends,
            metadata={"description": getattr(tool, "description", "")},
        )

    return graph


def find_common_dependencies(commands: list[str], tools: list[str]) -> dict[str, list[str]]:
    """Find dependency coverage for selected commands/tools."""
    cmd_graph = build_command_graph()
    tool_graph = build_tool_graph()

    result: dict[str, list[str]] = {}
    for name in set(commands) | set(tools):
        deps: list[str] = []
        if name in cmd_graph._nodes:
            deps.extend(cmd_graph.get_dependencies(name))
        if name in tool_graph._nodes:
            deps.extend(tool_graph.get_dependencies(name))
        if deps:
            result[name] = deps
    return result


def render_graph_summary() -> str:
    """Render a lightweight textual summary for diagnostics."""
    cmd_graph = build_command_graph()
    tool_graph = build_tool_graph()

    lines = [
        "# Dependency Graph Summary",
        "",
        "## Commands",
        f"- Total: {len(cmd_graph._nodes)}",
        f"- Roots: {', '.join(cmd_graph.get_roots()) if cmd_graph.get_roots() else '(none)'}",
        "",
        "## Tools",
        f"- Total: {len(tool_graph._nodes)}",
        f"- Roots: {', '.join(tool_graph.get_roots()) if tool_graph.get_roots() else '(none)'}",
        "",
    ]

    cycles = cmd_graph.find_cycles() + tool_graph.find_cycles()
    if cycles:
        lines.append("## Cycles Detected")
        for cycle in cycles:
            lines.append(f"- {' -> '.join(cycle)}")
    else:
        lines.append("## No cycles detected")

    return "\n".join(lines)


__all__ = [
    "GraphNode",
    "GraphEdge",
    "DependencyGraph",
    "build_command_graph",
    "build_tool_graph",
    "find_common_dependencies",
    "render_graph_summary",
]
