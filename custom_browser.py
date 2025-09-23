#!/usr/bin/env python3
"""
Custom AgentCore Browser that properly initializes Playwright
"""

from strands_tools.browser import AgentCoreBrowser
from strands_tools.browser.models import InitSessionAction, BrowserSession
from playwright.async_api import async_playwright, Browser as PlaywrightBrowser
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


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
