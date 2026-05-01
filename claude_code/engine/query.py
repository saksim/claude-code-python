"""
Claude Code Python - Query Engine
Handles the conversation loop and tool execution.

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
import time
from typing import Any, AsyncGenerator, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from claude_code.api.client import (
    APIClient, APIClientConfig, APIProvider,
    MessageParam, QueryOptions, StreamEvent, ToolParam
)
from claude_code.tools import Tool, ToolRegistry, ToolContext, ToolResult, ToolDefinition
from claude_code.tools.registry import create_default_registry
from claude_code.permissions import create_permission_checker
from claude_code.services.hooks_manager import HookEvent


class StopReason(Enum):
    """Reasons for query stopping.
    
    Attributes:
        END_TURN: Normal end of turn
        TOOL_USE: Stopped for tool use
        MAX_TOKENS: Max tokens reached
        STOP_SEQUENCE: Stop sequence encountered
        ABORTED: Query was aborted
        ERROR: Error occurred
    """
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"
    ABORTED = "aborted"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Message:
    """A message in the conversation.
    
    Using frozen=True for immutability.
    
    Attributes:
        id: Unique message identifier
        role: Message role (user/assistant/system)
        content: Message content
        timestamp: Message timestamp
        name: Optional name for function calls
        tool_call_id: Optional tool call ID
        tool_name: Optional tool name
        tool_input: Optional tool input
    """
    id: str
    role: str
    content: str | list[dict[str, Any]]
    timestamp: float = field(default_factory=time.time)
    
    # Optional metadata
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None
    
    def to_param(self) -> MessageParam:
        """Convert to API message format.
        
        Returns:
            MessageParam for API call.
        """
        return MessageParam(role=self.role, content=self.content)


@dataclass
class ToolUse:
    """A tool use request from the model.
    
    Attributes:
        id: Unique tool use identifier
        name: Tool name to call
        input: Tool input parameters
        start_time: Timestamp when tool use started
    """
    id: str
    name: str
    input: dict[str, Any]
    start_time: float = field(default_factory=time.time)


@dataclass
class QueryResult:
    """Result from a query.
    
    Attributes:
        messages: List of messages in conversation
        stop_reason: Reason for query stopping
        usage: Optional usage statistics
        error: Optional error message
    """
    messages: list[Message]
    stop_reason: StopReason
    usage: Optional[dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class QueryConfig:
    """Configuration for a query session.
    
    Attributes:
        model: Model identifier
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        thinking_config: Thinking configuration
        max_output_tokens: Maximum output tokens
        tools: List of available tools
        tool_choice: Tool choice strategy
        system_prompt: System prompt
        should_stop: Callback for stop condition
    """
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: Optional[float] = None
    thinking_config: Optional[dict[str, Any]] = None
    
    # Token limits
    max_output_tokens: Optional[int] = None
    
    # Tool settings
    tools: list[Tool] = field(default_factory=list)
    tool_choice: Optional[str] = None  # "auto", "any", or specific tool name
    
    # System prompt
    system_prompt: Optional[str] = None
    
    # Callback for stopping
    should_stop: Optional[Callable[[], bool]] = None
    
    # Permission propagation (wired from Config)
    permission_mode: str = "default"
    always_allow: list[str] = field(default_factory=list)
    always_deny: list[str] = field(default_factory=list)
    session_id: Optional[str] = None
    working_directory: Optional[str] = None
    memory_scope: str = "project"


@dataclass 
class ToolCallResult:
    """Result from executing a tool."""
    tool_use: ToolUse
    result: ToolResult
    duration_ms: float


class QueryEngine:
    """
    Core query engine that manages conversation flow and tool execution.
    
    This is the heart of Claude Code - it handles sending messages to the API,
    processing tool calls, and maintaining conversation state.
    """
    
    def __init__(
        self,
        api_client: APIClient,
        config: Optional[QueryConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.api_client = api_client
        self.config = config or QueryConfig()
        self.tool_registry = tool_registry or create_default_registry()
        
        # Conversation state
        self.messages: list[Message] = []
        self.conversation_id = str(uuid4())
        
        # Tool execution state
        self.abort_event = asyncio.Event()
        self.pending_tool_calls: dict[str, ToolUse] = {}
        self.tool_results: list[ToolCallResult] = []
        
        # Statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Cache for tool definitions and API params
        self._cached_config_hash: Optional[int] = None
        self._cached_tools: list[ToolParam] = []
        
        # Stream handling
        self._stream_task: Optional[asyncio.Task] = None
        self._streaming = False
        
        # Ensure model-visible tool list is populated from registry by default.
        self._ensure_configured_tools()

    def _record_event(
        self,
        *,
        event_type: str,
        payload: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Best-effort event journal write for runtime audit trail."""
        journal = getattr(self, "event_journal", None)
        append_event = getattr(journal, "append_event", None)
        if not callable(append_event):
            return
        try:
            append_event(
                event_type=event_type,
                payload=dict(payload or {}),
                session_id=self.config.session_id,
                conversation_id=self.conversation_id,
                source="query_engine",
                metadata=dict(metadata or {}),
            )
        except Exception:
            # Journal persistence must not interrupt query execution.
            pass
    
    def _ensure_configured_tools(self) -> None:
        """Populate query config tools from registry when not explicitly set."""
        if self.config.tools:
            return
        
        configured: list[Tool] = []
        seen: set[str] = set()
        for tool_name in self.tool_registry.get_names():
            if tool_name in seen:
                continue
            seen.add(tool_name)
            try:
                tool = self.tool_registry.get(tool_name)
            except Exception:
                # Skip tools that fail to initialize lazily.
                continue
            if tool is not None:
                configured.append(tool)
        
        self.config.tools = configured
    
    async def query(
        self,
        user_input: str,
        attachments: Optional[list[dict]] = None,
    ) -> AsyncGenerator[Message | ToolUse | ToolCallResult | dict, None]:
        """
        Process a user query through the model and tool loop.
        
        Yields:
            - Message: Assistant responses
            - ToolUse: Tool call requests
            - ToolCallResult: Tool execution results
            - dict: Status updates (usage, stop_reason, etc.)
        """
        # Add user message
        user_message = self._create_user_message(user_input, attachments)
        self.messages.append(user_message)
        self._sync_message_to_active_session(user_message)
        self._record_event(
            event_type="query.started",
            payload={
                "input": user_input,
                "has_attachments": bool(attachments),
                "memory_scope": self.config.memory_scope,
            },
        )
        self._record_active_memory_hit(query_text=user_input)
        self._record_event(
            event_type="message.user",
            payload={
                "message_id": user_message.id,
                "content": user_message.content,
            },
        )
        yield user_message
        
        # Build API messages
        api_messages = [msg.to_param() for msg in self.messages]
        
        # Build tools
        tools = self._build_tools()
        
        # Build options
        options = QueryOptions(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            tools=tools,
            system=self.config.system_prompt,
            thinking=self.config.thinking_config,
        )
        
        # Main query loop
        max_turns = 20
        turn_count = 0
        
        while turn_count < max_turns:
            turn_count += 1
            
            # Check abort
            if self.abort_event.is_set():
                break
            
            # Check stop condition
            if self.config.should_stop and self.config.should_stop():
                break
            
            try:
                # Stream response
                assistant_message = None
                tool_uses = []
                
                async for event in self.api_client.create_message_streaming(
                    api_messages,
                    options
                ):
                    if event.type == "text" and event.content:
                        # Yield streaming text
                        yield {"type": "text", "content": event.content["text"]}
                    
                    elif event.type == "message":
                        # Final message
                        assistant_message = self._parse_assistant_message(
                            event.content["content"]
                        )
                
                # If no streaming happened, try non-streaming
                if assistant_message is None:
                    response = await self.api_client.create_message(
                        api_messages,
                        options
                    )
                    assistant_message = self._parse_assistant_message(
                        response.content
                    )
                
                # Add to conversation
                self.messages.append(assistant_message)
                self._sync_message_to_active_session(assistant_message)
                api_messages.append(assistant_message.to_param())
                self._record_event(
                    event_type="message.assistant",
                    payload={
                        "message_id": assistant_message.id,
                        "content": assistant_message.content,
                    },
                )
                yield assistant_message
                
                # Extract tool uses
                tool_uses = self._extract_tool_uses(assistant_message)
                
                if not tool_uses:
                    # No tool calls - done
                    self._record_event(
                        event_type="query.completed",
                        payload={
                            "stop_reason": StopReason.END_TURN.value,
                            "message_count": len(self.messages),
                            "tool_call_count": len(self.tool_results),
                        },
                    )
                    yield {
                        "type": "stop_reason",
                        "reason": StopReason.END_TURN.value
                    }
                    break
                
                # Execute tool calls
                if len(tool_uses) == 1:
                    # Single tool — no need for gather overhead
                    tool_use = tool_uses[0]
                    yield tool_use
                    result = await self._execute_tool(tool_use)
                    self.tool_results.append(result)
                    yield result
                    tool_result_message = self._create_tool_result_message(result)
                    self.messages.append(tool_result_message)
                    self._sync_message_to_active_session(tool_result_message)
                    api_messages.append(tool_result_message.to_param())
                else:
                    # Multiple tools — execute in parallel when safe
                    safe_tool_names = set()
                    for tu in tool_uses:
                        tool = self.tool_registry.get(tu.name)
                        if tool and tool.is_concurrency_safe():
                            safe_tool_names.add(tu.name)
                    
                    if all(tu.name in safe_tool_names for tu in tool_uses):
                        # All tools are concurrency-safe — execute in parallel
                        for tu in tool_uses:
                            yield tu
                        results = await asyncio.gather(
                            *[self._execute_tool(tu) for tu in tool_uses]
                        )
                        for tu, result in zip(tool_uses, results):
                            self.tool_results.append(result)
                            yield result
                            tool_result_message = self._create_tool_result_message(result)
                            self.messages.append(tool_result_message)
                            self._sync_message_to_active_session(tool_result_message)
                            api_messages.append(tool_result_message.to_param())
                    else:
                        # Mixed or unsafe tools — execute sequentially
                        for tool_use in tool_uses:
                            yield tool_use
                            result = await self._execute_tool(tool_use)
                            self.tool_results.append(result)
                            yield result
                            tool_result_message = self._create_tool_result_message(result)
                            self.messages.append(tool_result_message)
                            self._sync_message_to_active_session(tool_result_message)
                            api_messages.append(tool_result_message.to_param())
                
            except Exception as e:
                await self._trigger_hook_event(
                    HookEvent.ON_ERROR,
                    {
                        "source": "query_engine",
                        "phase": "query_loop",
                        "conversation_id": self.conversation_id,
                        "session_id": self.config.session_id or self.conversation_id,
                        "working_directory": self.config.working_directory or os.getcwd(),
                        "model": self.config.model,
                        "error": str(e),
                    },
                )
                yield {"type": "error", "error": str(e)}
                self._record_event(
                    event_type="query.error",
                    payload={
                        "error": str(e),
                    },
                )
                yield {"type": "stop_reason", "reason": StopReason.ERROR.value}
                break
    
    def _create_user_message(
        self,
        content: str,
        attachments: Optional[list[dict]] = None,
    ) -> Message:
        """Create a user message."""
        message_content = content
        
        if attachments:
            # Add attachments to content
            attachment_texts = []
            for att in attachments:
                att_type = att.get("type", "file")
                if att_type == "file":
                    attachment_texts.append(f"[Attached: {att.get('path', 'file')}]")
                elif att_type == "image":
                    attachment_texts.append(f"[Image: {att.get('path', 'image')}]")
            
            if attachment_texts:
                message_content = content + "\n\n" + "\n".join(attachment_texts)
        
        return Message(
            id=str(uuid4()),
            role="user",
            content=message_content,
        )
    
    def _create_tool_result_message(self, result: ToolCallResult) -> Message:
        """Create a message for a tool result."""
        content = result.result.content
        blocks: list[dict[str, Any]] = []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "content" in item:
                    blocks.append({
                        "type": "tool_result",
                        "tool_use_id": result.tool_use.id,
                        "content": item.get("content", ""),
                        "is_error": result.result.is_error,
                    })
                else:
                    blocks.append({
                        "type": "tool_result",
                        "tool_use_id": result.tool_use.id,
                        "content": str(item),
                        "is_error": result.result.is_error,
                    })
        else:
            blocks.append({
                "type": "tool_result",
                "tool_use_id": result.tool_use.id,
                "content": str(content),
                "is_error": result.result.is_error,
            })
        
        return Message(
            id=str(uuid4()),
            role="user",
            content=blocks,
            tool_call_id=result.tool_use.id,
            name=result.tool_use.name,
        )
    
    def _normalize_content_block(self, block: Any) -> Optional[dict[str, Any]]:
        """Normalize provider-specific content blocks to a dict format."""
        if isinstance(block, dict):
            block_type = block.get("type")
            if block_type == "text":
                return {"type": "text", "text": block.get("text", "")}
            if block_type == "tool_use":
                return {
                    "type": "tool_use",
                    "id": block.get("id", str(uuid4())),
                    "name": block.get("name", ""),
                    "input": block.get("input", {}),
                }
            return block
        
        block_type = getattr(block, "type", None)
        if block_type == "text":
            return {"type": "text", "text": getattr(block, "text", "")}
        if block_type == "tool_use":
            return {
                "type": "tool_use",
                "id": getattr(block, "id", str(uuid4())),
                "name": getattr(block, "name", ""),
                "input": getattr(block, "input", {}) or {},
            }
        
        if hasattr(block, "name") and hasattr(block, "input"):
            return {
                "type": "tool_use",
                "id": getattr(block, "id", str(uuid4())),
                "name": getattr(block, "name", ""),
                "input": getattr(block, "input", {}) or {},
            }
        
        text_value = getattr(block, "text", None)
        if text_value is not None:
            return {"type": "text", "text": str(text_value)}
        
        return None
    
    def _parse_assistant_message(self, content: Any) -> Message:
        """Parse assistant message from API response."""
        parsed_content: str | list[dict[str, Any]]
        if isinstance(content, list):
            normalized_blocks: list[dict[str, Any]] = []
            text_parts: list[str] = []
            for block in content:
                normalized = self._normalize_content_block(block)
                if normalized is None:
                    continue
                normalized_blocks.append(normalized)
                if normalized.get("type") == "text":
                    text_parts.append(str(normalized.get("text", "")))
            parsed_content = normalized_blocks if normalized_blocks else "".join(text_parts)
        elif isinstance(content, dict) and isinstance(content.get("content"), list):
            return self._parse_assistant_message(content["content"])
        else:
            parsed_content = str(content)
        
        return Message(
            id=str(uuid4()),
            role="assistant",
            content=parsed_content,
        )
    
    def _extract_tool_uses(self, message: Message) -> list[ToolUse]:
        """Extract tool uses from assistant message."""
        tool_uses = []
        
        # Parse tool calls from message content
        # This is a simplified version - real implementation would
        # parse the actual API response format
        content = message.content
        
        if isinstance(content, list):
            for block in content:
                normalized = self._normalize_content_block(block)
                if not normalized:
                    continue
                if normalized.get("type") == "tool_use":
                    tool_uses.append(ToolUse(
                        id=normalized.get("id", str(uuid4())),
                        name=normalized.get("name", ""),
                        input=normalized.get("input", {}) or {},
                    ))
        
        return tool_uses
    
    def _build_tools(self) -> list[ToolParam]:
        """Build tool parameters for API.
        
        Caches the result when tool list hasn't changed,
        avoiding redundant ToolDefinition → ToolParam conversion
        on every conversation turn.
        """
        config_hash = hash(tuple(t.name for t in self.config.tools))
        if config_hash == self._cached_config_hash and self._cached_tools:
            return self._cached_tools
        
        tools = []
        for tool in self.config.tools:
            definition = tool.get_definition()
            tools.append(ToolParam(
                name=definition.name,
                description=definition.description,
                input_schema=definition.input_schema,
            ))
        self._cached_config_hash = config_hash
        self._cached_tools = tools
        return tools

    def _sync_message_to_active_session(self, message: Message) -> None:
        """Persist runtime message into active session source-of-truth."""
        try:
            from claude_code.engine.session import SessionManager
        except Exception:
            return

        manager = getattr(self, "session_manager", None)
        if not isinstance(manager, SessionManager):
            return

        session = manager.get_current_session()
        target_session_id = self.config.session_id
        if target_session_id and (session is None or session.id != target_session_id):
            session = manager.switch_session(target_session_id)

        if session is None:
            session = manager.ensure_current_session()
            self.config.session_id = session.id

        if self.config.working_directory:
            session.metadata.working_directory = self.config.working_directory
        if self.config.model:
            session.metadata.model = self.config.model

        if session.has_message(message.id):
            return

        message_metadata = {
            "conversation_id": self.conversation_id,
            "source": "query_engine",
        }
        if message.name:
            message_metadata["name"] = message.name
        if message.tool_input is not None:
            message_metadata["tool_input"] = message.tool_input

        session.add_message(
            role=message.role,
            content=message.content,
            id=message.id,
            timestamp=message.timestamp,
            tool_call_id=message.tool_call_id,
            tool_name=message.tool_name,
            metadata=message_metadata,
        )

    def _record_active_memory_hit(self, *, query_text: str) -> None:
        """Record active memory match information for runtime observability."""
        memory = getattr(self, "memory", None)
        if memory is None:
            return
        snapshot_scoped = getattr(memory, "snapshot_scoped", None)
        if not callable(snapshot_scoped):
            return
        scope = self.config.memory_scope or "project"
        try:
            snapshot = snapshot_scoped(
                scope,
                working_directory=self.config.working_directory,
                limit=20,
            )
        except Exception:
            return
        if not snapshot:
            return
        query_terms = {part.lower() for part in query_text.split() if part.strip()}
        matched_keys = sorted(
            key
            for key, value in snapshot.items()
            if key.lower() in query_terms
            or any(term in str(value).lower() for term in query_terms)
        )
        if not matched_keys:
            return
        self._record_event(
            event_type="memory.hit",
            payload={
                "scope": scope,
                "matched_keys": matched_keys,
                "matched_count": len(matched_keys),
            },
        )

    def _archive_session_to_history(self, session: Any) -> int:
        """Archive persisted session into history storage."""
        try:
            from claude_code.services.history_manager import HistoryManager
        except Exception:
            return 0

        history_manager = getattr(self, "history_manager", None)
        if not isinstance(history_manager, HistoryManager):
            return 0

        messages = [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp,
                "tool_call_id": message.tool_call_id,
                "tool_name": message.tool_name,
                "metadata": message.metadata,
            }
            for message in getattr(session, "messages", [])
        ]
        if not messages:
            return 0

        session_metadata = getattr(session, "metadata", None)
        working_directory = getattr(session_metadata, "working_directory", None)
        model = getattr(session_metadata, "model", None)
        session_id = getattr(session, "id", None)
        if not session_id:
            return 0

        return history_manager.archive_session_messages(
            session_id=session_id,
            messages=messages,
            working_directory=working_directory,
            model=model,
        )

    async def _trigger_hook_event(
        self,
        event: HookEvent,
        context: dict[str, Any],
    ) -> list[Any]:
        """Trigger hook event if runtime hooks manager is attached."""
        hooks_manager = getattr(self, "hooks_manager", None)
        if hooks_manager is None or not hasattr(hooks_manager, "trigger"):
            return []

        try:
            return await hooks_manager.trigger(event, context)
        except Exception:
            return []

    def _serialize_hook_results(self, results: list[Any]) -> list[dict[str, Any]]:
        """Normalize hook trigger results for event journal payloads."""
        serialized: list[dict[str, Any]] = []
        for item in results:
            to_dict = getattr(item, "to_dict", None)
            if callable(to_dict):
                try:
                    data = to_dict()
                    if isinstance(data, dict):
                        serialized.append(data)
                        continue
                except Exception:
                    pass

            hook_name = getattr(item, "hook_name", None)
            success = getattr(item, "success", None)
            output = getattr(item, "output", None)
            error = getattr(item, "error", None)
            duration_ms = getattr(item, "duration_ms", None)
            serialized.append(
                {
                    "hook_name": hook_name if hook_name is not None else "<unknown>",
                    "success": bool(success) if success is not None else False,
                    "output": output if output is not None else "",
                    "error": error,
                    "duration_ms": float(duration_ms) if duration_ms is not None else 0.0,
                }
            )
        return serialized

    def _record_hook_execution_event(
        self,
        *,
        event: HookEvent,
        hook_context: dict[str, Any],
        results: list[Any],
    ) -> None:
        """Record hook execution outcomes into event journal."""
        self._record_event(
            event_type="hook.execution",
            payload={
                "hook_event": event.value,
                "tool_name": hook_context.get("tool_name"),
                "tool_use_id": hook_context.get("tool_use_id"),
                "phase": hook_context.get("phase"),
                "results": self._serialize_hook_results(results),
            },
        )

    def _build_tool_hook_context(
        self,
        tool_use: ToolUse,
        *,
        phase: str,
        duration_ms: Optional[float] = None,
        result: Optional[ToolResult] = None,
        error: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build normalized hook context payload for tool lifecycle events."""
        payload: dict[str, Any] = {
            "source": "query_engine",
            "phase": phase,
            "conversation_id": self.conversation_id,
            "session_id": self.config.session_id or self.conversation_id,
            "working_directory": self.config.working_directory or os.getcwd(),
            "model": self.config.model,
            "tool_name": tool_use.name,
            "tool_use_id": tool_use.id,
            "tool_input": tool_use.input,
        }
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if result is not None:
            payload["is_error"] = result.is_error
            payload["tool_output"] = result.content
        if error:
            payload["error"] = error
        return payload

    async def _emit_tool_outcome_hooks(
        self,
        tool_use: ToolUse,
        result: ToolResult,
        duration_ms: float,
        *,
        error_message: Optional[str] = None,
    ) -> None:
        """Emit after_tool and on_error hooks for tool completion."""
        after_context = self._build_tool_hook_context(
            tool_use,
            phase=HookEvent.AFTER_TOOL.value,
            duration_ms=duration_ms,
            result=result,
        )
        after_results = await self._trigger_hook_event(
            HookEvent.AFTER_TOOL,
            after_context,
        )
        self._record_hook_execution_event(
            event=HookEvent.AFTER_TOOL,
            hook_context=after_context,
            results=after_results,
        )

        if result.is_error:
            error_context = self._build_tool_hook_context(
                tool_use,
                phase=HookEvent.ON_ERROR.value,
                duration_ms=duration_ms,
                result=result,
                error=error_message or str(result.content),
            )
            error_results = await self._trigger_hook_event(
                HookEvent.ON_ERROR,
                error_context,
            )
            self._record_hook_execution_event(
                event=HookEvent.ON_ERROR,
                hook_context=error_context,
                results=error_results,
            )
    
    async def _execute_tool(self, tool_use: ToolUse) -> ToolCallResult:
        """Execute a tool call."""
        start_time = time.time()
        permission_checker = create_permission_checker(
            mode=self.config.permission_mode,
            always_allow=list(self.config.always_allow),
            always_deny=list(self.config.always_deny),
        )
        permission_evaluation = permission_checker.evaluate(tool_use.name)
        self._record_event(
            event_type="permission.requested",
            payload={
                "tool_use_id": tool_use.id,
                "tool_name": tool_use.name,
                "tool_input": tool_use.input,
                "permission_mode": self.config.permission_mode,
            },
        )
        self._record_event(
            event_type="permission.decided",
            payload={
                "tool_use_id": tool_use.id,
                "tool_name": tool_use.name,
                "allowed": permission_evaluation.allowed,
                "decision_reason": permission_evaluation.reason,
                "permission_mode": self.config.permission_mode,
            },
        )
        self._record_event(
            event_type="tool.started",
            payload={
                "tool_use_id": tool_use.id,
                "tool_name": tool_use.name,
                "tool_input": tool_use.input,
            },
        )
        before_context = self._build_tool_hook_context(
            tool_use,
            phase=HookEvent.BEFORE_TOOL.value,
        )
        before_results = await self._trigger_hook_event(
            HookEvent.BEFORE_TOOL,
            before_context,
        )
        self._record_hook_execution_event(
            event=HookEvent.BEFORE_TOOL,
            hook_context=before_context,
            results=before_results,
        )

        async def _finalize(result: ToolResult, error_message: Optional[str] = None) -> ToolCallResult:
            duration_ms = (time.time() - start_time) * 1000
            await self._emit_tool_outcome_hooks(
                tool_use,
                result,
                duration_ms,
                error_message=error_message,
            )
            event_type = "tool.failed" if result.is_error else "tool.completed"
            self._record_event(
                event_type=event_type,
                payload={
                    "tool_use_id": tool_use.id,
                    "tool_name": tool_use.name,
                    "duration_ms": duration_ms,
                    "is_error": result.is_error,
                    "tool_output": result.content,
                    "error": error_message,
                },
            )
            return ToolCallResult(
                tool_use=tool_use,
                result=result,
                duration_ms=duration_ms,
            )
        
        # Get tool from registry
        tool = self.tool_registry.get(tool_use.name)
        
        if not tool:
            error_message = f"Unknown tool: {tool_use.name}"
            return await _finalize(
                ToolResult(
                    content=error_message,
                    is_error=True,
                    tool_use_id=tool_use.id,
                ),
                error_message=error_message,
            )
        
        # Create context
        context = ToolContext(
            working_directory=self.config.working_directory or os.getcwd(),
            environment={},
            abort_signal=self.abort_event,
            permission_mode=self.config.permission_mode,
            always_allow=list(self.config.always_allow),
            always_deny=list(self.config.always_deny),
            model=self.config.model,
            session_id=self.config.session_id or self.conversation_id,
            memory_scope=self.config.memory_scope,
            conversation_id=self.conversation_id,
            api_provider=(
                getattr(getattr(self.api_client, "config", None), "provider", None).value
                if hasattr(getattr(getattr(self.api_client, "config", None), "provider", None), "value")
                else str(getattr(getattr(self.api_client, "config", None), "provider", ""))
            ),
            task_manager=getattr(self, "task_manager", None),
            tool_registry=self.tool_registry,
        )

        if not permission_evaluation.allowed:
            error_message = (
                f"Permission denied for tool: {tool_use.name} "
                f"(mode={context.permission_mode})"
            )
            return await _finalize(
                ToolResult(
                    content=error_message,
                    is_error=True,
                    tool_use_id=tool_use.id,
                ),
                error_message=error_message,
            )
        
        try:
            # Validate input
            is_valid, error = tool.validate_input(tool_use.input)
            if not is_valid:
                error_message = f"Invalid input: {error}"
                return await _finalize(
                    ToolResult(
                        content=error_message,
                        is_error=True,
                        tool_use_id=tool_use.id,
                    ),
                    error_message=error_message,
                )
            
            # Execute
            result = await tool.execute(tool_use.input, context)
            result.tool_use_id = tool_use.id
            
            return await _finalize(result)
            
        except Exception as e:
            error_message = f"Tool execution error: {str(e)}"
            return await _finalize(
                ToolResult(
                    content=error_message,
                    is_error=True,
                    tool_use_id=tool_use.id,
                ),
                error_message=error_message,
            )
    
    def interrupt(self):
        """Interrupt the current query."""
        self.abort_event.set()
    
    def resume(self):
        """Resume from an interrupted state."""
        self.abort_event.clear()
    
    def get_messages(self) -> list[Message]:
        """Get all messages in the conversation."""
        return self.messages.copy()
    
    def clear(self):
        """Clear conversation history."""
        self.messages.clear()
        self.tool_results.clear()
    
    def get_statistics(self) -> dict:
        """Get session statistics."""
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.conversation_id,
            "total_messages": len(self.messages),
            "total_turns": len(self.messages) // 2,
            "tool_call_count": len(self.tool_results),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost,
            "start_time": getattr(self, '_start_time', None),
        }
    
    def set_mode(self, mode: str):
        """Set the engine mode (e.g., 'init', 'normal')."""
        self._mode = mode
    
    def set_permission_mode(self, mode):
        """Set the permission mode."""
        self.config.permission_mode = mode.value if hasattr(mode, 'value') else str(mode)
    
    def get_tasks(self) -> list[dict]:
        """Get current tasks."""
        return getattr(self, '_tasks', [])
    
    def get_hooks(self) -> list[dict]:
        """Get configured hooks."""
        return getattr(self, '_hooks', [])
    
    async def load_skill(self, skill_name: str) -> dict[str, Any]:
        """Load a skill by name."""
        from claude_code.skills.registry import get_skill_registry, load_all_skills

        load_all_skills(
            project_dir=self.config.working_directory or os.getcwd(),
            include_bundled=True,
        )
        registry = get_skill_registry()
        skill = registry.get(skill_name)
        if skill is None:
            raise ValueError(f"Skill not found: {skill_name}")
        return {
            "status": "loaded",
            "skill": skill_name,
            "source": str(skill.source.value if hasattr(skill.source, "value") else skill.source),
        }
    
    def set_effort(self, level: str):
        """Set effort level (low, medium, high)."""
        self._effort = level
    
    def get_last_message(self) -> Optional[str]:
        """Get the last assistant message."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                content = msg.content
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts: list[str] = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(str(block.get("text", "")))
                    if parts:
                        return "".join(parts)
        return None
    
    async def compact(self, custom_instructions: Optional[str] = None) -> dict:
        """Compact the conversation history."""
        if not self.messages:
            return {"status": "no_messages"}
        
        original_count = len(self.messages)
        
        # Keep system prompt and first few messages
        keep_count = min(3, original_count)
        kept_messages = self.messages[:keep_count]
        
        # Create summary
        summary = f"[Previous conversation summarized - {original_count} messages condensed]"
        
        self.messages = kept_messages + [
            Message(
                id=str(uuid4()),
                role="system",
                content=f"Conversation summary: {summary}"
            )
        ]
        
        return {
            "status": "success",
            "messages_summarized": original_count - len(self.messages),
            "tokens_saved": "estimated",
        }
    
    async def create_branch(self, branch_name: Optional[str] = None) -> dict:
        """Create a conversation branch."""
        import datetime
        
        branch_id = str(uuid4())
        branch_name = branch_name or f"branch-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        return {
            "status": "success",
            "branch_id": branch_id,
            "name": branch_name,
        }
    
    async def resume_session(self, session_id: Optional[str] = None) -> bool:
        """Resume a previous session."""
        from claude_code.engine.session import SessionManager

        manager = getattr(self, "session_manager", None)
        if not isinstance(manager, SessionManager):
            manager = SessionManager()
            self.session_manager = manager

        current_session = manager.get_current_session()
        target_session_id = session_id
        if target_session_id is None:
            sessions = manager.list_sessions()
            if not sessions:
                return False
            target_session_id = sessions[0].id

        if (
            current_session is not None
            and target_session_id is not None
            and current_session.id != target_session_id
        ):
            self._archive_session_to_history(current_session)

        session = manager.load_session(target_session_id)
        if session is None:
            return False

        restored: list[Message] = []
        for record in session.messages:
            restored.append(
                Message(
                    id=record.id,
                    role=record.role,
                    content=record.content,
                    timestamp=record.timestamp,
                    tool_call_id=record.tool_call_id,
                    tool_name=record.tool_name,
                )
            )

        self.messages = restored
        self.tool_results = []
        self.conversation_id = session.id
        self.config.session_id = session.id
        if session.metadata.working_directory:
            self.config.working_directory = session.metadata.working_directory
        return True
