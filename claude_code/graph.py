"""
Claude Code Python - Command and Tool Graph
用于分析命令和工具之间的依赖关系
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass(frozen=True, slots=True)
class GraphNode:
    """图节点"""
    name: str
    node_type: str  # "command" or "tool"
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """图边"""
    from_node: str
    to_node: str
    edge_type: str = "depends_on"


class DependencyGraph:
    """
    依赖图 - 分析命令和工具之间的关系
    """
    
    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
    
    def add_node(self, name: str, node_type: str, depends_on: List[str] = None, metadata: Dict = None) -> None:
        """添加节点"""
        node = GraphNode(
            name=name,
            node_type=node_type,
            depends_on=depends_on or [],
            metadata=metadata or {},
        )
        self._nodes[name] = node
        
        for dep in node.depends_on:
            edge = GraphEdge(from_node=name, to_node=dep)
            self._edges.append(edge)
            self._adjacency[name].append(dep)
            self._reverse_adjacency[dep].append(name)
    
    def get_dependencies(self, name: str) -> List[str]:
        """获取节点的依赖"""
        node = self._nodes.get(name)
        return node.depends_on if node else []
    
    def get_dependents(self, name: str) -> List[str]:
        """获取依赖该节点的节点"""
        return self._reverse_adjacency.get(name, []).copy()
    
    def topological_sort(self) -> List[str]:
        """拓扑排序 - 返回依赖顺序"""
        in_degree = defaultdict(int)
        all_nodes = set(self._nodes.keys())
        
        for node in all_nodes:
            if node not in in_degree:
                in_degree[node] = 0
        
        for edge in self._edges:
            in_degree[edge.to_node] += 1
        
        queue = [n for n in all_nodes if in_degree[n] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def find_cycles(self) -> List[List[str]]:
        """检测循环依赖"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:])
            
            rec_stack.remove(node)
        
        for node in self._nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def get_roots(self) -> List[str]:
        """获取根节点（无依赖）"""
        return [n for n in self._nodes if not self._nodes[n].depends_on]
    
    def get_leaves(self) -> List[str]:
        """获取叶子节点（无依赖者）"""
        return [n for n in self._nodes if not self._reverse_adjacency.get(n)]


def build_command_graph() -> DependencyGraph:
    """构建命令依赖图"""
    from ..commands.registry import get_all_commands
    
    graph = DependencyGraph()
    commands = get_all_commands()
    
    for name, cmd in commands.items():
        depends = []
        
        if hasattr(cmd, "command_type"):
            if str(cmd.command_type.value) == "local":
                depends = ["config", "permissions"]
        
        graph.add_node(
            name=name,
            node_type="command",
            depends_on=depends,
            metadata={"description": cmd.description},
        )
    
    return graph


def build_tool_graph() -> DependencyGraph:
    """构建工具依赖图"""
    from claude_code.tools import create_default_registry
    
    graph = DependencyGraph()
    registry = create_default_registry()
    tools = registry.list_all()
    
    for tool in tools:
        depends = []
        
        if "mcp" in tool.name.lower():
            depends = ["mcp"]
        elif tool.name in ("ask_user_question",):
            depends = ["read"]
        elif tool.name in ("edit", "write"):
            depends = ["read"]
        
        graph.add_node(
            name=tool.name,
            node_type="tool",
            depends_on=depends,
            metadata={"description": tool.description},
        )
    
    return graph


def find_common_dependencies(commands: List[str], tools: List[str]) -> Dict[str, List[str]]:
    """查找命令和工具的共同依赖"""
    cmd_graph = build_command_graph()
    tool_graph = build_tool_graph()
    
    all_names = set(commands) | set(tools)
    common: Dict[str, List[str]] = {}
    
    for name in all_names:
        deps = []
        
        if name in cmd_graph._nodes:
            deps.extend(cmd_graph.get_dependencies(name))
        
        if name in tool_graph._nodes:
            deps.extend(tool_graph.get_dependencies(name))
        
        if deps:
            common[name] = deps
    
    return common


def render_graph_summary() -> str:
    """渲染图摘要"""
    cmd_graph = build_command_graph()
    tool_graph = build_tool_graph()
    
    lines = [
        "# Dependency Graph Summary",
        "",
        "## Commands",
        f"- Total: {len(cmd_graph._nodes)}",
        f"- Roots: {', '.join(cmd_graph.get_roots())}",
        "",
        "## Tools",
        f"- Total: {len(tool_graph._nodes)}",
        f"- Roots: {', '.join(tool_graph.get_roots())}",
        "",
    ]
    
    cycles = cmd_graph.find_cycles() + tool_graph.find_cycles()
    if cycles:
        lines.append("## Cycles Detected")
        for cycle in cycles:
            lines.append(f"- {' -> '.join(cycle)}")
    else:
        lines.append("## No cycles detected ✓")
    
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
