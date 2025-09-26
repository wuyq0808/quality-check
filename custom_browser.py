#!/usr/bin/env python3
"""
Custom AgentCore Browser that properly initializes Playwright
"""

from strands_tools.browser import AgentCoreBrowser
from strands_tools.browser.models import (
    InitSessionAction, BrowserSession, BrowserInput,
    ListLocalSessionsAction, NavigateAction, ClickAction,
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
import asyncio

logger = logging.getLogger(__name__)


class ClickCoordinateAction(BaseModel):
    """Action model for clicking at specific pixel coordinates"""
    type: Literal["click_coordinate"] = "click_coordinate"
    x: int  # X coordinate in pixels
    y: int  # Y coordinate in pixels
    session_name: str
    description: Optional[str] = "Click at coordinates"


class PressAndHoldAction(BaseModel):
    """Action model for pressing and holding at current mouse position"""
    type: Literal["press_and_hold"] = "press_and_hold"
    hold_time: float  # Hold duration in seconds
    session_name: str
    description: Optional[str] = "Press and hold mouse button at current position"


class HumanMouseAction(BaseModel):
    """Action model for human-like mouse movements and interactions"""
    type: Literal["human_mouse_move"] = "human_mouse_move"
    start_x: int  # Starting X coordinate
    start_y: int  # Starting Y coordinate
    end_x: int  # Ending X coordinate
    end_y: int  # Ending Y coordinate
    session_name: str
    description: Optional[str] = "Simulate human-like mouse movements and natural clicking"


class TypeWithKeyboardAction(BaseModel):
    """Action model for typing text using keyboard presses (no selector needed)"""
    type: Literal["type_with_keyboard"] = "type_with_keyboard"
    text: str  # Text to type using keyboard presses
    session_name: str
    description: Optional[str] = "Type text using keyboard presses"


class CustomBrowserInput(BaseModel):
    """Extended BrowserInput with custom coordinate click action"""
    action: Union[
        # All original actions from BrowserInput
        InitSessionAction,
        ListLocalSessionsAction,
        NavigateAction,
        ClickAction,
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
        # Our custom actions
        ClickCoordinateAction,
        PressAndHoldAction,
        HumanMouseAction,
        TypeWithKeyboardAction,
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

            # Only support Playwright browser sessions
            session_browser = session
            session_context = session_browser.contexts[0] if session_browser.contexts else await session_browser.new_context()

            # Get existing page or create new one
            pages = session_context.pages
            session_page = pages[0] if pages else await session_context.new_page()

            # Setup Chrome Linux browser emulation
            await self._setup_chrome_linux_browser(session_page)

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

    async def _setup_chrome_linux_browser(self, page):
        """Setup browser to mimic Chrome on Linux"""
        logger.info("Setting Chrome Linux headers...")
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        })

        logger.info("Overriding browser detection properties with evaluate...")
        await page.evaluate("""() => {
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // Override userAgent to match Chrome Linux
            Object.defineProperty(navigator, 'userAgent', {
                get: () => 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                configurable: true
            });

            // Override platform to match Linux
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Linux x86_64',
                configurable: true
            });
        }""")

        logger.info("Checking overridden browser properties...")
        browser_properties = await page.evaluate("""() => {
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                webdriver: navigator.webdriver
            };
        }""")
        logger.info("Browser properties after override:")
        for key, value in browser_properties.items():
            logger.info(f"  {key}: {value}")

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

        # CUSTOM OVERRIDE: Handle our custom actions
        if isinstance(action, ClickCoordinateAction):
            return self.click_coordinate(action)
        elif isinstance(action, PressAndHoldAction):
            return self.press_and_hold(action)
        elif isinstance(action, HumanMouseAction):
            return self.human_mouse_move(action)
        elif isinstance(action, TypeWithKeyboardAction):
            return self.type_with_keyboard(action)

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

    def press_and_hold(self, action: PressAndHoldAction) -> Dict[str, Any]:
        """Handle press and hold action"""
        return self._execute_async(self._async_press_and_hold(action))

    def human_mouse_move(self, action: HumanMouseAction) -> Dict[str, Any]:
        """Handle human-like mouse movements and interactions"""
        return self._execute_async(self._async_human_mouse_move(action))

    def type_with_keyboard(self, action: TypeWithKeyboardAction) -> Dict[str, Any]:
        """Handle typing with keyboard presses"""
        return self._execute_async(self._async_type_with_keyboard(action))

    async def _async_click_coordinate(self, action: ClickCoordinateAction) -> Dict[str, Any]:
        """Async click at specific pixel coordinates implementation"""
        session_name = action.session_name

        # Check if session exists
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()

            await page.mouse.click(action.x, action.y)
            logger.info(f"Clicked at coordinates ({action.x}, {action.y})")

            return {
                "status": "success",
                "content": [
                    {
                        "json": {
                            "action": "click_coordinate",
                            "coordinates": {"x": action.x, "y": action.y},
                            "sessionName": session_name
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to click at coordinates in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to click at coordinates: {str(e)}"}]}

    async def _async_press_and_hold(self, action: PressAndHoldAction) -> Dict[str, Any]:
        """Async press and hold at specific pixel coordinates implementation"""
        session_name = action.session_name

        # Check if session exists
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()

            # Press down, hold, then release
            await page.mouse.down()
            await asyncio.sleep(action.hold_time)
            await page.mouse.up()

            return {
                "status": "success",
                "content": [
                    {
                        "json": {
                            "action": "press_and_hold",
                            "holdTime": action.hold_time,
                            "sessionName": session_name
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to press and hold at coordinates in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to press and hold at coordinates: {str(e)}"}]}

    async def _async_human_mouse_move(self, action: HumanMouseAction) -> Dict[str, Any]:
        """Async human-like mouse movements and interactions implementation"""
        import math
        import random

        session_name = action.session_name

        # Check if session exists
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()

            # Hardcoded human-like behavior sequence
            # 1. Move naturally from start to end with curve
            await self._human_move_with_curve(page, action.start_x, action.start_y, action.end_x, action.end_y)

            # 2. Small pause after movement (human-like settling)
            await asyncio.sleep(random.uniform(0.1, 0.3))

            # 3. Small mouse movement after positioning (natural hand tremor)
            await asyncio.sleep(random.uniform(0.05, 0.1))
            await page.mouse.move(
                action.end_x + random.uniform(-2, 2),
                action.end_y + random.uniform(-2, 2)
            )

            return {
                "status": "success",
                "content": [
                    {
                        "json": {
                            "action": "human_mouse_move",
                            "start_coordinates": {"x": action.start_x, "y": action.start_y},
                            "end_coordinates": {"x": action.end_x, "y": action.end_y},
                            "sessionName": session_name
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to perform human mouse action in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to perform human mouse action: {str(e)}"}]}

    async def _human_move_with_curve(self, page, start_x, start_y, end_x, end_y):
        """Generate natural curved mouse movement from start to end"""
        import math
        import random

        # Calculate movement parameters
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        steps = max(8, int(distance / 10))

        # Create slight curve for natural movement
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2

        # Add perpendicular offset for curve
        if distance > 5:  # Only add curve for longer movements
            angle = math.atan2(end_y - start_y, end_x - start_x)
            curve_offset = distance * 0.2 * random.uniform(0.3, 0.8)
            ctrl_x = mid_x + math.cos(angle + math.pi/2) * curve_offset
            ctrl_y = mid_y + math.sin(angle + math.pi/2) * curve_offset
        else:
            ctrl_x, ctrl_y = mid_x, mid_y

        # Move in steps with variable timing
        for i in range(steps + 1):
            t = i / steps

            # Bezier curve calculation
            x = (1-t)**2 * start_x + 2*(1-t)*t * ctrl_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * ctrl_y + t**2 * end_y

            # Add micro-jitter
            x += random.uniform(-0.5, 0.5)
            y += random.uniform(-0.5, 0.5)

            await page.mouse.move(int(x), int(y))

            # Variable speed - slower at start/end
            speed_factor = 1 - abs(0.5 - t) * 0.4
            await asyncio.sleep(0.02 + speed_factor * 0.03)

    async def _async_list_tabs(self, action: ListTabsAction) -> Dict[str, Any]:
        """CUSTOM OVERRIDE: List tabs including untracked context pages"""
        session_name = action.session_name

        # Check if session exists
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()
            context = page.context

            # Wait and check for new pages multiple times
            for wait_round in range(5):  # Check 5 times over 5 seconds
                await page.wait_for_timeout(1000)

                all_pages = context.pages
                tracked_pages = set(session.tabs.values())

                # Add any untracked pages to session tabs
                for context_page in all_pages:
                    if context_page not in tracked_pages:
                        try:
                            new_title = await context_page.title()
                            new_tab_id = new_title
                        except Exception:
                            new_tab_id = f"tab_{len(session.tabs) + 1}"

                        session.add_tab(new_tab_id, context_page)
                        logger.info(f"Found untracked tab: '{new_tab_id}'")

            # Use original parent class logic
            tabs_info = {}
            for tab_id, page in session.tabs.items():
                try:
                    is_active = tab_id == session.active_tab_id
                    tabs_info[tab_id] = {"url": page.url, "active": is_active}
                except Exception as e:
                    tabs_info[tab_id] = {"error": f"Could not retrieve tab info: {str(e)}"}

            logger.info(f"Listed {len(session.tabs)} session tabs")

            import json
            return {"status": "success", "content": [{"text": json.dumps(tabs_info, indent=2)}]}

        except Exception as e:
            logger.error(f"failed to list tabs in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to list tabs: {str(e)}"}]}

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
                timeout=15000,  # 15 second timeout
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

    async def _async_type_with_keyboard(self, action: TypeWithKeyboardAction) -> Dict[str, Any]:
        """Async type with keyboard presses implementation"""
        session_name = action.session_name
        if session_name not in self._sessions:
            return {"status": "error", "content": [{"text": f"Session '{session_name}' not found"}]}

        try:
            session = self._sessions[session_name]
            page = session.get_active_page()

            for char in action.text:
                await page.keyboard.press(char)
                await asyncio.sleep(0.05)  # Small delay between key presses

            logger.info(f"Typed '{action.text}'")

            return {
                "status": "success",
                "content": [
                    {
                        "json": {
                            "action": "type_with_keyboard",
                            "text": action.text,
                            "sessionName": session_name
                        }
                    }
                ],
            }

        except Exception as e:
            logger.error(f"failed to type with keyboard in session {session_name}: {str(e)}")
            return {"status": "error", "content": [{"text": f"Failed to type with keyboard: {str(e)}"}]}

