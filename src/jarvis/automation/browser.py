"""Browser automation using Playwright."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


class BrowserAutomation:
    """Browser automation engine using Playwright."""

    def __init__(self):
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    async def initialize(self) -> None:
        """Launch browser instance."""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=False)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            logger.info("Browser automation initialized")
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install")

    async def navigate(self, url: str) -> dict:
        """Navigate to a URL."""
        if not self._page:
            return {"error": "Browser not initialized"}
        await self._page.goto(url, wait_until="domcontentloaded")
        return {"url": self._page.url, "title": await self._page.title()}

    async def click(self, selector: str) -> dict:
        """Click an element."""
        if not self._page:
            return {"error": "Browser not initialized"}
        await self._page.click(selector)
        return {"status": "clicked", "selector": selector}

    async def type_text(self, selector: str, text: str) -> dict:
        """Type text into an input."""
        if not self._page:
            return {"error": "Browser not initialized"}
        await self._page.fill(selector, text)
        return {"status": "typed", "selector": selector}

    async def screenshot(self, path: str = "screenshot.png") -> dict:
        """Take a screenshot."""
        if not self._page:
            return {"error": "Browser not initialized"}
        await self._page.screenshot(path=path)
        return {"status": "captured", "path": path}

    async def get_text(self, selector: str = "body") -> str:
        """Get text content of an element."""
        if not self._page:
            return ""
        return await self._page.text_content(selector) or ""

    async def execute_js(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        if not self._page:
            return None
        return await self._page.evaluate(script)

    async def close(self) -> None:
        """Close browser."""
        if self._browser:
            await self._browser.close()
        if hasattr(self, "_playwright"):
            await self._playwright.stop()
