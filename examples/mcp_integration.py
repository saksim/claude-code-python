"""
Example: MCP (Model Context Protocol) Integration
Shows how to connect to MCP servers.
"""

import asyncio
from claude_code.mcp import MCPClient, MCPManager


async def connect_to_filesystem_server():
    """Connect to a filesystem MCP server."""
    client = MCPClient("filesystem")
    
    # Connect using STDIO transport
    await client.connect_stdio(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."]
    )
    
    # List available tools
    tools = await client.list_tools()
    print("Available tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Call a tool
    result = await client.call_tool("list_directory", {".": "."})
    print(f"Directory contents: {result}")
    
    # Clean up
    await client.disconnect()


async def connect_to_http_server():
    """Connect to an HTTP-based MCP server."""
    client = MCPClient("http-server")
    
    # Connect using SSE transport
    await client.connect_sse(
        url="https://your-mcp-server.com/mcp",
        headers={"Authorization": "Bearer your-token"}
    )
    
    # Use the server
    tools = await client.list_tools()
    for tool in tools:
        print(f"  - {tool.name}")
    
    await client.disconnect()


async def manage_multiple_servers():
    """Manage multiple MCP server connections."""
    manager = MCPManager()
    
    # Add filesystem server
    fs = await manager.add_server(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."]
    )
    
    # Add custom server
    custom = await manager.add_server(
        name="custom",
        command="python",
        args=["/path/to/your/mcp/server.py"]
    )
    
    # Get tools from all servers
    all_tools = manager.get_all_tools()
    print("All available MCP tools:")
    for tool in all_tools:
        print(f"  - {tool['name']} (from {tool['server']})")
    
    # Use a specific server
    fs_client = manager.get_client("filesystem")
    if fs_client:
        await fs_client.list_tools()
    
    # Clean up all
    await manager.close_all()


async def create_mcp_server():
    """Example of creating a simple MCP server (for reference)."""
    # This shows what an MCP server implementation looks like
    # You would run this as a separate process
    
    """
    import asyncio
    import json
    from mcp.server import Server
    from mcp.types import Tool
    
    server = Server("my-server")
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="greet",
                description="Greet someone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name, arguments):
        if name == "greet":
            return f"Hello, {arguments['name']}!"
        raise ValueError(f"Unknown tool: {name}")
    
    async def main():
        async with server:
            await server.run(stdio)
    
    if __name__ == "__main__":
        asyncio.run(main())
    """
    pass


if __name__ == "__main__":
    print("MCP integration examples:")
    print("- connect_to_filesystem_server(): Connect to filesystem server")
    print("- manage_multiple_servers(): Manage multiple servers")
