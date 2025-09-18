#!/usr/bin/env python3
"""
Strands Agent with AgentCore Browser using Playwright WebSocket connection
This approach exposes the browser session via Playwright without passing tools directly to the agent
"""

from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.tools.browser_client import BrowserClient
from contextlib import contextmanager
from strands_tools.browser import AgentCoreBrowser
from playwright.sync_api import sync_playwright

# Configuration - matching strands_browser_direct.py
REGION = "us-east-1"  # Browser region
MODEL_REGION = "eu-west-1"  # Model region
BROWSER_ID = "recordingBrowserWithS3_20250916170045-Ec92oniUSi"

# Prompts
SYSTEM_PROMPT = """
You have direct access to browser tools. 
Use them to complete web navigation tasks.
After completing the task, you MUST close the browser session.
"""

USER_PROMPT = """For the Skyscanner hotels search task:
1. Navigate to skyscanner.com
2. Find and click the Hotels link/button to reach hotels page
3. Test the auto complete feature:

Auto-complete for destinations/hotels
Type in City name, does the main city destination show as the first results?
Type in City name check if relevant POI's show up; 
Type in City name check if POI's are all in the same language 
Type in City name with typo, check if it can handle typo and show the correct city name            
"""

@contextmanager
def browser_session_with_id(region: str, identifier: str):
    """Context manager for browser session with specific identifier"""
    client = BrowserClient(region)
    print(f"🔧 Browser client created for region: {region}")

    try:
        # Use the official pattern: pass identifier to start() method
        session_id = client.start(identifier=identifier, session_timeout_seconds=7200)
        print(f"🚀 Browser session started with identifier: {identifier}")
        print(f"📋 Session ID: {session_id}")
        yield client
    finally:
        try:
            client.stop()
            print("🔧 Browser session stopped")
        except Exception as e:
            print(f"⚠️ Error stopping session: {e}")

def create_browser_functions(page):
    """Create custom browser functions using Playwright page object"""
    from strands import tool

    @tool
    def navigate_to_url(url: str) -> str:
        """Navigate to a URL"""
        try:
            page.goto(url)
            return f"Successfully navigated to {url}"
        except Exception as e:
            return f"Error navigating to {url}: {str(e)}"

    @tool
    def click_element(selector: str) -> str:
        """Click an element by CSS selector"""
        try:
            page.click(selector)
            return f"Successfully clicked element: {selector}"
        except Exception as e:
            return f"Error clicking element {selector}: {str(e)}"

    @tool
    def type_text(selector: str, text: str) -> str:
        """Type text into an input field"""
        try:
            page.fill(selector, text)
            return f"Successfully typed '{text}' into {selector}"
        except Exception as e:
            return f"Error typing into {selector}: {str(e)}"

    @tool
    def get_page_title() -> str:
        """Get the current page title"""
        try:
            title = page.title()
            return f"Page title: {title}"
        except Exception as e:
            return f"Error getting page title: {str(e)}"

    @tool
    def take_screenshot(filename: str = "screenshot.png") -> str:
        """Take a screenshot of the current page"""
        try:
            page.screenshot(path=filename)
            return f"Screenshot saved as {filename}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"

    @tool
    def wait_for_element(selector: str, timeout: int = 5000) -> str:
        """Wait for an element to appear"""
        try:
            page.wait_for_selector(selector, timeout=timeout)
            return f"Element {selector} is now visible"
        except Exception as e:
            return f"Error waiting for element {selector}: {str(e)}"

    @tool
    def get_element_text(selector: str) -> str:
        """Get text content of an element"""
        try:
            text = page.text_content(selector)
            return f"Element text: {text}"
        except Exception as e:
            return f"Error getting text from {selector}: {str(e)}"

    return [navigate_to_url, click_element, type_text, get_page_title, take_screenshot,
            wait_for_element, get_element_text]

def run_agent_with_playwright():
    """Execute browser automation using Playwright connected to AgentCore browser session"""

    print("🔧 Initializing browser session with specific BROWSER_ID...")

    # Use custom context manager with specific BROWSER_ID
    with browser_session_with_id(REGION, BROWSER_ID) as client:
        # Generate WebSocket URL and headers
        ws_url, headers = client.generate_ws_headers()
        print(f"📡 WebSocket URL generated: {ws_url[:50]}...")
        print(f"🔑 Headers: {list(headers.keys())}")

        # Use Playwright to connect to the AgentCore browser
        with sync_playwright() as p:
            print("🎭 Connecting Playwright to AgentCore browser...")

            # Connect to browser using CDP over WebSocket
            browser = p.chromium.connect_over_cdp(ws_url, headers=headers)
            print("✅ Playwright connected to AgentCore browser!")

            # Get or create context and page
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            print("📄 Browser page ready!")

            # Create Bedrock model for the agent
            bedrock_model = BedrockModel(
                model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0",
                region_name=MODEL_REGION
            )

            # Create browser functions using AgentCore pattern
            browser_functions = create_browser_functions(page)

            # Create Strands agent with browser functions
            agent = Agent(
                name="BrowserTestAgent",
                model=bedrock_model,
                system_prompt=SYSTEM_PROMPT,
                tools=browser_functions  # Pass AgentCore browser tools
            )

            print("🤖 Created Strands agent with AgentCore browser tools")

            # Execute the browser automation task
            print("🔍 Executing task through Strands agent...")
            result = agent(USER_PROMPT)

            print("✅ Task completed successfully!")

            # Close browser
            browser.close()
            print("🔧 Browser closed")

            return str(result)

def main():
    """Main execution function"""
    print("🎯 Starting Skyscanner Auto-Complete Testing with Playwright...")
    print("=" * 60)

    try:
        result = run_agent_with_playwright()

        print("\n" + "=" * 60)
        print("🎉 EXECUTION RESULT:")
        print(result)

        print("\n🎉 SUCCESS: Browser automation with Playwright context manager completed!")

    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()