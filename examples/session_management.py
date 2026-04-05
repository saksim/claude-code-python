"""
Example: Session and History Management
Shows how to manage conversation sessions.
"""

import asyncio
from claude_code.engine.session import Session, SessionManager, SessionMetadata
from claude_code.api.client import APIClient, APIClientConfig
from claude_code.engine.query import QueryEngine, QueryConfig


def basic_session_operations():
    """Basic session management."""
    manager = SessionManager()
    
    # Create new session
    session = manager.create_session()
    print(f"Session ID: {session.id}")
    print(f"Created: {session.metadata.created_at}")
    
    # Add messages
    session.add_user_message("Hello, how are you?")
    session.add_assistant_message("I'm doing well, thanks for asking!")
    session.add_user_message("Can you help me with Python?")
    session.add_assistant_message("Of course! What would you like to know?")
    
    # Session auto-saves when messages are added
    
    # Get all messages
    messages = session.get_messages()
    print(f"\nConversation ({len(messages)} messages):")
    for msg in messages:
        print(f"  [{msg['role']}]: {msg['content'][:50]}...")
    
    # Clear session
    session.clear()
    print(f"\nCleared - Messages: {len(session.messages)}")
    
    # List all sessions
    sessions = manager.list_sessions()
    print(f"\nAll sessions: {len(sessions)}")


def session_persistence():
    """Load and save sessions."""
    manager = SessionManager()
    
    # Create and populate a session
    session = manager.create_session()
    session.add_user_message("Tell me about Python")
    session.add_assistant_message(
        "Python is a high-level programming language known for "
        "its simplicity and readability."
    )
    
    # Session is auto-saved
    session_id = session.id
    print(f"Created session: {session_id}")
    
    # Later, load the session
    loaded = manager.load_session(session_id)
    if loaded:
        print(f"Loaded session with {len(loaded.messages)} messages")


def session_with_query_engine():
    """Use sessions with the query engine."""
    from claude_code.engine.session import Session
    
    # Create session with metadata
    metadata = SessionMetadata(
        id="my-session-001",
        created_at=1234567890.0,
        last_active=1234567890.0,
        working_directory="/path/to/project",
        model="claude-sonnet-4-20250514",
    )
    
    session = Session(metadata=metadata)
    
    # Configure query engine to use session
    manager = SessionManager()
    manager.current_session = session
    session.attach_store(manager.store)
    
    # As messages are added to session, they're saved automatically


def export_session():
    """Export session data."""
    manager = SessionManager()
    session = manager.create_session()
    
    session.add_user_message("Question 1")
    session.add_assistant_message("Answer 1")
    session.add_user_message("Question 2")
    session.add_assistant_message("Answer 2")
    
    # Export to dict (JSON compatible)
    data = session.to_dict()
    import json
    json_str = json.dumps(data, indent=2)
    
    print("Exported session:")
    print(json_str[:500] + "...")


if __name__ == "__main__":
    print("Session management examples:")
    print("=" * 40)
    
    basic_session_operations()
