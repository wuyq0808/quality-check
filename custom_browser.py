#!/usr/bin/env python3
"""
Custom AgentCore Browser that properly initializes Playwright
"""

from strands_tools.browser import AgentCoreBrowser
from strands_tools.browser.models import (
    InitSessionAction, BrowserSession, BrowserInput,
    ListLocalSessionsAction, NavigateAction, ClickAction, TypeAction,
    EvaluateAction, PressKeyAction, GetTextAction, GetHtmlAction,
    ScreenshotAction, RefreshAction, BackAction, ForwardAction,
    NewTabAction, SwitchTabAction, CloseTabAction, ListTabsAction,
    GetCookiesAction, SetCookiesAction, NetworkInterceptAction,
    ExecuteCdpAction, CloseAction
)
from playwright.async_api import async_playwright, Browser as PlaywrightBrowser
from typing import Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from strands import tool
import logging
import base64
import os

logger = logging.getLogger(__name__)


class ClickCoordinateAction(BaseModel):
    """Action model for clicking at specific pixel coordinates"""
    type: Literal["click_coordinate"] = "click_coordinate"
    x: int  # X coordinate in pixels
    y: int  # Y coordinate in pixels
    session_name: str
    description: Optional[str] = "Click at coordinates"


class CustomBrowserInput(BaseModel):
    """Extended BrowserInput with custom coordinate click action"""
    action: Union[
        # All original actions from BrowserInput
        InitSessionAction,
        ListLocalSessionsAction,
        NavigateAction,
        ClickAction,
        TypeAction,
        EvaluateAction,
        PressKeyAction,
        GetTextAction,
        GetHtmlAction,
        ScreenshotAction,
        RefreshAction,
        BackAction,
        ForwardAction,
        NewTabAction,
        SwitchTabAction,
        CloseTabAction,
        ListTabsAction,
        GetCookiesAction,
        SetCookiesAction,
        NetworkInterceptAction,
        ExecuteCdpAction,
        CloseAction,
        # Our custom action
        ClickCoordinateAction,
    ] = Field(discriminator="type")
    wait_time: Optional[int] = Field(default=2, description="Time to wait after action in seconds")


class CustomAgentCoreBrowser(AgentCoreBrowser):
    """Custom AgentCoreBrowser with overridden session initialization"""

    async def _async_init_session(self, action: InitSessionAction) -> Dict[str, Any]:
        """Async initialize session implementation."""
        logger.info(f"initializing browser session: {action.description}")

        session_name = action.session_name

        # Check if session already exists
        if session_name in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' already exists"}]}

        try:
            # Create new browser instance for this session
            session = await self.create_browser_session()

            if isinstance(session, PlaywrightBrowser):
                # Normal non-persistent case
                session_browser = session
                session_context = session_browser.contexts[0] if session_browser.contexts else await session_browser.new_context()

                # CUSTOM OVERRIDE: Get existing page or create new one (instead of always creating new)
                pages = session_context.pages
                session_page = pages[0] if pages else await session_context.new_page()
            else:
                # Persistent context case
                session_context = session
                session_browser = session_context.browser
                session_page = await session_context.new_page()

            # Create and store session object
            session = BrowserSession(
                session_name=session_name,
                description=action.description,
                browser=session_browser,
                context=session_context,
                page=session_page,
            )
            session.add_tab("main", session_page)

            self._sessions[session_name] = session

            logger.info(f"initialized session: {session_name}")

            return {
                "status": "success",
                "content": [
                    {
                        "json": {
                            "sessionName": session_name,
                            "description": action.description,
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to initialize session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to initialize session: {str(e)}"}]}

    @tool
    def browser(self, browser_input: CustomBrowserInput) -> Dict[str, Any]:
        """CUSTOM OVERRIDE: Handle coordinate click actions + standard browser actions"""
        # Auto-start platform on first use
        if not self._started:
            self._start()

        if isinstance(browser_input, dict):
            action = CustomBrowserInput.model_validate(browser_input).action
        else:
            action = browser_input.action

        # CUSTOM OVERRIDE: Handle our coordinate click action
        if isinstance(action, ClickCoordinateAction):
            return self.click_coordinate(action)

        # Delegate all other actions to parent class
        # Convert back to original BrowserInput for parent compatibility
        original_browser_input = BrowserInput(
            action=action,
            wait_time=browser_input.wait_time if not isinstance(browser_input, dict) else browser_input.get("wait_time", 2)
        )
        return super().browser(original_browser_input)

    def click_coordinate(self, action: ClickCoordinateAction) -> Dict[str, Any]:
        """Handle coordinate click action"""
        return self._execute_async(self._async_click_coordinate(action))

    async def _async_click_coordinate(self, action: ClickCoordinateAction) -> Dict[str, Any]:
        """Async click at specific pixel coordinates implementation"""
        session_name = action.session_name

        # Check if session exists
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()

            # Track number of pages before click to detect new tabs
            context = page.context
            pages_before = len(context.pages)

            # CUSTOM OVERRIDE: Click at pixel coordinates using page.mouse.click like test_browser_simple.py
            await page.mouse.click(action.x, action.y)

            # Wait a moment for potential new tab to open
            await page.wait_for_timeout(1000)

            # Check if new tab/page opened
            pages_after = context.pages
            new_tab_id = None
            if len(pages_after) > pages_before:
                # New tab opened, add it to session and make it active
                new_page = pages_after[-1]  # Last opened page
                new_tab_id = f"tab_{len(session.tabs) + 1}"
                session.add_tab(new_tab_id, new_page)
                logger.info(f"New tab detected and added: {new_tab_id}")

            return {
                "status": "success",
                "content": [
                    {
                        "json": {
                            "action": "click_coordinate",
                            "coordinates": {"x": action.x, "y": action.y},
                            "sessionName": session_name,
                            "newTabDetected": len(pages_after) > pages_before,
                            "newTabId": new_tab_id
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to click at coordinates in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to click at coordinates: {str(e)}"}]}

    async def _async_screenshot(self, action: ScreenshotAction) -> Dict[str, Any]:
        """CUSTOM OVERRIDE: Take screenshot and return base64 image data for LLM vision"""
        session_name = action.session_name

        # Check if session exists
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()

            # Take PNG screenshot with timeout and skip font/animation waits
            screenshot_bytes = await page.screenshot(
                type='png',
                timeout=10000,  # 10 second timeout
                animations='disabled'  # Skip animation/font waits
            )

            # Use raw bytes directly as shown in AWS documentation
            return {
                "status": "success",
                "content": [
                    {
                        "image": {
                            "format": 'png',
                            "source": {
                                "bytes": screenshot_bytes  # Raw bytes directly
                            }
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to take screenshot in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to take screenshot: {str(e)}"}]}
