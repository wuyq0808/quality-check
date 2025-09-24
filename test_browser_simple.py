#!/usr/bin/env python3
"""
Simple browser test script - Direct Playwright browser usage
- Create browser session
- Navigate to Google Travel Hotels using playwright browser directly
- Wait 1 minute
- Close session
"""

import asyncio
import logging
from strands_tools.browser import AgentCoreBrowser
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

def test_browser_session():
    """Test basic browser session lifecycle with direct Playwright browser"""

    # Configure browser tool with AgentCore
    custom_browser_id = "recordingBrowserWithS3_20250916170045-Ec92oniUSi"
    browser_tool = AgentCoreBrowser(
        region='us-east-1',
        identifier=custom_browser_id,
        session_timeout=900,  # 15 minutes
    )

    try:
        print("🚀 Starting browser platform...")
        browser_tool.start_platform()

        print("🎭 Calling parent _start() to initialize Playwright...")
        browser_tool._start()

        print("🌐 Creating browser session...")
        playwright_browser = browser_tool._execute_async(browser_tool.create_browser_session())

        print("📄 Getting current page...")
        pages = playwright_browser.contexts[0].pages
        page = pages[0] if pages else browser_tool._execute_async(playwright_browser.contexts[0].new_page())

        print("🌐 Navigating to https://www.google.com/travel/hotels...")
        result = browser_tool._execute_async(page.goto("https://www.google.com/travel/hotels"))
        print(f"Navigation result: {result}")
        browser_tool._execute_async(asyncio.sleep(5))  # Wait 5 seconds

        print("📸 Taking initial screenshot...")
        browser_tool._execute_async(page.screenshot(path="google_travel_initial.png"))
        print(f"Screenshot saved: google_travel_initial.png")
        browser_tool._execute_async(asyncio.sleep(5))  # Wait 5 seconds

        print("🖱️ Clicking on destination input field...")
        browser_tool._execute_async(page.mouse.click(95, 50))
        print("Clicked on destination input field at (95, 50)")
        browser_tool._execute_async(asyncio.sleep(5))  # Wait 5 seconds

        print("📸 Taking screenshot after click...")
        browser_tool._execute_async(page.screenshot(path="google_travel_after_click.png"))
        print(f"Screenshot saved: google_travel_after_click.png")
        browser_tool._execute_async(asyncio.sleep(5))  # Wait 5 seconds

        print("⌨️ Filling input with 'A' using page.fill()...")
        browser_tool._execute_async(page.fill('input[placeholder="Search for places, hotels and more"]', "ABCD 1234"))
        print("Filled 'A' using page.fill()")
        browser_tool._execute_async(asyncio.sleep(5))  # Wait 5 seconds

        print("📸 Taking final screenshot...")
        browser_tool._execute_async(page.screenshot(path="google_travel_after_wait.png"))
        print(f"Final screenshot saved: google_travel_after_wait.png")

        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error occurred: {e}")

    finally:
        print("🔚 Closing browser platform...")
        browser_tool.close_platform()

if __name__ == "__main__":
    test_browser_session()