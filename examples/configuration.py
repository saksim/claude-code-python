"""
Example: Configuration and Permissions
Shows how to configure Claude Code Python.
"""

import os
from claude_code.config import Config, LocalSettings, PermissionMode, get_config


def global_config():
    """Work with global configuration."""
    # Get the global config (loads from ~/.claude-code-python/config.json)
    config = get_config()
    
    # Modify settings
    config.model = "claude-opus-4-20250514"
    config.verbose = True
    config.permission_mode = PermissionMode.AUTO
    
    # Add always-allow rules
    config.always_allow = [
        "bash ls *",           # Allow ls commands
        "read *",              # Allow all reads
        "glob *",              # Allow all glob
    ]
    
    # Save configuration
    config.save()
    
    print(f"Model: {config.model}")
    print(f"Permission mode: {config.permission_mode}")
    print(f"Always allow: {config.always_allow}")


def environment_variables():
    """Configuration via environment variables."""
    # Set API key
    os.environ["ANTHROPIC_API_KEY"] = "sk-..."
    
    # Set model
    os.environ["CLAUDE_MODEL"] = "claude-sonnet-4-20250514"
    
    # Set provider
    os.environ["CLAUDE_API_PROVIDER"] = "anthropic"
    
    # Set permission mode
    os.environ["CLAUDE_PERMISSION_MODE"] = "auto"
    
    # Load config (automatically picks up env vars)
    config = get_config()
    config.update_from_env()
    
    print(f"Loaded from env: API key set = {bool(config.api_key)}")
    print(f"Model: {config.model}")


def local_settings():
    """Per-project local settings."""
    # Local settings are stored in .claude-code-python.json
    local = LocalSettings(working_dir="/path/to/project")
    
    # Configure for this project
    local.permission_mode = "auto"
    local.always_allow = [
        "bash git *",          # Allow git commands
        "read src/*",          # Read from src directory
    ]
    
    # Add project-specific directories to scan
    local.additional_directories = [
        "/path/to/shared/library",
    ]
    
    # Save local settings
    local.save()
    
    print(f"Local settings for: {local.working_directory}")
    print(f"Permission mode: {local.permission_mode}")


def permission_modes():
    """Different permission modes explained."""
    
    # Default mode - asks before each tool
    default_config = Config()
    default_config.permission_mode = PermissionMode.DEFAULT
    
    # Auto mode - auto-approves based on rules
    auto_config = Config()
    auto_config.permission_mode = PermissionMode.AUTO
    auto_config.always_allow = [
        "bash ls *",
        "bash pwd",
        "read *",
        "glob *",
    ]
    
    # Plan mode - always asks
    plan_config = Config()
    plan_config.permission_mode = PermissionMode.PLAN
    
    # Bypass mode - no restrictions
    bypass_config = Config()
    bypass_config.permission_mode = PermissionMode.BYPASS
    
    print("Permission modes:")
    print(f"  Default: {PermissionMode.DEFAULT.value}")
    print(f"  Auto: {PermissionMode.AUTO.value}")
    print(f"  Plan: {PermissionMode.PLAN.value}")
    print(f"  Bypass: {PermissionMode.BYPASS.value}")


def permission_rules():
    """Permission rule syntax."""
    
    # Rules are in format: "tool_name pattern"
    
    rules = [
        # Allow all reads
        "read *",
        
        # Allow specific tool with any input
        "glob *",
        "grep *",
        
        # Allow bash with specific commands
        "bash ls *",
        "bash git status *",
        "bash git diff *",
        
        # Allow with input pattern
        "bash cat *",              # Any cat command
        "read *.py",               # Only Python files
    ]
    
    print("Permission rule examples:")
    for rule in rules:
        print(f"  {rule}")


if __name__ == "__main__":
    print("Configuration examples:")
    print("=" * 40)
    
    permission_modes()
