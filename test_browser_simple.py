#!/usr/bin/env python3
"""
Simple browser test script - Direct Playwright browser usage
- Create browser session
- Navigate to booking.com using playwright browser directly
- Wait 1 minute
- Close session
"""

import asyncio
from strands_tools.browser import AgentCoreBrowser
from playwright.async_api import async_playwright

async def test_browser_session():
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

        print("🎭 Initializing Playwright...")
        async with async_playwright() as p:
            # Set playwright on the browser tool
            browser_tool._playwright = p

            print("🌐 Creating browser session...")
            playwright_browser = await browser_tool.create_browser_session()

            print("📄 Getting current page...")
            pages = playwright_browser.contexts[0].pages
            page = pages[0] if pages else await playwright_browser.contexts[0].new_page()

            print("🌐 Navigating to https://www.booking.com...")
            result = await page.goto("https://booking.com")
            print(f"Navigation result: {result}")

            print("📸 Taking initial screenshot...")
            await page.screenshot(path="booking_initial.png")
            print(f"Screenshot saved: booking_initial.png")

            print("🖱️ Clicking on 'Where are you going?' field at coordinates...")
            await page.mouse.click(360, 365)
            print("Clicked on destination input field at (360, 365)")

            print("⏳ Waiting 60 seconds...")
            await asyncio.sleep(60)  # Wait 1 minute

            print("📸 Taking final screenshot...")
            await page.screenshot(path="booking_after_wait.png")
            print(f"Final screenshot saved: booking_after_wait.png")

            print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error occurred: {e}")

    finally:
        print("🔚 Closing browser platform...")
        browser_tool.close_platform()

if __name__ == "__main__":
    asyncio.run(test_browser_session())