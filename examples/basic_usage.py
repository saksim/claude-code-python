"""
Example: Basic Usage
Demonstrates core functionality of Claude Code Python.
"""

import asyncio
from claude_code import (
    QueryEngine,
    QueryConfig,
    APIClient,
    APIClientConfig,
    APIProvider,
    create_default_registry,
)


async def basic_query():
    """Simple query example."""
    config = APIClientConfig(
        api_key="your-api-key",  # Set via ANTHROPIC_API_KEY env var
        provider=APIProvider.ANTHROPIC,
    )
    
    api_client = APIClient(config)
    query_config = QueryConfig(
        model="claude-sonnet-4-20250514",
        system_prompt="You are a helpful coding assistant.",
    )
    
    engine = QueryEngine(
        api_client=api_client,
        config=query_config,
        tool_registry=create_default_registry(),
    )
    
    # Simple query
    async for event in engine.query("Hello, how are you?"):
        if isinstance(event, dict):
            if event.get("type") == "text":
                print(event["content"], end="")
        elif hasattr(event, "content"):
            print(event.content)


async def with_tools():
    """Query with tool usage."""
    config = APIClientConfig()
    api_client = APIClient(config)
    query_config = QueryConfig(
        model="claude-sonnet-4-20250514",
    )
    
    engine = QueryEngine(
        api_client=api_client,
        config=query_config,
    )
    
    async for event in engine.query(
        "List the Python files in the current directory"
    ):
        if hasattr(event, "name"):
            # Tool use
            print(f"Using tool: {event.name}")
        elif hasattr(event, "result"):
            # Tool result
            print(f"Result: {event.result.content}")
        elif isinstance(event, dict) and event.get("type") == "text":
            print(event["content"], end="")


async def session_management():
    """Session persistence example."""
    from claude_code import SessionManager
    
    manager = SessionManager()
    
    # Create new session
    session = manager.create_session()
    print(f"Created session: {session.id}")
    
    # Add messages
    session.add_user_message("Hello!")
    session.add_assistant_message("Hi there! How can I help?")
    
    # Session is auto-saved
    
    # Load session later
    loaded = manager.load_session(session.id)
    print(f"Messages: {len(loaded.messages)}")


if __name__ == "__main__":
    # Set your API key first!
    # import os
    # os.environ["ANTHROPIC_API_KEY"] = "your-key"
    
    print("Basic query example:")
    print("Run: python -m claude_code.main")
