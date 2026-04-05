"""
Claude Code Python - Analysis Tools
Code analysis and metrics tools.
"""

from __future__ import annotations

import os
import re
from typing import Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter


@dataclass
class CodeMetrics:
    """Code metrics."""
    lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0


@dataclass
class FileAnalysis:
    """Analysis of a single file."""
    path: str
    language: str
    metrics: CodeMetrics
    issues: list[dict] = field(default_factory=list)


class CodeAnalyzer:
    """Analyze code files."""
    
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "shell",
        ".bash": "shell",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
    }
    
    COMMENT_PATTERNS = {
        "python": (r'#.*$', r'""".*?"""', r"'''.*?'''"),
        "javascript": (r'//.*$', r'/\*.*?\*/'),
        "typescript": (r'//.*$', r'/\*.*?\*/'),
        "rust": (r'//.*$', r'/\*.*?\*/'),
        "go": (r'//.*$', r'/\*.*?\*/'),
        "java": (r'//.*$', r'/\*.*?\*/'),
        "c": (r'//.*$', r'/\*.*?\*/'),
        "cpp": (r'//.*$', r'/\*.*?\*/'),
        "csharp": (r'//.*$', r'/\*.*?\*/'),
        "ruby": (r'#.*$', r'=begin.*?=end'),
        "shell": (r'#.*$',),
        "html": (r'<!--.*?-->',),
        "css": (r'/\*.*?\*/',),
    }
    
    def detect_language(self, path: str) -> str:
        """Detect language from file extension."""
        ext = Path(path).suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(ext, "unknown")
    
    def analyze_file(self, path: str) -> FileAnalysis:
        """Analyze a single file."""
        language = self.detect_language(path)
        metrics = self._count_lines(path)
        issues = self._check_issues(path, language)
        
        return FileAnalysis(
            path=path,
            language=language,
            metrics=metrics,
            issues=issues,
        )
    
    def _count_lines(self, path: str) -> CodeMetrics:
        """Count lines in a file."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except:
            return CodeMetrics()
        
        metrics = CodeMetrics(lines=len(lines))
        
        in_block_comment = False
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                metrics.blank_lines += 1
                continue
            
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_block_comment = not in_block_comment
                metrics.comment_lines += 1
            elif in_block_comment:
                metrics.comment_lines += 1
            elif self._is_comment(stripped, self.detect_language(path)):
                metrics.comment_lines += 1
            else:
                metrics.code_lines += 1
        
        return metrics
    
    def _is_comment(self, line: str, language: str) -> bool:
        """Check if line is a comment."""
        patterns = self.COMMENT_PATTERNS.get(language, ('#', '//'))
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _check_issues(self, path: str, language: str) -> list[dict]:
        """Check for common issues."""
        issues = []
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return issues
        
        if len(content) > 100000:
            issues.append({
                "severity": "warning",
                "message": "File is very large (>100KB)",
                "line": 1,
            })
        
        if '\t' in content:
            issues.append({
                "severity": "warning",
                "message": "File contains tabs (use spaces)",
                "line": content[:content.index('\t')].count('\n') + 1,
            })
        
        trailing = len([l for l in content.split('\n') if l.rstrip() != l])
        if trailing > 0:
            issues.append({
                "severity": "info",
                "message": f"{trailing} lines have trailing whitespace",
                "line": 0,
            })
        
        return issues
    
    def analyze_directory(self, path: str, extensions: list[str] = None) -> list[FileAnalysis]:
        """Analyze all files in a directory."""
        analyses = []
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv', '__pycache__', 'dist', 'build')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                
                if extensions:
                    ext = Path(file).suffix.lower()
                    if ext not in extensions:
                        continue
                
                analysis = self.analyze_file(file_path)
                analyses.append(analysis)
        
        return analyses
    
    def get_summary(self, analyses: list[FileAnalysis]) -> dict:
        """Get summary of all analyses."""
        total = Counter()
        by_language = Counter()
        
        for a in analyses:
            total['files'] += 1
            total['lines'] += a.metrics.lines
            total['code_lines'] += a.metrics.code_lines
            total['comment_lines'] += a.metrics.comment_lines
            total['blank_lines'] += a.metrics.blank_lines
            
            by_language[a.language] += 1
        
        return {
            "total": dict(total),
            "by_language": dict(by_language),
        }


class ComplexityAnalyzer:
    """Analyze code complexity."""
    
    def count_functions(self, content: str, language: str) -> int:
        """Count functions."""
        patterns = {
            "python": r'\bdef\b|\basync def\b|\bclass\b',
            "javascript": r'\bfunction\b|\bconst\s+\w+\s*=\s*(?:async\s*)?\(|=>\s*{',
            "typescript": r'\bfunction\b|\bconst\s+\w+\s*=\s*(?:async\s*)?\(|=>\s*{|\bmethod\b',
            "rust": r'\bfn\b|\bpub\s+fn\b',
            "go": r'\bfunc\b',
            "java": r'\b(public|private|protected)?\s*(static)?\s*void\s+\w+\s*\(',
        }
        
        pattern = patterns.get(language, r'\bfunction\b')
        return len(re.findall(pattern, content))
    
    def calculate_complexity(self, path: str) -> int:
        """Calculate cyclomatic complexity."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return 0
        
        complexity = 1
        
        keywords = [r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b', r'\bcatch\b', r'\bcase\b', r'\b&&\b', r'\b\|\|\b']
        
        for keyword in keywords:
            complexity += len(re.findall(keyword, content))
        
        return complexity


__all__ = [
    "CodeAnalyzer",
    "ComplexityAnalyzer",
    "CodeMetrics",
    "FileAnalysis",
]
