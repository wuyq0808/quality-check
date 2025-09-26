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
import os
from strands_tools.browser import AgentCoreBrowser
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

def setup_chrome_linux_browser(browser_tool, page):
    """Setup browser to mimic Chrome on Linux"""
    print("🐧 Setting Chrome Linux headers...")
    browser_tool._execute_async(page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    }))

    print("🎭 Overriding browser detection properties with evaluate...")
    browser_tool._execute_async(page.evaluate("""() => {
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
    }"""))

    print("Checking overridden browser properties...")
    browser_properties = browser_tool._execute_async(page.evaluate("""() => {
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            webdriver: navigator.webdriver
        };
    }"""))
    print("Browser properties after override:")
    for key, value in browser_properties.items():
        print(f"  {key}: {value}")

def test_browser_session():
    """Test basic browser session lifecycle with direct Playwright browser"""

    # Create screenshots directory
    screenshots_dir = "test_browser_simple_screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

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

        # Setup Chrome Linux browser emulation
        setup_chrome_linux_browser(browser_tool, page)

        print("🌐 Navigating to Google Travel...")
        result = browser_tool._execute_async(page.goto("https://www.google.com/travel/search"))
        print(f"Navigation result: {result}")
        browser_tool._execute_async(asyncio.sleep(3))  # Wait 3 seconds

        print("📸 Taking screenshot...")
        browser_tool._execute_async(page.screenshot(path="test_browser_simple_screenshots/google_travel_screenshot.png"))
        print(f"Screenshot saved: test_browser_simple_screenshots/google_travel_screenshot.png")

        print("⏳ Waiting 10 seconds before clicking...")
        browser_tool._execute_async(asyncio.sleep(10))

        print("🖱️ Clicking cross (X) button to clear search...")
        browser_tool._execute_async(page.mouse.click(174, 80))  # Click at X button coordinates
        print("Cross button clicked")

        print("⏳ Waiting 5 seconds after click...")
        browser_tool._execute_async(asyncio.sleep(5))

        # Test keyboard methods with different letters
        print("⌨️ Testing keyboard methods...")

        # Method 1: keyboard.down() and keyboard.up()
        print("1. Using keyboard.down()/up() - typing 'M'")
        browser_tool._execute_async(page.keyboard.down("M"))
        browser_tool._execute_async(page.keyboard.up("M"))
        browser_tool._execute_async(asyncio.sleep(2))

        # Method 2: keyboard.press() with single letters
        print("2. Using keyboard.press() - pressing 'N' then 'P'")
        browser_tool._execute_async(page.keyboard.press("N"))
        browser_tool._execute_async(page.keyboard.press("P"))
        browser_tool._execute_async(asyncio.sleep(2))

        print("Keyboard methods tested!")

        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error occurred: {e}")

    finally:
        print("🔚 Closing browser platform...")
        browser_tool.close_platform()

if __name__ == "__main__":
    test_browser_session()