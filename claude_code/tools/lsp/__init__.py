"""
Claude Code Python - LSP Tool
Language Server Protocol integration.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class LSPState(Enum):
    """LSP connection state."""
    INITIAL = "initial"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LSPPosition:
    """Text document position."""
    line: int
    character: int


@dataclass
class LSPRange:
    """Text document range."""
    start: LSPPosition
    end: LSPPosition


@dataclass
class LSPDiagnostic:
    """ LSP diagnostic."""
    range: LSPRange
    severity: int
    message: str
    source: str = ""


@dataclass
class LSPCompletionItem:
    """ LSP completion item."""
    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None


class LSPClient:
    """
    LSP client implementation.
    
    Supports stdio-based language servers.
    """
    
    def __init__(
        self,
        command: str,
        args: list[str] = None,
        cwd: str = ".",
    ):
        self.command = command
        self.args = args or []
        self.cwd = cwd
        self._process = None
        self._reader = None
        self._writer = None
        self._request_id = 0
        self._pending: dict[str, asyncio.Future] = {}
        self._callbacks: dict[str, callable] = {}
        self._state = LSPState.INITIAL
        self._capabilities: dict = {}
        self._root_uri = ""
    
    @property
    def state(self) -> LSPState:
        return self._state
    
    async def start(self) -> None:
        """Start the LSP server."""
        if self._state == LSPState.RUNNING:
            return
        
        self._state = LSPState.STARTING
        
        try:
            self._process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                cwd=self.cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            self._reader = self._process.stdout
            self._writer = self._process.stdin
            
            self._state = LSPState.RUNNING
            
            asyncio.create_task(self._read_messages())
            
            await self._initialize()
            
        except Exception as e:
            self._state = LSPState.ERROR
            raise
    
    async def _read_messages(self) -> None:
        """Read messages from LSP server."""
        buffer = ""
        
        while True:
            try:
                chunk = await self._reader.read(4096)
                if not chunk:
                    break
                
                buffer += chunk.decode()
                
                while "\r\n\r\n" in buffer:
                    header, buffer = buffer.split("\r\n\r\n", 1)
                    headers = {}
                    for line in header.split("\r\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            headers[key.lower()] = value.strip()
                    
                    content_length = int(headers.get("content-length", 0))
                    
                    while len(buffer) < content_length:
                        chunk = await self._reader.read(4096)
                        buffer += chunk.decode()
                    
                    body = buffer[:content_length]
                    buffer = buffer[content_length:]
                    
                    message = json.loads(body)
                    await self._handle_message(message)
                    
            except Exception:
                break
    
    async def _handle_message(self, message: dict) -> None:
        """Handle incoming LSP message."""
        if "id" in message:
            req_id = str(message["id"])
            if req_id in self._pending:
                future = self._pending.pop(req_id)
                if "error" in message:
                    future.set_exception(Exception(message["error"]))
                else:
                    future.set_result(message.get("result"))
        elif "method" in message:
            method = message["method"]
            if method in self._callbacks:
                await self._callbacks[method](message.get("params"))
    
    async def _send_message(self, method: str, params: dict = None) -> dict:
        """Send an LSP message and wait for response."""
        req_id = str(self._next_id())
        
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params:
            message["params"] = params
        
        future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = future
        
        body = json.dumps(message)
        header = f"Content-Length: {len(body)}\r\n\r\n"
        
        self._writer.write((header + body).encode())
        await self._writer.drain()
        
        return await future
    
    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    async def _initialize(self) -> dict:
        """Send initialize request."""
        result = await self._send_message("initialize", {
            "processId": None,
            "rootUri": Path(self.cwd).as_uri(),
            "capabilities": {}
        })
        
        self._capabilities = result.get("capabilities", {})
        self._root_uri = result.get("rootUri", "")
        
        await self._send_notification("initialized", {})
        
        return result
    
    async def shutdown(self) -> None:
        """Shutdown the LSP server."""
        try:
            await self._send_message("shutdown")
        except:
            pass
        await self._send_notification("exit", {})
        await self.stop()
    
    async def stop(self) -> None:
        """Stop the LSP server."""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
        
        self._state = LSPState.STOPPED
    
    async def initialize(
        self,
        text_document: str,
        language_id: str,
    ) -> dict:
        """Initialize document."""
        return await self._send_message("textDocument/didOpen", {
            "textDocument": {
                "uri": Path(text_document).as_uri(),
                "languageId": language_id,
                "version": 1,
            }
        })
    
    async def get_completions(
        self,
        text_document: str,
        line: int,
        character: int,
    ) -> list[LSPCompletionItem]:
        """Get completions at position."""
        result = await self._send_message("textDocument/completion", {
            "textDocument": {"uri": Path(text_document).as_uri()},
            "position": {"line": line, "character": character},
        })
        
        items = []
        for item in (result.get("items") or result or []):
            items.append(LSPCompletionItem(
                label=item.get("label", ""),
                kind=item.get("kind"),
                detail=item.get("detail"),
                documentation=item.get("documentation"),
                insert_text=item.get("insertText"),
            ))
        
        return items
    
    async def get_definition(
        self,
        text_document: str,
        line: int,
        character: int,
    ) -> list[dict]:
        """Go to definition."""
        result = await self._send_message("textDocument/definition", {
            "textDocument": {"uri": Path(text_document).as_uri()},
            "position": {"line": line, "character": character},
        })
        
        return result if isinstance(result, list) else [result]
    
    async def get_references(
        self,
        text_document: str,
        line: int,
        character: int,
    ) -> list[dict]:
        """Find references."""
        result = await self._send_message("textDocument/references", {
            "textDocument": {"uri": Path(text_document).as_uri()},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": True}
        })
        
        return result if isinstance(result, list) else []
    
    async def get_diagnostics(
        self,
        text_document: str,
    ) -> list[LSPDiagnostic]:
        """Get diagnostics for document."""
        result = await self._send_message("textDocument/didOpen", {
            "textDocument": {"uri": Path(text_document).as_uri()}
        })
        
        return []
    
    async def format_document(
        self,
        text_document: str,
    ) -> str:
        """Format document."""
        result = await self._send_message("textDocument/formatting", {
            "textDocument": {"uri": Path(text_document).as_uri()},
            "options": {"tabSize": 4, "insertSpaces": True}
        })
        
        return ""
    
    def on_notification(self, method: str, callback: callable) -> None:
        """Register notification handler."""
        self._callbacks[method] = callback


class LSPServerManager:
    """Manages multiple LSP servers."""
    
    def __init__(self):
        self._servers: dict[str, LSPClient] = {}
    
    async def add_server(
        self,
        name: str,
        command: str,
        args: list[str] = None,
        cwd: str = ".",
    ) -> LSPClient:
        """Add and start an LSP server."""
        client = LSPClient(command, args, cwd)
        await client.start()
        self._servers[name] = client
        return client
    
    def get_server(self, name: str) -> Optional[LSPClient]:
        """Get an LSP server by name."""
        return self._servers.get(name)
    
    def list_servers(self) -> dict[str, dict]:
        """List all servers and their state."""
        return {
            name: {"state": server.state.value, "capabilities": server._capabilities}
            for name, server in self._servers.items()
        }
    
    async def remove_server(self, name: str) -> None:
        """Remove an LSP server."""
        if name in self._servers:
            await self._servers[name].stop()
            del self._servers[name]
    
    async def stop_all(self) -> None:
        """Stop all LSP servers."""
        for server in list(self._servers.values()):
            await server.stop()
        self._servers.clear()


_lsp_manager: Optional[LSPServerManager] = None


def get_lsp_manager() -> LSPServerManager:
    """Get the global LSP manager."""
    global _lsp_manager
    if _lsp_manager is None:
        _lsp_manager = LSPServerManager()
    return _lsp_manager


__all__ = [
    "LSPClient",
    "LSPServerManager",
    "LSPState",
    "LSPPosition",
    "LSPRange",
    "LSPDiagnostic",
    "LSPCompletionItem",
    "get_lsp_manager",
]
