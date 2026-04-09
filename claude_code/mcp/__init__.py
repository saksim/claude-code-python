"""MCP module."""

from claude_code.services.mcp.client import (
    MCPClient, MCPManager, MCPConnectionConfig,
    MCPTool, MCPResource, MCPConnectionState,
    MCPTransportType, MCPProtocol,
    MCPAuthType, MCPOAuthConfig, MCPAuthToken,
    MCPTransport, MCPStdIOTransport, MCPHTTPTransport, MCPWebSocketTransport,
)

from claude_code.mcp.server import (
    MCPServer,
    MCPServerConfig,
    MCPProtocolHandler,
    create_mcp_server,
    run_mcp_server,
)

__all__ = [
    # Client
    "MCPClient",
    "MCPManager", 
    "MCPConnectionConfig",
    "MCPTool",
    "MCPResource",
    "MCPConnectionState",
    "MCPTransportType",
    "MCPProtocol",
    "MCPAuthType",
    "MCPOAuthConfig",
    "MCPAuthToken",
    # Transports
    "MCPTransport",
    "MCPStdIOTransport",
    "MCPHTTPTransport",
    "MCPWebSocketTransport",
    # Server
    "MCPServer",
    "MCPServerConfig",
    "MCPProtocolHandler",
    "create_mcp_server",
    "run_mcp_server",
]
