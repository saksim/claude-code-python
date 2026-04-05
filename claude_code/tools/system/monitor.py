"""
Claude Code Python - Monitor Tool
Monitor system resources.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper error handling
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class MonitorTool(Tool):
    """Tool to monitor system resources.
    
    Provides CPU, memory, and disk usage information.
    Requires psutil package.
    """
    
    DEFAULT_RESOURCE = "all"
    
    @property
    def name(self) -> str:
        return "monitor"
    
    @property
    def description(self) -> str:
        return "Monitor system resources (CPU, memory, disk)"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "resource": {
                    "type": "string",
                    "enum": ["cpu", "memory", "disk", "all"],
                    "description": "Resource to monitor",
                    "default": "all"
                }
            }
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the monitor tool.
        
        Args:
            input_data: Dictionary containing resource to monitor
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with system resource information
        """
        resource = input_data.get("resource", self.DEFAULT_RESOURCE)
        
        try:
            import psutil
        except ImportError:
            return ToolResult(content="psutil not installed. Run: pip install psutil")
        
        try:
            info: list[str] = []
            
            if resource in ("cpu", "all"):
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count()
                info.append(f"CPU: {cpu_percent}% ({cpu_count} cores)")
            
            if resource in ("memory", "all"):
                mem = psutil.virtual_memory()
                info.append(
                    f"Memory: {mem.percent}% used "
                    f"({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)"
                )
            
            if resource in ("disk", "all"):
                disk = psutil.disk_usage('/')
                info.append(
                    f"Disk: {disk.percent}% used "
                    f"({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"
                )
            
            return ToolResult(content="\n".join(info))
            
        except OSError as e:
            return ToolResult(content=f"Error: {e}", is_error=True)
