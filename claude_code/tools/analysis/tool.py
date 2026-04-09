"""
Claude Code Python - Analysis Tool
Tool for analyzing code.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import os
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback
from claude_code.tools.analysis import CodeAnalyzer, ComplexityAnalyzer, FileAnalysis


class AnalyzeTool(Tool):
    """Tool to analyze code files and directories.
    
    This tool provides static code analysis capabilities including:
    - File and directory analysis
    - Language detection
    - Line counting (code, comments, blank)
    - Complexity analysis
    
    Attributes:
        name: analyze
        description: Analyze code files and directories
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "analyze"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Analyze code files and directories"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file or directory to analyze"
                },
                "extensions": {
                    "type": "array",
                    "description": "File extensions to analyze (e.g., ['.py', '.js'])",
                    "items": {"type": "string"}
                },
                "complexity": {
                    "type": "boolean",
                    "description": "Calculate cyclomatic complexity",
                    "default": False
                }
            },
            "required": ["path"]
        }
    
    def is_read_only(self) -> bool:
        """Tool only analyzes code, doesn't modify files.
        
        Returns:
            True since analysis is a read-only operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the code analysis.
        
        Args:
            input_data: Dictionary with 'path', optional 'extensions', 'complexity'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with analysis results.
        """
        path = input_data.get("path", "")
        extensions = input_data.get("extensions")
        include_complexity = input_data.get("complexity", False)
        
        if not path:
            return ToolResult(content="Error: path is required", is_error=True)
        
        if not os.path.exists(path):
            return ToolResult(content=f"Error: path not found: {path}", is_error=True)
        
        analyzer = CodeAnalyzer()
        
        if os.path.isfile(path):
            analysis = analyzer.analyze_file(path)
            return self._format_file_analysis(analysis, include_complexity)
        
        elif os.path.isdir(path):
            analyses = analyzer.analyze_directory(path, extensions)
            return self._format_analyses(analyses, include_complexity)
        
        return ToolResult(content="Error: invalid path", is_error=True)
    
    def _format_file_analysis(self, analysis: FileAnalysis, complexity: bool) -> ToolResult:
        lines = [f"# Analysis: {analysis.path}", ""]
        lines.append(f"Language: {analysis.language}")
        lines.append(f"Lines: {analysis.metrics.lines}")
        lines.append(f"  Code: {analysis.metrics.code_lines}")
        lines.append(f"  Comments: {analysis.metrics.comment_lines}")
        lines.append(f"  Blank: {analysis.metrics.blank_lines}")
        
        if complexity:
            comp = ComplexityAnalyzer()
            try:
                c = comp.calculate_complexity(analysis.path)
                lines.append(f"Complexity: {c}")
            except Exception:
                pass
        
        if analysis.issues:
            lines.append("")
            lines.append("## Issues")
            for issue in analysis.issues:
                lines.append(f"- [{issue['severity']}] {issue['message']}")
        
        return ToolResult(content="\n".join(lines))
    
    def _format_analyses(self, analyses: list[FileAnalysis], complexity: bool) -> ToolResult:
        if not analyses:
            return ToolResult(content="No files found")
        
        summary = CodeAnalyzer().get_summary(analyses)
        
        lines = ["# Code Analysis Summary", ""]
        
        total = summary['total']
        lines.append(f"Files: {total['files']}")
        lines.append(f"Total Lines: {total['lines']}")
        lines.append(f"  Code: {total['code_lines']}")
        lines.append(f"  Comments: {total['comment_lines']}")
        lines.append(f"  Blank: {total['blank_lines']}")
        
        lines.append("")
        lines.append("## By Language")
        for lang, count in sorted(summary['by_language'].items(), key=lambda x: -x[1]):
            lines.append(f"- {lang}: {count} files")
        
        if complexity:
            lines.append("")
            lines.append("## Complexity")
            for a in analyses[:10]:
                comp = ComplexityAnalyzer()
                c = comp.calculate_complexity(a.path)
                if c > 10:
                    lines.append(f"- {a.path}: {c}")
        
        return ToolResult(content="\n".join(lines))


__all__ = ["AnalyzeTool"]
