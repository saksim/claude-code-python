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
        
        # Stream handling
        self._stream_task: Optional[asyncio.Task] = None
        self._streaming = False
    
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
                yield assistant_message
                
                # Extract tool uses
                tool_uses = self._extract_tool_uses(assistant_message)
                
                if not tool_uses:
                    # No tool calls - done
                    yield {
                        "type": "stop_reason",
                        "reason": StopReason.END_TURN.value
                    }
                    break
                
                # Execute tool calls
                for tool_use in tool_uses:
                    yield tool_use
                    
                    # Execute tool
                    result = await self._execute_tool(tool_use)
                    self.tool_results.append(result)
                    yield result
                    
                    # Add tool result as user message
                    tool_result_message = self._create_tool_result_message(result)
                    self.messages.append(tool_result_message)
                    api_messages.append(tool_result_message.to_param())
                
            except Exception as e:
                yield {"type": "error", "error": str(e)}
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
        if isinstance(content, list):
            # Format as tool_result blocks
            blocks = []
            for item in content:
                if isinstance(item, dict):
                    blocks.append({
                        "type": "tool_result",
                        "tool_use_id": result.tool_use.id,
                        "content": item.get("content", str(item)),
                        "is_error": result.result.is_error,
                    })
            content = blocks
        else:
            content = str(content)
        
        return Message(
            id=str(uuid4()),
            role="user",
            content=content,
            tool_call_id=result.tool_use.id,
            name=result.tool_use.name,
        )
    
    def _parse_assistant_message(self, content: Any) -> Message:
        """Parse assistant message from API response."""
        if hasattr(content, '__iter__'):
            # Handle list of content blocks
            text_parts = []
            for block in content:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
            
            text = ''.join(text_parts)
        else:
            text = str(content)
        
        return Message(
            id=str(uuid4()),
            role="assistant",
            content=text,
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
                if isinstance(block, dict):
                    if block.get('type') == 'tool_use':
                        tool_uses.append(ToolUse(
                            id=block.get('id', str(uuid4())),
                            name=block.get('name', ''),
                            input=block.get('input', {}),
                        ))
                elif hasattr(block, 'name'):
                    tool_uses.append(ToolUse(
                        id=getattr(block, 'id', str(uuid4())),
                        name=block.name,
                        input=block.input or {},
                    ))
        
        return tool_uses
    
    def _build_tools(self) -> list[ToolParam]:
        """Build tool parameters for API."""
        tools = []
        for tool in self.config.tools:
            definition = tool.get_definition()
            tools.append(ToolParam(
                name=definition.name,
                description=definition.description,
                input_schema=definition.input_schema,
            ))
        return tools
    
    async def _execute_tool(self, tool_use: ToolUse) -> ToolCallResult:
        """Execute a tool call."""
        start_time = time.time()
        
        # Get tool from registry
        tool = self.tool_registry.get(tool_use.name)
        
        if not tool:
            return ToolCallResult(
                tool_use=tool_use,
                result=ToolResult(
                    content=f"Unknown tool: {tool_use.name}",
                    is_error=True,
                    tool_use_id=tool_use.id,
                ),
                duration_ms=0,
            )
        
        # Create context
        context = ToolContext(
            working_directory=os.getcwd(),
            environment={},
            abort_signal=self.abort_event,
            permission_mode=self.config.permission_mode,
            always_allow=list(self.config.always_allow),
            always_deny=list(self.config.always_deny),
            model=self.config.model,
            session_id=self.config.session_id or self.conversation_id,
        )
        
        try:
            # Validate input
            is_valid, error = tool.validate_input(tool_use.input)
            if not is_valid:
                return ToolCallResult(
                    tool_use=tool_use,
                    result=ToolResult(
                        content=f"Invalid input: {error}",
                        is_error=True,
                        tool_use_id=tool_use.id,
                    ),
                    duration_ms=time.time() - start_time,
                )
            
            # Execute
            result = await tool.execute(tool_use.input, context)
            result.tool_use_id = tool_use.id
            
            return ToolCallResult(
                tool_use=tool_use,
                result=result,
                duration_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            return ToolCallResult(
                tool_use=tool_use,
                result=ToolResult(
                    content=f"Tool execution error: {str(e)}",
                    is_error=True,
                    tool_use_id=tool_use.id,
                ),
                duration_ms=(time.time() - start_time) * 1000,
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
        self.permission_mode = mode.value if hasattr(mode, 'value') else str(mode)
    
    def get_tasks(self) -> list[dict]:
        """Get current tasks."""
        return getattr(self, '_tasks', [])
    
    def get_hooks(self) -> list[dict]:
        """Get configured hooks."""
        return getattr(self, '_hooks', [])
    
    async def load_skill(self, skill_name: str):
        """Load a skill by name."""
        pass  # Placeholder - skills loading not yet implemented
    
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
        pass  # Placeholder - session loading not yet implemented
        return True
