"""
Claude Code Python - Browser Tool
Browser automation using Playwright.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
- Enum for type safety
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

from claude_code.tools.base import Tool


class BrowserType(Enum):
    """Browser type enumeration.
    
    Attributes:
        CHROMIUM: Google Chromium browser
        FIREFOX: Mozilla Firefox browser
        WEBKIT: WebKit browser (Safari)
    """
    CHROMIUM = auto()
    FIREFOX = auto()
    WEBKIT = auto()


@dataclass(frozen=True, slots=True)
class BrowserConfig:
    """Browser configuration for automation.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        browser_type: Type of browser to use
        headless: Whether to run in headless mode
        viewport: Browser viewport dimensions (width, height)
        user_agent: Optional custom user agent string
        timeout: Default timeout in milliseconds
    """
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    viewport: tuple[int, int] = (1280, 720)
    user_agent: Optional[str] = None
    timeout: float = 30000


class BrowserTool(Tool):
    """Browser automation tool using Playwright.
    
    This tool provides browser automation capabilities including:
    - Navigation to URLs
    - Clicking elements
    - Typing text
    - Taking screenshots
    - Executing JavaScript
    - Getting page HTML
    
    Note: Requires playwright to be installed.
    
    Attributes:
        name: browser
        description: Automate browser actions (requires playwright)
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "browser"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Automate browser actions (requires playwright)"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "type", "screenshot", "evaluate", "get_html", "wait"],
                    "description": "Action to perform"
                },
                "url": {
                    "type": "string",
                    "description": "URL to navigate to (for navigate action)"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for click/type actions"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type into input field"
                },
                "script": {
                    "type": "string",
                    "description": "JavaScript code to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in milliseconds",
                    "default": 30000
                }
            },
            "required": ["action"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies browser state.
        
        Returns:
            False since browser actions navigate and interact with pages.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: Any,
        on_progress: Optional[Any] = None,
    ) -> Any:
        """Execute the browser automation action.
        
        Args:
            input_data: Dictionary with 'action' and action-specific parameters.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult or error dictionary.
        """
        action = input_data.get("action")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {"error": "Playwright not installed. Run: pip install playwright && playwright install"}
        
        config = BrowserConfig(headless=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=config.headless)
            page = await browser.new_page()
            
            try:
                if action == "navigate":
                    url = input_data.get("url")
                    if not url:
                        return {"error": "URL required for navigate"}
                    await page.goto(url)
                    return {"success": True, "url": page.url}
                
                elif action == "click":
                    selector = input_data.get("selector")
                    if not selector:
                        return {"error": "Selector required for click"}
                    await page.click(selector)
                    return {"success": True}
                
                elif action == "type":
                    selector = input_data.get("selector")
                    text = input_data.get("text", "")
                    if not selector:
                        return {"error": "Selector required for type"}
                    await page.fill(selector, text)
                    return {"success": True}
                
                elif action == "screenshot":
                    selector = input_data.get("selector")
                    path = input_data.get("path", "screenshot.png")
                    
                    if selector:
                        await page.locator(selector).screenshot(path=path)
                    else:
                        await page.screenshot(path=path)
                    
                    return {"success": True, "path": path}
                
                elif action == "evaluate":
                    script = input_data.get("script")
                    if not script:
                        return {"error": "Script required for evaluate"}
                    result = await page.evaluate(script)
                    return {"success": True, "result": result}
                
                elif action == "get_html":
                    selector = input_data.get("selector")
                    if selector:
                        html = await page.locator(selector).inner_html()
                    else:
                        html = await page.content()
                    return {"success": True, "html": html}
                
                elif action == "wait":
                    selector = input_data.get("selector")
                    timeout = input_data.get("timeout", 5000)
                    
                    if selector:
                        await page.wait_for_selector(selector, timeout=timeout)
                    return {"success": True}
                
                else:
                    return {"error": f"Unknown action: {action}"}
                    
            finally:
                await browser.close()


class BrowserContext:
    """Manages browser contexts."""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._page = None
        self._browser = None
    
    async def __aenter__(self):
        from playwright.async_api import async_playwright
        
        self._playwright = await async_playwright().start()
        
        if self.config.browser_type == BrowserType.CHROMIUM:
            self._browser = await self._playwright.chromium.launch(headless=self.config.headless)
        elif self.config.browser_type == BrowserType.FIREFOX:
            self._browser = await self._playwright.firefox.launch(headless=self.config.headless)
        else:
            self._browser = await self._playwright.webkit.launch(headless=self.config.headless)
        
        self._page = await self._browser.new_page(
            viewport={"width": self.config.viewport[0], "height": self.config.viewport[1]}
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    @property
    def page(self):
        return self._page


def create_browser_tool() -> BrowserTool:
    """Create browser tool."""
    return BrowserTool()


__all__ = [
    "BrowserTool",
    "BrowserConfig",
    "BrowserType",
    "BrowserContext",
    "create_browser_tool",
]
